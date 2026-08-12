#!/usr/bin/env python3
"""Mirror mimugarten.nl into static HTML: localize assets, strip WP/Elementor JS, keep visual CSS."""
from __future__ import annotations

import hashlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://mimugarten.nl"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

CDN_HOSTS = (
    "mimugarten.nl",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
)
KEEP_EXTERNAL_SCRIPT = (
    "cdn-cookieyes.com",
    "googletagmanager.com",
    "assets.calendly.com",
)
LOCALIZE_PREFIXES = ("/wp-content/", "/wp-includes/")

asset_map: dict[str, str] = {}


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


ASSET_EXTENSIONS = (
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".avif", ".woff", ".woff2", ".ttf", ".otf", ".eot",
)


def should_localize(url: str) -> bool:
    if not url or url.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
        return False
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path = urllib.parse.unquote(parsed.path)
    lower = path.lower()

    if host in ("fonts.googleapis.com", "fonts.gstatic.com"):
        return True

    if host.endswith("mimugarten.nl") or not host:
        if any(lower.startswith(p) for p in LOCALIZE_PREFIXES):
            return True
        if lower.endswith(ASSET_EXTENSIONS):
            return True
        return False

    return False


def local_rel_for(url: str) -> str:
    if url in asset_map:
        return asset_map[url]
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)
    name = Path(path).name or "asset"
    name = re.sub(r"[^A-Za-z0-9._+-]+", "_", name)
    ext = Path(name).suffix.lower()
    if not ext:
        if "css" in url:
            ext = ".css"
        elif "woff2" in url:
            ext = ".woff2"
        elif "woff" in url:
            ext = ".woff"
        elif ".js" in url:
            ext = ".js"
        else:
            ext = ""
        if ext and not name.endswith(ext):
            name += ext
    if ext == ".css" or name.endswith(".css"):
        folder = "assets/css"
    elif ext in {".woff", ".woff2", ".ttf", ".otf", ".eot"}:
        folder = "assets/fonts"
    elif ext in {".js", ".mjs"}:
        folder = "assets/js"
    elif ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".avif"}:
        folder = "assets/img"
    else:
        folder = "assets/misc"
    digest = hashlib.md5(url.encode()).hexdigest()[:8]
    stem = Path(name).stem[:80]
    suffix = Path(name).suffix or ext
    local = f"{folder}/{stem}_{digest}{suffix}"
    asset_map[url] = "/" + local
    return asset_map[url]


def abs_url(url: str, base: str = BASE) -> str:
    return urllib.parse.urljoin(base, url)


def download_asset(url: str) -> str | None:
    url = abs_url(url.split("#")[0])
    url = url.replace("&amp;", "&")
    if not should_localize(url):
        return None
    local_abs = local_rel_for(url)
    dest = ROOT / local_abs.lstrip("/")
    if dest.exists() and dest.stat().st_size > 0:
        return local_abs
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = http_get(url)
        dest.write_bytes(data)
        print(f"  asset {len(data):7d} {local_abs}")
        if local_abs.endswith(".css"):
            css = data.decode("utf-8", errors="replace")
            dest.write_text(localize_css(css, url), encoding="utf-8")
        return local_abs
    except Exception as e:
        print(f"  FAIL {url} -> {e}")
        return None


def localize_css(css: str, css_url: str) -> str:
    def repl(m: re.Match[str]) -> str:
        raw = m.group(1).strip("'\"")
        if raw.startswith("data:"):
            return m.group(0)
        u = abs_url(raw, css_url)
        if not should_localize(u):
            return m.group(0)
        local = download_asset(u)
        return f'url("{local}")' if local else m.group(0)

    css = re.sub(r"url\(([^)]+)\)", repl, css)
    css = re.sub(r"font-display:\s*block", "font-display:swap", css)
    return css


def fetch_pages() -> list[str]:
    xml = http_get(BASE + "/page-sitemap.xml").decode("utf-8", errors="replace")
    root = ET.fromstring(xml)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    pages: set[str] = set()
    for loc in root.findall(".//sm:loc", ns):
        if loc.text is None:
            continue
        path = urllib.parse.urlparse(loc.text).path or "/"
        if "/wp-content/" in path:
            continue
        if not path.endswith("/"):
            path = path.rstrip("/") + "/"
        pages.add(path if path != "//" else "/")
    return sorted(pages, key=lambda p: (p.count("/"), p))


def path_to_href(path: str) -> str:
    path = path.split("?")[0].split("#")[0]
    if re.search(r"\.[a-z0-9]{2,5}$", path, re.I):
        return path if path.startswith("/") else "/" + path
    if path in ("", "/"):
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path += "/"
    return path


def page_outfile(path: str) -> Path:
    path = path_to_href(path)
    if path == "/":
        return ROOT / "index.html"
    parts = path.strip("/").split("/")
    return ROOT / Path(*parts) / "index.html"


