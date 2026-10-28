"""Build the guide: data/verbs.yaml -> Jinja2 -> HTML/CSS -> PDF (WeasyPrint).

    python3 build.py            # writes output/guide.html and the PDF
"""
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup, escape

from conj.core import (IMP_PERSONS, PERSONS, ROOT, conj_class, form, is_irregular,
                       load, regular, split)

OUT_DIR = ROOT / "output"
PDF = OUT_DIR / "Conjugacion_Espanola_Guia_Definitiva.pdf"
HTML = OUT_DIR / "guide.html"

DATA = load()
VERBS = DATA["verbs"]

# ----------------------------------------------------------------------
#  Book outline: the table of contents, running headers and section
#  numbers all come from here.
# ----------------------------------------------------------------------
OUTLINE = [
    {"id": "part0", "num": "0", "title": "Le système",
     "summary": "Chaque forme verbale espagnole est faite de trois pièces. Apprends-les une fois pour toutes.",
     "sections": [("s-formula", "La formule"),
                  ("s-markers", "Les marques voyagent"),
                  ("s-check", "Le test des 2 secondes"),
                  ("ex-part0", "Entraînement")]},
    {"id": "part1", "num": "1", "title": "Le présent",
     "summary": "Presente de indicativo : ce que tu fais, ce qui est vrai, ce qui se passe maintenant.",
     "sections": [("s-pres-regular", "Verbes réguliers : -ar, -er, -ir"),
                  ("s-boot", "Les verbes « botte » (diphtongue)"),
                  ("s-yo", "Irréguliers seulement à yo"),
                  ("s-irregular", "Verbes totalement irréguliers"),
                  ("s-reflexive", "Verbes pronominaux"),
                  ("s-gustar", "Les verbes comme gustar"),
                  ("s-serestar", "Ser ou estar ?"),
                  ("s-mistakes", "Erreurs des francophones"),
                  ("ex-part1", "Entraînement")]},
    {"id": "part2", "num": "2", "title": "Le passé",
     "summary": "Trois passés : ce que tu as fait aujourd’hui, ce que tu as fait hier, ce qui se passait.",
     "sections": [("s-perfecto", "Pretérito perfecto : he hablado"),
                  ("s-indefinido", "Pretérito indefinido : hablé"),
                  ("s-indef-irr", "Indefinido : radicaux irréguliers"),
                  ("s-imperfecto", "Pretérito imperfecto : hablaba"),
                  ("s-contrast", "Indefinido ou imperfecto ?"),
                  ("ex-part2", "Entraînement")]},
    {"id": "part3", "num": "3", "title": "Futur et conditionnel",
     "summary": "Projets, prédictions et demandes polies, tous construits sur l’infinitif.",
     "sections": [("s-ira", "Ir a + infinitif"),
                  ("s-futuro", "Futuro simple"),
                  ("s-condicional", "Condicional"),
                  ("ex-part3", "Entraînement")]},
    {"id": "part4", "num": "4", "title": "L’impératif",
     "summary": "Donner des consignes : fais-le, ne le fais pas, dis-le-moi.",
     "sections": [("s-imp-aff", "L’impératif affirmatif"),
                  ("s-imp-neg", "L’impératif négatif"),
                  ("s-imp-pron", "Placer les pronoms"),
                  ("ex-part4", "Entraînement")]},
    {"id": "part5", "num": "5", "title": "Le subjonctif",
     "summary": "Le mode des souhaits, des sentiments, du doute et de ce qui n’est pas encore réel.",
     "sections": [("s-subj-pres", "Subjonctif présent"),
                  ("s-subj-irr", "Subjonctif présent : irréguliers"),
                  ("s-subj-imp", "Subjonctif imparfait"),
                  ("s-subj-use", "Quand employer le subjonctif ?"),
                  ("ex-part5", "Entraînement")]},
    {"id": "part6", "num": "6", "title": "Référence",
     "summary": "Tous les temps des trois verbes modèles et des 25 verbes irréguliers essentiels.",
     "sections": [("s-master", "Tableaux complets des modèles"),
                  ("s-quickref", "Les 25 irréguliers essentiels"),
                  ("s-nonfinite", "Gérondif et participe"),
                  ("s-index", "Index des verbes")]},
    {"id": "answers", "num": "", "title": "Corrigés",
     "summary": "", "sections": []},
]
SECTION_TITLES = {sid: t for p in OUTLINE for sid, t in p["sections"]}
SECTION_NUMS = {}
for p in OUTLINE:
    for i, (sid, _) in enumerate(p["sections"], 1):
        SECTION_NUMS[sid] = f"{p['num']}.{i}" if not sid.startswith("ex-") else ""
