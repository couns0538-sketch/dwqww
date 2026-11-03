#!/usr/bin/env bash
# test_tools.sh SCRATCH - Opus R14-B: tests of abba.py and doc_lint.py (exit codes and the lines they must print).
# SCRATCH must not exist (it is created; nothing is deleted). About 30 s; the abba runs use mask 0xC at Idle.
set -u
here=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
S=${1:?usage: test_tools.sh NEW_SCRATCH_DIR}
[ -e "$S" ] && { echo "test_tools: $S exists (use a new folder)"; exit 2; }
mkdir -p "$S" || exit 2
fail=0
check() {  # check NAME WANT_EXIT GOT_EXIT OUTPUT_FILE [REGEX...]
  local name=$1 want=$2 got=$3 out=$4 ok=1; shift 4
  [ "$got" = "$want" ] || ok=0
  for rx in "$@"; do grep -qE -- "$rx" "$out" || { ok=0; echo "   missing: $rx"; }; done
  if [ $ok = 1 ]; then echo "PASS $name"; else echo "FAIL $name (exit $got, want $want; output $out)"; fail=1; fi
}
ab() { "$PY" -I -B "$here/abba.py" --load-seconds 0 "$@"; }

ab --out "$S/ab_rate" --pairs 3 --metric 'rate ([0-9,]+) rows/h' --higher-better --identity 'id=(\w+)' --identity-ab \
   --a "echo 'id=x rate 1,000 rows/h'" --b "echo 'id=x rate 2,000 rows/h'" > "$S/ab_rate.out" 2>&1
check abba-rate 0 $? "$S/ab_rate.out" 'geometric mean 2\.0000, 95% CI 2\.0000 \.\. 2\.0000' 'identity: A = B'
ab --out "$S/ab_wall" --pairs 2 --a "sleep 0.4" --b "sleep 0.1" > "$S/ab_wall.out" 2>&1
check abba-wall 0 $? "$S/ab_wall.out" 'speed-up of B over A \(A/B per pair\)' 'slot 1 BA'
ab --out "$S/ab_id" --pairs 2 --identity 'id=(\w+)' --identity-ab --a "echo id=x" --b "echo id=y" > "$S/ab_id.out" 2>&1
check abba-identity-differs 2 $? "$S/ab_id.out" "identity A \['x'\] != B \['y'\]"
ab --out "$S/ab_drift" --pairs 3 --identity 'n=(\d+)' --a 'echo n=$RANDOM' --b "echo n=1" > "$S/ab_drift.out" 2>&1
check abba-identity-within-arm 2 $? "$S/ab_drift.out" 'differs from the first A run'
ab --out "$S/ab_fail" --pairs 2 --a true --b "exit 3" > "$S/ab_fail.out" 2>&1
check abba-run-fails 1 $? "$S/ab_fail.out" 'run 000_B exited 3'
ab --out "$S/ab_fail" --pairs 2 --a true --b true > "$S/ab_exists.out" 2>&1
check abba-out-exists 2 $? "$S/ab_exists.out" 'exists \(write fresh'
ab --out "$S/ab_nometric" --pairs 2 --metric 'x ([0-9]+)' --a "echo x 5" --b "echo none" > "$S/ab_nometric.out" 2>&1
check abba-metric-missing 2 $? "$S/ab_nometric.out" '--metric found nothing in run 000_B'
ab --out "$S/ab_args" --pairs 1 --a true --b true > "$S/ab_args.out" 2>&1
check abba-pairs-1 2 $? "$S/ab_args.out" 'pairs must be >= 2'
[ ! -e "$S/ab_args" ] || { echo "FAIL abba-pairs-1 created its folder"; fail=1; }
ab --out "$S/ab_mask" --pairs 2 --mask xyz --a true --b true > "$S/ab_mask.out" 2>&1
check abba-bad-mask 2 $? "$S/ab_mask.out" 'not a hex CPU mask'
ab --out "$S/ab_nan" --pairs 2 --metric 'v=([0-9.]+)' --a "echo v=1.2.3" --b "echo v=1" > "$S/ab_nan.out" 2>&1
check abba-metric-not-a-number 2 $? "$S/ab_nan.out" "group 1 is '1\.2\.3', not a number"