def rewrite_hrefs(html: str) -> str:
    def repl(m: re.Match[str]) -> str:
        attr, href = m.group(1), m.group(2)
        href = href.replace("&amp;", "&")
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            return m.group(0)
        if href.startswith("/configurator"):
            return m.group(0)
        for prefix in (BASE, "http://mimugarten.nl", "https://www.mimugarten.nl"):
            if href.startswith(prefix):
                p = urllib.parse.urlparse(href).path or "/"
                q = urllib.parse.urlparse(href).query
                new = path_to_href(p)
                if q:
                    new += "?" + q
                return f'{attr}="{new}"'
        if href.startswith("/") and not href.startswith("//"):
            p = urllib.parse.urlparse(href).path or "/"
            q = urllib.parse.urlparse(href).query
            new = path_to_href(p)
            if q:
                new += "?" + q.split("&utm_")[0]  # strip tracking params on lang links
            return f'{attr}="{new}"'
        return m.group(0)

    html = re.sub(r'(href|action)=["\']([^"\']+)["\']', repl, html)
    return html


def localize_html_urls(html: str) -> str:
    def repl(m: re.Match[str]) -> str:
        prefix, url = m.group(1), m.group(2)
        url = url.replace("&amp;", "&")
        if not should_localize(url):
            return m.group(0)
        local = download_asset(url)
        return f"{prefix}{local}" if local else m.group(0)

    html = re.sub(
        r'((?:href|src|data-src|poster|content)=["\']|url\(["\']?)(https?://[^"\'\)\s>]+)',
        repl,
        html,
        flags=re.I,
    )
    html = re.sub(
        r'((?:href|src)=["\'])(/wp-[^"\']+)',
        repl,
        html,
        flags=re.I,
    )

    def srcset_repl(m: re.Match[str]) -> str:
        parts = []
        for part in m.group(1).split(","):
            bits = part.strip().split()
            if not bits:
                continue
            u, rest = bits[0], " ".join(bits[1:])
            u = u.replace("&amp;", "&")
            if should_localize(u):
                local = download_asset(u)
                if local:
                    u = local
            parts.append((u + (" " + rest if rest else "")).strip())
        return 'srcset="' + ", ".join(parts) + '"'

    html = re.sub(r'srcset=["\']([^"\']+)["\']', srcset_repl, html, flags=re.I)
    return promote_lazy_images(html)


def promote_lazy_images(html: str) -> str:
    def fix_img(m: re.Match[str]) -> str:
        tag = m.group(0)
        if re.search(r"\ssrc=", tag):
            return tag
        dm = re.search(r'\sdata-src="([^"]*)"', tag)
        if dm:
            return re.sub(r"<img\b", f'<img src="{dm.group(1)}"', tag, count=1)
        return tag

    return re.sub(r"<img\b[^>]*>", fix_img, html, flags=re.I)


def strip_wp_js(html: str) -> str:
    def keep_script(tag: str) -> bool:
        if any(h in tag for h in KEEP_EXTERNAL_SCRIPT):
            return True
        if re.search(r"gtag\s*\(", tag):
            return True
        if "static-interactions.js" in tag or "swiper.min.js" in tag:
            return True
        return False

    def script_repl(m: re.Match[str]) -> str:
        return m.group(0) if keep_script(m.group(0)) else ""

    html = re.sub(r"<script\b[\s\S]*?</script>", script_repl, html, flags=re.I)
    html = re.sub(r"<script\b[^>]*/>", script_repl, html, flags=re.I)
    html = re.sub(r'<link[^>]+as=["\']script["\'][^>]*>', "", html, flags=re.I)
    return html


def strip_wp_head_noise(html: str) -> str:
    patterns = [
        r'<link[^>]+rel=["\']alternate["\'][^>]+type=["\']application/rss\+xml["\'][^>]*>',
        r'<link[^>]+rel=["\']alternate["\'][^>]+oembed[^>]*>',
        r'<link[^>]+rel=["\']alternate["\'][^>]+type=["\']application/json[^>]*>',
        r'<link[^>]+rel=["\']https://api\.w\.org/["\'][^>]*>',
        r'<link[^>]+rel=["\']EditURI["\'][^>]*>',
        r'<link[^>]+rel=["\']shortlink["\'][^>]*>',
        r'<link[^>]+href=["\'][^"\']*xmlrpc\.php[^"\']*["\'][^>]*>',
        r'<meta[^>]+name=["\']generator["\'][^>]*>',
    ]
    for pat in patterns:
        html = re.sub(pat, "", html, flags=re.I)
    return strip_elementor_lazy_bg(html)


def strip_elementor_lazy_bg(html: str) -> str:
    """Elementor hides lazy backgrounds without frontend JS; show them on static pages."""
    return re.sub(
        r"<style>\s*\.e-con\.e-parent:nth-of-type\(n\+4\)[\s\S]*?</style>\s*",
        "",
        html,
        flags=re.I,
    )


def fix_canonical(html: str, path: str) -> str:
    canon = BASE + path_to_href(path)
    if re.search(r'rel=["\']canonical["\']', html, re.I):
        html = re.sub(
            r'<link[^>]+rel=["\']canonical["\'][^>]*>',
            f'<link rel="canonical" href="{canon}">',
            html,
            count=1,
            flags=re.I,
        )
    return html


