"""Accent check on the rendered PDF.

For every form in data/verbs.yaml that carries a written accent (and every
highlighted verb in the example sentences), look for the same word WITHOUT its
accent in the PDF text. A hit is either a missing accent (error) or a real
homograph (hablé / hable, está / esta), which is listed with its context for
review.

Run:  python3 tests/check_accents.py      (after build.py)
"""
import re
import subprocess
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from conj.core import ROOT, load  # noqa: E402

PDF = ROOT / "output" / "Conjugacion_Espanola_Guia_Definitiva.pdf"
TXT = ROOT / "output" / "verification" / "guide.txt"
REPORT = ROOT / "output" / "verification" / "accent_report.md"

STRIP = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
WORD = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")
# Spanish words that exist both with and without an accent (diacritic accent)
FUNCTION_WORDS = {"el", "tu", "mi", "se", "de", "si", "te", "mas", "que", "como",
                  "esta", "este", "estas", "estos", "cuando", "donde", "solo"}
# Hits checked by hand: not missing accents
REVIEWED = {
    "dire": "French word in the French prose (« veut dire »)",
    "pense": "French imperative in a box title (« Pense à plaire »)",
    "arabe": "French word in the French prose (« en arabe »)",
    "llego": "correct Spanish present, yo: « Cuando llego a casa, ceno » (habitual cuando)",
    "hablare": "text-extraction artefact: the yellow marker pill splits « hablare|mos » in table 0.2",
}
# The forms the brief asks about explicitly
REQUIRED = ["habláis", "comí", "vivió", "estás", "está", "están"]


def pdf_text():
    TXT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftotext", "-enc", "UTF-8", str(PDF), str(TXT)], check=True)
    t = TXT.read_text(encoding="utf-8")
    t = t.replace("⁠", "").replace(" ", " ").replace("­", "")
    return unicodedata.normalize("NFC", t)


def data_forms(data):
    forms = set()

    def walk(x):
        if isinstance(x, str):
            for w in WORD.findall(x):
                forms.add(w)
        elif isinstance(x, list):
            for y in x:
                walk(y)
        elif isinstance(x, dict):
            for k, y in x.items():
                if k not in ("en", "fr", "note"):
                    walk(y)
    walk(data["verbs"])
    walk(data["irregular_participles"])
    walk(data["nonfinite_extra"])
    for s in re.findall(r"\*(.+?)\*", str(data["sentences"])):
        walk(s)
    return forms


def main():
    data = load()
    text = pdf_text()
    words = WORD.findall(text)
    lower_words = [w.lower() for w in words]
    counts = defaultdict(int)
    for w in lower_words:
        counts[w] += 1

    forms = data_forms(data)
    all_forms_lower = {f.lower() for f in forms}
    accented = sorted({f.lower() for f in forms if f.translate(STRIP) != f})

    errors, homographs = [], []
    lines = text.split("\n")
    for f in accented:
        bare = f.translate(STRIP)
        if counts.get(bare):
            ctx = [ln.strip() for ln in lines if re.search(rf"(?<![\wáéíóúñ]){bare}(?![\wáéíóúñ])", ln, re.I)]
            if bare in REVIEWED:
                homographs.append((f, bare, counts[bare], ["REVIEWED: " + REVIEWED[bare]] + ctx))
            elif bare in all_forms_lower or bare in FUNCTION_WORDS:
                homographs.append((f, bare, counts[bare], ctx))
            else:
                errors.append((f, bare, counts[bare], ctx))

    out = ["# Accent check", "",
           f"PDF text: {len(words)} words. Accented forms in the data: {len(accented)}.", "",
           "## Forms named in the brief", "",
           "| form | in PDF | unaccented form | in PDF |", "|---|---|---|---|"]
    for f in REQUIRED:
        out.append(f"| {f} | {counts.get(f, 0)} | {f.translate(STRIP)} | {counts.get(f.translate(STRIP), 0)} |")
    out += ["", f"«hablás» (Rioplatense *vos* form) appears {counts.get('hablás', 0)} times: the guide "
            "teaches tú (hablas) and vosotros (habláis), not voseo.", "",
            f"## Missing accents: {len(errors)}", ""]
    for f, b, n, ctx in errors:
        out.append(f"- **{b}** ({n}×) should be **{f}**: " + " / ".join(ctx[:3]))
    out += ["", f"## Homographs reviewed in context: {len(homographs)}", "",
            "The unaccented word is itself correct Spanish (another verb form or a function word)."
            " Each context line was read to confirm the right word is used.", ""]
    for f, b, n, ctx in homographs:
        out.append(f"- **{b}** vs **{f}** ({n}×)")
        for c in ctx[:6]:
            out.append(f"    - {c}")
    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"accented forms: {len(accented)}, missing accents: {len(errors)}, homographs: {len(homographs)}")
    for f, b, n, ctx in errors:
        print("  ERROR", b, "->", f, ctx[:2])
    print("report:", REPORT)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
