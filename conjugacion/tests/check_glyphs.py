"""Glyph check: every character of the book's text must exist in the font that
renders it (Inter / Fraunces, with DejaVu as the fallback for symbols).

Run:  python3 tests/check_glyphs.py      (after build.py)
"""
import html
import re
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "output" / "guide.html"
PDF = ROOT / "output" / "Conjugacion_Espanola_Guia_Definitiva.pdf"
REPORT = ROOT / "output" / "verification" / "glyph_report.md"
MUST = "¿¡ñáéíóúüÁÉÍÓÚÑ"


def cmap(path):
    return set(TTFont(str(path)).getBestCmap())


def main():
    fonts = ROOT / "static" / "fonts"
    inter = cmap(fonts / "inter-latin-400-normal.woff")
    fraunces = cmap(fonts / "fraunces-latin-600-normal.woff")
    dejavu_path = subprocess.run(["fc-match", "-f", "%{file}", "DejaVu Sans"],
                                 capture_output=True, text=True).stdout
    dejavu = cmap(dejavu_path)

    src = HTML.read_text(encoding="utf-8")
    src = re.sub(r"<style.*?</style>|<[^>]+>", " ", src, flags=re.S)
    text = html.unescape(src)
    chars = sorted({c for c in text if not c.isspace() and ord(c) > 32})

    missing, fallback = [], []
    for c in chars:
        cp = ord(c)
        if cp in (0x2060,):          # word joiner: invisible format character
            continue
        if cp in inter and cp in fraunces:
            continue
        if cp in inter or cp in fraunces:
            # used in only one family: still fine unless it shows up in the other
            if cp in dejavu:
                continue
        if cp in dejavu:
            fallback.append(c)
            continue
        missing.append(c)

    fonts_used = subprocess.run(["pdffonts", str(PDF)], capture_output=True, text=True).stdout

    lines = ["# Glyph check", "",
             f"Distinct characters in the book: {len(chars)}", "",
             "Required Spanish characters: " + " ".join(
                 f"{c} ({'ok' if ord(c) in inter and ord(c) in fraunces else 'MISSING'})" for c in MUST), "",
             f"Characters drawn by the DejaVu fallback (symbols absent from the Google Fonts latin subset): "
             f"{' '.join(fallback) or 'none'}", "",
             f"Characters with no glyph in any font: {' '.join(missing) or 'none'}", "",
             "## Fonts embedded in the PDF", "", "```", fonts_used.strip(), "```"]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(chars)} distinct chars; fallback: {''.join(fallback)!r}; missing: {''.join(missing)!r}")
    print(fonts_used)
    bad_must = [c for c in MUST if not (ord(c) in inter and ord(c) in fraunces)]
    return 1 if missing or bad_must else 0


if __name__ == "__main__":
    sys.exit(main())
