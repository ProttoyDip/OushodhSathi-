"""Synthetic eval images for OushodhSathi: medicine strips/boxes/prescriptions and BP monitor screens.

Every image is drawn in code (HTML rendered by headless Chrome, then photo-like damage with PIL).
No real packaging, logos or manufacturer names. Each image carries a small "SYNTHETIC" mark.
Labels follow eval/labels.csv and eval/bp_labels.csv formats.

  python make_synthetic.py OUT_DIR
"""
from __future__ import annotations

import asyncio
import csv
import io
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from playwright.async_api import async_playwright

FONTS = Path("/home/claude/synthfonts")
F_BN = FONTS / "fontsource-noto-sans-bengali-5.3.0/files/noto-sans-bengali-bengali-700-normal.woff2"
F_BN4 = FONTS / "fontsource-noto-sans-bengali-5.3.0/files/noto-sans-bengali-bengali-400-normal.woff2"
F_HAND = FONTS / "fontsource-caveat-5.3.0/files/caveat-latin-700-normal.woff2"
F_COND = FONTS / "fontsource-roboto-condensed-5.3.0/files/roboto-condensed-latin-700-normal.woff2"
F_COND4 = FONTS / "fontsource-roboto-condensed-5.3.0/files/roboto-condensed-latin-400-normal.woff2"

R = random.Random(20261119)

# brand, generic (display), strength as printed, form, bangla name
MEDS = [
    ("Napa", "Paracetamol", "500 mg", "Tablet", "নাপা"),
    ("Ace", "Paracetamol", "500 mg", "Tablet", "এইস"),
    ("Napa Extra", "Paracetamol + Caffeine", "500 mg + 65 mg", "Tablet", "নাপা এক্সট্রা"),
    ("Seclo", "Omeprazole", "20 mg", "Capsule", "সেকলো"),
    ("Maxpro", "Esomeprazole", "20 mg", "Tablet", "ম্যাক্সপ্রো"),
    ("Sergel", "Esomeprazole", "20 mg", "Tablet", "সার্জেল"),
    ("Camlodin", "Amlodipine", "5 mg", "Tablet", "ক্যামলোডিন"),
    ("Amdocal", "Amlodipine", "5 mg", "Tablet", "অ্যামডোকাল"),
    ("Amdocal Plus", "Amlodipine + Atenolol", "5 mg + 25 mg", "Tablet", "অ্যামডোকাল প্লাস"),
    ("Angilock", "Losartan Potassium", "50 mg", "Tablet", "অ্যানজিলক"),
    ("Osartil", "Losartan Potassium", "50 mg", "Tablet", "ওসারটিল"),
    ("Osartil Plus", "Losartan + Hydrochlorothiazide", "50 mg + 12.5 mg", "Tablet", "ওসারটিল প্লাস"),
    ("Comet", "Metformin Hydrochloride", "500 mg", "Tablet", "কমেট"),
    ("Secrin", "Glimepiride", "2 mg", "Tablet", "সেক্রিন"),
    ("Rivotril", "Clonazepam", "0.5 mg", "Tablet", "রিভোট্রিল"),
    ("Tryptin", "Amitriptyline", "10 mg", "Tablet", "ট্রিপটিন"),
    ("Clofenac", "Diclofenac Sodium", "50 mg", "Tablet", "ক্লোফেনাক"),
    ("Naprosyn", "Naproxen", "250 mg", "Tablet", "ন্যাপ্রোসিন"),
    ("Ecosprin", "Aspirin", "75 mg", "Tablet", "ইকোস্প্রিন"),
    ("Atova", "Atorvastatin", "10 mg", "Tablet", "অ্যাটোভা"),
]
BYNAME = {m[0]: m for m in MEDS}
INKS = ["#c0392b", "#1f4e9c", "#117a43", "#7d3c98", "#b9770e", "#0e6655", "#a93226", "#1a5276"]
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def bn_strength(s: str) -> str:
    return s.translate(BN_DIGITS).replace("mg", "মিগ্রা")


def expiry() -> tuple[str, str]:
    y, m = R.choice([2025, 2026, 2027, 2028]), R.randint(1, 12)
    return f"{y}-{m:02d}", f"{m:02d}/{y}"


_FACES = None


