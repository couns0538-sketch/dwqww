#!/usr/bin/env bash
# commit_push.sh - checked commit + push for the speed job branch (own code).
# usage: bash opus_speed/tools/commit_push.sh <message file>
# Gates (each must pass, exit codes are checked, nothing is piped through tail):
#   1. name_lint on code files (.ps1 / .py / .sh are kept out of the git clean filter, so they must be clean as written;
#      .md / .txt / .tsv pass through the 'novendor' clean filter on commit);
#   2. ctrl_char_check on everything (no BEL / BS / FF bytes from collapsed backslashes);
#   3. PowerShell 5.1 parse check of every .ps1 (opus_speed, and the branch's pack folder).
# Then: stage the branch's folders, unstage bytecode caches, commit as couns0538-sketch (no trailer), push.
# Branch-aware since 2026-11-06 (SingularNonCut job): the checked-out branch picks the staged folders and the literal
# push line; any other branch exits 2 before anything is staged.
#   opus-speed-20261105           -> opus_speed skills (unchanged)
#   opus-singular-noncut-20261105 -> opus_singular_noncut opus_speed skills
#   2026-11-06 leftover ports (each cut from 277a8f90, one pack folder each):
#   opus-cut-nott-lmr-20261105    -> opus_cut_nott_lmr opus_speed skills
#   opus-tt-cut-node-20261105     -> opus_tt_cut_node opus_speed skills
#   opus-nmp-tt-capture-20261105  -> opus_nmp_tt_capture opus_speed skills
#   2026-11-06 5-hour brief (each cut from the opus-speed tip after the runner audit, one pack folder each):
#   opus-nnue-int8-vnni-20261106  -> opus_nnue_int8_vnni opus_speed skills
#   opus-tt-replace-cache-20261106 -> opus_tt_replace_cache opus_speed skills
# A new pack folder must also be in the sparse patterns (MSYS_NO_PATHCONV=1 git sparse-checkout add /<pack>/), or
# `git add` skips it and the script stops (fail closed).
set -u
MSG="$1"
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
cd /f/ospd/wt || exit 2
[ -f "$MSG" ] || { echo "commit_push: no message file $MSG"; exit 2; }
BR=$(git rev-parse --abbrev-ref HEAD)
case "$BR" in
  opus-speed-20261105) PACK="" ;;
  opus-singular-noncut-20261105) PACK=opus_singular_noncut ;;
  opus-cut-nott-lmr-20261105) PACK=opus_cut_nott_lmr ;;
  opus-tt-cut-node-20261105) PACK=opus_tt_cut_node ;;
  opus-nmp-tt-capture-20261105) PACK=opus_nmp_tt_capture ;;
  opus-nnue-int8-vnni-20261106) PACK=opus_nnue_int8_vnni ;;
  opus-tt-replace-cache-20261106) PACK=opus_tt_replace_cache ;;
  *) echo "commit_push: branch '$BR' is not a branch of this script - nothing committed"; exit 2 ;;
esac
DIRS="$PACK opus_speed skills"
for d in $DIRS; do [ -d "$d" ] || { echo "commit_push: folder $d missing on $BR - nothing committed"; exit 2; }; done
# modified, untracked AND already staged code files (review LOW 10)
CODE=$( { git ls-files -mo --exclude-standard $DIRS; git diff --cached --name-only -- $DIRS; } | sort -u | grep -E '\.(ps1|py|sh)$' || true)
if [ -n "$CODE" ]; then
  $PY -I -B opus_speed/tools/name_lint.py $CODE > /f/ospd/tmp/lint_code.txt; rc=$?
  if [ $rc -ne 0 ]; then cat /f/ospd/tmp/lint_code.txt; echo "commit_push: vendor names in code files - not committed"; exit 1; fi
fi
$PY -I -B opus_speed/tools/ctrl_char_check.py $DIRS > /f/ospd/tmp/ctrl.txt; rc=$?
if [ $rc -ne 0 ]; then cat /f/ospd/tmp/ctrl.txt; echo "commit_push: control bytes - not committed"; exit 1; fi
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\ps_parse_check.ps1' -Dir 'F:\ospd\wt\opus_speed' > /f/ospd/tmp/parse.txt; rc=$?
if [ $rc -ne 0 ]; then grep -v ': ok$' /f/ospd/tmp/parse.txt; echo "commit_push: PowerShell parse errors - not committed"; exit 1; fi
if [ -n "$PACK" ]; then
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\ps_parse_check.ps1' -Dir "F:\\ospd\\wt\\$PACK" > /f/ospd/tmp/parse_pack.txt; rc=$?
  if [ $rc -ne 0 ]; then grep -v ': ok$' /f/ospd/tmp/parse_pack.txt; echo "commit_push: PowerShell parse errors - not committed"; exit 1; fi
fi
# fail closed (2026-11-06): in a sparse checkout `git add` skips folders outside the sparse patterns with exit 1 and the
# old script committed and pushed the rest anyway (948e0334 lost the new pack files)
git add -A $DIRS || { echo "commit_push: git add failed (sparse-checkout patterns: git sparse-checkout list) - not committed"; exit 1; }
LEFT=$(git ls-files -mo --exclude-standard $DIRS | grep -v '__pycache__' || true)
[ -z "$LEFT" ] || { echo "commit_push: not staged after git add - not committed:"; echo "$LEFT"; exit 1; }
git restore --staged opus_speed/jobc/tools/__pycache__ 2>/dev/null || true
if git diff --cached --quiet; then echo "commit_push: nothing to commit"; exit 0; fi
git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit -q -F "$MSG" || exit 1
case "$BR" in
  opus-speed-20261105) git push -q -u origin opus-speed-20261105 || exit 1 ;;
  opus-singular-noncut-20261105) git push -q -u origin opus-singular-noncut-20261105 || exit 1 ;;
  opus-cut-nott-lmr-20261105) git push -q -u origin opus-cut-nott-lmr-20261105 || exit 1 ;;
  opus-tt-cut-node-20261105) git push -q -u origin opus-tt-cut-node-20261105 || exit 1 ;;
  opus-nmp-tt-capture-20261105) git push -q -u origin opus-nmp-tt-capture-20261105 || exit 1 ;;
  opus-nnue-int8-vnni-20261106) git push -q -u origin opus-nnue-int8-vnni-20261106 || exit 1 ;;
  opus-tt-replace-cache-20261106) git push -q -u origin opus-tt-replace-cache-20261106 || exit 1 ;;
esac
echo "commit_push: $(git log --oneline -1)"