SECTION_HDR = {sid: (f"{SECTION_NUMS[sid]} · {t}" if SECTION_NUMS[sid] else f"{t} · Partie {p['num']}")
               for p in OUTLINE for sid, t in p["sections"]}

TENSE_SHORT = {
    "presente": "Presente", "indefinido": "Indefinido", "imperfecto": "Imperfecto",
    "futuro": "Futuro", "condicional": "Condicional", "subj_presente": "Subj. presente",
    "subj_imperfecto": "Subj. imperfecto", "perfecto": "Perfecto",
}
PERSON_LABELS = [p["label"] for p in DATA["persons"]]
PERSON_SHORT = ["yo", "tú", "él", "nos.", "vos.", "ellos"]

# ----------------------------------------------------------------------
#  Index registry: verb -> [(section_id, label)]
# ----------------------------------------------------------------------
INDEX = {}
_current_section = {"id": None}


def _register(verb):
    sid = _current_section["id"]
    if not sid:
        return ""
    entries = INDEX.setdefault(verb, [])
    if sid not in [e[0] for e in entries]:
        entries.append((sid, SECTION_TITLES.get(sid, sid)))
        return Markup(f' id="ix-{escape(verb)}-{sid}"')
    return ""


def anchor(verb):
    """An empty element carrying the index anchor (for rows inside tables)."""
    a = _register(verb)
    return Markup(f"<span class=\"ix\"{a}></span>") if a else ""


def section(sid):
    """Called from the template at every section heading."""
    _current_section["id"] = sid
    return ""


# ----------------------------------------------------------------------
#  Rendering helpers used by the templates
# ----------------------------------------------------------------------
def cls(verb):
    try:
        return conj_class(verb)
    except KeyError:
        return "ir"


def fmt(verb, tense, p, mark_irregular=True):
    """One conjugated form as HTML: stem + coloured ending; parts that differ
    from the regular rule get the dotted 'irr' underline."""
    v = VERBS[verb]
    text = v[tense][p]
    c = cls(verb)
    pron = ""
    if v.get("reflexive"):
        pron, text = text.split(" ", 1)
    stem, end = split(DATA, verb, tense, p, text)
    irr_stem = irr_end = False
    if mark_irregular and is_irregular(verb, tense, p, text if not pron else f"{pron} {text}") \
            and not v.get("reflexive"):
        try:
            rstem, rend = split(DATA, verb, tense, p, regular(verb, tense, p))
        except (KeyError, ValueError):
            rstem, rend = None, None
        irr_stem = stem != rstem
        irr_end = end != rend
    out = ""
    if pron:
        out += f'<span class="pron">{escape(pron)}</span> '
    if not end:
        return Markup(out + f'<span class="whole e-{c}{" irr" if irr_stem else ""}">{escape(stem)}</span>')
    out += f'<span class="stem{" irr" if irr_stem else ""}">{escape(stem)}</span>'
    out += f'<span class="end e-{c}{" irr" if irr_end else ""}">{escape(end)}</span>'
    return Markup(out)


def fmt_plain(verb, tense, p):
    """A whole form, coloured, irregular-marked (imperative, gerund…)."""
    if tense == "imperativo":
        text = VERBS[verb]["imperativo"][IMP_PERSONS.index(p)]
    elif tense in ("gerundio", "participio"):
        text = VERBS[verb][tense]
    else:
        text = VERBS[verb][tense][p]
    if text is None:
        return Markup('<span class="na">—</span>')
    irr = is_irregular(verb, tense, p, text)
    return Markup(f'<span class="whole e-{cls(verb)}{" irr" if irr else ""}">{escape(text)}</span>')


