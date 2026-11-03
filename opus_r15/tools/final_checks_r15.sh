#!/usr/bin/env bash
# final_checks_r15.sh OUT_DIR - R15 end-of-round checks in one command (the automated half of the bug check).
#   1 every candidate patch on a FRESH lock copy: patch -p1 -F0, plain build, pin_check OFF (-Full, = lock pins) and
#     ON with -Expect = the ON nodes recorded by cand_pack (d11-d22 exact: the patch file reproduces the gate exe's
#     ON tree, since the kit proved plain = LTO+PGO for the ON line)
#   2 index_check.py (exe sha256 / md5, record checks, CI tied to the built patch, advertised option + range)
#   3 every tool self-test (pin_check, smoke2m, cleanroom_lint, index_check, gate_summary, cand_pack, ci_record, MCP)
#   4 cleanroom_lint over all patches and every commit message of the branch; doc_lint over opus_r15 + the skills
#   5 the worktree is clean and equal to its remote branch
# Own work on CPUs 0-1 at Idle (the tools pin themselves). OUT_DIR must not exist. Exit 0 = every step passed.
set -u
out=${1:?out dir}; [ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }; mkdir -p "$out"
W=/d/o15/wt; T=$W/opus_r15/tools
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
PC="$(cygpath -w "$T/pin_check.ps1")"
fails=0
step() { echo "=== $1 $(date '+%T')"; }
res() { if [ "$2" = 0 ]; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
step "1 patches on fresh lock copies"
for rj in /d/o15/cands/c*/RESULT.json; do
  d=$(dirname "$rj"); name=$(basename "$d")
  patch="$W/opus_r15/cands/$name/$name.patch"
  [ -f "$patch" ] || { res "$name: patch file in the branch" 1; continue; }
  opt=$("$PY" -I -B -c "import json,sys; r=json.load(open(sys.argv[1],encoding='utf-8-sig')); print(r['option']+'='+r['on'])" "$(cygpath -w "$rj")")
  expect=$("$PY" -I -B -c "import json,sys; b=json.load(open(sys.argv[1],encoding='utf-8-sig'))['pin_on']; print(','.join(f'{k}={b[k]}' for k in ('d11','d13','d16','d20','d22')))" "$(cygpath -w "$rj")")
  src="$out/src_$name"
  bash "$T/fresh_lock.sh" "$src" > /dev/null && (cd "$src" && patch -p1 -F0 --dry-run < "$patch" > /dev/null && patch -p1 -F0 -s < "$patch" && git add -A && git -c user.name=o15 -c user.email=o15@local commit -q -m fc)
  rc=$?; res "$name: patch applies to a fresh d4f4312 copy" $rc
  [ $rc = 0 ] || continue
  bash "$T/plain_build_r15.sh" "$src" "$out/plain_$name" > "$out/build_$name.log" 2>&1; rc=$?; res "$name: plain build ($(grep -c 'warning:' "$out/plain_$name/build.log" 2>/dev/null) warnings)" $rc
  [ $rc = 0 ] || continue
  exe="$(cygpath -w "$out/plain_$name/forge_plain.exe")"
  powershell -NoProfile -ExecutionPolicy Bypass -File "$PC" -Exe "$exe" -Full > "$out/pin_off_$name.txt" 2>&1; res "$name: OFF = lock pins d11-d22 + perft" $?
  powershell -NoProfile -ExecutionPolicy Bypass -File "$PC" -Exe "$exe" -Options "$opt" -Expect "$expect" > "$out/pin_on_$name.txt" 2>&1; res "$name: ON $opt = recorded nodes $expect" $?
done
step "2 index_check"
"$PY" -I -B "$T/index_check.py" > "$out/index_check.txt" 2>&1; rc=$?; tail -1 "$out/index_check.txt"; res "index_check" $rc
step "3 tool self-tests"
bash "$T/test_pin_check.sh" "$out/t_pin" > "$out/t_pin.log" 2>&1; res "test_pin_check ($(tail -2 "$out/t_pin.log" | head -1))" $?
bash "$T/test_smoke2m.sh" "$out/t_smoke" > "$out/t_smoke.log" 2>&1; res "test_smoke2m ($(tail -2 "$out/t_smoke.log" | head -1))" $?
"$PY" -I -B "$T/test_cleanroom_lint.py" "$(cygpath -w "$out/t_clean")" > "$out/t_clean.log" 2>&1; res "test_cleanroom_lint ($(tail -2 "$out/t_clean.log" | head -1))" $?
"$PY" -I -B "$T/test_index_check.py" "$(cygpath -w "$out/t_index")" > "$out/t_index.log" 2>&1; res "test_index_check ($(tail -2 "$out/t_index.log" | head -1))" $?
bash "$T/test_gate_summary.sh" "$out/t_gate" > "$out/t_gate.log" 2>&1; res "test_gate_summary ($(tail -2 "$out/t_gate.log" | head -1))" $?
bash "$T/test_cand_pack.sh" "$out/t_pack" > "$out/t_pack.log" 2>&1; res "test_cand_pack ($(tail -2 "$out/t_pack.log" | head -1))" $?
"$PY" -I -B "$T/test_ci_record.py" "$(cygpath -w "$out/t_ci")" > "$out/t_ci.log" 2>&1; res "test_ci_record ($(tail -2 "$out/t_ci.log" | head -1))" $?
"$PY" -I -B "$W/opus_r15/mcp/test_forge_uci_mcp.py" > "$out/t_mcp.log" 2>&1; res "test_forge_uci_mcp ($(tail -2 "$out/t_mcp.log" | head -1))" $?
step "4 clean-room + documents"
pl=$(ls "$W"/opus_r15/cands/*/*.patch | sed 's/^/--patch /' | tr '\n' ' ')
"$PY" -I -B "$T/cleanroom_lint.py" $pl > "$out/cleanroom_patches.txt" 2>&1; res "cleanroom_lint patches ($(tail -1 "$out/cleanroom_patches.txt"))" $?
"$PY" -I -B "$T/cleanroom_lint.py" --commits origin/main..HEAD --git-dir "$W" > "$out/cleanroom_commits.txt" 2>&1; res "cleanroom_lint commit messages ($(tail -1 "$out/cleanroom_commits.txt"))" $?
"$PY" -I -B "$T/doc_lint.py" "$W/opus_r15" "$W/.github" /c/Users/Administrator/.claude/skills/forge-r15-candidates /c/Users/Administrator/.claude/skills/forge-gate-summary > "$out/doc_lint.txt" 2>&1; res "doc_lint ($(tail -1 "$out/doc_lint.txt"))" $?
step "5 worktree clean and in sync"
git -C "$W" fetch -q origin opus-r15-20261103 2>/dev/null
dirty=$(git -C "$W" status --porcelain); local_h=$(git -C "$W" rev-parse HEAD); remote_h=$(git -C "$W" rev-parse origin/opus-r15-20261103)
[ -z "$dirty" ] && [ "$local_h" = "$remote_h" ]; res "worktree clean, HEAD $local_h = origin" $?
echo "final_checks_r15: $fails failure(s) $(date '+%F %T')"
exit $fails
