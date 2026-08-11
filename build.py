#!/usr/bin/env python3
"""Generate the Mimu Garten static site (DE + NL). Run: python3 build.py"""
from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://mimugarten.nl"
CONFIG_DE = f"{SITE}/configurator/?lang=de"
CONFIG_NL = f"{SITE}/configurator/?lang=nl"
AW_ID = "AW-18058170287"
COOKIEYES = "806335fda999c933e5c7de34bfc208fa"

# Live URL path → (lang, file path relative to ROOT, title, description, hreflang peer path)
# Generated as path/index.html when path ends with /, else path.html


def img(name: str, depth: int = 0) -> str:
    prefix = "../" * depth
    return f'{prefix}assets/img/{name}'


def asset(path: str, depth: int = 0) -> str:
    return ("../" * depth) + path


PAGES: list[dict] = []


def add_page(**kwargs):
    PAGES.append(kwargs)


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("wrote", path.relative_to(ROOT))


def depth_for(out_rel: str) -> int:
    # index.html at root = 0; nl/index.html = 1; uberdachung/index.html = 1; nl/overkapping/index.html = 2
    parts = Path(out_rel).parts
    return max(0, len(parts) - 1)


def shell(page: dict) -> str:
    lang = page["lang"]
    out = page["out"]
    depth = depth_for(out)
    title = page["title"]
    description = page["description"]
    canonical = page["canonical"]
    hreflang_de = page.get("hreflang_de", canonical)
    hreflang_nl = page.get("hreflang_nl")
    og_image = page.get("og_image") or img("68c3c145cd34af3e61e6eeb0_DSC03674-2-1024x683.avif", depth)
    if not og_image.startswith("http"):
        og_image_abs = f"{SITE}/{og_image.lstrip('./')}" if not og_image.startswith("../") else f"{SITE}/assets/img/{Path(og_image).name}"
    else:
        og_image_abs = og_image
    # Always absolute OG from local assets folder name
    if "assets/img/" in og_image or og_image.startswith("../") or not og_image.startswith("http"):
        og_image_abs = f"{SITE}/assets/img/{Path(og_image).name}"

    config = CONFIG_NL if lang == "nl" else CONFIG_DE
    contact = asset("nl/contact/" if lang == "nl" else "contact/", depth) if False else None
    # Build nav links with correct relative prefixes
    def href(path: str) -> str:
        # path like "" | "uberdachung/" | "nl/" | "nl/overkapping/"
        if path == "":
            target = asset("index.html", depth) if depth == 0 else asset("" if False else ("../" * depth)[:-0] or "index.html", 0)
        # simpler: compute from root-relative
        root_rel = path if path.endswith("/") or path == "" else path + "/"
        if root_rel == "/":
            root_rel = ""
        # from current file to root then to target
        to_root = "../" * depth
        if root_rel == "":
            return f"{to_root}index.html" if depth else "index.html"
        return f"{to_root}{root_rel}"

    # Fix href helper properly
    def h(p: str) -> str:
        to_root = "../" * depth
        if p in ("", "/"):
            return f"{to_root}index.html" if depth else "index.html"
        p = p.strip("/") + "/"
        return f"{to_root}{p}"

    if lang == "de":
        home, products, montage, showroom, contact_p = "", "unsere-produkte/", "montage-und-service/", "showroom-roermond/", "contact/"
        cookie_p = "cookie-policy-eu/"
        submenu = [
            ("uberdachung/", "Überdachung"),
            ("wintergarten/", "Wintergärten"),
            ("sonnenschutz-fur-terrassenuberdachungen/", "Sonnenschutz"),
            ("glasschiebewande/", "Glasschiebewände"),
            ("pergamon-aluminium-terrassenuberdachung/", "Pergamon"),
        ]
        nav_labels = ("Home", "Unsere Produkte", "Montage und Service", "Showroom", "Kontakt")
        cta_config, cta_advice = "Konfigurator", "Kostenlose Beratung"
        top_addr = "Ausstellungsadresse: Schipperswal 32, 6041 TC Roermond, Niederlande"
        aria_nav, aria_menu = "Hauptnavigation", "Menü öffnen"
        footer_blurb = "Aluminium-Terrassenüberdachungen und Glasschiebewände aus eigener Produktion — Beratung, Fertigung und Montage aus einer Hand."
        footer_products, footer_contact = "Unsere Produkte", "Kontakt"
        footer_hours = "Montag – Samstag: 09:00 – 17:00<br>Sonntag: 12:00 – 17:00"
        cookie_label = "Cookie Policy (EU)"
        cookie_text = 'Wir verwenden Cookies, um Ihnen die bestmögliche Nutzererfahrung zu bieten. Weitere Informationen finden Sie in unserer <a href="' + h(cookie_p) + '">Cookie Policy</a>.'
        accept, reject = "Akzeptieren", "Ablehnen"
        rights = "Alle Rechte vorbehalten."
        peer_label, peer_href = "NL", h(hreflang_nl or "nl/")
        self_lang_label = "DE"
        lang_peer_current = False
    else:
        home, products, montage, showroom, contact_p = "nl/", "nl/onze-producten/", "nl/montage-en-service/", "nl/showroom-roermond/", "nl/contact/"
        cookie_p = "nl/cookiebeleid-eu/"
        submenu = [
            ("nl/overkapping/", "Overkapping"),
            ("nl/serre/", "Wintertuinen"),
            ("nl/zonwering-voor-terrasoverkappingen/", "Zonwering"),
            ("nl/glazen-schuifwanden/", "Glazen schuifwanden"),
            ("nl/pergamon-aluminium-terrasoverkapping/", "Pergamon"),
        ]
        nav_labels = ("Home", "Onze producten", "Montage en service", "Showroom", "Contact")
        cta_config, cta_advice = "Configurator", "Gratis advies"
        top_addr = "Showroom: Schipperswal 32, 6041 TC Roermond, Nederland"
        aria_nav, aria_menu = "Hoofdnavigatie", "Menu openen"
        footer_blurb = "Aluminium terrasoverkappingen en glazen schuifwanden uit eigen productie — advies, fabricage en montage uit één hand."
        footer_products, footer_contact = "Onze producten", "Contact"
        footer_hours = "Maandag – zaterdag: 09:00 – 17:00<br>Zondag: 12:00 – 17:00"
        cookie_label = "Cookiebeleid (EU)"
        cookie_text = 'We gebruiken cookies voor de beste gebruikerservaring. Meer info in ons <a href="' + h(cookie_p) + '">cookiebeleid</a>.'
        accept, reject = "Accepteren", "Weigeren"
        rights = "Alle rechten voorbehouden."
        peer_label, peer_href = "DE", h(hreflang_de or "/")
        self_lang_label = "NL"
        lang_peer_current = False

    current_canon = canonical.strip("/")
    def is_current(path: str) -> str:
        p = path.strip("/")
        return ' aria-current="page"' if p == current_canon else ""

    submenu_html = "\n".join(
        f'            <li><a href="{h(p)}"{is_current(p)}>{lab}</a></li>' for p, lab in submenu
    )
    products_open = any(current_canon == p.strip("/") for p, _ in submenu) or current_canon in {
        products.strip("/"), "unsere-produkte", "nl/onze-producten"
    }

    hreflang_tags = f'''<link rel="alternate" hreflang="de" href="{SITE}{hreflang_de}">
<link rel="alternate" hreflang="de-DE" href="{SITE}{hreflang_de}">'''
    if hreflang_nl:
        hreflang_tags += f'''
<link rel="alternate" hreflang="nl" href="{SITE}{hreflang_nl}">
<link rel="alternate" hreflang="nl-NL" href="{SITE}{hreflang_nl}">'''
    hreflang_tags += f'\n<link rel="alternate" hreflang="x-default" href="{SITE}{hreflang_de}">'

    json_ld = page.get("json_ld") or default_json_ld(lang)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{SITE}{canonical}">
{hreflang_tags}
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{canonical}">
<meta property="og:site_name" content="Mimu Garten">
<meta property="og:locale" content="{"de_DE" if lang == "de" else "nl_NL"}">
<meta property="og:image" content="{og_image_abs}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{img('cropped-Frame-27-scaled-1-32x32.png', depth)}" type="image/png">
<link rel="apple-touch-icon" href="{img('cropped-Frame-27-scaled-1-180x180.png', depth)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Roboto+Serif:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset('assets/css/style.css', depth)}">
<script type="application/ld+json">{json_ld}</script>
<script id="cookieyes" type="text/javascript" src="https://cdn-cookieyes.com/client_data/{COOKIEYES}/script.js"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id={AW_ID}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{AW_ID}');
</script>
</head>
<body>
  <div class="topbar">
    <div class="container">
      <div class="topbar-info">
        <a href="tel:+31475252151">+31 (0)475 252 151</a>
        <a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a>
        <span>{top_addr}</span>
      </div>
      <div class="topbar-social">
        <div class="lang-switch" aria-label="Language">
          <a href="{h(hreflang_de) if lang == "nl" else h(canonical if lang == "de" else hreflang_de)}"{" aria-current=\"true\"" if lang == "de" else ""}>DE</a>
          <a href="{h(hreflang_nl) if hreflang_nl else h("nl/")}"{" aria-current=\"true\"" if lang == "nl" else ""}>NL</a>
        </div>
        <a href="https://www.facebook.com/profile.php?id=61583749628509" target="_blank" rel="noopener">Facebook</a>
        <a href="https://www.instagram.com/mimugarten/" target="_blank" rel="noopener">Instagram</a>
      </div>
    </div>
  </div>

  <header class="site-header">
    <div class="container">
      <a class="logo" href="{h(home)}" aria-label="Mimu Garten">
        <img src="{img('Frame-27-300x56.png', depth)}" alt="Mimu Garten" width="150" height="28" loading="eager">
      </a>
      <button class="nav-toggle" aria-label="{aria_menu}" aria-expanded="false"><span></span><span></span><span></span></button>
      <nav class="nav" aria-label="{aria_nav}">
        <ul class="nav-list">
          <li><a href="{h(home)}"{is_current(home)}>{nav_labels[0]}</a></li>
          <li class="has-submenu{" is-open" if products_open else ""}">
            <a href="{h(products)}"{is_current(products)}>{nav_labels[1]}</a>
            <ul class="submenu">
{submenu_html}
            </ul>
          </li>
          <li><a href="{h(montage)}"{is_current(montage)}>{nav_labels[2]}</a></li>
          <li><a href="{h(showroom)}"{is_current(showroom)}>{nav_labels[3]}</a></li>
          <li><a href="{h(contact_p)}"{is_current(contact_p)}>{nav_labels[4]}</a></li>
        </ul>
      </nav>
      <div class="nav-cta">
        <a class="btn btn-outline" href="{config}">{cta_config}</a>
        <a class="btn btn-primary" href="{h(contact_p)}">{cta_advice}</a>
      </div>
    </div>
  </header>

