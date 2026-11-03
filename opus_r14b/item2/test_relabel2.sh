#!/usr/bin/env bash
# test_relabel2.sh SCRATCH_DIR - Opus R14-B item 2: exit-code tests of relabel2.py (bad input -> 2, changed
# configuration or a busy job -> 3, tampered published shard -> 4) on small own inputs, plus a mini kill / resume
# (md5 of the assembled files = an uninterrupted job). SCRATCH_DIR must not exist. Uses the R13 probe (5000 nodes;
# 20000 for the kill / resume pair) on CPUs 2-3 at Idle. One PASS/FAIL line per case; exit 0 = all PASS.
set -u
d=${1:?scratch dir}
here=$(cd "$(dirname "$0")" && pwd)   # before the cd below: $0 may be relative
R=$here/relabel2.py
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
P=${PROBE:-'C:\o13\p5\forge_data_probe.exe'}
src=${SRC:-/d/grok-pc-data/selfplay_out/forge_selfplay_001.txt}
# a missing tool or input would make every "expect exit 2" case pass for the wrong reason
for f in "$R" "$PY" "$src"; do [ -f "$f" ] || { echo "not found: $f" >&2; exit 2; }; done
[ -e "$d" ] && { echo "refusing existing $d" >&2; exit 2; }
mkdir -p "$d" && cd "$d" || exit 1
fails=0
expect() {  # expect CODE NAME CMD...
  local want=$1 name=$2; shift 2
  "$@" >"$name.out" 2>"$name.err"; local got=$?
  if [ "$got" = "$want" ]; then echo "PASS $name (exit $got): $(head -c 160 "$name.err" | tr '\n' ' ')"
  else echo "FAIL $name: exit $got, wanted $want: $(head -c 300 "$name.err" | tr '\n' ' ')"; fails=$((fails + 1)); fi
}
check() {  # check NAME CONDITION-CMD...: one more PASS/FAIL line for a property of the files
  local name=$1; shift
  if "$@"; then echo "PASS $name"; else echo "FAIL $name"; fails=$((fails + 1)); fi
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
{ head -n 50 good.txt; printf 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -\t0 1 | 20 | 0.5\n'; } > bad_tab.txt
for f in bad_fen_fields bad_piece bad_score bad_result bad_fields bad_empty_line bad_terminal bad_noresult bad_tab; do
  expect 2 "prepare_$f" "$PY" -I -B "$R" prepare --job "job_$f" --run-id t --selfplay "$f.txt"
  if [ -e "job_$f/rows.tsv" ]; then echo "FAIL prepare_$f published rows.tsv"; fails=$((fails + 1)); fi
done
# --jobs 2 (two checking processes): the same error, naming the same row, as --jobs 1
for f in bad_piece bad_empty_line bad_terminal bad_tab; do
  expect 2 "prepare_j2_$f" "$PY" -I -B "$R" prepare --job "job_j2_$f" --run-id t --selfplay "$f.txt" --jobs 2
  check "prepare_j2_${f}_same_error" cmp -s "prepare_$f.err" "prepare_j2_$f.err"
done
expect 0 prepare_terminal_dropped "$PY" -I -B "$R" prepare --job job_term_drop --run-id t --selfplay bad_terminal.txt --drop-terminal
expect 2 prepare_missing_file "$PY" -I -B "$R" prepare --job job_missing --run-id t --selfplay no_such_file.txt
expect 3 prepare_existing_job "$PY" -I -B "$R" prepare --job job_term_drop --run-id t --selfplay good.txt
# each input once: the same games twice would get two game ids and could land in both splits
cp good.txt good_copy.txt
expect 2 prepare_same_file_twice "$PY" -I -B "$R" prepare --job job_twice --run-id t --selfplay good.txt good.txt
expect 2 prepare_same_content_twice "$PY" -I -B "$R" prepare --job job_twice2 --run-id t --selfplay good.txt good_copy.txt
expect 2 prepare_val_ppm_range "$PY" -I -B "$R" prepare --job job_ppm --run-id t --selfplay good.txt --val-ppm 2000000
# an input that grows while prepare reads it (like the self-play file still being written): appended after the last row
cp good.txt growing.txt
expect 2 prepare_input_changed "$PY" -I -B -c "import sys
sys.path.insert(0, sys.argv[1])
import relabel2
orig = relabel2.iter_rows
def grow(*args):
    yield from orig(*args)
    with open('growing.txt', 'a', newline='\n') as f:
        f.write(open('good.txt').readline())
relabel2.iter_rows = grow
sys.exit(relabel2.main(sys.argv[2:]))" "$here" prepare --job job_grow --run-id t --selfplay growing.txt
check prepare_input_changed_nothing_published test ! -e job_grow/rows.tsv
# a file after the --rows cut may change (e.g. the live self-play file at the end of the list): it is never read
head -n 450 "$src" | tail -n 50 > later.txt
expect 0 prepare_unread_input_changed "$PY" -I -B -c "import sys
sys.path.insert(0, sys.argv[1])
import relabel2
orig = relabel2.iter_rows
def grow(*args):
    with open('later.txt', 'a', newline='\n') as f:
        f.write(open('good.txt').readline())
    yield from orig(*args)
relabel2.iter_rows = grow
sys.exit(relabel2.main(sys.argv[2:]))" "$here" prepare --job job_unread --run-id t --selfplay good.txt later.txt --rows 300
check prepare_unread_input_marked grep -q '"read": false' job_unread/prepare.json
# normalized input (Astra records): source order must hold across all files
"$PY" -I -B -c "import sys
sys.path.insert(0, sys.argv[1])
import records
with open('good.txt', encoding='utf-8') as f, open('norm_all.jsonl', 'x', encoding='utf-8', newline='\n') as out:
    for i, line in enumerate(f, 1):
        out.write(records.dumps(records.selfplay_record(line, 'forge_selfplay_001.txt', i)) + '\n')" "$here/astra"
head -n 60 norm_all.jsonl > norm_a.jsonl; sed -n '50,100p' norm_all.jsonl > norm_b.jsonl
sed -n '61,100p' norm_all.jsonl > norm_c.jsonl; head -n 100 norm_all.jsonl > norm_100.jsonl
expect 2 prepare_normalized_overlap "$PY" -I -B "$R" prepare --job job_nov --run-id t --normalized norm_a.jsonl norm_b.jsonl
expect 0 prepare_normalized_two_files "$PY" -I -B "$R" prepare --job job_n2 --run-id t --normalized norm_a.jsonl norm_c.jsonl
expect 0 prepare_normalized_one_file "$PY" -I -B "$R" prepare --job job_n1 --run-id t --normalized norm_100.jsonl
check normalized_two_files_same_rows cmp -s job_n2/rows.tsv job_n1/rows.tsv
expect 2 prepare_j2_normalized "$PY" -I -B "$R" prepare --job job_j2n --run-id t --normalized norm_100.jsonl --jobs 2
expect 2 prepare_j3 "$PY" -I -B "$R" prepare --job job_j3 --run-id t --selfplay good.txt --jobs 3
# --jobs 2 gives the same rows.tsv: whole file, a --rows cut, and 30,000 lines (8 blocks of 4,096, several in flight)
head -n 30000 "$src" > lines30k.txt
for spec in "whole good.txt 0" "cut good.txt 300" "big lines30k.txt 0"; do
  set -- $spec
  expect 0 "prepare_j1_$1" "$PY" -I -B "$R" prepare --job "jp1_$1" --run-id t --selfplay "$2" --rows "$3"
  expect 0 "prepare_j2_$1" "$PY" -I -B "$R" prepare --job "jp2_$1" --run-id t --selfplay "$2" --rows "$3" --jobs 2
  check "prepare_j2_${1}_same_rows" cmp -s "jp1_$1/rows.tsv" "jp2_$1/rows.tsv"
done
# a game that runs from one file into the next (R8 v5 writes fixed 1M-position shards) stays one game: good.txt cut
# inside its first game into two files gives the same game partition as the whole file; files out of name order -> 2
head -n 30 good.txt > s_a.txt; tail -n +31 good.txt > s_b.txt
expect 0 prepare_straddle "$PY" -I -B "$R" prepare --job jsa --run-id t --selfplay s_a.txt s_b.txt
expect 0 prepare_straddle_j2 "$PY" -I -B "$R" prepare --job jsa2 --run-id t --selfplay s_a.txt s_b.txt --jobs 2
bounds() { awk -F'\t' 'NR > 1 && $2 != prev {print $1} {prev = $2}' "$1"; }
check straddle_same_partition_as_one_file cmp -s <(bounds jsa/rows.tsv) <(bounds jp1_whole/rows.tsv)
check straddle_one_game_id test "$(awk -F'\t' '$1 == 29 || $1 == 30 {print $2}' jsa/rows.tsv | sort -u | wc -l)" = 1
check straddle_j2_same_rows cmp -s jsa/rows.tsv jsa2/rows.tsv
expect 2 prepare_files_out_of_order "$PY" -I -B "$R" prepare --job jso --run-id t --selfplay s_b.txt s_a.txt
# a good job: run 2 shards, then a busy job and configuration changes (exit 3) and a tampered shard (exit 4)
expect 0 prepare_good "$PY" -I -B "$R" prepare --job jg --run-id g --selfplay good.txt --rows 300
expect 0 run_two_shards "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100 --max-shards 2
expect 2 run_not_a_job "$PY" -I -B "$R" run --job no_such_job --run-id g --probe "$P" --nodes 5000 --shard-size 100
expect 2 run_missing_probe "$PY" -I -B "$R" run --job jg --run-id g --probe no_such_probe.exe --nodes 5000 --shard-size 100
expect 2 run_shard_size_zero "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 0
expect 2 run_bad_until "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100 --until tomorrow
expect 3 run_busy_job "$PY" -I -B -c "import msvcrt, subprocess, sys
f = open('jg/job.lock', 'a+b'); f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
sys.exit(subprocess.call(sys.argv[1:]))" "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100
check run_busy_job_message grep -q "another relabel2.py process" run_busy_job.err
expect 3 run_other_nodes "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 6000 --shard-size 100
expect 3 run_other_shard_size "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 50
expect 3 run_other_run_id "$PY" -I -B "$R" run --job jg --run-id other --probe "$P" --nodes 5000 --shard-size 100
expect 4 assemble_unfinished "$PY" -I -B "$R" assemble --job jg --run-id g
printf 'x' >> jg/shards/shard_00001/labels.tsv   # tamper with this test's own published shard
expect 4 run_tampered_shard "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100
printf 'x' >> jg/rows.tsv
expect 4 run_tampered_rows "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100
# mini kill / resume: 1,200 rows at 20000 nodes in shards of 100, a hard exit after 5 s, resume, assemble; the
# assembled files must equal an uninterrupted job's byte for byte, and the manifest is published with them
head -n 1500 "$src" > big.txt
expect 0 prepare_full "$PY" -I -B "$R" prepare --job jm --run-id m --selfplay big.txt --rows 1200
expect 0 run_full "$PY" -I -B "$R" run --job jm --run-id m --probe "$P" --nodes 20000 --shard-size 100
expect 0 assemble_full "$PY" -I -B "$R" assemble --job jm --run-id m
check manifest_published_with_data test -f jm/final/MANIFEST.json
check no_final_part_left test -z "$(ls -d jm/final.part.* 2>/dev/null)"
expect 3 assemble_again "$PY" -I -B "$R" assemble --job jm --run-id m
expect 0 prepare_kill "$PY" -I -B "$R" prepare --job jk --run-id m --selfplay big.txt --rows 1200
expect 137 run_hard_exit "$PY" -I -B "$R" run --job jk --run-id m --probe "$P" --nodes 20000 --shard-size 100 --test-kill-after-seconds 5
expect 0 run_resume "$PY" -I -B "$R" run --job jk --run-id m --probe "$P" --nodes 20000 --shard-size 100
expect 0 assemble_resumed "$PY" -I -B "$R" assemble --job jk --run-id m
for f in train.txt val.txt labels.tsv; do check "resumed_equals_uninterrupted_$f" cmp -s "jm/final/$f" "jk/final/$f"; done
echo "interrupted attempts kept: $(ls -d jk/shards/*.part.* 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ')"
echo "failures: $fails"
exit $((fails > 0))
