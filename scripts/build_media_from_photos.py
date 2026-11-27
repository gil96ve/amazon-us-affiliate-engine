#!/usr/bin/env python3
"""Compone PNG + MP4 usando fotos reales aportadas por el operador.

Uso:
    python scripts/build_media_from_photos.py

Busca assets/products/<ASIN>.<ext> o assets/products/<slug>.<ext>.
Si existe una segunda foto con sufijo -2, se usa para la variante 2.
No Describe precios ni inventa especificaciones: solo compone la foto
con el hook verificado, el CTA y el disclosure exactos.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PHOTO_DIR = ROOT / "assets" / "products"
MEDIA_ROOT = ROOT / "docs" / "media"
W, H = 1280, 720
REGULAR = Path(r"C:\Windows\Fonts\segoeui.ttf")
BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")
DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
CTA = "Check Latest Price on Amazon"
TAG = "vettedgearlab-20"
EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def find_photo(*stems: str) -> Path | None:
    for stem in stems:
        for suffix in ("", "-2"):
            for ext in EXTENSIONS:
                candidate = PHOTO_DIR / f"{stem}{suffix}{ext}"
                if candidate.is_file():
                    return candidate
    return None


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def wrap_pixels(draw: ImageDraw.ImageDraw, text: str, used: ImageFont.FreeTypeFont,
                max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=used) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def compose(photo: Path, output: Path, variant: int, headline: str,
            subtitle: str, asin: str) -> None:
    accent = "#2ec4a6" if variant == 1 else "#f2b544"
    with Image.open(photo) as source:
        image = source.convert("RGB")

    # Ajuste de portada. La variante 2 desplaza el recorte para dar otro encuadre.
    scale = max(W / image.width, H / image.height) * (1.06 if variant == 2 else 1.0)
    new_size = (max(W, int(image.width * scale)), max(H, int(image.height * scale)))
    image = image.resize(new_size, Image.Resampling.LANCZOS)
    left = max(0, min(image.width - W, int((image.width - W) * (0.25 if variant == 2 else 0.5))))
    top = max(0, min(image.height - H, int((image.height - H) * (0.7 if variant == 2 else 0.4))))
    image = image.crop((left, top, left + W, top + H))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    if variant == 1:
        for x in range(W):
            alpha = int(205 * max(0.0, 1.0 - x / 760))
            overlay_draw.line((x, 0, x, H), fill=(7, 20, 26, alpha))
    else:
        for y in range(H):
            alpha = int(195 * max(0.0, (y - 250) / 470))
            overlay_draw.line((0, y, W, y), fill=(7, 20, 26, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    f_eyebrow, f_head = font(REGULAR, 24), font(BOLD, 58)
    f_sub, f_meta = font(REGULAR, 27), font(REGULAR, 21)
    f_cta, f_small = font(BOLD, 26), font(REGULAR, 16)

    text_y = 150 if variant == 1 else 360
    text_x = 80
    note = "Photo supplied by operator"
    draw.text((80, 60), f"{'01' if variant == 1 else '02'} / PRODUCT MEDIA",
              font=f_eyebrow, fill=accent)
    draw.text((W - 80 - draw.textlength(note, font=f_small), 64), note,
              font=f_small, fill="#d7e2df")

    for line in wrap_pixels(draw, headline, f_head, 620)[:3]:
        draw.text((text_x, text_y), line, font=f_head, fill="#f7faf9")
        text_y += 68
    text_y += 14
    for line in wrap_pixels(draw, subtitle, f_sub, 620)[:2]:
        draw.text((text_x, text_y), line, font=f_sub, fill="#d7e2df")
        text_y += 36

    draw.text((80, 555), asin, font=f_meta, fill="#d7e2df")
    draw.rounded_rectangle((80, 590, 520, 648), radius=14, fill=accent)
    cta_w = draw.textlength(CTA, font=f_cta)
    draw.text((80 + (440 - cta_w) / 2, 603), CTA, font=f_cta, fill="#0d1b24")
    draw.text((80, 675), DISCLOSURE, font=f_small, fill="#d7e2df")
    draw.text((W - 80 - draw.textlength(TAG, font=f_small), 675), TAG,
              font=f_small, fill="#d7e2df")
    image.save(output, "PNG", optimize=True)


def make_clip(ffmpeg: str, image_path: Path, output_path: Path) -> None:
    vf = ("zoompan=z='min(pzoom+0.0005,1.08)':"
          "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          "d=1:s=1280x720:fps=30")
    subprocess.run(
        [ffmpeg, "-y", "-loop", "1", "-framerate", "30", "-i", str(image_path),
         "-vf", vf, "-t", "6", "-an", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output_path)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def main() -> None:
    if not PHOTO_DIR.is_dir():
        print("Sin fotos: crea assets/products/ y copia las imágenes allí.")
        return

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ERROR: ffmpeg no disponible en PATH")

    products = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))["records"]
    assets = json.loads((ROOT / "data" / "content_assets.json").read_text(encoding="utf-8"))["records"]
    asset_by_run = {item["run_id"]: item for item in assets}
    updated: list[str] = []

    for product in products:
        run_id = product["run_id"]
        record = asset_by_run.get(run_id)
        generated = (record or {}).get("generated_media")
        if not generated:
            continue
        asin = product["product"]["asin"]
        slug = generated["images"][0].split("/")[1]
        primary = find_photo(asin, slug)
        # La segunda foto se busca con sufijo -2 de forma explícita.
        second = next(
            (PHOTO_DIR / f"{stem}-2{ext}" for stem in (asin, slug) for ext in EXTENSIONS
             if (PHOTO_DIR / f"{stem}-2{ext}").is_file()),
            None,
        )
        if primary is None:
            continue
        photos = [primary, second or primary]

        target_dir = MEDIA_ROOT / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        for variant in (1, 2):
            make_image = target_dir / f"image-{variant}.png"
            make_clip_path = target_dir / f"clip-{variant}.mp4"
            compose(
                photos[variant - 1], make_image, variant,
                record["hooks"][0], record["title_thumbnail_ideas"][0]["title"], asin,
            )
            make_clip(ffmpeg, make_image, make_clip_path)

        generated["note"] = "Photo supplied by operator; composed locally with PIL/ffmpeg."
        generated["type"] = "operator_photo_composite"
        updated.append(asin)

    if updated:
        (ROOT / "data" / "content_assets.json").write_text(
            json.dumps({"schema_version": "1.0", "records": assets},
                       indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"updated_asins": updated}, ensure_ascii=False))


if __name__ == "__main__":
    main()