<main id="content">
{page["body"]}
</main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          <h4>Mimu Garten</h4>
          <p>{footer_blurb}</p>
          <div class="footer-social">
            <a href="https://www.facebook.com/profile.php?id=61583749628509" target="_blank" rel="noopener">Facebook</a>
            <a href="https://www.instagram.com/mimugarten/" target="_blank" rel="noopener">Instagram</a>
          </div>
        </div>
        <div>
          <h4>{footer_products}</h4>
          <ul>
{chr(10).join(f'            <li><a href="{h(p)}">{lab}</a></li>' for p, lab in submenu)}
          </ul>
        </div>
        <div>
          <h4>{footer_contact}</h4>
          <ul>
            <li>Schipperswal 32, 6041 TC Roermond</li>
            <li>{footer_hours}</li>
            <li><a href="tel:+31475252151">+31 (0)475 252 151</a></li>
            <li><a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 Mimu Garten. {rights}</span>
        <a href="{h(cookie_p)}">{cookie_label}</a>
      </div>
    </div>
  </footer>

  <a class="wa-float" href="https://wa.me/31475252151" target="_blank" rel="noopener" aria-label="WhatsApp">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 3.5A11 11 0 0 0 3.4 17.7L2 22l4.4-1.3A11 11 0 1 0 20.5 3.5zm-8.5 17a9 9 0 0 1-4.6-1.3l-.3-.2-2.6.8.8-2.5-.2-.3A9 9 0 1 1 12 20.5zm5.2-6.7c-.3-.1-1.6-.8-1.9-.9s-.4-.1-.6.1-.7.9-.8 1-.3.2-.6.1a7.4 7.4 0 0 1-2.2-1.4 8.2 8.2 0 0 1-1.5-1.9c-.2-.3 0-.4.1-.6l.5-.6c.1-.2.1-.3 0-.5s-.6-1.4-.8-1.9-.4-.4-.6-.4h-.5c-.2 0-.5.1-.7.3a2.3 2.3 0 0 0-.7 1.7 4 4 0 0 0 .8 2.1 9.1 9.1 0 0 0 3.5 3.4 11 11 0 0 0 2.2.9 2.6 2.6 0 0 0 1.7.1 2 2 0 0 0 1.3-1.1 1.6 1.6 0 0 0 .1-1.1c-.1-.1-.3-.2-.6-.3z"/></svg>
  </a>

  <div class="cookie-banner" data-cookie-banner hidden>
    <p>{cookie_text}</p>
    <div class="cookie-actions">
      <button class="btn btn-primary" type="button" data-cookie-accept>{accept}</button>
      <button class="btn btn-outline" type="button" data-cookie-reject>{reject}</button>
    </div>
  </div>

  <script src="{asset('assets/js/main.js', depth)}"></script>