STATIC_OVERRIDES = '<link rel="stylesheet" href="/assets/css/static-overrides.css">'
STATIC_SCRIPTS = (
    '<script src="/assets/js/swiper.min.js" defer></script>\n'
    '<script src="/assets/js/static-interactions.js" defer></script>'
)

CONFIGURATOR_DE = "https://mimugarten.nl/configurator/?lang=de"
CONFIGURATOR_NL = "https://mimugarten.nl/configurator/?lang=nl"
WHATSAPP_HREF = "https://wa.me/31627557231"

LANG_SWITCHER_RE = re.compile(
    r'<nav\s+class="trp-language-switcher[\s\S]*?</nav>',
    re.I,
)
SOCIAL_ICONS_RE = re.compile(
    r'<div class="elementor-social-icons-wrapper elementor-grid" role="list">[\s\S]*?</div>',
    re.I,
)
HEADER_ACTIONS_RE = re.compile(
    r'\s*<div class="mimu-header-actions">[\s\S]*?</div>\s*',
    re.I,
)
HEADER_ACTIONS_INSERT_RE = re.compile(
    r'(data-id="f71a76a"[\s\S]*?</div>\s*\n)(\t\t\t\t\t</div>\s*\n\t\t\t\t</div>\s*\n\t\t\t\t</header>)',
    re.I,
)

WHATSAPP_ICON_SVG = (
    '<svg aria-hidden="true" viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg">'
    '<path fill="currentColor" d="M380.9 97.1C339 55.2 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 '
    "0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 0 224.1-99.6 "
    "224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.7l-6.7-4-69.8 18.3L72 "
    "359.2l-4.4-7c-18.5-29.4-28.2-63.3-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 0 95.6 19.2 "
    "130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.2-37.9-18-5.1-1.9-8.8-2.8-12.5 2.8-3.7 5.1-14.4 18-17.6 21.8-3.2 3.7-6.5 4.2-12 1.4-32.6-16.3-54-29.1-75.5-66-5.7-9.8 5.7-9.1 16.3-30.1 1.8-3.7.9-6.9-.5-9.7-1.4-2.8-12.5-30.1-17.1-41.2-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3 0 27.3 19.9 53.7 22.6 57.4 2.8 3.7 39.1 59.7 94.8 83.8 35.2 15.2 49 16.5 66.6 13.9 10.7-1.6 32.8-13.4 37.4-26.4 4.6-13 4.6-24.1 3.2-26.4-1.3-2.5-5-3.9-10.5-6.6z\"/>"
    "</svg>"
)


def build_inline_lang_switcher(lang_nav: str, nl: bool) -> str:
    code = "DE" if nl else "NL"
    aria = "Deutsch" if nl else "Nederlands"
    html = re.sub(r'\s*style="[^"]*"', "", lang_nav)
    html = html.replace("trp-floating-switcher", "")
    html = html.replace("trp-switcher-position-top", "")
    html = re.sub(
        r'class="trp-language-switcher([^"]*)"',
        r'class="trp-language-switcher mimu-lang-switcher trp-ls-inline\1"',
        html,
        count=1,
    )
    if "mimu-lang-label" not in html:
        html = re.sub(
            r'(<a href="[^"]+" class="trp-language-item"[^>]*>[\s\S]*?)(</a>)',
            rf'\1<span class="mimu-lang-label">{code}</span>\2',
            html,
            count=1,
        )
    html = re.sub(
        r'(<a href="[^"]+" class="trp-language-item"[^>]*)(>)',
        rf'\1 aria-label="{aria}"\2',
        html,
        count=1,
    )
    return html


def build_header_actions(nl: bool, social_inner: str, lang_nav: str) -> str:
    config_url = CONFIGURATOR_NL if nl else CONFIGURATOR_DE
    config_label = "Configurator" if nl else "Konfigurator"
    contact_href = "/nl/contact/" if nl else "/contact/"
    contact_label = "Contact" if nl else "Kontakt"
    wa_label = "WhatsApp chatten" if not nl else "WhatsApp chat"
    lang_html = build_inline_lang_switcher(lang_nav, nl)
    social_block = ""
    if social_inner:
        social_block = (
            f'\t\t\t\t\t<div class="mimu-header-social elementor-widget elementor-widget-social-icons">\n'
            f"\t\t\t\t\t\t{social_inner}\n"
            f"\t\t\t\t\t</div>\n"
        )
    return (
        f'\t\t\t\t\t<div class="mimu-header-actions">\n'
        f"{social_block}"
        f'\t\t\t\t\t\t<a class="mimu-header-wa" href="{WHATSAPP_HREF}" target="_blank" '
        f'rel="noopener noreferrer" aria-label="{wa_label}">{WHATSAPP_ICON_SVG}</a>\n'
        f'\t\t\t\t\t\t<div class="mimu-lang-wrap">\n'
        f"\t\t\t\t\t\t{lang_html}\n"
        f"\t\t\t\t\t\t</div>\n"
        f'\t\t\t\t\t\t<a class="mimu-header-btn mimu-header-btn--solid" href="{config_url}" '
        f'target="_blank" rel="noopener noreferrer">{config_label}</a>\n'
        f'\t\t\t\t\t\t<a class="mimu-header-btn mimu-header-btn--outline" href="{contact_href}">'
        f"{contact_label}</a>\n"
        f"\t\t\t\t\t</div>\n"
    )


