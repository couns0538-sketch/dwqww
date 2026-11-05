#!/usr/bin/env bash
# commit_push.sh - checked commit + push for the speed job branch (own code).
# usage: bash opus_speed/tools/commit_push.sh <message file>
# Gates (each must pass, exit codes are checked, nothing is piped through tail):
#   1. name_lint on code files (.ps1 / .py / .sh are kept out of the git clean filter, so they must be clean as written;
#      .md / .txt / .tsv pass through the 'novendor' clean filter on commit);
#   2. ctrl_char_check on everything (no BEL / BS / FF bytes from collapsed backslashes);
#   3. PowerShell 5.1 parse check of every .ps1.
# Then: stage opus_speed/ and skills/, unstage bytecode caches, commit as couns0538-sketch (no trailer), push.
set -u
MSG="$1"
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
cd /f/ospd/wt || exit 2
[ -f "$MSG" ] || { echo "commit_push: no message file $MSG"; exit 2; }
# modified, untracked AND already staged code files (review LOW 10)
CODE=$( { git ls-files -mo --exclude-standard opus_speed skills; git diff --cached --name-only -- opus_speed skills; } | sort -u | grep -E '\.(ps1|py|sh)$' || true)
if [ -n "$CODE" ]; then
  $PY -I -B opus_speed/tools/name_lint.py $CODE > /f/ospd/tmp/lint_code.txt; rc=$?
  if [ $rc -ne 0 ]; then cat /f/ospd/tmp/lint_code.txt; echo "commit_push: vendor names in code files - not committed"; exit 1; fi
fi
$PY -I -B opus_speed/tools/ctrl_char_check.py opus_speed skills > /f/ospd/tmp/ctrl.txt; rc=$?
if [ $rc -ne 0 ]; then cat /f/ospd/tmp/ctrl.txt; echo "commit_push: control bytes - not committed"; exit 1; fi
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\ps_parse_check.ps1' -Dir 'F:\ospd\wt\opus_speed' > /f/ospd/tmp/parse.txt; rc=$?
if [ $rc -ne 0 ]; then grep -v ': ok$' /f/ospd/tmp/parse.txt; echo "commit_push: PowerShell parse errors - not committed"; exit 1; fi
git add -A opus_speed skills
git restore --staged opus_speed/jobc/tools/__pycache__ 2>/dev/null || true
if git diff --cached --quiet; then echo "commit_push: nothing to commit"; exit 0; fi
git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit -q -F "$MSG" || exit 1
git push -q -u origin opus-speed-20261105 || exit 1
echo "commit_push: $(git log --oneline -1)"
