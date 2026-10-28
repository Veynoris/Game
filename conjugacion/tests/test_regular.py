"""Regenerate every REGULAR form from the rule (stem + theme vowel + person
marker) and compare it with data/verbs.yaml.

Run:  python3 -m pytest tests/test_regular.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from conj.core import (IMP_PERSONS, PERSONS, SIMPLE_TENSES, bare, conj_class,  # noqa: E402
                       form, load, regular, regular_reflexive)

DATA = load()
REGULAR = {k: v for k, v in DATA["verbs"].items() if v.get("regular")}


def regular_cases():
    for name, v in REGULAR.items():
        skip = set(v.get("regular_except", []))
        for t in SIMPLE_TENSES:
            if t in v and t not in skip:
                for i, p in enumerate(PERSONS):
                    if v.get("reflexive"):
                        yield name, t, p, regular_reflexive(name, i), v[t][i]
                    else:
                        yield name, t, p, regular(name, t, i), v[t][i]
        if "imperativo" in v and "imperativo" not in skip:
            for p, f in zip(IMP_PERSONS, v["imperativo"]):
                yield name, "imperativo", p, regular(name, "imperativo", p), f
        for t in ("gerundio", "participio"):
            if t in v and t not in skip:
                yield name, t, "-", regular(name, t, 0), v[t]


CASES = list(regular_cases())


@pytest.mark.parametrize("verb,tense,person,expected,actual", CASES,
                         ids=[f"{c[0]}-{c[1]}-{c[2]}" for c in CASES])
def test_regular_form_matches_rule(verb, tense, person, expected, actual):
    assert actual == expected, f"{verb} {tense} {person}: yaml «{actual}» ≠ rule «{expected}»"


def test_enough_regular_forms():
    # hablar/comer/vivir alone give 3 × (7×6 + 5 + 2) = 147 forms
    assert len(CASES) >= 300


@pytest.mark.parametrize("tense", SIMPLE_TENSES)
@pytest.mark.parametrize("cls,dummy", [("ar", "tomar"), ("er", "meter"), ("ir", "partir")])
def test_endings_table_matches_rule(tense, cls, dummy):
    """The endings shown in the book's ending charts follow from the rule."""
    t = DATA["tenses"][tense]
    base = {"stem": dummy[:-2], "infinitive": dummy, "yo_stem": dummy[:-2],
            "ellos_pret": regular(dummy, "indefinido", 5)[:-3]}[t["base"]]
    for i, ending in enumerate(t["endings"][cls]):
        got = base + ending
        if tense == "subj_imperfecto" and i == 3:
            got = base[:-1] + {"a": "á", "e": "é", "i": "í"}[base[-1]] + ending
        assert got == regular(dummy, tense, i), (tense, cls, i)


def test_regular_except_really_irregular():
    for name, v in REGULAR.items():
        for t in v.get("regular_except", []):
            assert v[t] != regular(name, t, 0)


def test_irregular_participles_listed_in_verbs():
    for x in DATA["irregular_participles"]:
        v = DATA["verbs"].get(x["verb"])
        if v and "participio" in v:
            assert v["participio"] == x["participle"]


def test_future_stems_match_tables():
    for x in DATA["future_stems"]:
        v = DATA["verbs"][x["verb"]]
        assert v["futuro"][0] == x["stem"] + "é"
        assert v["condicional"][0] == x["stem"] + "ía"


def test_strong_preterite_stems_match_tables():
    for x in DATA["strong_preterite_stems"]:
        v = DATA["verbs"][x["verb"]]
        assert v["indefinido"][0] == x["stem"] + "e", x
        ellos = "eron" if x["stem"].endswith("j") else "ieron"
        assert v["indefinido"][5] == x["stem"] + ellos, x


def test_subj_imperfecto_built_from_ellos_preterite():
    """tuvieron -> tuviera, for every verb that has both tenses."""
    for name, v in DATA["verbs"].items():
        if "subj_imperfecto" in v and "indefinido" in v:
            assert v["subj_imperfecto"][0] == v["indefinido"][5][:-3] + "ra", name


def test_every_exercise_lookup_resolves():
    n = 0
    for part, groups in DATA["exercises"].items():
        for g in groups:
            assert 1 <= len(g["items"])
            for it in g["items"]:
                assert ("lookup" in it) != ("answer" in it), it
                if "lookup" in it:
                    lk = it["lookup"]
                    assert form(DATA, lk["verb"], lk["tense"], lk["person"]), it
                n += 1
    assert n >= 60


def test_exercise_count_per_part():
    for part, groups in DATA["exercises"].items():
        n = sum(len(g["items"]) for g in groups)
        assert 10 <= n <= 15, (part, n)


def test_conj_class():
    assert conj_class("oír") == "ir"
    assert conj_class("levantarse") == "ar"
    assert bare("ser") == "ser"
