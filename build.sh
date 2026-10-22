#!/bin/bash
# Builds docs/index.html (served by GitHub Pages) from the master single-file app.
# Usage: ./build.sh [path/to/Index.html]
set -euo pipefail
SRC="${1:-$HOME/Documents/SSVM/SSVM Rota app/Index.html}"
cd "$(dirname "$0")"
mkdir -p build docs

# 1. Split the master file: inline <style> and the text/babel app script
python3 - "$SRC" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
css = re.search(r"<style>(.*?)</style>", s, re.S).group(1)
app = re.search(r'<script type="text/babel">(.*)</script>\s*</body>', s, re.S).group(1)
open("build/custom.css", "w", encoding="utf-8").write(css)
open("build/app.jsx", "w", encoding="utf-8").write(app)
PY

# 2. Compile JSX once here instead of in every visitor's browser
npx --yes esbuild@0.24.2 build/app.jsx --loader:.jsx=jsx --target=es2019 --minify --outfile=build/app.js --log-level=warning

# 3. Generate only the Tailwind classes the app uses
cat > build/tw.css <<'CSS'
@tailwind base;
@tailwind components;
@tailwind utilities;
CSS
npx --yes tailwindcss@3.4.17 -i build/tw.css -o build/tailwind.css --content build/app.jsx --minify 2>/dev/null

# 4. Assemble the final page
python3 - <<'PY'
css = open("build/tailwind.css", encoding="utf-8").read() + open("build/custom.css", encoding="utf-8").read()
js = open("build/app.js", encoding="utf-8").read().replace("</script", "<\\/script")
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>
<meta name="theme-color" content="#4f46e5"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-title" content="SSVM Rota"/>
<title>SSVM Volunteer Rota</title>
<link rel="icon" type="image/svg+xml" href="icons/icon.svg"/>
<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png"/>
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png"/>
<link rel="manifest" href="manifest.webmanifest"/>
<style>{css}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.3.1/umd/react.production.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.3.1/umd/react-dom.production.min.js"></script>
</head>
<body class="bg-slate-50">
<div id="root"></div>
<script>{js}</script>
</body>
</html>
"""
open("docs/index.html", "w", encoding="utf-8").write(html)
PY
touch docs/.nojekyll
ls -la docs/index.html
