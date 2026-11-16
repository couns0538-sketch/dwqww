#!/usr/bin/env bash
# job1_part1.sh -- the 70 runs of Part 1 on O (and, with SET=G, Part 2 on G).
# One run per line of the settings table: S14 plus ONE setting moved to -c or +c.
# Usage: job1_part1.sh EXE SETFILE OUTDIR SETPREFIX
set -u
EXE="${1:?exe}"; SET="${2:?setfile}"; OUT="${3:?outdir}"; PFX="${4:?prefix}"
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
run_one() {
  local name="$1" val="$2" tag="$3"
  local f="$OUT/${PFX}_${name}_${tag}.rows"
  [ -s "$f" ] && { echo "skip $f (exists)"; return; }
  python3 "$L1/rows.py" --exe "$EXE" --set "$SET" --out "$f" --depth 12 \
    --opts "${S14};${name}=${val}" --meta "$f.meta" > "$f.run.log" 2>&1
  echo "done $name=$tag rc=$? $(tail -n 1 "$f.run.log" | head -c 120)"
}
export -f run_one
export EXE SET OUT PFX S14 L1
cat > "$OUT/table.txt" <<'EOF'
LmrQuietBase 85 101
LmrQuietDivisor 193 217
LmrNoisyBase 7 19
LmrNoisyDivisor 313 353
NullMoveBase 4 6
NullMoveDepthDivisor 2 4
NullMoveEvalDivisor 180 220
RfpDepth 7 9
RfpMargin 66 78
RfpImproving 34 46
RazorBase 130 170
RazorMultiplier 325 375
FutilityDepth 6 8
FutilityBase 88 112
FutilityMultiplier 100 120
LmpBase 7 9
HistoryPruneMultiplier 2020 2420
SeeQuietMultiplier 21 27
SeeNoisyMultiplier 138 162
SingularDepth 5 7
SingularMargin 1 3
IirDepth 1 3
ProbcutDepth 4 6
ProbcutMargin 165 195
QsFutilityMargin 146 174
QsSeeMargin 34 46
AspirationDelta 16 20
HistoryBonusQuadratic 21 27
HistoryBonusLinear 48 60
HistoryBonusMax 2032 2392
LmrHistoryDivisor 5143 6143
LmrCutoffThreshold 2 4
MaterialCorrectionWeight 90 110
CaptureFutilityMultiplier 225 275
CaptureFutilityDepth 5 7
EOF
# build the command list: setting, value, tag
: > "$OUT/cmds.txt"
while read -r n lo hi; do
  echo "$n $lo m" >> "$OUT/cmds.txt"
  echo "$n $hi p" >> "$OUT/cmds.txt"
done < "$OUT/table.txt"
# run with 3 lanes
while read -r n v t; do echo "$n $v $t"; done < "$OUT/cmds.txt" | \
  xargs -P 3 -L 1 bash -c 'run_one "$0" "$1" "$2"'
echo ALL_DONE