def patch_header(html: str, path: str = "") -> str:
    if "elementor-location-header" not in html:
        return html

    nl = path.startswith("/nl")
    lang_m = LANG_SWITCHER_RE.search(html)
    if not lang_m:
        return html

    social_m = SOCIAL_ICONS_RE.search(html)
    social_inner = social_m.group(0) if social_m else ""
    actions = build_header_actions(nl, social_inner, lang_m.group(0))

    html = LANG_SWITCHER_RE.sub("", html, count=1)
    html = HEADER_ACTIONS_RE.sub("", html)
    html = re.sub(r"\s*mimu-header-domi", "", html)
    html = re.sub(
        r"(<header[^>]*class=\")",
        r"\1mimu-header-domi ",
        html,
        count=1,
    )
    html = re.sub(
        r'(<div class="elementor-element elementor-element-f752168[^>]*)>',
        r'\1 aria-hidden="true">',
        html,
        count=1,
    )
    html = re.sub(
        r"menu-item-163(?! mimu-nav-btn)",
        "menu-item-163 mimu-nav-btn",
        html,
    )

    if HEADER_ACTIONS_INSERT_RE.search(html):
        html = HEADER_ACTIONS_INSERT_RE.sub(r"\1" + actions + r"\2", html, count=1)
    return html

CHATGPT_ARTIFACT = re.compile(
    r'<div class="flex flex-col text-sm pb-25"><article[^>]*data-testid="conversation-turn[^"]*"[\s\S]*?</article></div>',
    re.I,
)


