#!/usr/bin/env bash
# test_cand_pack.sh OUT_DIR - fast self-test of cand_pack.ps1's refusals and early stops (no kit build is started):
# bad tag / name, missing patch, -NoPatch with a patch, an option line with ';', an existing RESULT.json, an existing
# source tag (exit 2); a patch with a planted name term (cleanroom_lint FAIL, exit 1); a patch that does not apply
# (exit 3). Everything goes to OUT_DIR (its own -Root and -BranchDir), never to D:\o15\cands. Exit 0 = all as expected.
set -u
out=${1:?out dir}; [ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }; mkdir -p "$out/root/cands" "$out/branch"
D="$(cd "$(dirname "$0")" && pwd)"
CP="$(cygpath -w "$D/cand_pack.ps1")"
R="$(cygpath -w "$out/root")"; B="$(cygpath -w "$out/branch")"
GOOD="$(cygpath -w "$D/../cands/c1_prunelmrhist/c1_prunelmrhist.patch")"
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
name0=$("$PY" -I -B -c "import sys; sys.path.insert(0, r'$(cygpath -w "$D")'); import cleanroom_lint as c; print(c.terms(c.NAMES_B64)[0])")
sed "s|+int PruneLmrHist = 0;|+int PruneLmrHist = 0; // after $name0|" "$D/../cands/c1_prunelmrhist/c1_prunelmrhist.patch" > "$out/named.patch"
sed 's|int FailLowContinuationBonus = 0;|int FailLowContinuationBonusX = 0;|' "$D/../cands/c1_prunelmrhist/c1_prunelmrhist.patch" > "$out/broken.patch"
mkdir -p "$out/root/cands/c9_exists"; echo '{}' > "$out/root/cands/c9_exists/RESULT.json"
mkdir -p "$out/root/src_pack/t9used"
fails=0; n=0
case_() { name=$1; want=$2; shift 2; n=$((n + 1))
  powershell -NoProfile -ExecutionPolicy Bypass -File "$CP" "$@" -Root "$R" -BranchDir "$B" > "$out/$name.txt" 2>&1; rc=$?
  if [ "$rc" = "$want" ]; then echo "PASS $name (exit $rc): $(tail -1 "$out/$name.txt")"; else echo "FAIL $name: exit $rc, want $want: $(tail -3 "$out/$name.txt" | tr '\n' ' ')"; fails=$((fails + 1)); fi; }
case_ bad_tag 2 -Name c9_a -Tag 'BAD-TAG' -Patch "$GOOD" -Option PruneLmrHist -On 1
case_ bad_name 2 -Name 'C9 A' -Tag t9a -Patch "$GOOD" -Option PruneLmrHist -On 1
case_ missing_patch 2 -Name c9_b -Tag t9b -Patch 'D:\o15\no_such.patch' -Option PruneLmrHist -On 1
case_ nopatch_with_patch 2 -Name c9_c -Tag t9c -NoPatch -Patch "$GOOD"
case_ two_options 2 -Name c9_d -Tag t9d -Patch "$GOOD" -Option 'PruneLmrHist=1;QsMovePrune' -On 3
case_ result_exists 2 -Name c9_exists -Tag t9e -Patch "$GOOD" -Option PruneLmrHist -On 1
case_ tag_used 2 -Name c9_f -Tag t9used -Patch "$GOOD" -Option PruneLmrHist -On 1
case_ lint_fails 1 -Name c9_g -Tag t9g -Patch "$(cygpath -w "$out/named.patch")" -Option PruneLmrHist -On 1
grep -q '"cleanroom_lint"' "$out/root/cands/c9_g/RESULT.json" 2>/dev/null || { echo "FAIL lint_fails: no RESULT.json with the lint check"; fails=$((fails + 1)); }
case_ patch_not_applying 3 -Name c9_h -Tag t9h -Patch "$(cygpath -w "$out/broken.patch")" -Option PruneLmrHist -On 1
[ -e /d/o15/w/t9g_pc1 ] || [ -e /d/o15/w/t9h_pc1 ] && { echo "FAIL: a kit build was started"; fails=$((fails + 1)); }
echo "$((n - fails)) / $n cases as expected"
[ $fails = 0 ] && echo "ALL PASS" || echo "FAILURES: $fails"
exit $fails