def fontfaces() -> str:
    """Fonts embedded as data URLs (file:// URLs do not load from a set_content page)."""
    global _FACES
    if _FACES is None:
        import base64
        _FACES = "".join(
            f"@font-face{{font-family:{n};src:url(data:font/woff2;base64,{base64.b64encode(p.read_bytes()).decode()}) format('woff2')}}"
            for n, p in [("BN", F_BN), ("BN4", F_BN4), ("HAND", F_HAND), ("COND", F_COND), ("COND4", F_COND4)])
    return _FACES


def page(body: str, w: int, h: int, bg: str = "transparent") -> str:
    return (f"<html><head><style>{fontfaces()} html,body{{margin:0;background:{bg};width:{w}px;height:{h}px;"
            f"overflow:hidden}} *{{box-sizing:border-box}} .syn{{position:absolute;font:10px COND4;color:#0007;"
            f"letter-spacing:1px}}</style></head><body>{body}</body></html>")


def strip_html(med, exp_print: str, bangla: bool) -> tuple[str, int, int]:
    brand, generic, strength, form, bn = med
    ink = R.choice(INKS)
    w, h = 980, 360
    pockets = "".join(
        f"<div style='position:absolute;left:{70 + c * 170}px;top:{60 + r * 140}px;width:110px;height:110px;"
        f"border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff,#cfd3d6 45%,#8e959b);"
        f"box-shadow:inset -6px -8px 12px #0004'></div>"
        for r in range(2) for c in range(5))
    name = (f"<span style='font:700 30px BN'>{bn} {bn_strength(strength)}</span>" if bangla
            else f"<span style='font:700 30px COND'>{brand} {strength}</span>")
    rows = "".join(
        f"<div style='position:absolute;left:{x}px;top:{y}px;color:{ink};transform:rotate(-8deg);white-space:nowrap'>{name}</div>"
        for y in (30, 168, 300) for x in (-40, 330, 700))
    small = (f"<div style='position:absolute;left:20px;bottom:8px;font:400 15px COND4;color:#333'>"
             f"{generic} {strength} {form} &nbsp; Batch: {R.randint(10, 99)}{R.choice('ABCDEFG')}{R.randint(100, 999)}"
             f" &nbsp; MFG: {R.randint(1, 12):02d}/2024 &nbsp; EXP: {exp_print}</div>")
    body = (f"<div style='position:relative;width:{w}px;height:{h}px;border-radius:14px;overflow:hidden;"
            f"background:linear-gradient(115deg,#e9ecef,#b7bdc2 30%,#f4f6f7 50%,#a9b0b6 72%,#dde1e4)'>"
            f"{rows}{pockets}{small}<div class=syn style='right:10px;top:6px'>SYNTHETIC</div></div>")
    return page(body, w, h), w, h


def box_html(med, exp_print: str, bangla: bool) -> tuple[str, int, int]:
    brand, generic, strength, form, bn = med
    ink = R.choice(INKS)
    w, h = 820, 520
    title = (f"<div style='font:700 78px BN;color:{ink}'>{bn}</div>"
             f"<div style='font:700 40px BN;color:#222'>{bn_strength(strength)} {'ট্যাবলেট' if form == 'Tablet' else 'ক্যাপসুল'}</div>"
             f"<div style='font:400 26px COND4;color:#333;margin-top:8px'>{generic} BP</div>"
             if bangla else
             f"<div style='font:700 92px COND;color:{ink};letter-spacing:-1px'>{brand}<sup style='font-size:28px'>&reg;</sup></div>"
             f"<div style='font:700 40px COND;color:#222'>{strength} {form}</div>"
             f"<div style='font:400 26px COND4;color:#333;margin-top:8px'>{generic} BP</div>")
    body = (f"<div style='position:relative;width:{w}px;height:{h}px;background:#fbfbf7;border:3px solid #ddd;"
            f"padding:46px 54px'><div style='position:absolute;left:0;top:0;width:100%;height:28px;background:{ink}'></div>"
            f"{title}<div style='position:absolute;left:54px;bottom:40px;font:400 22px COND4;color:#444'>"
            f"3 x 10 {form}s &nbsp;|&nbsp; Store below 30&deg;C, away from light</div>"
            f"<div style='position:absolute;right:40px;bottom:40px;font:700 22px COND;color:#222;text-align:right'>"
            f"Batch No: {R.randint(1000, 9999)}<br>EXP: {exp_print}</div>"
            f"<div class=syn style='right:12px;top:34px'>SYNTHETIC</div></div>")
    return page(body, w, h), w, h