def nonfinite(verb, kind):
    """Gerund / participle with the ending split off."""
    text = VERBS[verb][kind] if verb in VERBS and kind in VERBS[verb] else None
    if text is None:
        for x in DATA["nonfinite_extra"]:
            if x["verb"] == verb:
                text = x[kind]
    c = cls(verb)
    ends = ["ando", "iendo", "yendo"] if kind == "gerundio" else ["ado", "ido", "ído"]
    for e in ends:
        if text.endswith(e) and len(text) > len(e):
            try:
                irr = regular(verb, kind, 0) != text
            except (KeyError, ValueError):
                irr = True
            reg_end = None
            try:
                reg_end = [x for x in ends if regular(verb, kind, 0).endswith(x)][0]
            except (KeyError, ValueError, IndexError):
                pass
            stem_irr = irr and text[:-len(e)] != stem_of_safe(verb)
            end_irr = irr and e != reg_end
            return Markup(f'<span class="stem{" irr" if stem_irr else ""}">{escape(text[:-len(e)])}</span>'
                          f'<span class="end e-{c}{" irr" if end_irr else ""}">{escape(e)}</span>')
    return Markup(f'<span class="whole e-{c} irr">{escape(text)}</span>')


def stem_of_safe(verb):
    return verb[:-2]


def marker(verb, tense, p):
    """Form with the person marker in a yellow pill (for 'the markers travel')."""
    text = VERBS[verb][tense][p]
    m = DATA["persons"][p]["marker"]
    if p in (0, 2) or not m:
        return Markup(f'<span class="mk-plain">{escape(text)}</span>')
    if text.endswith(m):
        return Markup(f'<span class="mk-plain">{escape(text[:-len(m)])}</span>'
                      f'<span class="pill">{escape(m)}</span>')
    return Markup(f'<span class="mk-plain mk-exc">{escape(text)}</span>')


def stars(s):
    """'*Hablo* español' -> highlighted verb."""
    s = str(escape(s))
    return Markup(re.sub(r"\*(.+?)\*", r'<b class="hl">\1</b>', s))


def answer(item):
    if "answer" in item:
        return item["answer"]
    lk = item["lookup"]
    a = form(DATA, lk["verb"], lk["tense"], lk["person"])
    if lk.get("cap"):
        a = a[0].upper() + a[1:]
    return a


def blank(q):
    s = str(escape(q))
    return Markup(s.replace("___", '<span class="blank"></span>'))


def formula_check(verb, p):
    """stem + theme vowel + marker, asserted against the data."""
    c = cls(verb)
    st = verb[:-2]
    vowel = DATA["classes"][c]["theme_vowel"]
    m = DATA["persons"][p]["marker"]
    actual = VERBS[verb]["presente"][p]
    assert st + vowel + m == actual, (verb, p, st + vowel + m, actual)
    return {"stem": st, "vowel": vowel, "marker": m, "form": actual, "cls": c}


def strong_preterite(verb_stem):
    return verb_stem


def env():
    e = Environment(loader=FileSystemLoader(str(ROOT / "templates")),
                    undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    e.globals.update(
        D=DATA, V=VERBS, P=PERSONS, IMP=IMP_PERSONS, PL=PERSON_LABELS, PS=PERSON_SHORT,
        OUTLINE=OUTLINE, ST=SECTION_TITLES, SN=SECTION_NUMS, HDR=SECTION_HDR, TS=TENSE_SHORT,
        fmt=fmt, fmt_plain=fmt_plain, nonfinite=nonfinite, marker=marker,
        stars=stars, answer=answer, blank=blank, cls=cls, form=lambda *a: form(DATA, *a),
        section=section, reg=_register, anchor=anchor, INDEX=INDEX, formula_check=formula_check,
        zip=zip, enumerate=enumerate, len=len, sorted=sorted,
    )
    return e


NBSP = "\u00a0"


def french_spacing(html):
    """Non-breaking space before : ; ? ! and inside « » (French typography).
    Only touches text between tags; Spanish never has a space before ? or !."""
    def fix(text):
        text = re.sub(r" ([:;?!»])", NBSP + r"\1", text)
        # never break a suffix such as -er or -gar at its hyphen
        text = re.sub(r"(?<![\w-])-([a-záéíóúñ]{1,6})\b", "-\u2060\\1", text)
        return text.replace("« ", "«" + NBSP)
    return re.sub(r">([^<]+)<", lambda m: ">" + fix(m.group(1)) + "<", html)


def build(pdf=True):
    OUT_DIR.mkdir(exist_ok=True)
    html = french_spacing(env().get_template("book.html").render())
    HTML.write_text(html, encoding="utf-8")
    if pdf:
        from weasyprint import HTML as WHTML
        WHTML(string=html, base_url=str(ROOT / "templates")).write_pdf(str(PDF))
    return HTML, PDF


if __name__ == "__main__":
    h, p = build(pdf="--html-only" not in sys.argv)
    print("html:", h)
    print("pdf: ", p)
