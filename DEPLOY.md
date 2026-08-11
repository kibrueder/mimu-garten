# Deploy: static marketing + Hostinger configurator

## Recommended (same domain)

Keep **Hostinger** as the origin for `mimugarten.nl` so `/configurator/` keeps working:

1. Back up the current WordPress install.
2. Upload this static site into `public_html` (or the site root), **without deleting** the existing `configurator/` folder.
3. Remove / disable WordPress files that conflict with static paths (`index.php`, WP core) once static `index.html` is in place.
4. Confirm:
   - `https://mimugarten.nl/` serves the new static home
   - `https://mimugarten.nl/configurator/?lang=de` still loads THE REAL MAG app
   - Contact form: if not using Netlify, change forms in `build.py` to a PHP mail endpoint or Formspree, then rebuild

## Alternative (Netlify for marketing)

1. Deploy this repo to Netlify (publish = `.`, build command `python3 build.py` or pre-build locally).
2. Point the apex/www DNS to Netlify **only if** you also keep the configurator reachable:
   - **Option A:** Subdomain on Hostinger, e.g. `configurator.mimugarten.nl` → update all CTA URLs in `build.py` (`CONFIG_DE` / `CONFIG_NL`), rebuild.
   - **Option B:** Reverse proxy `/configurator/*` from Netlify to Hostinger (Netlify redirects/edge proxy to the Hostinger origin).
3. Enable Netlify Forms in the UI so `contact` / `contact-nl` submissions arrive by email.

## Do not

- Delete `/configurator/` or `/configurator/phpfiles/` on Hostinger.
- Point the whole domain at Netlify without a plan for the PHP configurator.
- Clone Domiveranda’s calculator (branded third-party app).

## Checklist after go-live

- [ ] DE + NL pages load, language switch works
- [ ] Images load from `/assets/img/`
- [ ] Konfigurator / Configurator buttons open live configurator with correct `lang`
- [ ] Google Ads / CookieYes fire on marketing pages
- [ ] Contact form delivers mail
- [ ] `sitemap.xml` / `robots.txt` reachable
- [ ] Old WP admin locked down or removed
