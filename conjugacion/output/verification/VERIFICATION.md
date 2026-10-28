# Verification report: La Conjugaison Espagnole

PDF: `output/Conjugacion_Espanola_Guia_Definitiva.pdf` (A4, 62 pages, explanations in French)

## 1. Regular forms regenerated from the rule

`tests/test_regular.py` (pytest): **374 passed, 0 failed**.

- `conj/core.py` builds every regular form from stem + theme vowel + person marker. The rule is written from the morphology, not copied from the YAML endings tables.
- Checked: the 344 regular forms of the regular verbs (hablar, comer, vivir, trabajar, estudiar, beber, aprender, escribir, gustar and the three reflexive verbs), across all their tenses, imperatives, gerunds and participles.
- Also checked: all endings tables, the future and indefinido stem lists, the subj. imperfecto derived from the ellos indefinido form, that every exercise answer resolves, and 10–15 exercises per part.
- Mutation test: deliberately corrupting *habláis → hablais* and *vivió → vivio* made exactly those 2 tests fail.

## 2. Irregular verbs cross-checked with verbecc 2.0.3

`tests/test_irregular_verbecc.py`: **1,608 forms checked, 0 unexplained mismatches.**

The cross-check covers every form in the data: all 40 verbs, every tense, the imperatives, gerunds and participles. The full line-by-line list of checked forms is in `verbecc_report.md`.

Two differences were reviewed by hand, and the guide keeps its form in both cases:

| verb | guide | verbecc | why the guide is right |
|---|---|---|---|
| ir, imperative nosotros | **vamos** | vayamos | *¡Vamos!* / *vámonos* is the normal affirmative command |
| haber, presente él | **ha** | hay | *ha* is the auxiliary (*ha comido*); *hay* is taught separately |

Three verb forms are deliberately shown as "—" (not used in practice): the imperative of **haber** and of **poder**.

## 3. Accents

`tests/check_accents.py` on the extracted PDF text: 620 accented forms searched, **0 missing accents**. Details are in `accent_report.md`.

| form | in PDF | unaccented form | in PDF |
|---|---|---|---|
| habláis | yes | hablais | 0 |
| comí | yes | comi | 0 |
| vivió | yes | vivio | 0 |
| estás | yes | estas | 0 |
| está | yes | esta | 5 (all demonstratives: *esta semana / calle / tarde*) |
| están | yes | estan | 0 |

- **hablás** (the Rioplatense *vos* form) appears 0 times. The guide teaches tú *hablas* and vosotros *habláis*.
- 26 homographs were reviewed in context (hable/hablé, hablara/hablará, como/cómo…); all are correct.
- 5 raw hits are not errors: French words (*dire, pense, arabe*), the correct present *llego*, and a pill-split artefact (*hablare|mos*).
- Every Spanish question word after `¿` carries its accent (¿Qué, ¿Cómo, ¿Dónde).

## 4. Pages and glyphs

- All 62 pages were rendered at 100 dpi (`tools/render_pages.sh`) and looked at. Fixes made during review:
  - a callout left alone on a page
  - headings orphaned at page bottoms
  - tables running about 2 mm past the right margin
  - SVG text that WeasyPrint rendered garbled (replaced with HTML labels)
  - missing → / ≈ glyphs (added DejaVu fallback)
  - hyphenated suffixes (-er, -gar) breaking across lines
- Automated pass on every page: only the full-bleed cover and part dividers reach past the right margin, and no page is nearly empty.
- `tests/check_glyphs.py`: 105 distinct characters, **0 without a glyph**. ¿ ¡ ñ á é í ó ú ü Á É Í Ó Ú Ñ are all in Inter and Fraunces. Only ᵉ → ≈ ✓ ✗ come from DejaVu.
- Fonts embedded: the bundled Google Fonts files (Inter, Fraunces; SIL OFL) and DejaVu for symbols.
- Navigation: 629 internal links (a clickable contents page and index), and PDF bookmarks for every part and section.