def rx_html(meds) -> tuple[str, int, int]:
    w, h = 900, 1150
    lines = "".join(
        f"<div style='font:700 {R.randint(42, 50)}px HAND;color:#1c2a6b;margin:26px 0 0 {R.randint(0, 30)}px;"
        f"transform:rotate({R.uniform(-3, 2):.1f}deg)'>{i}. {'Cap' if m[3] == 'Capsule' else 'Tab'}. {m[0]} {m[2]}"
        f"&nbsp;&nbsp; {R.choice(['1+0+1', '1+1+1', '0+0+1', '1+0+0'])} &nbsp; {R.choice(['7 days', '1 month', 'cont.'])}</div>"
        for i, m in enumerate(meds, 1))
    body = (f"<div style='position:relative;width:{w}px;height:{h}px;background:#fffdf6;padding:60px'>"
            f"<div style='height:150px;border-bottom:3px solid #2b5d9b;display:flex;gap:20px;align-items:center'>"
            f"<div style='width:520px;height:34px;background:#111'></div>"
            f"<div style='font:400 18px COND4;color:#555'>[identifying details removed]</div></div>"
            f"<div style='font:700 80px COND;color:#2b5d9b;margin-top:30px'>R<sub style='font-size:46px'>x</sub></div>"
            f"{lines}<div class=syn style='right:18px;bottom:14px'>SYNTHETIC</div></div>")
    return page(body, w, h, "#fffdf6"), w, h


def bp_html(sys_: int, dia: int, pulse: int, model: int) -> tuple[str, int, int]:
    w, h = 700, 820
    shell = ["#f1f1ef", "#dfe6ee", "#2f3338"][model]
    lcd = ["#b9c8a8", "#c7d3d8", "#9fb3a0"][model]
    seg = "font:700 {s}px COND;color:#1e2a22;letter-spacing:4px;text-align:right"
    body = (f"<div style='position:relative;width:{w}px;height:{h}px;background:{shell};border-radius:60px;"
            f"padding:70px 70px'><div style='background:{lcd};border-radius:18px;height:560px;padding:24px 40px;"
            f"box-shadow:inset 0 0 18px #0005'>"
            f"<div style='display:flex;justify-content:space-between'><span style='font:700 22px COND4'>SYS mmHg</span>"
            f"<span style='{seg.format(s=150)}'>{sys_}</span></div>"
            f"<div style='display:flex;justify-content:space-between'><span style='font:700 22px COND4'>DIA mmHg</span>"
            f"<span style='{seg.format(s=150)}'>{dia}</span></div>"
            f"<div style='display:flex;justify-content:space-between'><span style='font:700 22px COND4'>PULSE /min</span>"
            f"<span style='{seg.format(s=90)}'>{pulse}</span></div></div>"
            f"<div style='margin:34px auto 0;width:150px;height:60px;border-radius:30px;background:#2a6fd6'></div>"
            f"<div class=syn style='right:30px;top:24px;color:#8888'>SYNTHETIC</div></div>")
    return page(body, w, h), w, h


# ---------- photo-like damage ----------

def on_table(img: Image.Image, size=(1600, 1200)) -> Image.Image:
    bg = Image.new("RGB", size, R.choice([(120, 92, 70), (205, 198, 186), (70, 80, 95), (160, 150, 140)]))
    noise = Image.effect_noise(size, 18).convert("RGB")
    bg = Image.blend(bg, noise, 0.08)
    img = img.rotate(R.uniform(-14, 14), expand=True, resample=Image.BICUBIC)
    scale = min(size[0] * 0.8 / img.width, size[1] * 0.8 / img.height, 1.4)
    img = img.resize((int(img.width * scale), int(img.height * scale)))
    x = R.randint(20, max(21, size[0] - img.width - 20))
    y = R.randint(20, max(21, size[1] - img.height - 20))
    bg.paste(img, (x, y), img if img.mode == "RGBA" else None)
    return bg


