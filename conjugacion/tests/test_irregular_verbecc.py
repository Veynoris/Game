"""Cross-check every form in data/verbs.yaml against the verbecc conjugator.

Run:  python3 -m pytest tests/test_irregular_verbecc.py   (or python3 tests/test_irregular_verbecc.py)
Writes a line-by-line report to output/verification/verbecc_report.md
"""
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from conj.core import IMP_PERSONS, PERSONS, ROOT, SIMPLE_TENSES, bare, load  # noqa: E402

# verbecc mood/tense for each of our tenses
MAP = {
    "presente": ("indicativo", "presente"),
    "indefinido": ("indicativo", "pretérito-perfecto-simple"),
    "imperfecto": ("indicativo", "pretérito-imperfecto"),
    "futuro": ("indicativo", "futuro"),
    "condicional": ("condicional", "presente"),
    "subj_presente": ("subjuntivo", "presente"),
    "subj_imperfecto": ("subjuntivo", "pretérito-imperfecto-1"),
}
# verbecc person rows: yo tú vos él ella usted nosotros vosotros ellos ellas ustedes
ROW = {"yo": 0, "tu": 1, "el": 3, "nosotros": 6, "vosotros": 7, "ellos": 8}
# imperativo afirmativo rows: tú vos él ella usted nosotros vosotros ellos ellas ustedes
IMP_ROW = {"tu": 0, "usted": 4, "nosotros": 5, "vosotros": 6, "ustedes": 9}

# Differences reviewed by hand: our form is the one the guide teaches.
REVIEWED = {
    ("ir", "imperativo", "nosotros"):
        "«vamos» is the normal affirmative nosotros command (¡Vamos!, vámonos); "
        "verbecc gives the subjunctive-based «vayamos».",
    ("haber", "presente", "el"):
        "«ha» is the auxiliary (ha comido); verbecc gives the impersonal «hay», "
        "which the guide teaches separately.",
}

REPORT = ROOT / "output" / "verification" / "verbecc_report.md"


def _nfc(s):
    return unicodedata.normalize("NFC", s)


def _strip_pronoun(s):
    parts = s.split(" ")
    return " ".join(parts[1:]) if len(parts) > 1 else s


def verbecc_tables(verbs):
    from verbecc import CompleteConjugator
    cg = CompleteConjugator("es")
    out = {}
    for v in verbs:
        out[v] = json.loads(cg.conjugate(v).to_json())["moods"]
    return out


def run():
    data = load()
    entries = dict(data["verbs"])
    for x in data["nonfinite_extra"]:
        entries.setdefault(x["verb"], {}).update(
            {"gerundio": x["gerundio"], "participio": x["participio"]})
    for x in data["irregular_participles"]:
        entries.setdefault(x["verb"], {}).setdefault("participio", x["participle"])

    names = [bare(n) for n in entries]
    ref = verbecc_tables(sorted(set(names)))

    lines, mismatches, checked = [], [], 0
    for name, v in entries.items():
        b = bare(name)
        moods = ref[b]
        lines.append(f"\n### {name}\n")
        for t in SIMPLE_TENSES:
            if t not in v:
                continue
            mood, tn = MAP[t]
            row = []
            for i, p in enumerate(PERSONS):
                ours = v[t][i]
                if v.get("reflexive"):
                    ours = ours.split(" ", 1)[1]
                theirs = _nfc(_strip_pronoun(moods[mood][tn][ROW[p]]["c"][0]))
                checked += 1
                ok = _nfc(ours) == theirs
                row.append(ours if ok else f"**{ours}≠{theirs}**")
                if not ok and (name, t, p) in REVIEWED:
                    row[-1] = f"{ours} (reviewed: {REVIEWED[(name, t, p)]})"
                elif not ok:
                    mismatches.append((name, t, p, ours, theirs))
            lines.append(f"- {t}: " + ", ".join(row))
        if "imperativo" in v:
            row = []
            for p, ours in zip(IMP_PERSONS, v["imperativo"]):
                theirs = _nfc(moods["imperativo"]["afirmativo"][IMP_ROW[p]]["c"][0])
                if ours is None:
                    row.append(f"— (not used; verbecc lists «{theirs}»)")
                    continue
                checked += 1
                ok = _nfc(ours) == theirs
                row.append(ours if ok else f"**{ours}≠{theirs}**")
                if not ok and (name, "imperativo", p) in REVIEWED:
                    row[-1] = f"{ours} (reviewed: {REVIEWED[(name, 'imperativo', p)]})"
                elif not ok:
                    mismatches.append((name, "imperativo", p, ours, theirs))
            lines.append("- imperativo: " + ", ".join(row))
        for t, key in (("gerundio", "gerundio"), ("participio", "participo")):
            if t in v:
                theirs = _nfc(moods[key][key][0]["c"][0])
                checked += 1
                ok = _nfc(v[t]) == theirs
                lines.append(f"- {t}: " + (v[t] if ok else f"**{v[t]}≠{theirs}**"))
                if not ok:
                    mismatches.append((name, t, "-", v[t], theirs))

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    head = [
        "# verbecc cross-check",
        "",
        f"Forms checked: **{checked}**, unexplained mismatches: **{len(mismatches)}**, "
        f"reviewed differences: **{len(REVIEWED)}**",
        "",
        "Every form below was compared with verbecc (Spanish, vosotros forms,",
        "imperfect subjunctive in -ra). Mismatches are shown as **ours≠verbecc**.",
    ]
    REPORT.write_text("\n".join(head + lines) + "\n", encoding="utf-8")
    return checked, mismatches


def test_verbecc_agrees():
    checked, mismatches = run()
    assert checked > 1000
    assert not mismatches, "\n".join(map(str, mismatches))


if __name__ == "__main__":
    c, m = run()
    print(f"checked {c} forms, {len(m)} mismatches")
    for x in m:
        print("  ", x)
    print("report:", REPORT)
    sys.exit(1 if m else 0)
