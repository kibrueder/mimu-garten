# Mimu Garten — static site

Clean static HTML rebuild of [mimugarten.nl](https://mimugarten.nl) (formerly WordPress + Elementor).

## Preview

```bash
python3 build.py
python3 -m http.server 4321
```

Open http://localhost:4321

## Edit content

- Shared chrome / SEO shell / pages: [`build.py`](build.py)
- Styles: [`assets/css/style.css`](assets/css/style.css)
- Interactions: [`assets/js/main.js`](assets/js/main.js)
- Images: [`assets/img/`](assets/img/)

Re-run `python3 build.py` after editing `build.py`.

## Configurator

Marketing CTAs link to the **existing** app (unchanged):

- DE: `https://mimugarten.nl/configurator/?lang=de`
- NL: `https://mimugarten.nl/configurator/?lang=nl`

Do not put the configurator in this static build. Keep `/configurator/` on Hostinger (PHP render backend). See [DEPLOY.md](DEPLOY.md).

## Tracking & forms

- Google tag: `AW-18058170287` (same as live)
- CookieYes: existing site key
- Contact forms: Netlify Forms (`contact` / `contact-nl`) → thank-you pages

## Deploy

Publish directory = `.` (this folder). Details in [DEPLOY.md](DEPLOY.md).
