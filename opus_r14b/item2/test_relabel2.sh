#!/usr/bin/env bash
# test_relabel2.sh SCRATCH_DIR - Opus R14-B item 2: exit-code tests of relabel2.py (bad input -> 2, changed
# configuration -> 3, tampered published shard -> 4) on small own inputs. SCRATCH_DIR must not exist. Uses the R13
# probe at 5000 nodes for the few rows that get labelled. Prints one PASS/FAIL line per case; exit 0 = all PASS.
set -u
d=${1:?scratch dir}
[ -e "$d" ] && { echo "refusing existing $d" >&2; exit 2; }
mkdir -p "$d" && cd "$d" || exit 1
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
R=$(cd "$(dirname "$0")" && pwd)/relabel2.py
P=${PROBE:-'C:\o13\p5\forge_data_probe.exe'}
src=${SRC:-/d/grok-pc-data/selfplay_out/forge_selfplay_001.txt}
fails=0
expect() {  # expect CODE NAME CMD...
  local want=$1 name=$2; shift 2
  "$@" >"$name.out" 2>"$name.err"; local got=$?
  if [ "$got" = "$want" ]; then echo "PASS $name (exit $got): $(head -c 160 "$name.err" | tr '\n' ' ')"
  else echo "FAIL $name: exit $got, wanted $want: $(head -c 300 "$name.err" | tr '\n' ' ')"; fails=$((fails + 1)); fi
}
head -n 400 "$src" > good.txt
# bad inputs (exit 2), nothing published
{ head -n 50 good.txt; echo 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 | 20 | 0.5'; } > bad_fen_fields.txt
{ head -n 50 good.txt; echo 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNX w KQkq - 0 1 | 20 | 0.5'; } > bad_piece.txt
{ head -n 50 good.txt; echo 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | x20 | 0.5'; } > bad_score.txt
{ head -n 50 good.txt; echo 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 20 | 0.7'; } > bad_result.txt
{ head -n 50 good.txt; echo 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 20'; } > bad_fields.txt
{ head -n 50 good.txt; echo ''; head -n 60 good.txt | tail -n 10; } > bad_empty_line.txt
{ head -n 50 good.txt; echo '7k/6Q1/6K1/8/8/8/8/8 b - - 0 60 | -32000 | 1'; } > bad_terminal.txt
{ head -n 50 good.txt; echo 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 20 | ?'; } > bad_noresult.txt
for f in bad_fen_fields bad_piece bad_score bad_result bad_fields bad_empty_line bad_terminal bad_noresult; do
  expect 2 "prepare_$f" "$PY" -I -B "$R" prepare --job "job_$f" --run-id t --selfplay "$f.txt"
  if [ -e "job_$f/rows.tsv" ]; then echo "FAIL prepare_$f published rows.tsv"; fails=$((fails + 1)); fi
done
expect 0 prepare_terminal_dropped "$PY" -I -B "$R" prepare --job job_term_drop --run-id t --selfplay bad_terminal.txt --drop-terminal
expect 2 prepare_missing_file "$PY" -I -B "$R" prepare --job job_missing --run-id t --selfplay no_such_file.txt
expect 3 prepare_existing_job "$PY" -I -B "$R" prepare --job job_term_drop --run-id t --selfplay good.txt
# a good job: run 2 shards, then configuration changes (exit 3) and a tampered shard (exit 4)
expect 0 prepare_good "$PY" -I -B "$R" prepare --job jg --run-id g --selfplay good.txt --rows 300
expect 0 run_two_shards "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100 --max-shards 2
expect 3 run_other_nodes "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 6000 --shard-size 100
expect 3 run_other_shard_size "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 50
expect 3 run_other_run_id "$PY" -I -B "$R" run --job jg --run-id other --probe "$P" --nodes 5000 --shard-size 100
expect 4 assemble_unfinished "$PY" -I -B "$R" assemble --job jg --run-id g
printf 'x' >> jg/shards/shard_00001/labels.tsv   # tamper with this test's own published shard
expect 4 run_tampered_shard "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100
printf 'x' >> jg/rows.tsv
expect 4 run_tampered_rows "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100
echo "failures: $fails"
exit $((fails > 0))
