#!/usr/bin/env bash
# pc_honesty.sh : check the PC r15 build against file 5's three rows of known numbers.
# A fresh process for every line; each regime's setoptions are sent in full and every option name
# must exist (the runner stops on "unknown option" / "invalid value" / "ERROR").
set -u
EXE="${1:-$HOME/pcbuild/forge}"
OUT="${2:-$HOME/pcregime}"
mkdir -p "$OUT"

{
  echo "== meta"
  echo "exe_started=$EXE"
  sha256sum "$EXE"
  "$EXE" <<< "uci
quit" | grep "^id name"
  echo "gcc=$(g++ --version | head -1)"
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "flags=-DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4 -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1"
} | tee "$OUT/meta.txt"

S14=(
  "setoption name LmrQuietBase value 93"
  "setoption name LmrQuietDivisor value 205"
  "setoption name LmrNoisyBase value 13"
  "setoption name LmrNoisyDivisor value 333"
  "setoption name LmrHistoryDivisor value 5643"
  "setoption name NullMoveBase value 5"
  "setoption name LmpBase value 8"
  "setoption name HistoryPruneMultiplier value 2220"
  "setoption name HistoryBonusQuadratic value 24"
  "setoption name HistoryBonusLinear value 54"
  "setoption name HistoryBonusMax value 2212"
  "setoption name SingularDepth value 6"
  "setoption name IirDepth value 2"
  "setoption name NonPawnCorrection value true"
)
PC20=(
  "setoption name CuckooRep value true"
  "setoption name HistRework value 2"
  "setoption name TtPruneV2 value true"
  "setoption name CorrHistV2 value true"
  "setoption name MateAlphaGuard value true"
  "setoption name OwnBook value false"
)

run() { # tag regime bench-depth
  local tag="$1"; local bench="$2"
  shift 2
  local in="$OUT/$tag.in"
  {
    echo "uci"
    for line in "$@"; do echo "$line"; echo "isready"; done
    echo "isready"
    echo "bench $bench"
    echo "quit"
  } > "$in"
  "$EXE" < "$in" > "$OUT/$tag.out" 2>&1
  local bad
  bad=$(grep -cE "unknown option|invalid value|ERROR" "$OUT/$tag.out")
  local nodes
  nodes=$(grep -oE "nodes [0-9]+" "$OUT/$tag.out" | tail -1 | awk '{print $2}')
  printf '%-22s bad_lines=%s  nodes=%s\n' "$tag" "$bad" "${nodes:-MISSING}"
}

echo
echo "== row 1: NO setoption at all"
run "none_bench11" 11
run "none_bench13" 13
run "none_bench16" 16
printf 'none_perft5' > "$OUT/none_perft5.in"
printf 'uci\nisready\nposition startpos\ngo perft 5\nquit\n' > "$OUT/none_perft5.in"
"$EXE" < "$OUT/none_perft5.in" > "$OUT/none_perft5.out" 2>&1
echo "none_perft5            nodes=$(grep -E '^nodes ' "$OUT/none_perft5.out" | tail -1 | awk '{print $2}')"

echo
echo "== row 2: S14"
run "s14_bench11" 11 "${S14[@]}"
run "s14_bench13" 13 "${S14[@]}"

echo
echo "== row 3: PC20 (S14 + the six)"
run "pc20_bench11" 11 "${S14[@]}" "${PC20[@]}"
run "pc20_bench13" 13 "${S14[@]}" "${PC20[@]}"
