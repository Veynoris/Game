"""Shared logic for the guide: loading the data, the regular-conjugation rule,
lookups, and splitting a form into stem + ending for display.

The rule below is written from the morphology (stem + theme vowel + person
marker), NOT copied from the endings tables in verbs.yaml, so the tests can use
it to check the hand-written data independently.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "verbs.yaml"

PERSONS = ["yo", "tu", "el", "nosotros", "vosotros", "ellos"]
IMP_PERSONS = ["tu", "usted", "nosotros", "vosotros", "ustedes"]
SIMPLE_TENSES = ["presente", "indefinido", "imperfecto", "futuro", "condicional",
                 "subj_presente", "subj_imperfecto"]

STRESS = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}
UNSTRESS = {v: k for k, v in STRESS.items()}
# person markers: yo / tú / él / nosotros / vosotros / ellos
MARK = ["", "s", "", "mos", "is", "n"]


def load(path=DATA):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def conj_class(inf):
    """'ar', 'er' or 'ir' (oír counts as -ir)."""
    base = inf[:-2] if inf.endswith("se") else inf
    return {"ar": "ar", "er": "er", "ir": "ir", "ír": "ir"}[base[-2:]]


def bare(inf):
    """levantarse -> levantar"""
    return inf[:-2] if inf.endswith("se") and inf not in ("ser",) else inf


def stem_of(inf):
    return bare(inf)[:-2]


def stress(v):
    return STRESS.get(v, v)


# ----------------------------------------------------------------------
#  The regular rule: stem + theme vowel + person marker
# ----------------------------------------------------------------------
def regular(inf, tense, p):
    """Regular form of `inf` in `tense` for person index p (0..5),
    or for imperativo: p in IMP_PERSONS. Returns a string."""
    inf = bare(inf)
    c = conj_class(inf)
    st = stem_of(inf)
    v = {"ar": "a", "er": "e", "ir": "e"}[c]          # theme vowel

    if tense == "presente":
        if p == 0:
            return st + "o"                            # yo: -o replaces the vowel
        if c == "ir" and p in (3, 4):
            v = "i"                                    # vivimos, vivís
        if p == 4:
            # stressed vowel + -is; i + is merge: viv-í-s
            return st + ("ís" if v == "i" else stress(v) + "is")
        return st + v + MARK[p]

    if tense == "imperfecto":
        tv = "aba" if c == "ar" else "ía"
        if p == 3:
            tv = "ába" if c == "ar" else "ía"          # hablábamos / comíamos
        return st + tv + MARK[p]

    if tense == "futuro":
        # infinitive + é / á / e + marker
        tv = ["é", "á", "á", "e", "é", "á"][p]
        return inf + tv + MARK[p]

    if tense == "condicional":
        return inf + "ía" + MARK[p]

    if tense == "indefinido":
        tv = "a" if c == "ar" else "i"
        if p == 0:
            return st + ("é" if c == "ar" else "í")
        if p == 1:
            return st + tv + "ste"                     # no -s: hablaste
        if p == 2:
            return st + ("ó" if c == "ar" else "ió")
        if p == 3:
            return st + tv + "mos"
        if p == 4:
            return st + tv + "steis"
        return st + ("aron" if c == "ar" else "ieron")

    if tense == "subj_presente":
        yo = regular(inf, "presente", 0)
        base = yo[:-1]                                 # from the yo form
        ov = "e" if c == "ar" else "a"                 # the opposite vowel
        if p == 4:
            return base + stress(ov) + "is"
        return base + ov + MARK[p]

    if tense == "subj_imperfecto":
        base = regular(inf, "indefinido", 5)[:-3]      # hablaron -> habla
        if p == 3:
            return base[:-1] + stress(base[-1]) + "ramos"
        return base + "ra" + MARK[p]

    if tense == "imperativo":
        if p == "tu":
            return regular(inf, "presente", 2)
        if p == "vosotros":
            return inf[:-1] + "d"
        idx = {"usted": 2, "nosotros": 3, "ustedes": 5}[p]
        return regular(inf, "subj_presente", idx)

    if tense == "gerundio":
        return st + ("ando" if c == "ar" else "iendo")
    if tense == "participio":
        return st + ("ado" if c == "ar" else "ido")

    raise ValueError(tense)


def regular_reflexive(inf, p):
    pron = ["me", "te", "se", "nos", "os", "se"][p]
    return f"{pron} {regular(inf, 'presente', p)}"


# ----------------------------------------------------------------------
#  Lookups in the data
# ----------------------------------------------------------------------
def form(data, verb, tense, person):
    """Read a form from the data. Supports two derived tenses:
    perfecto (haber + participio) and imperativo_neg (no + subjuntivo)."""
    v = data["verbs"][verb]
    if tense == "perfecto":
        return f"{form(data, 'haber', 'presente', person)} {v['participio']}"
    if tense == "imperativo_neg":
        idx = {"tu": 1, "usted": 2, "nosotros": 3, "vosotros": 4, "ustedes": 5}[person]
        return f"no {v['subj_presente'][idx]}"
    if tense == "imperativo":
        return v["imperativo"][IMP_PERSONS.index(person)]
    if tense in ("gerundio", "participio"):
        return v[tense]
    return v[tense][PERSONS.index(person)]


# ----------------------------------------------------------------------
#  Display: split into stem + ending
# ----------------------------------------------------------------------
EXTRA_ENDINGS = {
    "presente": {0: ["oy"]},
    "indefinido": {0: ["e", "i"], 1: ["iste"], 2: ["o", "io"], 3: ["imos"],
                   4: ["isteis"], 5: ["ieron", "eron"]},
    "subj_presente": {0: ["é"], 2: ["é"]},
}


def split(data, inf, tense, p, text):
    """Return (stem, ending) for display. ending may be '' (whole form shown
    as one irregular block)."""
    if text is None:
        return None, None
    t = data["tenses"].get(tense)
    cands = set()
    if t:
        for cls in ("ar", "er", "ir"):
            cands.add(t["endings"][cls][p])
    cands.update(EXTRA_ENDINGS.get(tense, {}).get(p, []))
    best = ""
    for e in cands:
        if text.endswith(e) and len(e) > len(best) and len(text) - len(e) >= 1:
            best = e
    if not best:
        return text, ""
    return text[: -len(best)], best


def is_irregular(inf, tense, p, text):
    if text is None or inf in ("caber", "valer"):
        return text is not None and tense in ("futuro", "condicional")
    try:
        return regular(inf, tense, p) != text
    except (KeyError, ValueError):
        return True
