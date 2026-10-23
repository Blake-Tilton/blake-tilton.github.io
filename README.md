# blake-tilton.github.io

Portfolio for Blake Tilton. Static site on GitHub Pages — no build server, no framework.

## Editing

- **Words and layout:** edit `tools/index.src.html`, then run `python3 tools/build.py` to regenerate `index.html`.
  - `<x-img slug="..." alt="..." sizes="...">` becomes a responsive image.
  - `<x-video slug="..." kind="reel|loop" label="...">` becomes a video with a poster.
- **Styles:** `assets/css/site.css` (colors and sizes are variables at the top).
- **Behavior:** `assets/js/site.js` (tabs/routing, gallery filter, lightbox, contact form).

## Adding media

1. Put the source file in `~/Documents/Resume/Work/...`.
2. Add a line to `IMAGES` or `VIDEOS` in `tools/media.py`.
3. Run `python3 tools/media.py --only <slug>` (add `--images` to skip video), then `python3 tools/build.py`.

Video tools are small Swift helpers; compile once with the commands at the top of `tools/media.py`.

## Contact form

Posts to a Google Apps Script web app that logs to a Sheet and emails Blake. The email address is never in this repo.

## Preview locally

```
python3 -m http.server 8765
```
