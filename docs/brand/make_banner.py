"""Build docs/brand/banner-{light,dark}.svg with every word outlined as paths, so GitHub
renders the wordmark without web fonts.

Needs: pip install uharfbuzz fonttools, and these OFL fonts from github.com/google/fonts
(ofl/schibstedgrotesk, ofl/anekbangla, ofl/instrumentsans) in FONT_DIR:
  SchibstedGrotesk.ttf, AnekBangla.ttf, InstrumentSans.ttf
Usage: python docs/brand/make_banner.py FONT_DIR
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).resolve().parent
W, H = 1280, 320

THEMES = {
    "light": dict(bg="#F3F5F9", ink="#0E1530", soft="#3A4466", neel="#2A3B91", dye="#1F2C6E",
                  stitch="#8F9BD6", hem="rgba(255,255,255,0.4)", foil_hi="#F1F3F7", foil="#C8CDD6",
                  foil_lo="#9EA6B4", card="#FFFFFF", rule="#DFE3EC", red="#B42318"),
    "dark": dict(bg="#0A0E1C", ink="#E8EBF6", soft="#B3BAD3", neel="#98A8F6", dye="#182255",
                 stitch="#46529A", hem="rgba(255,255,255,0.3)", foil_hi="#8E95A2", foil="#69717F",
                 foil_lo="#434A57", card="#11172C", rule="#1D2443", red="#F2877C"),
}


@lru_cache
def instance(path: str, axes: tuple) -> TTFont:
    font = TTFont(path)
    if "fvar" in font:
        font = instantiateVariableFont(font, dict(axes))
    return font


def text_path(font_path: Path, text: str, size: float, x: float, y: float, axes: dict, features=None) -> tuple[str, float]:
    """Shape `text` with HarfBuzz and return (svg path data, advance width in px)."""
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    font = hb.Font(face)
    font.set_variations(axes)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    tt = instance(str(font_path), tuple(sorted(axes.items())))
    glyphs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = size / tt["head"].unitsPerEm
    pen = SVGPathPen(glyphs)
    cx = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        gx = x + (cx + pos.x_offset) * scale
        gy = y - pos.y_offset * scale
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, gx, gy)))
        cx += pos.x_advance
    return pen.getCommands(), cx * scale


def build(fonts: Path, theme: str) -> str:
    c = THEMES[theme]
    sg, anek, inst = fonts / "SchibstedGrotesk.ttf", fonts / "AnekBangla.ttf", fonts / "InstrumentSans.ttf"
    left = 96
    word, ww = text_path(sg, "OushodhSathi", 74, left, 168, {"wght": 650}, {"kern": True})
    bn, _ = text_path(anek, "ওষুধসাথী", 58, left + ww + 24, 168, {"wght": 500, "wdth": 100})
    tag, _ = text_path(inst, "A pharmacist for every elderly home in Bangladesh.", 24, left, 222, {"wght": 450, "wdth": 100})
    sub, _ = text_path(inst, "AI for perception. Rules and clinicians for judgement.", 18, left, 256, {"wght": 450, "wdth": 100})

    # right: an indigo-dyed cloth panel with a stitched hem, holding one piece of medicine strip
    px, py, pw, ph = 900, 40, 300, 240
    sx, sy, sw, sh = px + 40, py + 66, 220, 108
    blisters = "".join(
        f'<circle cx="{sx + 26}" cy="{sy + 34 + i * 40}" r="11" fill="url(#dome-{theme})" stroke="{c["foil_lo"]}" stroke-width="1"/>'
        for i in range(2)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="OushodhSathi (ওষুধসাথী) — a pharmacist for every elderly home in Bangladesh">
  <defs>
    <linearGradient id="foil-{theme}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c["foil_lo"]}"/><stop offset="0.45" stop-color="{c["foil_hi"]}"/>
      <stop offset="0.7" stop-color="{c["foil"]}"/><stop offset="1" stop-color="{c["foil_lo"]}"/>
    </linearGradient>
    <radialGradient id="dome-{theme}" cx="0.35" cy="0.3" r="0.8">
      <stop offset="0" stop-color="{c["foil_hi"]}"/><stop offset="0.6" stop-color="{c["foil"]}"/><stop offset="1" stop-color="{c["foil_lo"]}"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="{c["bg"]}"/>
  <path d="M{left} 80 H{left + 150}" stroke="{c["stitch"]}" stroke-width="3" stroke-dasharray="12 8" stroke-linecap="round"/>
  <path d="{word}" fill="{c["ink"]}"/>
  <path d="{bn}" fill="{c["neel"]}"/>
  <path d="{tag}" fill="{c["soft"]}"/>
  <path d="{sub}" fill="{c["soft"]}" fill-opacity="0.8"/>
  <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="26" fill="{c["dye"]}"/>
  <rect x="{px + 11}" y="{py + 11}" width="{pw - 22}" height="{ph - 22}" rx="18" fill="none" stroke="{c["hem"]}" stroke-width="2" stroke-dasharray="10 7"/>
  <g transform="rotate(-6 {sx + sw / 2} {sy + sh / 2})">
    <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="9" fill="{c["card"]}"/>
    <rect x="{sx}" y="{sy}" width="52" height="{sh}" rx="9" fill="url(#foil-{theme})"/>
    <rect x="{sx + 40}" y="{sy}" width="12" height="{sh}" fill="url(#foil-{theme})"/>
    {blisters}
    <rect x="{sx + 70}" y="{sy + 24}" width="78" height="12" rx="6" fill="{c["ink"]}" fill-opacity="0.85"/>
    <rect x="{sx + 70}" y="{sy + 48}" width="96" height="18" rx="9" fill="{c["red"]}" fill-opacity="0.16"/>
    <rect x="{sx + 70}" y="{sy + 82}" width="124" height="5" rx="2.5" fill="{c["neel"]}"/>
  </g>
</svg>
'''


if __name__ == "__main__":
    font_dir = Path(sys.argv[1])
    for t in THEMES:
        (OUT / f"banner-{t}.svg").write_text(build(font_dir, t), encoding="utf-8")
        print("wrote", OUT / f"banner-{t}.svg")