</body>
</html>
"""


def default_json_ld(lang: str) -> str:
    desc = (
        "Die besten Terrassenüberdachungen und Wintergärten aus Roermond."
        if lang == "de"
        else "De beste terrasoverkappingen en wintertuinen uit Roermond."
    )
    return (
        '{"@context":"https://schema.org","@type":["LocalBusiness","Organization"],'
        '"name":"Mimu Garten","url":"https://mimugarten.nl","email":"info@mimugarten.nl",'
        '"telephone":"+31475252151","description":"' + desc + '",'
        '"address":{"@type":"PostalAddress","streetAddress":"Schipperswal 32",'
        '"addressLocality":"Roermond","postalCode":"6041 TC","addressCountry":"NL"},'
        '"geo":{"@type":"GeoCoordinates","latitude":"51.2008818","longitude":"5.9932208"},'
        '"openingHours":["Mo-Sa 09:00-17:00","Su 12:00-17:00"],'
        '"image":"https://mimugarten.nl/assets/img/Frame-27-scaled.png"}'
    )


def faq(items):
    parts = ['<div class="faq">']
    for q, a in items:
        parts.append(
            f'<details class="faq-item"><summary>{q}</summary><p>{a}</p></details>'
        )
    parts.append("</div>")
    return "\n".join(parts)


def testimonials(entries, eyebrow, heading):
    cards = "\n".join(
        f'''<div class="card"><div class="testimonial-stars">★★★★★</div><p>{q}</p>
        <div class="testimonial-name">{n} <span class="testimonial-city">{c}</span></div></div>'''
        for q, n, c in entries
    )
    return f'''<section class="section section--soft"><div class="container">
      <div class="section-head section-head--center"><span class="eyebrow">{eyebrow}</span><h2>{heading}</h2></div>
      <div class="testimonial-scroller">{cards}</div></div></section>'''


def info_block(lang: str, depth: int):
    if lang == "de":
        return f'''<section class="section section--tight"><div class="container split">
        <div><span class="eyebrow">Öffnungszeiten</span><h3 class="mt-0">Ausstellungsadresse</h3>
        <p>Schipperswal 32<br>6041 TC Roermond<br>Niederlande — Neben dem Designer Outlet Center</p>
        <p>Montag bis Samstag: 09:00 – 17:00<br>Sonntag: 12:00 – 17:00</p>
        <p><a href="tel:+31475252151">+31 (0)475 252 151</a><br><a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a></p></div>
        <div class="split-media map-embed"><iframe src="https://maps.google.com/maps?q=Schipperswal%2032%2C%206041%20TC%20Roermond&t=m&z=13&output=embed&iwloc=near" loading="lazy" title="Mimu Garten Standort"></iframe></div>
      </div></section>'''
    return f'''<section class="section section--tight"><div class="container split">
        <div><span class="eyebrow">Openingstijden</span><h3 class="mt-0">Showroomadres</h3>
        <p>Schipperswal 32<br>6041 TC Roermond<br>Nederland — naast Designer Outlet Center</p>
        <p>Maandag tot zaterdag: 09:00 – 17:00<br>Zondag: 12:00 – 17:00</p>
        <p><a href="tel:+31475252151">+31 (0)475 252 151</a><br><a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a></p></div>
        <div class="split-media map-embed"><iframe src="https://maps.google.com/maps?q=Schipperswal%2032%2C%206041%20TC%20Roermond&t=m&z=13&output=embed&iwloc=near" loading="lazy" title="Mimu Garten locatie"></iframe></div>
      </div></section>'''


def showroom_cta(lang: str, depth: int):
    contact = ("../" * depth) + ("nl/contact/" if lang == "nl" else "contact/")
    if lang == "de":
        return f'''<section class="section section--green"><div class="container split">
        <div><span class="eyebrow">Showroom Roermond</span>
        <h2>Erleben Sie Mimu Garten live in unserem Showroom.</h2>
        <p>Besuchen Sie unseren Showroom und erleben Sie hautnah, wie Ihre maßgeschneiderte Terrassenüberdachung entsteht — von der ersten Idee bis zur perfekten Montage.</p>
        <a class="btn btn-primary" href="{contact}">Kostenlose Beratung buchen</a></div>
        <div class="split-media"><img src="{img("68c2d3e26cad3cab87ac390a_DSC04598-1-683x1024.avif", depth)}" alt="Showroom Mimu Garten" loading="lazy" width="683" height="1024"></div>
      </div></section>'''
    return f'''<section class="section section--green"><div class="container split">
        <div><span class="eyebrow">Showroom Roermond</span>
        <h2>Beleef Mimu Garten live in onze showroom.</h2>
        <p>Bezoek onze showroom en ervaar hoe uw terrasoverkapping op maat tot stand komt — van het eerste idee tot de perfecte montage.</p>
        <a class="btn btn-primary" href="{contact}">Gratis advies boeken</a></div>
        <div class="split-media"><img src="{img("68c2d3e26cad3cab87ac390a_DSC04598-1-683x1024.avif", depth)}" alt="Showroom Mimu Garten" loading="lazy" width="683" height="1024"></div>
      </div></section>'''


# ---------------------------------------------------------------------------
# PAGE BODIES
# ---------------------------------------------------------------------------

def home_de(depth=0):
    return f'''
    <section class="hero"><div class="container hero-grid">
      <div>
        <span class="eyebrow">Terrassenüberdachungen &amp; Glasschiebewände</span>
        <h1>Genießen Sie jede Jahreszeit unter Ihrer eigenen Terrassenüberdachung</h1>
        <p class="lead">Hochwertige Aluminium-Terrassenüberdachungen aus eigener Produktion — von der Beratung bis zur Montage alles aus einer Hand.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{CONFIG_DE}">Mimu Garten Designer öffnen</a>
          <a class="btn btn-outline" href="contact/">Kostenlose Beratung</a>
        </div>
      </div>
      <div class="hero-media">
        <img src="{img("68c3c145cd34af3e61e6eeb0_DSC03674-2-1024x683.avif", depth)}" alt="Terrassenüberdachung von Mimu Garten" width="1024" height="683" loading="eager">
      </div>
    </div></section>

    <section class="section"><div class="container">
      <div class="section-head"><span class="eyebrow">Unsere Produkte</span><h2>Für jeden Außenbereich die passende Lösung</h2></div>
      <div class="grid grid--3">
        <div class="card"><h3>Terrassenüberdachungen</h3><p>Genießen Sie Ihre Terrasse bei jedem Wetter und schaffen Sie einen komfortablen Wohnbereich im Freien.</p><a class="link" href="uberdachung/">Erfahren Sie mehr →</a></div>
        <div class="card"><h3>Wintergärten</h3><p>Ein stilvoller Anbau mit viel Glas für mehr Licht und zusätzlichen Wohnraum.</p><a class="link" href="wintergarten/">Erfahren Sie mehr →</a></div>
        <div class="card"><h3>Sonnenschutz</h3><p>Markisensysteme für einen komfortablen Außenbereich das ganze Jahr über.</p><a class="link" href="sonnenschutz-fur-terrassenuberdachungen/">Erfahren Sie mehr →</a></div>
        <div class="card"><h3>Glasschiebewände</h3><p>Elegante Erweiterung für jede Terrassenüberdachung — geschützt und lichtdurchflutet.</p><a class="link" href="glasschiebewande/">Erfahren Sie mehr →</a></div>
        <div class="card"><h3>Pergamon</h3><p>Das robusteste System im Sortiment — maximale Stabilität und Premium-Verarbeitung.</p><a class="link" href="pergamon-aluminium-terrassenuberdachung/">Erfahren Sie mehr →</a></div>
      </div>
    </div></section>

    <section class="section section--soft"><div class="container">
      <div class="section-head section-head--center"><span class="eyebrow">Von der Vision zur Realität</span><h2>Der Weg zu Ihrer perfekten Terrassenüberdachung</h2></div>
      <div class="steps">
        <div class="step"><span class="step-num">Schritt 1</span><h3>Beratung &amp; Aufmaß</h3><p>Wir besuchen Sie vor Ort, beraten Sie persönlich und nehmen millimetergenaue Maße.</p></div>
        <div class="step"><span class="step-num">Schritt 2</span><h3>Individuelles Design</h3><p>Maßgefertigt und harmonisch in die Architektur Ihres Hauses integriert.</p></div>
        <div class="step"><span class="step-num">Schritt 3</span><h3>Professionelle Montage</h3><p>Komplette Montage durch unser Team — mit 10 Jahren Garantie auf Produkt und Montage.</p></div>
      </div>
    </div></section>

    <section class="section"><div class="container split">
      <div><span class="eyebrow">Über Mimu Garten</span><h2>Ihr Wohnraum, elegant erweitert.</h2>
        <p>Als Hersteller fertigen wir hochwertige Aluminium-Terrassenüberdachungen und Glasschiebewände in unserer eigenen Produktion. Ohne Zwischenhändler — alles aus einer Hand.</p>
        <p>So garantieren wir höchste Qualität, perfekte Passgenauigkeit und langlebige Lösungen, die den Wert Ihres Hauses steigern.</p></div>
      <div class="split-media"><img src="{img("68c3c175bbf4ef1c832edd73_DSC04456-1024x683.avif", depth)}" alt="Terrasse mit Überdachung" loading="lazy" width="1024" height="683"></div>
    </div></section>

    <section class="section section--soft"><div class="container split reverse">
      <div><span class="eyebrow">Warum Mimu Garten?</span><h2>Full-Service ohne Stress</h2>
        <p>Von der Planung über die Produktion bis zur Montage erhalten Sie alles aus einer Hand.</p>
        <ul class="usp-list"><li>100% Professionelle Montage</li><li>Kein Stress mit Bausätzen</li><li>Premium-Materialien und Maßanfertigung</li></ul></div>
      <div class="split-media"><img src="{img("68c2d4901f68fbab63640167_enhanced_6e62555f-4159-4c4b-9f74-d517b4f5d428-p-1600-1-1024x683.webp", depth)}" alt="Montage" loading="lazy" width="1024" height="683"></div>
    </div></section>

    {testimonials([
        ("Sehr zufrieden mit unserer Terrassenüberdachung von Mimu Garten. Gute Beratung, pünktliche Lieferung und professionelle Montage.", "Michael Schneider", "Köln"),
        ("Sehr gute Erfahrung mit Mimu Garten. Unsere Terrassenüberdachung wurde schnell geliefert und sauber montiert.", "Andreas Müller", "Düsseldorf"),
        ("Sehr zufrieden mit unserem Carport von Mimu Garten. Gute Qualität und schnelle, saubere Montage.", "Thomas Becker", "Dortmund"),
        ("Die Glasschiebewände sind top. Gute Beratung, pünktliche Lieferung und professionelle Montage.", "Stefan Wagner", "Essen"),
        ("Unsere Terrassenüberdachung mit Glasschiebewänden sieht super aus. Alles wurde sauber und schnell montiert.", "Daniel Krüger", "Bonn"),
    ], "Referenzen", "Mit Präzision gefertigt. Von Hausbesitzern geliebt.")}

    <section class="section"><div class="container">
      <div class="section-head section-head--center"><span class="eyebrow">Häufig gestellte Fragen</span><h2>Alles, was Sie vor Ihrem Projekt wissen müssen</h2></div>
      {faq([
        ("Kann ich einen Bausatz kaufen und die Terrassenüberdachung selbst montieren?", "Mimu Garten ist auf hochwertige Komplettmontagen spezialisiert. Wir bieten keine Bausätze zur Selbstmontage an."),
        ("Wie lange dauert die professionelle Montage?", "Die meisten maßgefertigten Terrassenüberdachungen werden innerhalb von 1 bis 2 Tagen vollständig montiert."),
        ("Werden Ihre Terrassenüberdachungen individuell für mein Haus angefertigt?", "Ja, jede Terrassenüberdachung wird individuell geplant und millimetergenau gefertigt."),
        ("Benötige ich eine Baugenehmigung?", "Das hängt von der Gemeinde und der Größe ab. Im Rahmen der Beratung informieren wir Sie gerne."),
      ])}
    </div></section>
    {info_block("de", depth)}
'''


def home_nl(depth=1):
    return f'''
    <section class="hero"><div class="container hero-grid">
      <div>
        <span class="eyebrow">Terrasoverkappingen &amp; glazen schuifwanden</span>
        <h1>Geniet elk seizoen onder uw eigen terrasoverkapping</h1>
        <p class="lead">Hoogwaardige aluminium terrasoverkappingen uit eigen productie — van advies tot montage alles uit één hand.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="{CONFIG_NL}">Mimu Garten Designer openen</a>
          <a class="btn btn-outline" href="contact/">Gratis advies</a>
        </div>
      </div>
      <div class="hero-media">
        <img src="{img("68c3c145cd34af3e61e6eeb0_DSC03674-2-1024x683.avif", depth)}" alt="Terrasoverkapping van Mimu Garten" width="1024" height="683" loading="eager">
      </div>
    </div></section>

    <section class="section"><div class="container">
      <div class="section-head"><span class="eyebrow">Onze producten</span><h2>Voor elke buitenruimte de juiste oplossing</h2></div>
      <div class="grid grid--3">
        <div class="card"><h3>Terrasoverkappingen</h3><p>Geniet bij elk weer van uw terras met een comfortabele buitenruimte.</p><a class="link" href="overkapping/">Meer informatie →</a></div>
        <div class="card"><h3>Wintertuinen</h3><p>Een stijlvolle aanbouw met veel glas voor meer licht en woonruimte.</p><a class="link" href="serre/">Meer informatie →</a></div>
        <div class="card"><h3>Zonwering</h3><p>Markiezen voor een comfortabele buitenruimte het hele jaar door.</p><a class="link" href="zonwering-voor-terrasoverkappingen/">Meer informatie →</a></div>
        <div class="card"><h3>Glazen schuifwanden</h3><p>Elegante uitbreiding voor elke overkapping — beschermd en licht.</p><a class="link" href="glazen-schuifwanden/">Meer informatie →</a></div>
        <div class="card"><h3>Pergamon</h3><p>Het stevigste systeem in het assortiment — maximale stabiliteit.</p><a class="link" href="pergamon-aluminium-terrasoverkapping/">Meer informatie →</a></div>
      </div>
    </div></section>

    <section class="section section--soft"><div class="container">
      <div class="section-head section-head--center"><span class="eyebrow">Van visie naar realiteit</span><h2>De weg naar uw perfecte terrasoverkapping</h2></div>
      <div class="steps">
        <div class="step"><span class="step-num">Stap 1</span><h3>Advies &amp; inmeten</h3><p>Wij komen bij u langs, adviseren persoonlijk en meten millimeternauwkeurig in.</p></div>
        <div class="step"><span class="step-num">Stap 2</span><h3>Individueel ontwerp</h3><p>Op maat gemaakt en harmonieus afgestemd op de architectuur van uw woning.</p></div>
        <div class="step"><span class="step-num">Stap 3</span><h3>Professionele montage</h3><p>Volledige montage door ons team — met 10 jaar garantie op product en montage.</p></div>
      </div>
    </div></section>

    <section class="section"><div class="container split">
      <div><span class="eyebrow">Over Mimu Garten</span><h2>Uw woonruimte, elegant uitgebreid.</h2>
        <p>Als fabrikant maken wij hoogwaardige aluminium terrasoverkappingen en glazen schuifwanden in onze eigen productie. Zonder tussenhandel — alles uit één hand.</p></div>
      <div class="split-media"><img src="{img("68c3c175bbf4ef1c832edd73_DSC04456-1024x683.avif", depth)}" alt="Terras met overkapping" loading="lazy" width="1024" height="683"></div>
    </div></section>

    {testimonials([
        ("Zeer tevreden over onze terrasoverkapping van Mimu Garten. Goed advies, snelle levering en professionele montage.", "Michael Schneider", "Keulen"),
        ("Zeer goede ervaring. Onze overkapping werd snel geleverd en netjes gemonteerd.", "Andreas Müller", "Düsseldorf"),
        ("Tevreden over ons carport. Goede kwaliteit en snelle, nette montage.", "Thomas Becker", "Dortmund"),
    ], "Referenties", "Met precisie gemaakt. Geliefd bij huiseigenaren.")}

    <section class="section"><div class="container">
      <div class="section-head section-head--center"><span class="eyebrow">Veelgestelde vragen</span><h2>Alles wat u vooraf wilt weten</h2></div>
      {faq([
        ("Kan ik een bouwpakket kopen en zelf monteren?", "Mimu Garten specialiseert zich in complete montages. Wij bieden geen zelfbouw-pakketten aan."),
        ("Hoe lang duurt de montage?", "De meeste overkappingen op maat worden binnen 1 tot 2 dagen volledig gemonteerd."),
        ("Wordt mijn overkapping op maat gemaakt?", "Ja, elke overkapping wordt individueel gepland en millimeternauwkeurig gefabriceerd."),
      ])}
    </div></section>
    {info_block("nl", depth)}
'''


def product_page(lang, depth, eyebrow, h1, sections_html):
    return f'''<section class="hero hero--compact"><div class="container">
      <span class="eyebrow">{eyebrow}</span><h1>{h1}</h1>
      <div class="hero-actions"><a class="btn btn-primary" href="{CONFIG_NL if lang == "nl" else CONFIG_DE}">{"Configurator" if lang == "nl" else "Konfigurator"}</a></div>
    </div></section>{sections_html}'''


def contact_body(lang, depth):
    thanks = "nl/dank-u/" if lang == "nl" else "danke/"
    to_root = "../" * depth
    if lang == "de":
        return f'''<section class="hero hero--compact"><div class="container"><span class="eyebrow">Kontakt</span>
      <h1>Kostenlose Beratung anfordern</h1>
      <p class="lead">Schreiben Sie uns — wir melden uns schnellstmöglich.</p></div></section>
    <section class="section"><div class="container split">
      <form class="form" name="contact" method="POST" netlify netlify-honeypot="bot-field" action="/{thanks}">
        <input type="hidden" name="form-name" value="contact">
        <p class="form-note" hidden><label>Don’t fill: <input name="bot-field"></label></p>
        <div class="form-row">
          <label>Name *<input name="name" required></label>
          <label>E-Mail *<input type="email" name="email" required></label>
        </div>
        <div class="form-row">
          <label>Telefon<input type="tel" name="phone"></label>
          <label>Ort<input name="city"></label>
        </div>
        <label>Nachricht *<textarea name="message" required></textarea></label>
        <p class="form-note">Mit dem Absenden stimmen Sie der Verarbeitung Ihrer Daten zur Bearbeitung der Anfrage zu.</p>
        <button class="btn btn-primary" type="submit">Nachricht senden</button>
      </form>
      <div>
        <h2>Mimu Garten</h2>
        <p>Schipperswal 32<br>6041 TC Roermond, Niederlande</p>
        <p><a href="tel:+31475252151">+31 (0)475 252 151</a><br><a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a></p>
        <p><a class="btn btn-outline" href="{CONFIG_DE}">Zum Konfigurator</a></p>
        <div class="split-media map-embed" style="margin-top:1.5rem"><iframe src="https://maps.google.com/maps?q=Schipperswal%2032%2C%206041%20TC%20Roermond&t=m&z=13&output=embed&iwloc=near" loading="lazy" title="Karte"></iframe></div>
      </div>
    </div></section>'''
    return f'''<section class="hero hero--compact"><div class="container"><span class="eyebrow">Contact</span>
      <h1>Vraag gratis advies aan</h1>
      <p class="lead">Stuur ons een bericht — wij nemen zo snel mogelijk contact op.</p></div></section>
    <section class="section"><div class="container split">
      <form class="form" name="contact-nl" method="POST" netlify netlify-honeypot="bot-field" action="/{thanks}">
        <input type="hidden" name="form-name" value="contact-nl">
        <p class="form-note" hidden><label>Don’t fill: <input name="bot-field"></label></p>
        <div class="form-row">
          <label>Naam *<input name="name" required></label>
          <label>E-mail *<input type="email" name="email" required></label>
        </div>
        <div class="form-row">
          <label>Telefoon<input type="tel" name="phone"></label>
          <label>Plaats<input name="city"></label>
        </div>
        <label>Bericht *<textarea name="message" required></textarea></label>
        <p class="form-note">Door te versturen stemt u in met de verwerking van uw gegevens voor deze aanvraag.</p>
        <button class="btn btn-primary" type="submit">Bericht versturen</button>
      </form>
      <div>
        <h2>Mimu Garten</h2>
        <p>Schipperswal 32<br>6041 TC Roermond, Nederland</p>
        <p><a href="tel:+31475252151">+31 (0)475 252 151</a><br><a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a></p>
        <p><a class="btn btn-outline" href="{CONFIG_NL}">Naar de configurator</a></p>
        <div class="split-media map-embed" style="margin-top:1.5rem"><iframe src="https://maps.google.com/maps?q=Schipperswal%2032%2C%206041%20TC%20Roermond&t=m&z=13&output=embed&iwloc=near" loading="lazy" title="Kaart"></iframe></div>
      </div>
    </div></section>'''


def simple_prose(lang, depth, eyebrow, h1, paragraphs, extra=""):
    cfg = CONFIG_NL if lang == "nl" else CONFIG_DE
    label = "Configurator" if lang == "nl" else "Konfigurator"
    paras = "\n".join(f"<p>{p}</p>" for p in paragraphs)
    return f'''<section class="hero hero--compact"><div class="container">
      <span class="eyebrow">{eyebrow}</span><h1>{h1}</h1>
      <div class="hero-actions"><a class="btn btn-primary" href="{cfg}">{label}</a></div>
    </div></section>
    <section class="section"><div class="container prose">{paras}{extra}</div></section>
    {showroom_cta(lang, depth)}
    {info_block(lang, depth)}'''


def register_all():
    # HOME
    add_page(lang="de", out="index.html", canonical="/", hreflang_de="/", hreflang_nl="/nl/",
             title="Beste Terrassenüberdachungen für NRW aus Roermond",
             description="Mit einer hochwertigen Terrassenüberdachung genießen Sie Ihre Terrasse bei jedem Wetter und schaffen einen komfortablen Wohnbereich im Freien.",
             body=home_de(0), og_image="68c3c145cd34af3e61e6eeb0_DSC03674-2-1024x683.avif")
    add_page(lang="nl", out="nl/index.html", canonical="/nl/", hreflang_de="/", hreflang_nl="/nl/",
             title="Beste Terrasoverkappingen voor NRW uit Roermond",
             description="Met een hoogwaardige terrasoverkapping geniet u bij elk weer van uw terras en creëert u een comfortabele buitenruimte.",
             body=home_nl(1), og_image="68c3c145cd34af3e61e6eeb0_DSC03674-2-1024x683.avif")

    # Product / content pages DE
    de_pages = [
        ("uberdachung/index.html", "/uberdachung/", "/nl/overkapping/", "Überdachung - Mimu Garten",
         "Das Leben draußen sollte nicht vom Wetter abhängen. Mit einer individuell geplanten Terrassenüberdachung von Mimu Garten schaffen Sie einen geschützten Wohnbereich im Freien.",
         "Terrassenüberdachungen nach Maß", "Entdecken Sie die Qualität und Präzision von Mimu Garten.",
         ["Das Leben draußen sollte nicht vom Wetter abhängen. Mit einer individuell geplanten Terrassenüberdachung von Mimu Garten schaffen Sie einen geschützten und stilvollen Wohnbereich im Freien.",
          "Unsere maßgefertigten Lösungen verbinden hochwertiges Design, langlebige Materialien und präzise Verarbeitung — perfekt abgestimmt auf Ihr Haus.",
          "Wir arbeiten ausschließlich mit eigenen Montageteams und bieten keine Bausätze an."]),
        ("wintergarten/index.html", "/wintergarten/", "/nl/serre/", "Wintergärten - Mimu Garten",
         "Ein Wintergarten ist weit mehr als nur ein Anbau. Er verbindet Ihr Zuhause mit dem Garten und schafft einen lichtdurchfluteten Raum.",
         "Wintergärten nach Maß", "Erleben Sie den Unterschied mit Mimu Garten.",
         ["Ein Wintergarten verbindet Ihr Zuhause mit dem Garten und schafft einen lichtdurchfluteten Raum voller Wohnqualität.",
          "Unsere Wintergärten werden aus robustem Aluminium und hochwertigem Sicherheitsglas gefertigt — wetterbeständig und pflegeleicht.",
          "Von der Beratung bis zur Montage erhalten Sie alles aus einer Hand."]),
        ("sonnenschutz-fur-terrassenuberdachungen/index.html", "/sonnenschutz-fur-terrassenuberdachungen/", "/nl/zonwering-voor-terrasoverkappingen/",
         "Sonnenschutz für Terrassenüberdachungen - Mimu Garten",
         "Unser Sonnenschutz für Terrassenüberdachungen wurde entwickelt, um maximalen Komfort und effektiven Hitzeschutz zu bieten.",
         "Sonnenschutz", "Genießen Sie Ihre Terrasse — mit optimalem Sonnenschutz",
         ["Effektiver Hitzeschutz, langlebige Materialien und maßgeschneiderte Lösungen für Ihre Überdachung.",
          "Unterdach- und Aufdachmarkisen, optional mit Somfy-Motorisierung.",
          "Standardfarbe RAL 7016 Anthrazit Struktur — weitere RAL-Farben auf Anfrage."]),
        ("glasschiebewande/index.html", "/glasschiebewande/", "/nl/glazen-schuifwanden/", "Glasschiebewände - Mimu Garten",
         "Eine Glasschiebewand bietet ein luxuriöses und funktionales Upgrade und schafft einen geschützten Wohnraum für das ganze Jahr.",
         "Glasschiebewände", "Mehr Licht. Mehr Raum. Jederzeit geschützt.",
         ["Premium-Glasoptionen mit 10 mm ESG, modularen Schienensystemen und robuster Aluminiumkonstruktion.",
          "Standardfarbe RAL 7016 — weitere RAL-Farben erhältlich.",
          "Ideal als Upgrade für bestehende und neue Terrassenüberdachungen."]),
        ("pergamon-aluminium-terrassenuberdachung/index.html", "/pergamon-aluminium-terrassenuberdachung/", "/nl/pergamon-aluminium-terrasoverkapping/",
         "Pergamon Aluminium Terrassenüberdachung - Mimu Garten",
         "Die Pergamon-Serie steht für maximale Stabilität, große Spannweiten und eine hochwertige Verarbeitung bis ins Detail.",
         "Pergamon Aluminium Veranda", "Robuste Premium-Überdachung mit statischer Berechnung.",
         ["Große Spannweiten von bis zu 600 × 400 cm mit Glasdach auf nur zwei Pfosten.",
          "Extra starke Profile, Statik nach deutscher Norm, modular erweiterbar mit Glasschiebewänden, Sonnenschutz und LED.",
          "Standard RAL 7016 Anthrazit Struktur — weitere Farben auf Anfrage."]),
        ("unsere-produkte/index.html", "/unsere-produkte/", "/nl/onze-producten/", "Unsere Produkte - Mimu Garten",
         "Entdecken Sie unsere hochwertigen Lösungen: Überdachungen, Wintergärten, Sonnenschutz, Glasschiebewände und Pergamon.",
         "Unsere Produkte", "Hochwertige Lösungen für Ihren Außenbereich",
         ["Von stabilen Überdachungen bis zu flexiblen Glasschiebewänden — alles aus eigener Produktion.",
          "Die Pergamon ist unsere stärkste Konstruktion mit Statik für den deutschen Markt.",
          "Konfigurieren Sie Ihre Wunschüberdachung online oder besuchen Sie unseren Showroom in Roermond."]),
        ("montage-und-service/index.html", "/montage-und-service/", "/nl/montage-en-service/", "Montage und Service - Mimu Garten",
         "Eine hochwertige Terrassenüberdachung ist nur dann wirklich wertvoll, wenn Montage und Service stimmen.",
         "Montage und Service", "Professionelle Montage aus einer Hand",
         ["Eigenes Montageteam, klare Abläufe und 10 Jahre Garantie auf Produkt und fachgerechte Montage.",
          "Keine Bausätze — wir übernehmen Planung, Fertigung und Montage komplett.",
          "Die meisten Projekte sind innerhalb von 1–2 Tagen montiert."]),
        ("showroom-roermond/index.html", "/showroom-roermond/", "/nl/showroom-roermond/", "Showroom Roermond - Mimu Garten",
         "Besuchen Sie den Mimu Garten Showroom in Roermond neben dem Designer Outlet Center.",
         "Showroom Roermond", "Erleben Sie Qualität vor Ort",
         ["Schipperswal 32, 6041 TC Roermond — neben dem Designer Outlet Center.",
          "Öffnungszeiten: Mo–Sa 09:00–17:00, So 12:00–17:00.",
          "Vereinbaren Sie optional einen Beratungstermin für eine ausführliche Planung."]),
        ("terrassenueberdachung/index.html", "/terrassenueberdachung/", "/nl/terrassenueberdachung/", "Terrassenüberdachung Roermond - Mimu Garten",
         "Hersteller aus Holland · Showroom in Roermond — hochwertige Terrassenüberdachungen für NRW.",
         "Terrassenüberdachung Roermond", "Hersteller aus Holland · Showroom in Roermond",
         ["Mimu Garten fertigt und montiert Terrassenüberdachungen für Kunden in den Niederlanden und NRW.",
          "Maßanfertigung, eigene Produktion und professionelle Montage mit 10 Jahren Garantie.",
          "Starten Sie im Konfigurator oder besuchen Sie unseren Showroom."]),
    ]

    for out, canon, nl_peer, title, desc, eye, h1, paras in de_pages:
        d = depth_for(out)
        extra = ""
        if "sonnenschutz" in out:
            extra = f'''<div class="grid grid--2" style="margin-top:1.5rem">
              <div class="card"><img src="{img("Untitled-design-2.png", d)}" alt="Sonnenschutz Option" loading="lazy"></div>
              <div class="card"><img src="{img("Untitled-design-3.png", d)}" alt="Sonnenschutz Option" loading="lazy"></div>
              <div class="card"><img src="{img("Untitled-design-4.png", d)}" alt="Sonnenschutz Option" loading="lazy"></div>
              <div class="card"><img src="{img("Untitled-design-5.png", d)}" alt="Sonnenschutz Option" loading="lazy"></div>
            </div>'''
        if "montage" in out:
            extra = f'''<div class="grid grid--2" style="margin-top:1.5rem">
              <div class="split-media"><img src="{img("ChatGPT-Image-25-mei-2026-14_15_39-1024x768.png", d)}" alt="Montage" loading="lazy"></div>
              <div class="split-media"><img src="{img("ChatGPT-Image-25-mei-2026-14_39_46-768x1024.png", d)}" alt="Service" loading="lazy"></div>
            </div>'''
        if "showroom" in out:
            extra = f'''<div class="split-media" style="margin-top:1.5rem"><img src="{img("Mimu-Showroom-scaled.jpg", d)}" alt="Showroom" loading="lazy"></div>'''
        add_page(lang="de", out=out, canonical=canon, hreflang_de=canon, hreflang_nl=nl_peer,
                 title=title, description=desc, body=simple_prose("de", d, eye, h1, paras, extra))

    nl_pages = [
        ("nl/overkapping/index.html", "/nl/overkapping/", "/uberdachung/", "Overkapping - Mimu Garten",
         "Het buitenleven zou niet afhankelijk moeten zijn van het weer. Met een terrasoverkapping op maat van Mimu Garten geniet u meer van buiten.",
         "Terrasoverkappingen op maat", "Ontdek de kwaliteit en precisie van Mimu Garten.",
         ["Met een individueel geplande terrasoverkapping creëert u een beschermde, stijlvolle buitenruimte.",
          "Hoogwaardig design, duurzame materialen en precieze afwerking — afgestemd op uw woning.",
          "Wij werken uitsluitend met eigen montageteams en bieden geen bouwpakketten aan."]),
        ("nl/serre/index.html", "/nl/serre/", "/wintergarten/", "Wintertuinen - Mimu Garten",
         "Een wintertuin is veel meer dan een aanbouw. Hij verbindt uw woning met de tuin en zorgt voor meer licht en woonruimte.",
         "Wintertuinen op maat", "Ervaar het verschil met Mimu Garten.",
         ["Een wintertuin verbindt binnen en buiten tot een lichte, comfortabele leefruimte.",
          "Robuust aluminium en hoogwaardig veiligheidsglas — weersbestendig en onderhoudsarm.",
          "Van advies tot montage alles uit één hand."]),
        ("nl/zonwering-voor-terrasoverkappingen/index.html", "/nl/zonwering-voor-terrasoverkappingen/", "/sonnenschutz-fur-terrassenuberdachungen/",
         "Zonwering voor terrasoverkappingen - Mimu Garten",
         "Onze zonwering voor terrasoverkappingen is ontworpen voor maximaal comfort en effectieve hittebescherming.",
         "Zonwering", "Geniet van uw terras — met optimale zonwering",
         ["Effectieve hittebescherming, duurzame materialen en oplossingen op maat.",
          "Onderdak- en opdakmarkiezen, optioneel met Somfy-motor.",
          "Standaard RAL 7016 — andere RAL-kleuren op aanvraag."]),
        ("nl/glazen-schuifwanden/index.html", "/nl/glazen-schuifwanden/", "/glasschiebewande/", "Glazen schuifwanden - Mimu Garten",
         "Een glazen schuifwand biedt een luxe en functionele upgrade en creëert een beschermde woonruimte voor het hele jaar.",
         "Glazen schuifwanden", "Meer licht. Meer ruimte. Altijd beschermd.",
         ["Premium glasopties met 10 mm gehard veiligheidsglas en modulaire railsystemen.",
          "Standaard RAL 7016 — andere kleuren beschikbaar.",
          "Ideaal als upgrade voor bestaande en nieuwe overkappingen."]),
        ("nl/pergamon-aluminium-terrasoverkapping/index.html", "/nl/pergamon-aluminium-terrasoverkapping/", "/pergamon-aluminium-terrassenuberdachung/",
         "Pergamon Aluminium Terrasoverkapping - Mimu Garten",
         "De Pergamon-serie staat voor maximale stabiliteit, grote overspanningen en hoogwaardige afwerking.",
         "Pergamon Aluminium Veranda", "Robuuste premium-overkapping met statische berekening.",
         ["Grote overspanningen tot 600 × 400 cm met glasdak op slechts twee staanders.",
          "Extra sterke profielen, statiek volgens Duitse norm, modulair uitbreidbaar.",
          "Standaard RAL 7016 — andere kleuren op aanvraag."]),
        ("nl/onze-producten/index.html", "/nl/onze-producten/", "/unsere-produkte/", "Onze producten - Mimu Garten",
         "Ontdek onze hoogwaardige oplossingen: overkappingen, wintertuinen, zonwering, glazen schuifwanden en Pergamon.",
         "Onze producten", "Hoogwaardige oplossingen voor uw buitenruimte",
         ["Van stabiele overkappingen tot flexibele glazen schuifwanden — alles uit eigen productie.",
          "Pergamon is onze sterkste constructie met statiek voor de Duitse markt.",
          "Configureer online of bezoek onze showroom in Roermond."]),
        ("nl/montage-en-service/index.html", "/nl/montage-en-service/", "/montage-und-service/", "Montage en service - Mimu Garten",
         "Een hoogwaardige terrasoverkapping is pas echt waardevol als montage en service kloppen.",
         "Montage en service", "Professionele montage uit één hand",
         ["Eigen montageteam, duidelijke planning en 10 jaar garantie op product en montage.",
          "Geen bouwpakketten — wij verzorgen planning, productie en montage volledig.",
          "De meeste projecten zijn binnen 1–2 dagen gemonteerd."]),
        ("nl/showroom-roermond/index.html", "/nl/showroom-roermond/", "/showroom-roermond/", "Showroom Roermond - Mimu Garten",
         "Bezoek de Mimu Garten showroom in Roermond naast het Designer Outlet Center.",
         "Showroom Roermond", "Beleef kwaliteit ter plaatse",
         ["Schipperswal 32, 6041 TC Roermond — naast Designer Outlet Center.",
          "Openingstijden: ma–za 09:00–17:00, zo 12:00–17:00.",
          "Optioneel een adviesafspraak voor een uitgebreide planning."]),
        ("nl/terrassenueberdachung/index.html", "/nl/terrassenueberdachung/", "/terrassenueberdachung/", "Terrasoverkapping Roermond - Mimu Garten",
         "Fabrikant uit Nederland · Showroom in Roermond — hoogwaardige terrasoverkappingen voor NRW.",
         "Terrasoverkapping Roermond", "Fabrikant uit Nederland · Showroom in Roermond",
         ["Mimu Garten produceert en monteert terrasoverkappingen voor klanten in Nederland en NRW.",
          "Maatwerk, eigen productie en professionele montage met 10 jaar garantie.",
          "Start in de configurator of bezoek onze showroom."]),
    ]

    for out, canon, de_peer, title, desc, eye, h1, paras in nl_pages:
        d = depth_for(out)
        add_page(lang="nl", out=out, canonical=canon, hreflang_de=de_peer, hreflang_nl=canon,
                 title=title, description=desc, body=simple_prose("nl", d, eye, h1, paras))

    # Contact
    add_page(lang="de", out="contact/index.html", canonical="/contact/", hreflang_de="/contact/", hreflang_nl="/nl/contact/",
             title="Kontakt - Mimu Garten",
             description="Kontaktieren Sie Mimu Garten in Roermond für eine kostenlose Beratung zu Terrassenüberdachungen.",
             body=contact_body("de", 1))
    add_page(lang="nl", out="nl/contact/index.html", canonical="/nl/contact/", hreflang_de="/contact/", hreflang_nl="/nl/contact/",
             title="Contact - Mimu Garten",
             description="Neem contact op met Mimu Garten in Roermond voor gratis advies over terrasoverkappingen.",
             body=contact_body("nl", 2))

    # Thanks
    add_page(lang="de", out="danke/index.html", canonical="/danke/", hreflang_de="/danke/", hreflang_nl="/nl/dank-u/",
             title="Vielen Dank! - Mimu Garten", description="Vielen Dank für Ihre Nachricht.",
             body='''<section class="section"><div class="container prose"><h1>Vielen Dank!</h1>
             <p>Wir haben Ihre Nachricht erhalten und melden uns schnellstmöglich.</p>
             <p><a class="btn btn-primary" href="/">Zur Startseite</a>
             <a class="btn btn-outline" href="''' + CONFIG_DE + '''">Zum Konfigurator</a></p></div></section>''')
    add_page(lang="nl", out="nl/dank-u/index.html", canonical="/nl/dank-u/", hreflang_de="/danke/", hreflang_nl="/nl/dank-u/",
             title="Hartelijk dank! - Mimu Garten", description="Dank u wel voor uw bericht.",
             body='''<section class="section"><div class="container prose"><h1>Hartelijk dank!</h1>
             <p>We hebben uw bericht ontvangen en nemen zo snel mogelijk contact op.</p>
             <p><a class="btn btn-primary" href="/nl/">Naar home</a>
             <a class="btn btn-outline" href="''' + CONFIG_NL + '''">Naar configurator</a></p></div></section>''')

    # Cookie policies
    cookie_de = '''<section class="section"><div class="container prose">
      <h1>Cookie Policy (EU)</h1>
      <p>Diese Website verwendet notwendige Cookies sowie optionale Analyse- und Marketing-Cookies (über CookieYes und Google Tags), um die Website zu betreiben und Anfragen zu verbessern.</p>
      <p>Sie können Ihre Einwilligung jederzeit über das Cookie-Banner ändern. Kontakt: <a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a>.</p>
      <h2>Verantwortlich</h2>
      <p>Mimu Garten B.V., Schipperswal 32, 6041 TC Roermond, Niederlande.</p>
    </div></section>'''
    cookie_nl = '''<section class="section"><div class="container prose">
      <h1>Cookiebeleid (EU)</h1>
      <p>Deze website gebruikt noodzakelijke cookies en optionele analyse-/marketingcookies (via CookieYes en Google Tags) om de site te laten werken en aanvragen te verbeteren.</p>
      <p>U kunt uw toestemming via de cookiebanner wijzigen. Contact: <a href="mailto:info@mimugarten.nl">info@mimugarten.nl</a>.</p>
      <h2>Verantwoordelijke</h2>
      <p>Mimu Garten B.V., Schipperswal 32, 6041 TC Roermond, Nederland.</p>
    </div></section>'''
    add_page(lang="de", out="cookie-policy-eu/index.html", canonical="/cookie-policy-eu/", hreflang_de="/cookie-policy-eu/", hreflang_nl="/nl/cookiebeleid-eu/",
             title="Cookie Policy (EU) - Mimu Garten", description="Cookie Policy der Website mimugarten.nl.", body=cookie_de)
    add_page(lang="nl", out="nl/cookiebeleid-eu/index.html", canonical="/nl/cookiebeleid-eu/", hreflang_de="/cookie-policy-eu/", hreflang_nl="/nl/cookiebeleid-eu/",
             title="Cookiebeleid (EU) - Mimu Garten", description="Cookiebeleid van mimugarten.nl.", body=cookie_nl)


def write_sitemap():
    urls = []
    for p in PAGES:
        urls.append(f"  <url><loc>{SITE}{p['canonical']}</loc></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    write(ROOT / "sitemap.xml", xml)


def write_robots():
    write(ROOT / "robots.txt", f"""User-agent: *
