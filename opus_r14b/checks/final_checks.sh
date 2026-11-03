#!/usr/bin/env bash
# final_checks.sh OUT_DIR - Opus R14-B end-of-job checks in one command (STATUS.md "Plan for the rest of the window"),
# one step after the other; CPU work on CPUs 2-3 (the tools pin themselves). OUT_DIR must not exist. Steps:
#   1 doc_lint over every R14-B document tree (the three worktrees' opus_r14b + skills, .claude/skills)
#   2 make_index_r14b.sh (FILES.txt + SHA256SUMS of both item folders, sha256sum -c); the index must already be
#     committed: a FILES.txt / SHA256SUMS that changes here means a document was edited without re-indexing
#   3 fresh clones of the two item branches with this PC's default git settings: sha256sum -c SHA256SUMS in each
#   4 hash_sweep_r14b.sh: every cited hash matches a file, a commit or the allow list
#   5 tools/test_tools.sh (abba.py, doc_lint.py)
#   6 item 1 from its clone: tools/test_installer.sh, tools/test_scope.py
#   7 item 2 from its clone: relabel2.py sha256 = the frozen value in RELABEL_HANDOFF.md; checks/e2e_r8v5.sh
#   8 every worktree clean and in sync with its remote branch
# Exit 0 = every step passed. About 3 minutes.
set -u
out=${1:?out dir}
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out"
W=/d/grok-pc-data/dwqww/.claude/worktrees
C=$W/o14b-status/opus_r14b/checks
T=$W/o14b-status/opus_r14b/tools
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
fails=0
step() { echo "=== $1 $(date '+%T')"; }
res() { if [ "$2" = 0 ]; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
step "1 doc_lint"
bash "$T/opus.sh" lint > "$out/lint.log" 2>&1
rc=$?; tail -1 "$out/lint.log"; res "doc_lint (0 findings)" $rc
step "2 file index of both item folders"
bash "$C/make_index_r14b.sh" > "$out/index.log" 2>&1
rc=$?; grep "verify OK" "$out/index.log"
dirty=$(for w in o14b-l1 o14b-r2; do git -C "$W/$w" status --porcelain; done)
[ -z "$dirty" ] || { echo "index changed (commit it): $dirty"; rc=1; }
res "make_index: verify OK and nothing to commit" $rc
step "3 fresh clones: sha256sum -c"
for b in fast-loader relabel; do
  git clone -q --shared --no-checkout /d/grok-pc-data/dwqww "$out/clone_$b" && git -C "$out/clone_$b" checkout -q "origin/opus-r14b-$b" \
    || { res "clone $b" 1; continue; }
  item=$([ $b = fast-loader ] && echo item1 || echo item2)
  (cd "$out/clone_$b/opus_r14b/$item" && sha256sum -c --quiet SHA256SUMS) > "$out/sums_$b.log" 2>&1
  rc=$?; echo "clone $b at $(git -C "$out/clone_$b" rev-parse --short HEAD): $(wc -l < "$out/clone_$b/opus_r14b/$item/SHA256SUMS") files"
  res "$b: SHA256SUMS of a fresh clone" $rc
done
step "4 hash sweep"
bash "$C/hash_sweep_r14b.sh" "$out/hash_sweep.txt" > /dev/null 2>&1
rc=$?; grep "^tokens" "$out/hash_sweep.txt"; res "hash sweep (0 unmatched)" $rc
step "5 tools"
bash "$T/test_tools.sh" "$out/test_tools" > "$out/test_tools.log" 2>&1
rc=$?; echo "$(grep -c '^PASS' "$out/test_tools.log") PASS, $(grep -c '^FAIL' "$out/test_tools.log") FAIL"; res "test_tools.sh" $rc
step "6 item 1 from the clone"
L1=$out/clone_fast-loader/opus_r14b/item1
bash "$L1/tools/test_installer.sh" "$out/test_installer" > "$out/test_installer.log" 2>&1
rc=$?; tail -1 "$out/test_installer.log"; res "test_installer.sh" $rc
"$PY" -I -B "$L1/tools/test_scope.py" > "$out/test_scope.log" 2>&1
rc=$?; tail -1 "$out/test_scope.log"; res "test_scope.py" $rc
step "7 item 2 from the clone"
R2=$out/clone_relabel/opus_r14b/item2
frozen=$(grep -A1 "frozen at sha256" "$R2/RELABEL_HANDOFF.md" | grep -oE "[0-9a-f]{64}" | head -1)
now=$(sha256sum < "$R2/relabel2.py" | cut -d' ' -f1)
echo "relabel2.py $now, RELABEL_HANDOFF.md says $frozen"
res "relabel2.py = the frozen sha256" $([ -n "$frozen" ] && [ "$frozen" = "$now" ] && echo 0 || echo 1)
bash "$C/e2e_r8v5.sh" "$out/e2e" > "$out/e2e.log" 2>&1
rc=$?; tail -1 "$out/e2e.log"; res "e2e_r8v5.sh (worktree code = the frozen file above)" $rc
step "8 worktrees in sync"
for w in o14b-status o14b-l1 o14b-r2 o13-p6; do
  s=$(git -C "$W/$w" status -sb | head -1); d=$(git -C "$W/$w" status --porcelain | wc -l)
  echo "$w: $s; uncommitted $d"
  res "$w clean and in sync" $([ "$d" = 0 ] && [[ "$s" != *ahead* ]] && [[ "$s" != *behind* ]] && echo 0 || echo 1)
done
echo "=== failures: $fails $(date '+%F %T')"
exit $((fails > 0))
