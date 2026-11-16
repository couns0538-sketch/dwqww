#!/usr/bin/env bash
# fetch_glm.sh — dump glmflash5's job27 raw files into ./gl/ (text only). Nothing is written to their branch.
set -u
BR=cursor/glmflash5-work-cb5c
D="$(cd "$(dirname "$0")" && pwd)/gl"
mkdir -p "$D"
date -u +"fetch start %Y-%m-%dT%H:%M:%SZ" > "$D/stamps.txt"
git fetch -q --depth 1 origin "$BR" || { echo "FAIL fetch"; exit 2; }
CB=$(git rev-parse FETCH_HEAD)
echo "branch $BR commit $CB" >> "$D/stamps.txt"
git ls-tree -r --name-only "$CB" forge-combo29/tests_glmflash5_job27/ | sed 's#.*job27/##' > "$D/ls_job27.txt"
while read -r f; do
  [ -z "$f" ] && continue
  git show "$CB:forge-combo29/tests_glmflash5_job27/$f" > "$D/$f" 2>/dev/null
done < "$D/ls_job27.txt"
git show "$CB:forge-combo29/REPORT_glmflash5_job27.md" > "$D/REPORT_job27.md" 2>/dev/null
# every gamelist of the session, for the "are the openings disjoint" question
true > "$D/all_gamelists.txt"
echo "gamelists on the branch: $(wc -l < "$D/all_gamelists.txt")"
for p in $(cat "$D/all_gamelists.txt"); do
  n=$(echo "$p" | sed 's#.*/gamelist_##;s#\.txt##')
  d=$(echo "$p" | sed 's#forge-combo29/##;s#/gamelist_.*##')
  git show "$CB:$p" > "$D/gamelists_${n}.txt" 2>/dev/null
  echo "$n $d $(wc -l < "$D/gamelists_${n}.txt")" >> "$D/gamelist_index.txt"
done
date -u +"fetch done %Y-%m-%dT%H:%M:%SZ" >> "$D/stamps.txt"
ls "$D" | head -20; echo "..."; wc -l < "$D/gamelist_index.txt"
