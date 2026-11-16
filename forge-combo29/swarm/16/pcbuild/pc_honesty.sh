#!/usr/bin/env bash
# pc_honesty.sh EXE OUTDIR : the three setting regimes from FABLE_TO_swarm_5, each a fresh process per line.
#   none  : no setoption at all           (must be 312866 / 862329 / 3024920 / 4865609)
#   S14   : the 14 settings of file 1     (bench 11 242796, bench 13 656517)
#   PC20  : S14 + the six PC settings     (bench 11 278024, bench 13 587276)
# Every option name is checked against the exe's own uci list FIRST; stop on unknown/invalid.
set -u
EXE="${1:?exe}"; OUT="${2:?outdir}"
mkdir -p "$OUT"

# collect the option names the exe advertises
printf 'uci\nquit\n' | "$EXE" | sed -n 's/^option name \(.*\) type .*/\1/p' > "$OUT/option_names.txt"

S14_NAMES="LmrQuietBase LmrQuietDivisor LmrNoisyBase LmrNoisyDivisor LmrHistoryDivisor NullMoveBase LmpBase HistoryPruneMultiplier HistoryBonusQuadratic HistoryBonusLinear HistoryBonusMax SingularDepth IirDepth NonPawnCorrection"
PC_NAMES="CuckooRep HistRework TtPruneV2 CorrHistV2 MateAlphaGuard OwnBook"
missing=""
for n in $S14_NAMES $PC_NAMES; do
  grep -qx "$n" "$OUT/option_names.txt" || missing="$missing $n"
done
if [ -n "$missing" ]; then echo "STOP: options absent from the exe's uci list:$missing" | tee "$OUT/RESULT.txt"; exit 2; fi
echo "all 20 option names present in the uci list" | tee "$OUT/RESULT.txt"

s14_cmds() {
  cat <<'EOF'
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
EOF
}
pc20_cmds() {
  s14_cmds
  cat <<'EOF'
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false
EOF
}

run_regime() {
  local name="$1"; shift
  local opts="$1"
  {
    echo "### regime $name"
    for spec in "bench 11" "bench 13" "bench 16" "go perft 5"; do
      {
        printf 'uci\nisready\n'
        [ -n "$opts" ] && printf '%s\n' "$opts" && printf 'isready\n'
        printf 'ucinewgame\nisready\n%s\nquit\n' "$spec"
      } | "$EXE" > "$OUT/${name}_$(echo "$spec" | tr ' ' '_').raw" 2>&1
      n=$(grep -oE 'nodes[[:space:]]+[0-9]+' "$OUT/${name}_$(echo "$spec" | tr ' ' '_').raw" | tail -1 | grep -oE '[0-9]+$')
      printf '%-14s %-12s -> %s\n' "$name" "$spec" "${n:-NONE}"
      grep -qiE "unknown option|invalid value" "$OUT/${name}_$(echo "$spec" | tr ' ' '_').raw" && echo "   STOP: bad option line"
    done
  } | tee -a "$OUT/RESULT.txt"
}

run_regime none ""
run_regime s14 "$(s14_cmds)"
run_regime pc20 "$(pc20_cmds)"
echo "--- done, see $OUT/RESULT.txt"
