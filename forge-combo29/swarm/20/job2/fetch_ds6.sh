#!/usr/bin/env bash
# fetch_ds6.sh — dump deepseek6's long56 raw files to ./ds6/ as text, so the recount reads the branch's
# own bytes. Mangling: '/' -> '__'. Nothing here writes to any branch.
set -u
BR=for-fable-and-opus/deepseek6-work
D="$(cd "$(dirname "$0")" && pwd)/ds6"
mkdir -p "$D"
date -u +"fetch start %Y-%m-%dT%H:%M:%SZ" > "$D/stamps.txt"
git fetch -q --depth 1 origin "$BR" || { echo "FAIL fetch"; exit 2; }
CB=$(git rev-parse FETCH_HEAD)
echo "branch $BR commit $CB" >> "$D/stamps.txt"
git ls-tree -r --name-only "$CB" forge-combo29/tests_deepseek6_long56/ > "$D/ls_long56.txt"
git ls-tree -r --name-only "$CB" forge-combo29/ | grep -i 'longk' > "$D/ls_longK.txt"
sed -i 's#^forge-combo29/tests_deepseek6_long56/##' "$D/ls_long56.txt"
while read -r f; do
  [ -z "$f" ] && continue
  m=$(echo "$f" | tr '/' '_')          # one level of slash is enough here
  git show "$CB:forge-combo29/tests_deepseek6_long56/$f" > "$D/$m" 2>/dev/null
done < "$D/ls_long56.txt"
git show "$CB:forge-combo29/REPORT_deepseek6_long56.md" > "$D/report_long56.md" 2>/dev/null
date -u +"fetch done %Y-%m-%dT%H:%M:%SZ" >> "$D/stamps.txt"
ls -la "$D"
cat "$D/stamps.txt"