def place_many(imgs: list[Image.Image], size=(1800, 1350)) -> Image.Image:
    bg = Image.new("RGB", size, R.choice([(190, 176, 150), (110, 85, 64), (215, 215, 210)]))
    cols = len(imgs)
    for i, im in enumerate(imgs):
        im = im.rotate(R.uniform(-10, 10), expand=True, resample=Image.BICUBIC)
        s = min(size[0] / cols * 0.92 / im.width, size[1] * 0.8 / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)))
        x = int(i * size[0] / cols + R.randint(0, 20))
        y = R.randint(20, max(21, size[1] - im.height - 20))
        bg.paste(im, (x, y), im if im.mode == "RGBA" else None)
    return bg


def cut(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = R.choice(["left", "right"])
    keep = R.uniform(0.42, 0.62)
    box = (0, 0, int(w * keep), h) if side == "left" else (int(w * (1 - keep)), 0, w, h)
    piece = img.crop(box).convert("RGBA")
    mask = Image.new("L", piece.size, 255)
    d = ImageDraw.Draw(mask)
    edge_x = piece.width - 1 if side == "left" else 0
    pts = [(edge_x + R.randint(-14, 14) * (1 if side == "right" else -1), y) for y in range(0, h, 18)]
    poly = ([(piece.width, 0)] + pts + [(piece.width, h)]) if side == "left" else ([(0, 0)] + pts + [(0, h)])
    d.polygon(poly, fill=0)
    piece.putalpha(mask)
    return piece


def glare(img: Image.Image, strength=0.97) -> Image.Image:
    alpha = img.getchannel("A") if img.mode == "RGBA" else None
    img = img.convert("RGB")
    w, h = img.size
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    cx, cy = R.randint(int(w * .25), int(w * .75)), R.randint(int(h * .2), int(h * .8))
    rx, ry = R.randint(int(w * .18), int(w * .32)), R.randint(int(h * .2), int(h * .35))
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=int(255 * strength))
    layer = layer.filter(ImageFilter.GaussianBlur(min(rx, ry) * 0.3))
    white = Image.new("RGB", (w, h), (255, 255, 250))
    out = Image.composite(white, img, layer)
    if alpha is not None:
        out = out.convert("RGBA")
        out.putalpha(alpha)
    return out


def camera(img: Image.Image, blur=None) -> bytes:
    img = img.convert("RGB")
    b = R.uniform(0.3, 1.6) if blur is None else blur
    img = img.filter(ImageFilter.GaussianBlur(b))
    img = ImageEnhance.Brightness(img).enhance(R.uniform(0.75, 1.1))
    img = ImageEnhance.Color(img).enhance(R.uniform(0.85, 1.1))
    noise = Image.effect_noise(img.size, R.uniform(6, 14)).convert("RGB")
    img = Image.blend(img, noise, 0.05)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=R.randint(70, 88))
    return out.getvalue()


async def render(pw_page, html: str, w: int, h: int, transparent=True) -> Image.Image:
    await pw_page.set_viewport_size({"width": w, "height": h})
    await pw_page.set_content(html)
    await pw_page.evaluate("document.fonts.ready")
    png = await pw_page.screenshot(omit_background=transparent, full_page=False)
    return Image.open(io.BytesIO(png)).convert("RGBA")