F="$S/lint"; mkdir -p "$F"
printf 'a\x08b\n' > "$F/ctrl.md"; printf 'echo hi\r\necho ho\r\n' > "$F/crlf.sh"; printf '\xef\xbb\xbfprint(1)\n' > "$F/bom.py"
printf 'see C:o14bpgo2 and D:grok-pc-data\n' > "$F/drive.md"; printf 'x\n<<<<<<< HEAD\ny\n' > "$F/conflict.md"  # doc_lint: ignore
printf '| a | b |\n|---|---|\n| `x | y` | z |\n| only |\n| `x \\| y` | z |\n' > "$F/table.md"
printf '[t](missing.md) [ok](table.md) [w](https://x.y/z)\n' > "$F/link.md"; printf '\xff\xfe bad\n' > "$F/notutf8.txt"
"$PY" -I -B "$here/doc_lint.py" "$F" > "$S/lint.out" 2>&1
check doc_lint-findings 1 $? "$S/lint.out" 'ctrl.md:1: \[control\]' 'crlf.sh:1: \[crlf\] 2 CRLF' 'bom.py:1: \[utf8\] BOM' \
  "drive.md:1: \[drive\] 'C:[o]14bpgo2" "drive.md:1: \[drive\] 'D:[g]rok-pc-data" 'conflict.md:2: \[conflict\]' \
  'table.md:3: \[table\] 3 cells, header 2 \(dropped' 'table.md:4: \[table\] 1 cells, header 2 \(padded' \
  'link.md:1: \[link\] missing.md' 'notutf8.txt:1: \[utf8\] not UTF-8' 'doc_lint: 8 files, 10 findings'
grep -q 'table.md:5' "$S/lint.out" && { echo "FAIL doc_lint flagged an escaped pipe (table.md:5)"; fail=1; }
C="$S/lint_clean"; mkdir -p "$C"
printf 'fine C:/o14b and C:\\o14b, F:\\x; R14-B: ok; exit:K:FLAG; http://a.b\nskip C:o14bx (doc_lint: ignore)\n' > "$C/ok.md"
"$PY" -I -B "$here/doc_lint.py" "$C" > "$S/lint_clean.out" 2>&1
check doc_lint-clean 0 $? "$S/lint_clean.out" 'doc_lint: 1 files, 0 findings'
E="$S/lint_edge"; mkdir -p "$E/sub dir"; printf 'x\n' > "$E/sub dir/a b.md"
printf '[ok](sub%%20dir/a%%20b.md)\n\n| a | b |\n|-|-|\n| 1 | 2 | 3 |\n' > "$E/t.md"
"$PY" -I -B "$here/doc_lint.py" "$E" > "$S/lint_edge.out" 2>&1
check doc_lint-one-dash-table-and-encoded-link 1 $? "$S/lint_edge.out" 't.md:5: \[table\] 3 cells' 'doc_lint: 2 files, 1 findings'
A="$S/lint_after_table"; mkdir -p "$A"
printf '| a | b |\n|---|---|\n| 1 | 2 |\ntext right after\n\n| c | d |\n|---|---|\n| 3 | 4 |\n- a list item ends it\n' > "$A/t.md"
"$PY" -I -B "$here/doc_lint.py" "$A" > "$S/lint_after_table.out" 2>&1
check doc_lint-text-after-table 1 $? "$S/lint_after_table.out" 't.md:4: \[table\] text right after a table' 'doc_lint: 1 files, 1 findings'
"$PY" -I -B "$here/doc_lint.py" "$S/nonexistent" > "$S/lint_missing.out" 2>&1
check doc_lint-missing-path 2 $? "$S/lint_missing.out" 'does not exist'
bash "$here/opus.sh" help > "$S/opus_help.out" 2>&1
check opus-help 0 $? "$S/opus_help.out" '^  status' '^  lint' '^  abba' '^  engine' '^  bisect' '^  time' '^  load' '^  gpu' '^  test'
bash "$here/opus.sh" nope > "$S/opus_nope.out" 2>&1
check opus-unknown-command 2 $? "$S/opus_nope.out" "unknown command 'nope'"
bash "$here/opus.sh" load xyz > "$S/opus_load_bad.out" 2>&1  # bug hunt #13: was exit 0 with an empty list
check opus-load-bad-mask 2 $? "$S/opus_load_bad.out" "is not a hexadecimal CPU mask"
bash "$here/opus.sh" status --cl > "$S/opus_status_bad.out" 2>&1  # bug hunt #13: a misspelt option became the glob
check opus-status-unknown-option 2 $? "$S/opus_status_bad.out" "unknown option '--cl'"
bash "$here/opus.sh" time --since "2026-11-02 12:00" --until "2026-11-02 13:00" origin/opus-r14b-fast-loader > "$S/opus_time.out" 2>&1
check opus-time 0 $? "$S/opus_time.out" '^branch +commits' 'origin/opus-r14b-fast-loader'
X="$S/bisect_repo"; mkdir -p "$X"
( cd "$X" && git init -q && git config user.name t && git config user.email t@local && git config core.autocrlf false &&
  for i in $(seq 0 15); do if [ $i -lt 9 ]; then echo a > v; else echo b > v; fi; echo $i > n; git add v n;
  git commit -q -m "c$i"; done ) || { echo "FAIL bisect fixture"; fail=1; }
