## Site

Static HTML clone of mimugarten.nl (WordPress/Elementor source). Rebuild from live: `python3 mirror.py`.

Preview locally:

```
python3 -m http.server 4321
```

Deploy: upload this folder to Netlify (publish directory = `.`) **or** replace the WordPress docroot on Hostinger while leaving `/configurator/` intact.

Configurator stays external: `/configurator/?lang=de|nl` on Hostinger.
