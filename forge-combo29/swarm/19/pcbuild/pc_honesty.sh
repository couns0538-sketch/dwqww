#!/usr/bin/env bash
# pc_honesty.sh EXE OUTDIR : the PC build's known answers, all three regimes from file 5.
#   none : no setoption at all              -> bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft5 = 4865609
#   S14  : the 14 settings of file 1        -> bench 11 = 242796, bench 13 = 656517
#   PC20 : S14 + CuckooRep/HistRework 2/TtPruneV2/CorrHistV2/MateAlphaGuard/OwnBook false
#             -> bench 11 = 278024, bench 13 = 587276
# A fresh process per line. Every setoption is followed by isready and every answer line up to readyok is
# scanned for unknown option / invalid value / ERROR (STOP conditions).
set -u
EXE="${1:?exe}"; OUT="${2:?outdir}"
mkdir -p "$OUT"
EXE_ABS="$(readlink -f "$EXE")"
{
  echo "exe $EXE_ABS"
  sha256sum "$EXE_ABS"
  printf 'uci\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' | grep -E '^id name'
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/pc_honesty.meta"

s14=(
  "LmrQuietBase 93" "LmrQuietDivisor 205" "LmrNoisyBase 13" "LmrNoisyDivisor 333"
  "LmrHistoryDivisor 5643" "NullMoveBase 5" "LmpBase 8" "HistoryPruneMultiplier 2220"
  "HistoryBonusQuadratic 24" "HistoryBonusLinear 54" "HistoryBonusMax 2212"
  "SingularDepth 6" "IirDepth 2" "NonPawnCorrection true"
)
pc20_extra=(
  "CuckooRep true" "HistRework 2" "TtPruneV2 true" "CorrHistV2 true" "MateAlphaGuard true" "OwnBook false"
)

run_with() {   # run_with TAG "setting|setting|..." depth
  tag="$1"; settings="$2"; depth="$3"
  {
    echo uci
    echo isready
    if [ -n "$settings" ]; then
      IFS='|' read -ra arr <<< "$settings"
      for s in "${arr[@]}"; do
        echo "setoption name ${s% *} value ${s##* }"
        echo isready
      done
    fi
    echo "bench $depth"
    echo quit
  } > "$OUT/stream_${tag}_$depth.txt"
  "$EXE_ABS" < "$OUT/stream_${tag}_$depth.txt" 2>&1 | tr -d '\r' > "$OUT/raw_${tag}_$depth.txt"
  grep -E "unknown option|invalid value|ERROR" "$OUT/raw_${tag}_$depth.txt" > "$OUT/stop_${tag}_$depth.txt" || true
  grep -oE "bench depth $depth nodes [0-9]+" "$OUT/raw_${tag}_$depth.txt" | sed 's/.*nodes //'
}

echo "# PC build known answers (file 5)" 
printf '%-6s %-10s %-12s %s\n' regime depth measured expected
check() {  # check regime depth expected
  got=$(run_with "$1" "$2" "$3"); exp="$4"
  mark="OK"; [ "$got" != "$exp" ] && mark="MISMATCH"
  printf '%-6s %-10s %-12s %s  %s\n' "$1" "$3" "$got" "$exp" "$mark"
  echo "$1 $3 $got $exp $mark" >> "$OUT/pc_honesty.txt"
}

check none "" 11 312866
check none "" 13 862329
check none "" 16 3024920
# perft on the none regime
printf 'go perft 5\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' | grep -E '^nodes [0-9]+$' | sed 's/nodes //' > "$OUT/perft5_none.txt"
echo "perft5 5 $(cat "$OUT/perft5_none.txt") 4865609 $([ "$(cat "$OUT/perft5_none.txt")" = 4865609 ] && echo OK || echo MISMATCH)" | tee -a "$OUT/pc_honesty.txt"

S14=$(IFS='|'; echo "${s14[*]}")
PC20=$(IFS='|'; echo "${s14[*]}|${pc20_extra[*]}")
check S14 "$S14" 11 242796
check S14 "$S14" 13 656517
check PC20 "$PC20" 11 278024
check PC20 "$PC20" 13 587276

echo "--- STOP conditions found:"; ls "$OUT"/stop_*.txt 2>/dev/null | while read f; do [ -s "$f" ] && { echo "$f:"; cat "$f"; }; done; echo "(none printed = no refusal lines)"
date -u
