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
for f in "$R" "$PY" "$src" "$P"; do [ -f "$f" ] || { echo "not found: $f (set PY / SRC / PROBE)" >&2; exit 2; }; done
[ -e "$d" ] && { echo "refusing existing $d" >&2; exit 2; }
mkdir -p "$d" && cd "$d" || exit 1
# relabel2's default disk floor is 50 GB: on a fuller drive every prepare / run / assemble case would fail on it
free=$("$PY" -I -B -c "import shutil; print(int(shutil.disk_usage('.').free / 1024 ** 3))")
[ "$free" -ge 51 ] || { echo "the scratch drive has $free GB free; relabel2 keeps 50 GB free: use a scratch folder on a drive with more space" >&2; exit 2; }
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
{ head -n 50 good.txt; echo 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 99999999999 | 0.5'; } > bad_score_range.txt
for f in bad_fen_fields bad_piece bad_score bad_result bad_fields bad_empty_line bad_terminal bad_noresult bad_tab bad_score_range; do
  expect 2 "prepare_$f" "$PY" -I -B "$R" prepare --job "job_$f" --run-id t --selfplay "$f.txt"
  if [ -e "job_$f/rows.tsv" ]; then echo "FAIL prepare_$f published rows.tsv"; fails=$((fails + 1)); fi
done
# --jobs 2 (two checking processes): the same error, naming the same row, as --jobs 1
for f in bad_piece bad_empty_line bad_terminal bad_tab bad_score_range; do
  expect 2 "prepare_j2_$f" "$PY" -I -B "$R" prepare --job "job_j2_$f" --run-id t --selfplay "$f.txt" --jobs 2
  check "prepare_j2_${f}_same_error" cmp -s "prepare_$f.err" "prepare_j2_$f.err"
done
expect 0 prepare_terminal_dropped "$PY" -I -B "$R" prepare --job job_term_drop --run-id t --selfplay bad_terminal.txt --drop-terminal
expect 2 prepare_missing_file "$PY" -I -B "$R" prepare --job job_missing --run-id t --selfplay no_such_file.txt
# a Python without python-chess: one clear message up front, not "bad input" on the first row
expect 2 prepare_no_chess "$PY" -I -B -c "import sys
sys.modules['chess'] = None
sys.path.insert(0, sys.argv[1])
import relabel2
sys.exit(relabel2.main(sys.argv[2:]))" "$here" prepare --job job_nochess --run-id t --selfplay good.txt
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
# sort_normalized.py: a shuffled copy sorts back to source order byte for byte; an impossible RAM floor is refused
sort -R norm_all.jsonl > norm_shuf.jsonl
expect 0 sort_shuffled "$PY" -I -B "$here/sort_normalized.py" norm_sorted.jsonl norm_shuf.jsonl
check sort_restores_source_order cmp -s norm_sorted.jsonl norm_all.jsonl
expect 2 sort_ram_floor "$PY" -I -B "$here/sort_normalized.py" --min-free-ram-gb 100000 norm_x.jsonl norm_shuf.jsonl
check sort_ram_floor_wrote_nothing test ! -e norm_x.jsonl
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
# disk floor (PC rule, --min-free-gb): an impossible floor -> refuse before writing; run stops before the next shard
expect 3 prepare_disk_floor "$PY" -I -B "$R" prepare --job job_disk --run-id t --selfplay good.txt --min-free-gb 100000
check prepare_disk_floor_wrote_nothing test ! -e job_disk
expect 3 run_disk_floor "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100 --min-free-gb 100000
check run_disk_floor_no_new_shard test -z "$(ls -d jg/shards/shard_00002* 2>/dev/null)"
check run_disk_floor_logged grep -q "disk floor" jg/sessions.log
expect 0 status_partial "$PY" -I -B "$R" status --job jg
check status_partial_progress grep -q "2/3 shards, 200/240 rows" status_partial.out   # --rows 300 keeps whole games: 240
expect 2 status_not_a_job "$PY" -I -B "$R" status --job no_such_job
expect 2 run_not_a_job "$PY" -I -B "$R" run --job no_such_job --run-id g --probe "$P" --nodes 5000 --shard-size 100
expect 2 run_missing_probe "$PY" -I -B "$R" run --job jg --run-id g --probe no_such_probe.exe --nodes 5000 --shard-size 100
expect 2 run_shard_size_zero "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 0
expect 2 run_bad_until "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100 --until tomorrow
expect 2 run_mask_not_hex "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100 --mask xyz
expect 2 run_mask_too_big "$PY" -I -B "$R" run --job jg --run-id g --probe "$P" --nodes 5000 --shard-size 100 --mask 0x10000000000
expect 2 prepare_mask_too_big "$PY" -I -B "$R" prepare --job job_mask --run-id t --selfplay good.txt --mask 0x10000000000
check prepare_mask_too_big_wrote_nothing test ! -e job_mask
# a "probe" that dies at once (not a probe): exit 1, the stop and its cause in sessions.log, the attempt kept, nothing published
expect 0 prepare_bad_probe_job "$PY" -I -B "$R" prepare --job jbp --run-id bp --selfplay good.txt --rows 300
expect 1 run_bad_probe "$PY" -I -B "$R" run --job jbp --run-id bp --probe 'C:\Windows\System32\whoami.exe' --nodes 5000 --shard-size 100
check run_bad_probe_logged grep -qE "run stop run_id=bp tool=[0-9a-f]{16} after 0 new shards: ProbeError" jbp/sessions.log
check run_bad_probe_attempt_kept test -d jbp/shards/shard_00000.part.1
check run_bad_probe_nothing_published test -z "$(ls -d jbp/shards/shard_0000? 2>/dev/null)"
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
# Windows handle contention (a virus scanner or a reader holding a file for a moment): a shard publish that fails
# twice with PermissionError is retried; a status.json that stays locked is skipped with a warning, the run goes on
expect 0 prepare_retry "$PY" -I -B "$R" prepare --job jr --run-id r --selfplay good.txt --rows 300
expect 0 run_publish_retry "$PY" -I -B -c "import os, sys
sys.path.insert(0, sys.argv[1])
import relabel2
real, left = os.rename, [2]
def flaky(src, dst):
    if os.path.basename(str(dst)).startswith('shard_') and left[0] > 0:
        left[0] -= 1
        raise PermissionError(13, 'simulated: in use', str(dst))
    return real(src, dst)
os.rename = flaky
sys.exit(relabel2.main(sys.argv[2:]))" "$here" run --job jr --run-id r --probe "$P" --nodes 5000 --shard-size 100
check run_publish_retry_all_shards test "$(ls -d jr/shards/shard_????? | wc -l)" = 3
expect 0 prepare_retry2 "$PY" -I -B "$R" prepare --job jr2 --run-id r --selfplay good.txt --rows 300
expect 0 run_status_locked "$PY" -I -B -c "import os, sys, time
sys.path.insert(0, sys.argv[1])
import relabel2
real = os.replace
def locked(src, dst):
    if os.path.basename(str(dst)) == 'status.json':
        raise PermissionError(13, 'simulated: open in a reader', str(dst))
    return real(src, dst)
os.replace = locked
time.sleep = lambda s: None
sys.exit(relabel2.main(sys.argv[2:]))" "$here" run --job jr2 --run-id r --probe "$P" --nodes 5000 --shard-size 100
check run_status_locked_warned grep -q "not updated" run_status_locked.err
check run_status_locked_all_shards test "$(ls -d jr2/shards/shard_????? | wc -l)" = 3
# mini kill / resume: 1,200 rows at 20000 nodes in shards of 100, a hard exit after 5 s, resume, assemble; the
# assembled files must equal an uninterrupted job's byte for byte, and the manifest is published with them
head -n 1500 "$src" > big.txt
expect 0 prepare_full "$PY" -I -B "$R" prepare --job jm --run-id m --selfplay big.txt --rows 1200
expect 0 run_full "$PY" -I -B "$R" run --job jm --run-id m --probe "$P" --nodes 20000 --shard-size 100
expect 3 assemble_disk_floor "$PY" -I -B "$R" assemble --job jm --run-id m --min-free-gb 100000
check assemble_disk_floor_wrote_nothing test -z "$(ls -d jm/final* 2>/dev/null)"
expect 0 assemble_full "$PY" -I -B "$R" assemble --job jm --run-id m
check manifest_published_with_data test -f jm/final/MANIFEST.json
expect 0 run_complete_job "$PY" -I -B "$R" run --job jm --run-id m --probe "$P" --nodes 20000 --shard-size 100
check run_complete_job_no_work grep -q "nothing left to label" jm/sessions.log
expect 0 status_complete "$PY" -I -B "$R" status --job jm
check status_complete_progress grep -q "final published" status_complete.out
check no_final_part_left test -z "$(ls -d jm/final.part.* 2>/dev/null)"
expect 3 assemble_again "$PY" -I -B "$R" assemble --job jm --run-id m
expect 0 prepare_kill "$PY" -I -B "$R" prepare --job jk --run-id m --selfplay big.txt --rows 1200
expect 137 run_hard_exit "$PY" -I -B "$R" run --job jk --run-id m --probe "$P" --nodes 20000 --shard-size 100 --test-kill-after-seconds 5
expect 0 run_resume "$PY" -I -B "$R" run --job jk --run-id m --probe "$P" --nodes 20000 --shard-size 100
expect 0 assemble_resumed "$PY" -I -B "$R" assemble --job jk --run-id m
for f in train.txt val.txt labels.tsv; do check "resumed_equals_uninterrupted_$f" cmp -s "jm/final/$f" "jk/final/$f"; done
echo "interrupted attempts kept: $(ls -d jk/shards/*.part.* 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ')"
# damaged job state (bug hunts 22:11, 22:37): job_damage.py runs 35 cases x run / assemble / status, each on a fresh copy of a
# finished small job, and wants exit 4 / 3 / 2 with relabel2's reason line or a clean exit 0 - never a traceback
expect 0 job_damage "$PY" -I -B "$here/job_damage.py" job_damage_cases
# every refusal must give the expected reason: a missing file or a crash can also end with exit 2 / 3 / 4
while read -r name text; do
  check "reason_$name" grep -qF -- "$text" "$name.err"
done <<'EOF'
prepare_bad_fen_fields bad_fen_fields.txt:51: original full FEN required
prepare_bad_piece bad_piece.txt:51: invalid character in position part of fen
prepare_bad_score bad_score.txt:51: invalid literal for int()
prepare_bad_result bad_result.txt:51: invalid result: 0.7
prepare_bad_fields bad_fields.txt:51: expected FEN | STM score | White result
prepare_bad_empty_line bad_empty_line.txt:51: empty line
prepare_bad_terminal bad_terminal.txt:51: terminal position (no legal move) cannot be searched
prepare_bad_score_range bad_score_range.txt:51: score 99999999999 outside -32767..32767
prepare_bad_noresult bad_noresult.txt:51: no game result
prepare_bad_tab bad_tab.txt:51: FEN contains a tab
prepare_missing_file no_such_file.txt: input file not found
prepare_existing_job job directory exists
prepare_same_file_twice same file or same content as input 0
prepare_same_content_twice same file or same content as input 0
prepare_val_ppm_range 0 <= --val-ppm <= 1000000
prepare_input_changed changed while prepare read it
prepare_normalized_overlap must be in source order
prepare_j2_normalized --jobs 2 reads --selfplay input only
prepare_j3 --jobs 1 or 2
prepare_files_out_of_order give the --selfplay files in name order
run_not_a_job not a prepared job
run_missing_probe probe no_such_probe.exe not found
run_shard_size_zero --shard-size >= 1
run_bad_until --until 'tomorrow' is not YYYY-MM-DD HH:MM
run_mask_not_hex --mask 'xyz' is not hexadecimal
run_mask_too_big names a CPU this PC does not have
prepare_mask_too_big names a CPU this PC does not have
run_bad_probe ProbeError
run_other_nodes configuration differs from run_config.json: ['nodes']
run_other_shard_size configuration differs from run_config.json: ['shard_size']
run_other_run_id run id other != job run id g
assemble_unfinished shard 2 is not published
run_tampered_shard shard_00001: labels.tsv sha256 differs from its manifest
run_tampered_rows rows.tsv differs from prepare.json
assemble_again final exists
prepare_disk_floor must stay free (--min-free-gb)
run_disk_floor must stay free (--min-free-gb)
assemble_disk_floor must stay free (--min-free-gb)
status_not_a_job not a prepared job
prepare_no_chess python-chess is needed
sort_ram_floor must stay free (--min-free-ram-gb
EOF
echo "failures: $fails"
exit $((fails > 0))
