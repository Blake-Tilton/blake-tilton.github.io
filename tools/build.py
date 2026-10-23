"""Expand tools/index.src.html into index.html using assets/media.json.

Usage:  python3 tools/build.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools/index.src.html"
OUT = ROOT / "index.html"
MEDIA = json.loads((ROOT / "assets/media.json").read_text())


def attrs(tag: str) -> dict:
    found = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
    for flag in re.findall(r'\s(\w+)(?=[\s>])', tag):
        if flag not in found and flag not in ("x",):
            found[flag] = True
    return found


def info(slug: str) -> dict:
    if slug not in MEDIA:
        raise SystemExit(f"build: no media named {slug!r} in assets/media.json (run tools/media.py)")
    return MEDIA[slug]


def img_tag(m: re.Match) -> str:
    a = attrs(m.group(0))
    slug, d = a["slug"], info(a["slug"])
    sizes = d["sizes"]
    srcset = ", ".join(f"assets/img/{slug}-{w}.webp {w}w" for w in sizes)
    cls = f' class="{a["class"]}"' if "class" in a else ""
    load = 'fetchpriority="high"' if a.get("eager") else 'loading="lazy"'
    return (f'<img src="assets/img/{slug}-{sizes[0]}.webp" srcset="{srcset}" sizes="{a.get("sizes", "100vw")}" '
            f'width="{d["w"]}" height="{d["h"]}" alt="{html.escape(a.get("alt", ""), quote=True)}"{cls} {load} decoding="async">')


def video_tag(m: re.Match) -> str:
    a = attrs(m.group(0))
    slug, d = a["slug"], info(a["slug"])
    poster = f"assets/img/{slug}-poster-{d['sizes'][-1]}.webp"
    label = html.escape(a.get("label", ""), quote=True)
    src = f'<source src="assets/video/{slug}.mp4" type="video/mp4">'
    if a.get("kind") == "loop":
        return (f'<figure class="vid vid-loop"><video data-loop muted loop playsinline preload="none" poster="{poster}" '
                f'width="{d["w"]}" height="{d["h"]}" aria-label="{label}">{src}</video></figure>')
    return (f'<figure class="vid"><video controls playsinline preload="none" poster="{poster}" '
            f'width="{d["w"]}" height="{d["h"]}" aria-label="{label}">{src}</video>'
            f'<figcaption>{label} <span>{d.get("mb", "")} MB</span></figcaption></figure>')


def full_url(m: re.Match) -> str:
    slug = m.group(1)
    return f"assets/img/{slug}-{info(slug)['sizes'][-1]}.webp"


def main():
    text = SRC.read_text()
    text = re.sub(r"<!-- SOURCE for index.html.*?-->\n", "<!-- Generated from tools/index.src.html by tools/build.py. Edit the source, not this file. -->\n", text, flags=re.S)
    text = re.sub(r"<x-img\b[^>]*>", img_tag, text)
    text = re.sub(r"<x-video\b[^>]*>", video_tag, text)
    text = re.sub(r"\{\{full:([\w-]+)\}\}", full_url, text)
    # spec lines break only between segments, never inside "2013–2026"
    text = re.sub(r'(<p class="spec">)(.*?)(</p>)',
                  lambda m: m[1] + " · ".join(f'<span>{s}</span>' for s in m[2].split(" · ")) + m[3], text)
    OUT.write_text(text)
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
