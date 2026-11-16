#!/usr/bin/env bash
# Honesty check for the PC r15 build (FABLE_TO_swarm_5.md).
# Three regimes, each a FRESH process (file 4: pins are default-option numbers; S14 and PC20 are separate regimes):
#   none : no setoption at all
#   S14  : the 14 settings of file 1
#   PC20 : S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false
# Known answers from file 5's table.  Every line is a fresh engine process.
set -u
EXE="${1:?exe path}"
OUT="${2:?output dir}"
mkdir -p "$OUT"
S14=(
 "LmrQuietBase 93" "LmrQuietDivisor 205" "LmrNoisyBase 13" "LmrNoisyDivisor 333"
 "LmrHistoryDivisor 5643" "NullMoveBase 5" "LmpBase 8" "HistoryPruneMultiplier 2220"
 "HistoryBonusQuadratic 24" "HistoryBonusLinear 54" "HistoryBonusMax 2212"
 "SingularDepth 6" "IirDepth 2" "NonPawnCorrection true"
)
PC20=(
 "CuckooRep true" "HistRework 2" "TtPruneV2 true" "CorrHistV2 true" "MateAlphaGuard true" "OwnBook false"
)

opt_block() {   # $1 = regime
  # NOTE: every line must be "setoption name <NAME> value <VALUE>". The first version of this script wrote
  # "setoption name LmrQuietBase 93" (no `value`), the engine answered "unknown option LmrQuietBase 93", and the
  # S14 and PC20 rows below were really DEFAULT-option numbers. Fixed here; the wrong run is kept in
  # /tmp/pcout_broken/ so the error is on record.
  case "$1" in
    none) : ;;
    S14) for o in "${S14[@]}"; do printf 'setoption name %s value %s\n' "${o%% *}" "${o##* }"; done ;;
    PC20) for o in "${S14[@]}"; do printf 'setoption name %s value %s\n' "${o%% *}" "${o##* }"; done
          for o in "${PC20[@]}"; do printf 'setoption name %s value %s\n' "${o%% *}" "${o##* }"; done ;;
  esac
}

run() {  # $1 regime, $2 command, $3 tag
  { opt_block "$1"; printf '%s\nquit\n' "$2"; } | "$EXE" > "$OUT/$3.txt" 2>&1
  bad=$(grep -c -E "unknown option|invalid value|ERROR" "$OUT/$3.txt")
  printf '%-6s %-11s bad=%s %s\n' "$1" "$2" "$bad" "$(grep -E 'info string bench|^nodes ' "$OUT/$3.txt" | tail -1)"
}

echo "exe $EXE"
echo "sha256 $(sha256sum "$EXE" | cut -d' ' -f1)"
echo "id name: $(printf 'uci\nquit\n' | "$EXE" | grep 'id name')"
echo
echo "regime command   engine line"
for r in none S14 PC20; do
  for d in 11 13 16; do run "$r" "bench $d" "${r}_bench$d"; done
  printf 'position startpos\ngo perft 5\nquit\n' > /dev/null
  { opt_block "$r"; printf 'position startpos\ngo perft 5\nquit\n'; } | "$EXE" > "$OUT/${r}_perft5.txt" 2>&1
  printf '%-6s %-11s %s\n' "$r" "perft 5" "$(grep '^nodes ' "$OUT/${r}_perft5.txt" | tail -1)"
done
echo
echo "=== expected (file 5) ==="
echo "none: bench11 312866  bench13 862329  bench16 3024920  perft5 (not pinned per regime, base pin 4865609)"
echo "S14 : bench11 242796  bench13 656517"
echo "PC20: bench11 278024  bench13 587276"
