"""Build web media for the site from the source files in ~/Documents/Resume/Work.

Usage:  python3 tools/media.py [--only SLUG] [--images]

Images -> assets/img/<slug>-<w>.webp at each width in SIZES (never upscaled).
Videos -> assets/video/<slug>.mp4 (H.264) + assets/img/<slug>-poster-<w>.webp.
Writes assets/media.json with dimensions so the HTML can set width/height.

Videos need the Swift helpers compiled once (macOS):
  swiftc -O -o tools/bin/transcode tools/transcode.swift
  swiftc -O -o tools/bin/poster tools/poster.swift
  swiftc -O -o tools/bin/pdfpage tools/pdfpage.swift
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

WORK = Path.home() / "Documents/Resume/Work"
ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets/img"
VID = ROOT / "assets/video"
BIN = ROOT / "tools/bin"

# slug: (source relative to WORK, widths)
CONTENT = (800, 1600)   # project media in a detail panel
GALLERY = (800, 1200, 2000)   # personal gallery: grid tile (1x/2x) + full view
IMAGES = {
    "headshot":             ("Pro Pic.jpg", (240, 480)),

    "st-fb-camera":         ("School/Joey FB Cam.JPG", CONTENT),
    "st-bn-guide":          ("School/BN Guide 240131.pdf", CONTENT),

    "pbc-booth":            ("Church/PBC Media Photo.png", CONTENT),
    "pbc-logo":             ("Church/PBC Logo V TW on Grey.png", CONTENT),
    "pbc-first-christmas":  ("Sermon Series/FirstChristmas Full.png", CONTENT),
    "pbc-grab-a-corner":    ("Sermon Series/GAC Title.png", CONTENT),
    "pbc-membership":       ("Sermon Series/Membership Matters Title.jpg", CONTENT),
    "pbc-new-beginnings":   ("Sermon Series/New Beginnings Title.jpg", CONTENT),
    "pbc-palm-sunday":      ("Sermon Series/Palm Sunday 23 Title.jpg", CONTENT),
    "pbc-to-be-continued":  ("Sermon Series/To Be Continued Title.jpg", CONTENT),

    "nl-kids-wall":         ("Church/NL/16e0e418-88ab-4b25-95db-834fa7a5573b_rw_1920.JPG", CONTENT),
    "nl-master-plan":       ("Church/NL/38a26a7f-da21-46f8-a3e4-8d15970fbbef_rw_1920.jpg", CONTENT),
    "nl-join-us":           ("Church/NL/5df22c7a-8f19-4de8-928f-11b4f2e48a62_rw_3840.jpg", CONTENT),
    "nl-cards":             ("Church/NL/65eec586-b72f-49b5-b3a8-55d46dc5a006_rw_1920.jpg", CONTENT),
    "nl-next-step":         ("Church/NL/6fbbe646-c862-4eac-bd17-25ee03d33623_rw_1920.jpg", CONTENT),
    "nl-cup":               ("Church/NL/abe27409-1193-4aa5-98ce-85874d50e5bd_rw_1920.jpg", CONTENT),
    "nl-connect":           ("Church/NL/e0ef21fe-719b-4184-b0ab-4607cd207968_rw_1920.jpg", CONTENT),

    "ev-game-on":           ("VBS Camp/b817d172-03f6-4864-b808-8130269a97a1_rw_1920.jpg", CONTENT),
    "ev-chosen":            ("VBS Camp/5fa36288-bcb7-45c1-bbac-7d7dc279c83c_rw_1200.jpg", CONTENT),
    "ev-trust":             ("VBS Camp/8d537f16-df49-47f1-9940-e94a17d84e4b_rw_1200.jpg", CONTENT),
    "ev-treasure":          ("VBS Camp/13fff2cd-d462-4471-89d3-3c5c4950c8e6_rw_1200.jpg", CONTENT),
    "ev-camp-wannabe":      ("VBS Camp/0e800ba1-40a3-4c57-93ae-382f534cc8e9_rw_1200.jpg", CONTENT),
    "ev-faith":             ("VBS Camp/21457f61-9e0e-4cd2-9a21-a7a1f17f07ed_rw_1200.jpg", CONTENT),

    "p-lounge-chair":       ("Personal/Woodwork/103 Lounge Chair.png", GALLERY),
    "p-lounge-chair-sides": ("Furniture/Lounge Chair sides.png", GALLERY),
    "p-baringer-405":       ("Personal/Illustration/Baringer 405 - 1970s Car Illustration.png", GALLERY),
    "p-wolfman":            ("Personal/Illustration/WolfMan - Ballpoint Pen with Digital Color.png", GALLERY),
    "p-santa":              ("Personal/Illustration/Santa - 2024.png", GALLERY),
    "p-eggshell":           ("Personal/Illustration/EggShell - Digital Paint.png", GALLERY),
    "p-77-tee":             ("Personal/Illustration/77 - T-Shirt Design.png", GALLERY),
    "p-galahad":            ("Personal/Design/Galahad - Logo Design.png", GALLERY),
    "p-moses":              ("Personal/Design/Moses - 80s Logo Design.png", GALLERY),
    "ff-2022-tombstone":    ("Personal/Illustration/FrightFall/Tombstone- FrightFall 2022.jpg", GALLERY),
    "ff-2023-howl":         ("Personal/Illustration/FrightFall/Howl- FrightFall 2023.jpg", GALLERY),
    "ff-2023-mask":         ("Personal/Illustration/FrightFall/Mask- FrightFall  2023.jpg", GALLERY),
    "ff-2024-gargoyle":     ("Personal/Illustration/FrightFall/Gargoyle- FrightFall 2024.png", GALLERY),
    "ff-2025-vampire":      ("Personal/Illustration/FrightFall/Vampire - FrightFall 2025.png", GALLERY),
    "ff-2026-haunted-tape": ("Personal/Illustration/FrightFall/Haunted Tape - FrightFall 2026.png", GALLERY),
}

# slug: (source, max width, video kbps, keep audio, poster at seconds)
VIDEOS = {
    "st-av-reel-2425":    ("School/2425 AV Reel.mp4", 1920, 3500, True, 6),
    "st-showcase-2023":   ("School/ShowCase AV Student Work 23.mp4", 1920, 3500, True, 6),
    "st-bn-sting":        ("School/BN Sting Yellow.mov", 1920, 3000, True, 4),
    "st-sports-package":  ("School/Sports Package.mp4", 1920, 3000, True, 10),
    "pbc-easter-24":      ("Sermon Series/Easter 24 Title Loop.mp4", 1280, 1800, False, 2),
    "pbc-his-mercy":      ("Sermon Series/His Mercy Title Loop.mp4", 1280, 1800, False, 2),
    "pbc-live-by-faith":  ("Sermon Series/LbF Loop Title.mp4", 1280, 1800, False, 2),
    "pbc-more-grace":     ("Sermon Series/More Grace Title Loop.mp4", 1280, 1800, False, 2),
}


def open_source(src: Path) -> Image.Image:
    if src.suffix.lower() == ".pdf":
        tmp = Path(tempfile.mkdtemp())
        subprocess.run([BIN / "pdfpage", src, tmp], check=True)
        return Image.open(tmp / "p1.png")
    return Image.open(src)


def to_rgb(im: Image.Image) -> Image.Image:
    """Flatten transparency onto the site background so logos sit on grey."""
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (63, 63, 63, 255))
        return Image.alpha_composite(bg, im).convert("RGB")
    return im.convert("RGB")


def write_webp(im: Image.Image, slug: str, widths) -> dict:
    im = to_rgb(im)
    out = {"w": im.width, "h": im.height, "sizes": []}
    for w in widths:
        w = min(w, im.width)
        if w in out["sizes"]:
            continue
        h = round(im.height * w / im.width)
        im.resize((w, h), Image.LANCZOS).save(IMG / f"{slug}-{w}.webp", "WEBP", quality=82, method=6)
        out["sizes"].append(w)
    return out


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    IMG.mkdir(parents=True, exist_ok=True)
    VID.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "assets/media.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    for slug, (src, widths) in IMAGES.items():
        if only and slug != only:
            continue
        with open_source(WORK / src) as im:
            im.load()
            manifest[slug] = write_webp(im, slug, widths)
        print("img ", slug, manifest[slug]["sizes"])

    for slug, (src, maxw, kbps, audio, at) in VIDEOS.items():
        if (only and slug != only) or "--images" in sys.argv:
            continue
        out = VID / f"{slug}.mp4"
        r = subprocess.run([BIN / "transcode", WORK / src, out, str(maxw), str(kbps), "1" if audio else "0"])
        if r.returncode:  # some sources (ProRes 4444 + PCM) trip the reader; fall back to Apple's preset
            preset = "Preset1920x1080" if maxw >= 1920 else "Preset1280x720"
            subprocess.run(["avconvert", "-s", WORK / src, "-o", out, "-p", preset, "--replace"], check=True)
        frame = Path(tempfile.mkdtemp()) / "poster.png"
        subprocess.run([BIN / "poster", out, frame, str(at)], check=True)
        with Image.open(frame) as im:
            info = write_webp(im, f"{slug}-poster", (800, 1600))
        info["mb"] = round(out.stat().st_size / 1e6, 1)
        manifest[slug] = info
        print("vid ", slug, f'{info["mb"]} MB')

    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