G=$(git -C "$X" rev-list --reverse HEAD | head -1); B=$(git -C "$X" rev-parse HEAD)
isa="test \"\$(git -C '$X' show {sha}:v)\" = a"
REPO="$X" bash "$here/engine_bisect.sh" "$G" "$B" "$S/bis_find" --test "$isa" > "$S/bis_find.out" 2>&1
check bisect-finds-first-change 0 $? "$S/bis_find.out" "RESULT: first changed commit $(git -C "$X" rev-parse HEAD~6) .* c9\)"
REPO="$X" bash "$here/engine_bisect.sh" "$G" "$B" "$S/bis_skip" \
  --test "n=\$(git -C '$X' show {sha}:n); [ \$n = 8 ] || [ \$n = 9 ] && exit 125; $isa" > "$S/bis_skip.out" 2>&1
check bisect-skipped-range 3 $? "$S/bis_skip.out" "one of the skipped commits .*: $(git -C "$X" rev-parse --short=12 HEAD~7) $(git -C "$X" rev-parse --short=12 HEAD~6) - or $(git -C "$X" rev-parse --short=12 HEAD~5)"
REPO="$X" bash "$here/engine_bisect.sh" "$G" "$B" "$S/bis_none" --test true > "$S/bis_none.out" 2>&1
check bisect-nothing-to-find 1 $? "$S/bis_none.out" 'nothing to find'
REPO="$X" bash "$here/engine_bisect.sh" "$B" "$G" "$S/bis_order" --test true > "$S/bis_order.out" 2>&1
check bisect-not-ancestor 2 $? "$S/bis_order.out" 'is not an ancestor'
M="$S/bisect_merge_repo"; mkdir -p "$M"   # m0 - m1 - m2 (merge of side commit s1, which branched at m0)
( cd "$M" && git init -q && git config user.name t && git config user.email t@local && git config core.autocrlf false &&
  echo 0 > v && git add v && git commit -q -m m0 && git branch side && echo 1 > v && git commit -qam m1 &&
  git checkout -q side && echo s > w && git add w && git commit -q -m s1 && git checkout -q - &&
  git merge -q --no-ff -m m2 side ) > /dev/null 2>&1 || { echo "FAIL bisect merge fixture"; fail=1; }
REPO="$M" bash "$here/engine_bisect.sh" side HEAD "$S/bis_side" --test true > "$S/bis_side.out" 2>&1
check bisect-good-off-first-parent-line 2 $? "$S/bis_side.out" 'not on the first-parent line'
REPO="$M" bash "$here/engine_bisect.sh" HEAD~1~1 HEAD "$S/bis_line" --test true > "$S/bis_line.out" 2>&1
check bisect-good-on-first-parent-line 1 $? "$S/bis_line.out" 'nothing to find'
H="$S/hw.csv"   # HWiNFO layout: d.m.yyyy, unpadded H:M:S.fff, one unnamed value at the row end, a half-written last row
{ printf 'Date,Time,"GPU Utilization [%%]","GPU Computing (Compute 0) Usage [%%]","Total Errors []",\n'
  for i in $(seq 0 19); do printf '2.11.2026,10:%d:%d.000,%d.0,%d.0,0,7.0,\n' $((i / 6)) $(( (i % 6) * 10 )) $((i * 5)) $((i * 5)); done
  printf '2.11.2026,10:9:59.000,50.0'; } > "$H"
"$PY" -I -B "$here/gpu_util_stats.py" --csv "$H" --from "2026-11-02 10:00" --to "2026-11-02 10:05" > "$S/gpu.out" 2>&1
check gpu-util-window 0 $? "$S/gpu.out" ' 20 rows .the file covers 2026-11-02 10:00:00 -> ' 'GPU Utilization \[%\]: n 20, mean 47\.5, p10 10\.0, p50 50\.0, p90 90\.0' '>= 90 %: 10\.0 % of samples'
"$PY" -I -B "$here/gpu_util_stats.py" --csv "$H" --from "2026-11-02 11:00" --to "2026-11-02 12:00" > "$S/gpu_empty.out" 2>&1
check gpu-util-empty-window 2 $? "$S/gpu_empty.out" 'only 0 rows in the window'
[ $fail = 0 ] && echo "ALL PASS" || echo "SOME FAILED"
exit $fail
