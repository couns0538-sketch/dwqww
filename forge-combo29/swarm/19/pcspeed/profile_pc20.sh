#!/usr/bin/env bash
# profile_pc20.sh EXE OUTDIR REPS : perf profile of the PC build under PC20, Threads 1.
# PC20 = S14 + CuckooRep true / HistRework 2 / TtPruneV2 true / CorrHistV2 true / MateAlphaGuard true /
# OwnBook false. Every setoption followed by isready; every answer line scanned for refusal text.
# `bench 13` repeated REPS times in one process (bench is self-clearing, so every position is cold — 19-F23),
# which is the cheapest way to get many samples under PC20.
set -u
EXE="${1:?exe}"; OUT="${2:?outdir}"; REPS="${3:-40}"
mkdir -p "$OUT"
PERF=/usr/lib/linux-tools/6.8.0-149-generic/perf
EXE_ABS="$(readlink -f "$EXE")"
S14=("LmrQuietBase 93" "LmrQuietDivisor 205" "LmrNoisyBase 13" "LmrNoisyDivisor 333"
     "LmrHistoryDivisor 5643" "NullMoveBase 5" "LmpBase 8" "HistoryPruneMultiplier 2220"
     "HistoryBonusQuadratic 24" "HistoryBonusLinear 54" "HistoryBonusMax 2212"
     "SingularDepth 6" "IirDepth 2" "NonPawnCorrection true")
PC=("CuckooRep true" "HistRework 2" "TtPruneV2 true" "CorrHistV2 true" "MateAlphaGuard true" "OwnBook false")
{
  echo uci; echo isready
  for s in "${S14[@]}" "${PC[@]}"; do echo "setoption name ${s% *} value ${s##* }"; echo isready; done
  for i in $(seq 1 "$REPS"); do echo "bench 13"; done
  echo quit
} > "$OUT/stream.txt"
{
  echo "exe $EXE_ABS"; sha256sum "$EXE_ABS"
  printf 'uci\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' | grep -E '^id name'
  echo "perf: $("$PERF" --version)"; echo "paranoid $(cat /proc/sys/kernel/perf_event_paranoid)"
  echo "settings: PC20 (S14 + CuckooRep true / HistRework 2 / TtPruneV2 true / CorrHistV2 true / MateAlphaGuard true / OwnBook false)"
  echo "Threads: not set -> default 1"
  echo "workload: bench 13 x $REPS in one process (bench self-clears before each position, 19-F23)"
  echo "command: perf record -o DATA -F 1999 -g -- EXE < stream.txt"
  echo "date $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/profile.meta" 2>&1

"$PERF" record -o "$OUT/perf.data" -F 1999 -g -- "$EXE_ABS" < "$OUT/stream.txt" \
  > "$OUT/bench.stdout.txt" 2> "$OUT/perf.record.stderr.txt"
echo "record exit $?" >> "$OUT/profile.meta"
grep -cE "unknown option|invalid value|ERROR" "$OUT/bench.stdout.txt" > "$OUT/refusals.txt" || true
"$PERF" report -i "$OUT/perf.data" --stdio --no-children -g none --sort symbol > "$OUT/perf_symbols_all.txt" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio --children --sort symbol > "$OUT/perf_children.txt" 2>&1
rm -f "$OUT/perf.data"
date -u
grep -oE "bench depth 13 nodes [0-9]+" "$OUT/bench.stdout.txt" | sort | uniq -c
echo "refusals: $(cat "$OUT/refusals.txt")"
grep -E '^# Samples:' "$OUT/perf_symbols_all.txt"
