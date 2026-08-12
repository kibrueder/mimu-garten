# Mimu Garten — static clone

Exact visual clone of [mimugarten.nl](https://mimugarten.nl): live WordPress/Elementor HTML, localized assets, WP runtime JS removed.

## Rebuild from live site

```bash
python3 mirror.py
```

## Preview

```bash
python3 -m http.server 4321
```

Open http://127.0.0.1:4321

## Notes

- **Configurator** stays external: `/configurator/?lang=de|nl` on Hostinger (links unchanged).
- **Contact form** is still Elementor markup visually; wire Netlify/PHP mail separately if needed.
- **Edit content** by changing live WP then re-running `mirror.py`, or patch generated HTML (re-run overwrites).

See [DEPLOY.md](DEPLOY.md) for go-live.
