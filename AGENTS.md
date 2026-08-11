## Site

Static HTML rebuild of mimugarten.nl. No WordPress. No build step required at runtime (optional generator: `python3 build.py`).

Preview locally:

```
python3 -m http.server 4321
```

Deploy: upload this folder to Netlify (publish directory = `.`) **or** replace the WordPress docroot on Hostinger while leaving `/configurator/` intact.

Configurator stays external: `/configurator/?lang=de|nl` on Hostinger.
