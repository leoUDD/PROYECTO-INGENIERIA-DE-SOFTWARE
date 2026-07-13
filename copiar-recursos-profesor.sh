#!/usr/bin/env bash
set -e

mkdir -p frontend/compartido/recursos/videos

ORIGEN=$(find juego -type f -iname "TutorialProfesor.mp4" | head -n 1)

if [ -n "$ORIGEN" ]; then
  cp "$ORIGEN" frontend/compartido/recursos/videos/
  echo "Copiado: TutorialProfesor.mp4"
else
  echo "No se encontró TutorialProfesor.mp4."
  echo "La vista funcionará, pero el video no aparecerá."
fi