async def main(out: Path) -> None:
    photos, bp = out / "photos", out / "bp_photos"
    photos.mkdir(parents=True, exist_ok=True)
    bp.mkdir(parents=True, exist_ok=True)
    labels: list[dict] = []
    bplabels: list[dict] = []
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await br.new_page()

        async def item(med, kind="strip", bangla=False):
            ym, printed = expiry()
            html, w, h = (strip_html if kind == "strip" else box_html)(med, printed, bangla)
            return await render(pg, html, w, h), ym

        def save(name, data, rows, condition):
            (photos / name).write_bytes(data)
            for brand, strength, ym in rows:
                labels.append({"image_path": f"photos/{name}", "brand": brand, "strength": strength,
                               "expiry": ym, "condition": condition})

        pool = MEDS[:]
        R.shuffle(pool)
        nxt = iter(pool * 4)

        # 8 cut strips (expiry may be on the cut-off side: label it empty when the EXP text is not kept)
        for i in range(1, 9):
            med = next(nxt)
            img, ym = await item(med, "strip")
            piece = cut(img)
            exp_visible = False  # the EXP line sits at bottom-left; only trust it when the left part is kept
            # check: left-kept pieces start at x=0
            if piece.getbbox() and piece.getpixel((5, piece.height - 10))[3] > 0:
                exp_visible = piece.width > img.width * 0.55
            save(f"cut_{i:02d}.jpg", camera(on_table(piece)), [(med[0], med[2], ym if exp_visible else "")], "cut_strip")

        # 6 glare (two of them with 2 medicines)
        for i in range(1, 7):
            if i in (3, 6):
                a, b = next(nxt), next(nxt)
                ia, ya = await item(a, "strip")
                ib, yb = await item(b, "box")
                save(f"glare_{i:02d}.jpg", camera(place_many([glare(ia), glare(ib, 0.6)])), [(a[0], a[2], ya), (b[0], b[2], yb)], "glare")
            else:
                med = next(nxt)
                img, ym = await item(med, R.choice(["strip", "box"]))
                save(f"glare_{i:02d}.jpg", camera(on_table(glare(img))), [(med[0], med[2], ym)], "glare")

        # 5 Bangla print (boxes and strips); label brand in English (what the app should map to)
        for i in range(1, 6):
            med = next(nxt)
            img, ym = await item(med, "box" if i % 2 else "strip", bangla=True)
            save(f"bangla_{i:02d}.jpg", camera(on_table(img)), [(med[0], med[2], ym)], "bangla")

        # 5 handwritten prescriptions, 2-3 medicines each, no expiry on prescriptions
        for i in range(1, 6):
            meds = [next(nxt) for _ in range(R.choice([2, 3]))]
            html, w, h = rx_html(meds)
            img = await render(pg, html, w, h, transparent=False)
            save(f"handwritten_{i:02d}.jpg", camera(on_table(img, (1400, 1700))), [(m[0], m[2], "") for m in meds], "handwritten")

        # 6 clear baseline (two shelf photos with 3 medicines, combos included)
        combos = [BYNAME["Napa Extra"], BYNAME["Osartil Plus"], BYNAME["Amdocal Plus"]]
        for i in range(1, 7):
            if i in (2, 5):
                meds = [combos[i % 3], next(nxt), next(nxt)]
                parts = [await item(m, R.choice(["strip", "box"])) for m in meds]
                save(f"clear_{i:02d}.jpg", camera(place_many([p[0] for p in parts]), blur=0.4),
                     [(m[0], m[2], p[1]) for m, p in zip(meds, parts)], "clear")
            else:
                med = combos[i % 3] if i == 1 else next(nxt)
                img, ym = await item(med, R.choice(["strip", "box"]))
                save(f"clear_{i:02d}.jpg", camera(on_table(img), blur=0.4), [(med[0], med[2], ym)], "clear")

        # 20 BP monitor screens: 3 machine looks; clear / angled / glare
        for i in range(1, 21):
            s, d, pl = R.randint(108, 182), R.randint(62, 108), R.randint(56, 104)
            d = min(d, s - 30)
            html, w, h = bp_html(s, d, pl, i % 3)
            img = await render(pg, html, w, h)
            cond = ["clear", "angle", "glare"][i % 3]
            photo = on_table(img, (1200, 1400))
            if cond == "angle":
                photo = photo.transform(photo.size, Image.Transform.PERSPECTIVE,
                                        (1, R.uniform(-0.12, 0.12), 0, R.uniform(-0.08, 0.08), 1, 0, R.uniform(-2e-4, 2e-4), 0),
                                        Image.BICUBIC)
            if cond == "glare":
                photo = on_table(glare(img, 0.7), (1200, 1400))
            name = f"bp_{cond}_{i:02d}.jpg"
            (bp / name).write_bytes(camera(photo))
            bplabels.append({"image_path": f"bp_photos/{name}", "systolic": s, "diastolic": d, "pulse": pl})
        await br.close()

    with (out / "labels.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image_path", "brand", "strength", "expiry", "condition"])
        w.writeheader()
        w.writerows(labels)
    with (out / "bp_labels.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["image_path", "systolic", "diastolic", "pulse"])
        w.writeheader()
        w.writerows(bplabels)
    print(len(list(photos.iterdir())), "strip photos,", len(labels), "label rows;", len(bplabels), "BP photos")


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))