def strip_chatgpt_artifacts(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        chunk = match.group(0)
        paragraphs = re.findall(r"<p(?:\s[^>]*)?>([\s\S]*?)</p>", chunk)
        parts: list[str] = []
        for raw in paragraphs:
            text = re.sub(r"<[^>]+>", "", raw).strip()
            if len(text) > 20:
                parts.append(f"<p>{text}</p>")
        return "".join(parts) if parts else ""

    return CHATGPT_ARTIFACT.sub(repl, html)


def patch_content(html: str, path: str = "") -> str:
    nl = path.startswith("/nl")
    config_url = CONFIGURATOR_NL if nl else CONFIGURATOR_DE

    html = re.sub(
        r'href="/configurator/\?lang=de\]\(https://mimugarten\.nl/configurator/\?lang=de\)"',
        f'href="{CONFIGURATOR_DE}"',
        html,
        flags=re.I,
    )
    html = re.sub(
        r'href="/configurator/\?lang=nl\]\(https://mimugarten\.nl/configurator/\?lang=nl\)"',
        f'href="{CONFIGURATOR_NL}"',
        html,
        flags=re.I,
    )
    html = re.sub(
        r'href="(?:https://mimugarten\.nl)?/configurator/?(?:\?[^"]*)?"',
        f'href="{config_url}"',
        html,
        flags=re.I,
    )

    link_fixes = [
        ("/nl/terrasoverkapping/", "/nl/terrassenueberdachung/"),
        ("https://mimugarten.nl/nl/terrasoverkapping/", "https://mimugarten.nl/nl/terrassenueberdachung/"),
        ("/nl/glasschiebewande/", "/nl/glazen-schuifwanden/"),
        ("/nl/sonnenschutz-fur-terrassenuberdachungen/", "/nl/zonwering-voor-terrasoverkappingen/"),
    ]
    if nl:
        link_fixes.extend(
            [
                ('href="/glazen-schuiframen/"', 'href="/nl/glazen-schuifwanden/"'),
                ('href="/pergamon-aluminium-veranda/"', 'href="/nl/pergamon-aluminium-terrasoverkapping/"'),
            ]
        )
    else:
        link_fixes.extend(
            [
                ('href="/glazen-schuiframen/"', 'href="/glasschiebewande/"'),
                ('href="/pergamon-aluminium-veranda/"', 'href="/pergamon-aluminium-terrassenuberdachung/"'),
            ]
        )
    for old, new in link_fixes:
        html = html.replace(old, new)

    html = html.replace('href="info@mimugarten.nl"', 'href="mailto:info@mimugarten.nl"')
    html = html.replace("WAS KOSTET EIN WINTERGARTEN NACH MASS?", "WAS KOSTET EIN WINTERGARTEN NACH MAß?")
    html = html.replace("WINTERGÄRTEN NACH MASS", "WINTERGÄRTEN NACH MAß")
    html = strip_chatgpt_artifacts(html)
    return html


def strip_doekoe_credit(html: str) -> str:
    html = re.sub(
        r'<div class="elementor-element elementor-element-a3fd045[\s\S]*?</div>\s*',
        "",
        html,
        count=1,
        flags=re.I,
    )
    html = re.sub(
        r'<p>(?:Diese Website wurde|Deze website is)[\s\S]*?online-doekoe\.nl[\s\S]*?</p>',
        "",
        html,
        flags=re.I,
    )
    return html


FOOTER_PRODUCTS_SUBMENU = re.compile(
    r'<li class="menu-item[^"]*menu-item-159">'
    r'<a href="[^"]+"[^>]*class="elementor-item[^"]*"[^>]*>'
    r"(?:Unsere Produkte|Onze producten)"
    r'</a>\s*<ul class="sub-menu elementor-nav-menu--dropdown">'
    r'(?:\s*<li class="menu-item[\s\S]*?</li>)+\s*'
    r'</ul>\s*</li>\s*',
    re.I,
)

FOOTER_PRODUCTS_COLUMN_DE = """
\t\t<div class="elementor-element elementor-element-mimu-prods e-con-full e-flex e-con e-child" data-id="mimu-prods" data-element_type="container" data-e-type="container">
\t\t\t\t<div class="elementor-element elementor-element-mimu-prods-h elementor-widget elementor-widget-heading" data-id="mimu-prods-h" data-element_type="widget" data-e-type="widget" data-widget_type="heading.default">
\t\t\t\t\t<h2 class="elementor-heading-title elementor-size-default">Unsere Produkte</h2>\t\t\t\t</div>
\t\t\t\t<div class="elementor-element elementor-element-mimu-prods-n elementor-nav-menu__align-start elementor-nav-menu--dropdown-none elementor-widget elementor-widget-nav-menu" data-id="mimu-prods-n" data-element_type="widget" data-e-type="widget" data-widget_type="nav-menu.default">
\t\t\t\t\t\t\t\t<nav aria-label="Produkte" class="elementor-nav-menu--main elementor-nav-menu__container elementor-nav-menu--layout-vertical e--pointer-none">
\t\t\t\t<ul class="elementor-nav-menu sm-vertical mimu-footer-products"><li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-160"><a href="/uberdachung/" class="elementor-item">Überdachung</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-161"><a href="/wintergarten/" class="elementor-item">Wintergärten</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-500"><a href="/sonnenschutz-fur-terrassenuberdachungen/" class="elementor-item">Sonnenschutz für Terrassenüberdachungen</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-501"><a href="/glasschiebewande/" class="elementor-item">Glasschiebewände</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-502"><a href="/pergamon-aluminium-terrassenuberdachung/" class="elementor-item">Pergamon Aluminium Terrassenüberdachung</a></li>
</ul>\t\t\t</nav>
\t\t\t\t\t\t</div>
\t\t\t\t</div>
"""

FOOTER_PRODUCTS_COLUMN_NL = """
\t\t<div class="elementor-element elementor-element-mimu-prods e-con-full e-flex e-con e-child" data-id="mimu-prods" data-element_type="container" data-e-type="container">
\t\t\t\t<div class="elementor-element elementor-element-mimu-prods-h elementor-widget elementor-widget-heading" data-id="mimu-prods-h" data-element_type="widget" data-e-type="widget" data-widget_type="heading.default">
\t\t\t\t\t<h2 class="elementor-heading-title elementor-size-default">Onze producten</h2>\t\t\t\t</div>
\t\t\t\t<div class="elementor-element elementor-element-mimu-prods-n elementor-nav-menu__align-start elementor-nav-menu--dropdown-none elementor-widget elementor-widget-nav-menu" data-id="mimu-prods-n" data-element_type="widget" data-e-type="widget" data-widget_type="nav-menu.default">
\t\t\t\t\t\t\t\t<nav aria-label="Producten" class="elementor-nav-menu--main elementor-nav-menu__container elementor-nav-menu--layout-vertical e--pointer-none">
\t\t\t\t<ul class="elementor-nav-menu sm-vertical mimu-footer-products"><li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-160"><a href="/nl/overkapping/" class="elementor-item">Overkapping</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-161"><a href="/nl/serre/" class="elementor-item">Serres</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-500"><a href="/nl/zonwering-voor-terrasoverkappingen/" class="elementor-item">Zonwering voor terrasoverkappingen</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-501"><a href="/nl/glazen-schuifwanden/" class="elementor-item">Glazen schuifwanden</a></li>
<li class="menu-item menu-item-type-post_type menu-item-object-page menu-item-502"><a href="/nl/pergamon-aluminium-terrasoverkapping/" class="elementor-item">Pergamon Aluminium Terrasoverkapping</a></li>
</ul>\t\t\t</nav>
\t\t\t\t\t\t</div>
\t\t\t\t</div>
"""


def flatten_footer_menu_list(html: str, menu_id: str) -> str:
    start_tag = f'<ul id="{menu_id}" class="elementor-nav-menu sm-vertical">'
    start = html.find(start_tag)
    if start == -1:
        return html
    content_start = start + len(start_tag)
    depth = 1
    i = content_start
    end = content_start
    while i < len(html) and depth:
        if html.startswith("<ul", i):
            depth += 1
            i += 3
            continue
        if html.startswith("</ul>", i):
            depth -= 1
            end = i
            if depth == 0:
                break
            i += 5
            continue
        i += 1
    inner = html[content_start:end]
    new_inner = FOOTER_PRODUCTS_SUBMENU.sub("", inner)
    return html[:content_start] + new_inner + html[end:]


CMPLZ_SHORTCODE = re.compile(r"<p>\[cmplz-document[^\]]*\]</p>", re.I)

COOKIE_POLICY_DE = """
<div class="mimu-cookie-policy">
<p>Diese Cookie-Richtlinie erläutert, wie Mimu Garten („wir“, „uns“) Cookies und ähnliche Technologien auf mimugarten.nl verwendet.</p>
<h2>Was sind Cookies?</h2>
<p>Cookies sind kleine Textdateien, die beim Besuch einer Website auf Ihrem Gerät gespeichert werden. Sie helfen uns, die Website funktionsfähig zu halten, Nutzung zu analysieren und Marketing zu messen.</p>
<h2>Welche Cookies verwenden wir?</h2>
<ul>
<li><strong>Notwendig:</strong> für grundlegende Funktionen (z.&nbsp;B. Sprache, Cookie-Einwilligung).</li>
<li><strong>Analyse &amp; Marketing:</strong> Google Tag Manager / Google Ads (AW-18058170287) zur Messung von Anfragen und Kampagnen.</li>
<li><strong>Funktional:</strong> z.&nbsp;B. Calendly zur Terminbuchung im Showroom.</li>
<li><strong>CookieYes:</strong> speichert Ihre Cookie-Einstellungen.</li>
</ul>
<h2>Ihre Einwilligung</h2>
<p>Beim ersten Besuch können Sie über unser Cookie-Banner (CookieYes) auswählen, welche Kategorien Sie zulassen. Sie können Ihre Einstellungen jederzeit über den Link „Cookie-Einstellungen“ im Banner oder Footer ändern.</p>
<h2>Speicherdauer</h2>
<p>Session-Cookies werden nach dem Schließen des Browsers gelöscht. Persistente Cookies verbleiben je nach Zweck zwischen wenigen Tagen und bis zu 24 Monaten, sofern Sie sie nicht früher löschen.</p>
<h2>Kontakt</h2>
<p>Fragen zu dieser Richtlinie: <a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a> · Schipperswal 32, 6041 TC Roermond, Niederlande.</p>
<p><em>Stand: August 2026</em></p>
</div>
"""

COOKIE_POLICY_NL = """
<div class="mimu-cookie-policy">
<p>Dit cookiebeleid legt uit hoe Mimu Garten („wij“, „ons“) cookies en vergelijkbare technologieën gebruikt op mimugarten.nl.</p>
<h2>Wat zijn cookies?</h2>
<p>Cookies zijn kleine tekstbestanden die op uw apparaat worden opgeslagen wanneer u een website bezoekt. Ze helpen ons de site werkend te houden, gebruik te analyseren en marketing te meten.</p>
<h2>Welke cookies gebruiken wij?</h2>
<ul>
<li><strong>Noodzakelijk:</strong> voor basisfuncties (bijv. taal, cookie-toestemming).</li>
<li><strong>Analyse &amp; marketing:</strong> Google Tag Manager / Google Ads (AW-18058170287) voor het meten van aanvragen en campagnes.</li>
<li><strong>Functioneel:</strong> bijv. Calendly voor showroom-afspraken.</li>
<li><strong>CookieYes:</strong> slaat uw cookievoorkeuren op.</li>
</ul>
<h2>Uw toestemming</h2>
<p>Bij uw eerste bezoek kunt u via ons cookiebanner (CookieYes) kiezen welke categorieën u toestaat. U kunt uw instellingen op elk moment wijzigen via „Cookie-instellingen“ in het banner of de footer.</p>
<h2>Bewaartermijn</h2>
<p>Sessiecookies worden verwijderd wanneer u de browser sluit. Permanente cookies blijven afhankelijk van het doel enkele dagen tot maximaal 24 maanden bewaard, tenzij u ze eerder verwijdert.</p>
<h2>Contact</h2>
<p>Vragen over dit beleid: <a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a> · Schipperswal 32, 6041 TC Roermond, Nederland.</p>
<p><em>Laatst bijgewerkt: augustus 2026</em></p>
</div>
"""

SHOWROOM_SCRIPT_GARBAGE = re.compile(
    r"<p><!-- =+ --><script><br />[\s\S]*?</script><br /><!-- ABSCHLUSS CTA[\s\S]*?--></p>",
    re.I,
)

CALENDLY_HEAD = (
    '<link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet">\n'
    '<script src="https://assets.calendly.com/assets/external/widget.js" type="text/javascript" async></script>'
)

CALENDLY_CONVERSION = """<script>
window.addEventListener("message", function(e) {
  if (e.data && e.data.event === "calendly.event_scheduled" && typeof gtag === "function") {
    gtag("event", "calendly_booking", { event_category: "engagement", event_label: "showroom" });
  }
});
</script>"""

CANVAS_PATHS = frozenset(
    {
        "/showroom-roermond/",
        "/nl/showroom-roermond/",
        "/terrassenueberdachung/",
        "/nl/terrassenueberdachung/",
    }
)

CHROME_CSS_IDS = (
    "widget-icon-list-css",
    "widget-social-icons-css",
    "e-sticky-css",
    "widget-image-css",
    "widget-nav-menu-css",
    "widget-heading-css",
    "elementor-post-10-css",
    "elementor-post-18-css",
)

_chrome_cache: dict[str, tuple[str, str, str, str]] = {}


def neutralize_nav_active(html: str) -> str:
    html = re.sub(r"\s*current-menu-item\b", "", html)
    html = re.sub(r"\s*current_page_item\b", "", html)
    html = re.sub(r'\s*aria-current="page"', "", html)
    html = re.sub(r"\s*elementor-item-active\b", "", html)
    return html


def get_chrome(lang: str) -> tuple[str, str, str, str]:
    if lang not in _chrome_cache:
        template_path = ROOT / ("nl/index.html" if lang == "nl" else "index.html")
        template = template_path.read_text(encoding="utf-8")
        header_m = re.search(
            r'<header data-elementor-type="header"[\s\S]*?</header>',
            template,
        )
        footer_m = re.search(
            r'<footer data-elementor-type="footer"[\s\S]*?</footer>',
            template,
        )
        if not header_m or not footer_m:
            raise RuntimeError(f"Could not extract header/footer from {template_path}")
        css_links: list[str] = []
        for css_id in CHROME_CSS_IDS:
            link_m = re.search(rf'<link[^>]+id=[\'"]{css_id}[\'"][^>]*>', template)
            if link_m:
                css_links.append(link_m.group(0))
        skip_m = re.search(
            r'<a class="skip-link screen-reader-text"[^>]*>[\s\S]*?</a>',
            template,
        )
        skip = skip_m.group(0) if skip_m else ""
        _chrome_cache[lang] = (
            skip,
            neutralize_nav_active(header_m.group(0)),
            neutralize_nav_active(footer_m.group(0)),
            "\n".join(css_links),
        )
    return _chrome_cache[lang]


def patch_cookie_policy(html: str, path: str = "") -> str:
    if "cookie-policy-eu" not in path and "cookiebeleid-eu" not in path:
        return html
    content = COOKIE_POLICY_NL if path.startswith("/nl") else COOKIE_POLICY_DE
    html = CMPLZ_SHORTCODE.sub(content.strip(), html)
    html = re.sub(
        r'content="\[cmplz-document[^\]]*\]"',
        'content="Cookie policy"',
        html,
        flags=re.I,
    )
    return html


def patch_showroom(html: str, path: str = "") -> str:
    if "showroom-roermond" not in path:
        return html
    html = SHOWROOM_SCRIPT_GARBAGE.sub("", html)
    if "assets.calendly.com" not in html:
        html = re.sub(r"</head>", CALENDLY_HEAD + "\n</head>", html, count=1, flags=re.I)
    if "calendly.event_scheduled" not in html and "calendly_booking" not in html:
        html = re.sub(
            r"(<template id=\"tp-language\")",
            CALENDLY_CONVERSION + "\n\\1",
            html,
            count=1,
            flags=re.I,
        )
    return html


def patch_landing_content(html: str, path: str = "") -> str:
    if path.startswith("/nl"):
        html = html.replace(
            "10 Jahre Garantie auf Produkt &amp; Montage",
            "10 jaar garantie op product &amp; montage",
        )
        html = html.replace("10 Jahre Garantie auf Produkt & Montage", "10 jaar garantie op product & montage")
        html = html.replace(">10 Jahre<", ">10 jaar<")
        html = html.replace(">Garantie<", ">Garantie<")  # same in Dutch
        html = html.replace('href="/showroom-roermond/"', 'href="/nl/showroom-roermond/"')
    return html


def patch_canvas_chrome(html: str, path: str = "") -> str:
    if path not in CANVAS_PATHS or "elementor-location-header" in html:
        return html
    lang = "nl" if path.startswith("/nl") else "de"
    skip, header, footer, css = get_chrome(lang)
    for link in css.split("\n"):
        if link and link not in html:
            html = re.sub(r"</head>", link + "\n</head>", html, count=1, flags=re.I)
    chrome_before = f"\n{skip}\n{header}\n"
    html = re.sub(r"(<body[^>]*>)", r"\1" + chrome_before, html, count=1, flags=re.I)
    html = re.sub(
        r'(<template id="tp-language")',
        footer + "\n\n\\1",
        html,
        count=1,
        flags=re.I,
    )
    return html


def patch_footer(html: str, path: str = "") -> str:
    html = strip_doekoe_credit(html)
    if "elementor-element-045933a" not in html:
        return html

    html = flatten_footer_menu_list(html, "menu-1-045933a")
    html = flatten_footer_menu_list(html, "menu-2-045933a")

    if "elementor-element-mimu-prods" not in html:
        nl = path.startswith("/nl")
        column = FOOTER_PRODUCTS_COLUMN_NL if nl else FOOTER_PRODUCTS_COLUMN_DE
        html = html.replace(
            '<div class="elementor-element elementor-element-821679e',
            column + '\n\t\t<div class="elementor-element elementor-element-821679e',
            1,
        )
    return html


def inject_static_assets(html: str, path: str = "") -> str:
    html = re.sub(r'<link[^>]+href="/assets/css/static-overrides\.css"[^>]*>\s*', "", html, flags=re.I)
    html = re.sub(r'<script[^>]+src="/assets/js/static-interactions\.js"[^>]*>\s*</script>\s*', "", html, flags=re.I)
    html = re.sub(r'<script[^>]+src="/assets/js/swiper\.min\.js"[^>]*>\s*</script>\s*', "", html, flags=re.I)
    html = re.sub(r'<a class="mimu-wa-float"[\s\S]*?</a>\s*', "", html, flags=re.I)
    html = re.sub(r'<div id="wa"></div>\s*', "", html, flags=re.I)
    html = re.sub(
        r'<script[^>]+src="/assets/js/whatsapp-config-(?:de|nl)\.js"[^>]*>\s*</script>\s*',
        "",
        html,
        flags=re.I,
    )
    html = re.sub(
        r'<script[^>]+src="/assets/js/njt-whatsapp[^"]+\.js"[^>]*>\s*</script>\s*',
        "",
        html,
        flags=re.I,
    )
    html = re.sub(
        r'<script[^>]+src="/assets/js/whatsapp-popup[^"]+\.js"[^>]*>\s*</script>\s*',
        "",
        html,
        flags=re.I,
    )
    inject = f"{STATIC_OVERRIDES}\n{STATIC_SCRIPTS}\n"
    html = re.sub(r"</body>", inject + "</body>", html, count=1, flags=re.I)
    return html


def ensure_runtime_assets() -> None:
    pairs = [
        (
            f"{BASE}/wp-content/plugins/elementor/assets/lib/swiper/v8/swiper.min.js",
            ROOT / "assets/js/swiper.min.js",
        ),
    ]
    for url, dest in pairs:
        if dest.exists() and dest.stat().st_size > 0:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(http_get(url))
        print(f"  runtime {dest.relative_to(ROOT)}")


def process_page(path: str) -> None:
    print(f"\n=== {path} ===")
    html = http_get(BASE + path_to_href(path)).decode("utf-8", errors="replace")
    html = localize_html_urls(html)
    html = strip_wp_js(html)
    html = strip_wp_head_noise(html)
    html = rewrite_hrefs(html)
    html = fix_canonical(html, path)
    html = patch_content(html, path)
    html = patch_footer(html, path)
    html = patch_cookie_policy(html, path)
    html = patch_showroom(html, path)
    html = patch_landing_content(html, path)
    html = patch_header(html, path)
    html = patch_canvas_chrome(html, path)
    html = inject_static_assets(html, path)
    html = re.sub(r"\n{3,}", "\n\n", html)
    out = page_outfile(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size:,} bytes)")


