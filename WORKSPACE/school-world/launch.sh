#!/usr/bin/env bash
# THE LONG LIGHT — School World (desktop pygame)
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
if ! python3 -c "import pygame" 2>/dev/null; then
  echo "Installing pygame (user)…"
  pip3 install --user --break-system-packages pygame || {
    echo "Could not install pygame. Try: pip3 install --user pygame"
    exit 1
  }
fi
echo "⟡ Opening School World…"
exec python3 play.py "$@"
