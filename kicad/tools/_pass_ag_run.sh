#!/usr/bin/env bash
# Apply one Pass-AG edit, run DRC, gate. Usage: tools/_pass_ag_run.sh <edit>
set -euo pipefail
cd "$(dirname "$0")/.."
label="$1"
python3 tools/_pass_ag_try.py "$label"
kicad-cli pcb drc \
  --output "reports/_drc_passag_${label}.txt" \
  --format report \
  --severity-error \
  e-ink-watch.kicad_pcb
python3 tools/_pass_ag_gate.py "$label"