def write_site_files(pages: list[str]) -> None:
    urls = [f"  <url><loc>{BASE}{path_to_href(p)}</loc></url>" for p in pages]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n",
        encoding="utf-8",
    )
    redirects = [
        "/nl/terrasoverkapping  /nl/terrassenueberdachung/  301",
        "/nl/terrasoverkapping/  /nl/terrassenueberdachung/  301",
    ]
    for p in pages:
        if p == "/":
            continue
        clean = p.strip("/")
        redirects.append(f"/{clean}  /{clean}/  301")
    (ROOT / "_redirects").write_text("\n".join(redirects) + "\n", encoding="utf-8")
    (ROOT / "netlify.toml").write_text(
        """[build]
  publish = "."
  command = "python3 mirror.py"

[build.processing.html]
  pretty_urls = true

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
""",
        encoding="utf-8",
    )


def repatch_local() -> None:
    """Re-apply content patches to existing HTML without re-fetching from live."""
    _chrome_cache.clear()
    count = 0
    for html_path in sorted(ROOT.rglob("index.html")):
        rel = html_path.relative_to(ROOT)
        if rel.parts[0] == "assets":
            continue
        url_path = "/" if rel == Path("index.html") else "/" + "/".join(rel.parts[:-1]) + "/"
        html = html_path.read_text(encoding="utf-8")
        html = patch_content(html, url_path)
        html = patch_footer(html, url_path)
        html = patch_cookie_policy(html, url_path)
        html = patch_showroom(html, url_path)
        html = patch_landing_content(html, url_path)
        html = patch_header(html, url_path)
        html = patch_canvas_chrome(html, url_path)
        html = inject_static_assets(html, url_path)
        html = re.sub(r"\n{3,}", "\n\n", html)
        html_path.write_text(html, encoding="utf-8")
        count += 1
        print(f"repatched {rel}")
    print(f"\nRepatch complete — {count} pages.")


def main() -> None:
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "repatch":
        repatch_local()
        return
    ensure_runtime_assets()
    pages = fetch_pages()
    print(f"Pages: {len(pages)}")
    for path in pages:
        process_page(path)
    write_site_files(pages)
    print(f"\nDone — {len(pages)} pages, {len(asset_map)} assets mapped.")


if __name__ == "__main__":
    main()
