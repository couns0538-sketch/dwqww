#!/usr/bin/env bash
# p6crfix_failclosed.sh - R14-B: the three fail-closed paths CR's P6 crfix adds, each shown before (R13 code from git /
# R13's tb_probe build) and after (patched worktree files / the rebuilt tb_probe). Offline: the fetch-script cases use
# local copies of the 3-4 piece tables from D:\syzygy345 with a local checksum.md5, so nothing is downloaded.
set -uo pipefail
B=/c/o14b/p6crfix
F=$B/failclosed2
[ -e "$F" ] && { echo "refusing existing $F"; exit 2; }
mkdir -p "$F"
W=/d/grok-pc-data/dwqww/.claude/worktrees
P6=$W/o13-p6/opus_r13/p6
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
fails=0
export SYZYGY_MIRROR=http://127.0.0.1:9/no-network  # a test must never download: any fetch fails locally
expect() {  # expect NAME WANT_EXIT GOT_EXIT TEXT_FILE REGEX
  if [ "$3" = "$2" ] && grep -qE -- "$5" "$4"; then echo "PASS $1 (exit $3)"; else echo "FAIL $1: exit $3 (want $2), $(head -c 200 "$4" | tr '\n' ' ')"; fails=$((fails + 1)); fi
}
git -C "$W/o13-p6" show HEAD:opus_r13/p6/check_tb.py > "$F/check_tb_r13.py"
git -C "$W/o13-p6" show HEAD:opus_r13/p6/ci_fetch_tables.sh > "$F/ci_fetch_tables_r13.sh"
: > "$F/empty.fens"; : > "$F/empty.oracle"; : > "$F/empty.engine"
# tb_probe: missing and empty FEN files
"$B/tb_probe.exe" D:/syzygy345 "$F/no_such.fens" > "$F/a.out" 2>&1; expect tb_probe_missing_fens_new 2 $? "$F/a.out" "cannot open"
"$B/tb_probe.exe" D:/syzygy345 "$F/empty.fens" > "$F/b.out" 2>&1; expect tb_probe_empty_fens_new 2 $? "$F/b.out" "no FENs"
/c/o13/p6/tb_probe.exe D:/syzygy345 "$F/empty.fens" > "$F/c.out" 2>&1; expect tb_probe_empty_fens_r13_gap 0 $? "$F/c.out" "loaded 145 WDL"
# check_tb compare: empty oracle and engine output
"$PY" -I -B "$P6/check_tb.py" compare "$F/empty" "$F/empty.engine" > "$F/d.out" 2>&1; expect compare_empty_new 1 $? "$F/d.out" "both must be equal and non-zero"
"$PY" -I -B "$F/check_tb_r13.py" compare "$F/empty" "$F/empty.engine" > "$F/e.out" 2>&1; expect compare_empty_r13_gap 0 $? "$F/e.out" "."
# ci_fetch_tables.sh: 70 tables present -> pass; 69 -> the patched script fails, the R13 one passes
mkdir -p "$F/fetch70" "$F/fetch69" "$F/fetch69_r13"
names=$(cd /d/syzygy345 && ls | awk 'length($0) <= 10 && /rtb[wz]$/')
echo "3-4 piece table files in D:\\syzygy345: $(echo "$names" | wc -l)"
for n in $names; do cp /d/syzygy345/$n "$F/fetch70/"; done
(cd "$F/fetch70" && md5sum $names | sed 's/ [*]/  /' > checksum.md5)  # the mirror format: "md5  name" (no '*')
skip=$(echo "$names" | head -1)
for n in $names; do [ "$n" = "$skip" ] || { cp /d/syzygy345/$n "$F/fetch69/"; cp /d/syzygy345/$n "$F/fetch69_r13/"; }; done
grep -v " \*\?$skip\$" "$F/fetch70/checksum.md5" > "$F/fetch69/checksum.md5"; cp "$F/fetch69/checksum.md5" "$F/fetch69_r13/"
bash "$P6/ci_fetch_tables.sh" "$F/fetch70" > "$F/f.out" 2>&1; expect fetch_70_new 0 $? "$F/f.out" "tables: 70 present, 0 downloaded"
bash "$P6/ci_fetch_tables.sh" "$F/fetch69" > "$F/g.out" 2>&1; expect fetch_69_new 1 $? "$F/g.out" "FAIL: expected 70 3-4 piece table files, found 69"
bash "$F/ci_fetch_tables_r13.sh" "$F/fetch69_r13" > "$F/h.out" 2>&1; expect fetch_69_r13_gap 0 $? "$F/h.out" "tables: 69 present, 0 downloaded"
echo "fail-closed checks: failures $fails"
exit $((fails > 0))
