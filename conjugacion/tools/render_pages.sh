#!/bin/sh
# Render every page of the guide to PNG at 100 dpi for visual review.
set -e
cd "$(dirname "$0")/.."
rm -rf output/pages && mkdir -p output/pages
pdftoppm -r 100 -png output/Conjugacion_Espanola_Guia_Definitiva.pdf output/pages/page
ls output/pages | wc -l
