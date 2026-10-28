# La Conjugaison Espagnole

A Spanish verb-conjugation guide for French speakers (explanations in French), generated as a PDF.

- `data/verbs.yaml`: the single source of truth (tenses, endings, verbs, example sentences, exercises)
- `templates/`, `static/`: the Jinja2 templates and the print stylesheet (fonts are bundled, SIL OFL)
- `build.py`: YAML → Jinja2 → HTML → PDF (WeasyPrint)

```bash
pip install weasyprint jinja2 pyyaml pytest verbecc pypdf
python3 build.py                              # output/Conjugacion_Espanola_Guia_Definitiva.pdf
python3 -m pytest tests/test_regular.py       # regular forms vs the rule
python3 tests/test_irregular_verbecc.py       # every form vs verbecc
python3 tests/check_accents.py                # accent check on the PDF text
python3 tests/check_glyphs.py                 # glyph coverage
tools/render_pages.sh                         # PNG of every page at 100 dpi
```

The results are in `output/verification/VERIFICATION.md`.
