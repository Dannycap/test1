Patch Kit for Dannycap/test1
============================

This zip contains ONLY the files you need to replace or add so GitHub Pages works at:
https://dannycap.github.io/test1/

Files included:
- web/next.config.js                     (sets basePath/assetPrefix to /test1)
- .github/workflows/deploy.yml           (builds web and publishes to Pages)
- backend/app.py                         (CORS allowlist for your Pages + localhost)
- web/public/config.json                 (placeholder backend URL)

How to apply:
1) Unzip into your repo root (it will create/overwrite these paths).
2) Review changes if prompted, then commit and push:

   git add .
   git commit -m "Configure GH Pages and CORS for test1"
   git push

3) Enable GitHub Pages in repo Settings → Pages → GitHub Actions.
4) After the workflow finishes, your site is at:
   https://dannycap.github.io/test1/

Next step for backend:
- Deploy FastAPI (Render/Fly/Railway/etc.).
- Put the live URL into web/public/config.json (apiUrl).
- Push again to redeploy the Pages site with correct API endpoint.
