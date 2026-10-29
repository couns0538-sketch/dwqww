#!/usr/bin/env bash
# Print the latest CPU temperatures from the running HWiNFO64 sensor log (read-only). Job rule: pause my own work
# while the CPU hot spot reads above 80 C. The rule sensor is HWiNFO's "CPU IOD Hotspot" (the only CPU sensor
# HWiNFO names a hot spot); Tctl/Tdie is printed next to it (it sits at ~80 C from the PC's own gate + training load,
# see REPORT.md 00_baseline). Columns are found by header name, so a changed layout fails loudly.
# usage: cpu_temp.sh   -> "<date> <time> IOD_hotspot=<C> Tctl/Tdie=<C> CCD1=<C>"; exit 2 when IOD_hotspot > 80
set -euo pipefail
F="/c/Users/Administrator/grok-pc/nnue/tools/hwinfo/gpu_sensors.csv"
COLS="${TMPDIR:-/tmp}/r5a_hwinfo_cols.$$"
head -1 "$F" | tr ',' '\n' > "$COLS"
col() { grep -nF "\"$1\"" "$COLS" | head -1 | cut -d: -f1; }
C1=$(col "CPU IOD Hotspot [°C]"); C2=$(col "CPU (Tctl/Tdie) [°C]"); C3=$(col "CPU CCD1 (Tdie) [°C]")
[ -n "$C1" ] && [ -n "$C2" ] && [ -n "$C3" ] || { echo "cpu_temp: sensor columns not found"; exit 1; }
tail -1 "$F" | awk -F, -v a="$C1" -v b="$C2" -v c="$C3" '{
  printf "%s %s IOD_hotspot=%s Tctl/Tdie=%s CCD1=%s\n", $1, $2, $a, $b, $c; exit ($a > 80) ? 2 : 0 }'
