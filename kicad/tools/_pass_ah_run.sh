#!/usr/bin/env bash
# Apply one Pass-AH edit, run DRC, gate. Usage: tools/_pass_ah_run.sh <edit>
set -euo pipefail
cd "$(dirname "$0")/.."
label="$1"
KICAD_APPIMAGE="${KICAD_APPIMAGE:-/workspace/.kicad9/kicad-9.0.9-x86_64-lite.AppImage}"
python3 tools/_pass_ah_try.py "$label"
"$KICAD_APPIMAGE" --appimage-extract-and-run kicad-cli pcb drc \
  --output "reports/_drc_passah_${label}.txt" \
  --format report \
  --severity-error \
  e-ink-watch.kicad_pcb
python3 tools/_pass_ah_gate.py "$label"