Allow: /

Sitemap: {SITE}/sitemap.xml
""")


def write_redirects():
    # Netlify _redirects — configurator stays on origin Hostinger when DNS split;
    # if entire domain is on Netlify, proxy/external note is in README.
    write(ROOT / "_redirects", """# Clean URL helpers
/uberdachung              /uberdachung/              301
/wintergarten             /wintergarten/             301
/contact                  /contact/                  301
/nl                       /nl/                       301

# Configurator stays on Hostinger (external). If this site is deployed on the
# same Hostinger account beside /configurator/, remove the next line.
# /configurator/*  https://mimugarten.nl/configurator/:splat  200!
""")


def write_netlify():
    write(ROOT / "netlify.toml", """[build]
  publish = "."
  command = "python3 build.py"

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "SAMEORIGIN"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"

# Keep /configurator on Hostinger. If DNS points only here, set up a reverse
# proxy or subdomain (e.g. configurator.mimugarten.nl) and update CTAs.
""")


def main():
    register_all()
    for page in PAGES:
        write(ROOT / page["out"], shell(page))
    write_sitemap()
    write_robots()
    write_redirects()
    write_netlify()
    # Netlify forms detection needs a form in published HTML (already in contact pages)
    print(f"Generated {len(PAGES)} pages.")


if __name__ == "__main__":
    main()
