#!/usr/bin/env bash
# test_claim.sh -- the six known tests of claim.sh on a scratch repository (local bare + two clones).
set -u
R=/tmp/claim_test
rm -rf "$R"
mkdir -p "$R"
git init -q --bare "$R/bare.git"
git clone -q "$R/bare.git" "$R/A" 2>/dev/null
git clone -q "$R/bare.git" "$R/B" 2>/dev/null
BR="for-fable-and-opus/deepseek6-work"
for C in A B; do
  cd "$R/$C"
  git checkout -q -b "$BR"
  mkdir -p forge-combo29
  echo "seed" > forge-combo29/seed.txt
  git add -A && git commit -q -m "seed" && git push -q -u origin "$BR" 2>/dev/null
done
cp /tmp/ds6_work/forge-combo29/tests_deepseek6_job10/claim.sh "$R/claim.sh"
sed -i "s#^ROOT=.*#ROOT=\"\$(git rev-parse --show-toplevel)\"#" "$R/claim.sh"
echo "glm-5p3-flash" > /tmp/ds6_model_name
cd "$R/A"
echo "== T1: A claims a free item"
bash "$R/claim.sh" tests_deepseek6_testitem "test claim T1"; echo "T1 rc=$?"
echo "== T2: B claims the same item afterwards"
cd "$R/B"
git fetch -q origin "$BR"
git reset -q --hard "origin/$BR"
bash "$R/claim.sh" tests_deepseek6_testitem "test claim T2"; echo "T2 rc=$?"
echo "T2 check: A's CLAIM.txt unchanged: $(git show origin/$BR:forge-combo29/tests_deepseek6_testitem/CLAIM.txt | head -1)"
echo "== T3: race -- B fetches clean, A pushes while B is inside claim.sh (shim fires at B's push)"
cd "$R/A"
git fetch -q origin "$BR"; git reset -q --hard "origin/$BR"
mkdir -p "$R/shim"
cat > "$R/shim/git" <<'SHIM'
#!/usr/bin/env bash
if [ "$1" = "push" ]; then
  ( cd /tmp/claim_test/A && /usr/bin/git fetch -q origin for-fable-and-opus/deepseek6-work 2>/dev/null
    /usr/bin/git reset -q --hard origin/for-fable-and-opus/deepseek6-work 2>/dev/null
    /usr/bin/git rm -rq --cached forge-combo29/tests_deepseek6_raceitem/CLAIM.txt 2>/dev/null
    rm -f forge-combo29/tests_deepseek6_raceitem/CLAIM.txt
    mkdir -p forge-combo29/tests_deepseek6_raceitem
    printf 'model: glm-5p3-flash\nRACER-A\n' > forge-combo29/tests_deepseek6_raceitem/CLAIM.txt
    /usr/bin/git add forge-combo29/tests_deepseek6_raceitem/CLAIM.txt
    /usr/bin/git commit -q -m "A wins the race item"
    /usr/bin/git push -q origin for-fable-and-opus/deepseek6-work 2>/dev/null )
  exec /usr/bin/git "$@"
fi
exec /usr/bin/git "$@"
SHIM
chmod +x "$R/shim/git"
cd "$R/B"
git fetch -q origin "$BR"; git reset -q --hard "origin/$BR"
git fetch -q origin "$BR"; git reset -q --hard "origin/$BR"
mkdir -p forge-combo29/tests_deepseek6_raceitem
echo "model: glm-5p3-flash" > forge-combo29/tests_deepseek6_raceitem/CLAIM.txt
git add forge-combo29/tests_deepseek6_raceitem/CLAIM.txt
git commit -q -m "B's own claim, committed before fetching"
PATH="$R/shim:$PATH" bash "$R/claim.sh" tests_deepseek6_raceitem "test claim T3"; echo "T3 rc=$?"
echo "T3 check: B HEAD = A's commit? $([ "$(git rev-parse HEAD)" = "$(git rev-parse origin/$BR)" ] && echo yes || echo no); B's claim file: $(cat forge-combo29/tests_deepseek6_raceitem/CLAIM.txt | tr '\n' ' ')"
echo "== T4: B with an uncommitted file"
cd "$R/B"
echo "dirt" > forge-combo29/uncommitted.txt
bash "$R/claim.sh" tests_deepseek6_freeitem "test claim T4"; echo "T4 rc=$?"
rm -f forge-combo29/uncommitted.txt
echo "== T5: a claim 91 minutes old lapses"
cd "$R/A"
git fetch -q origin "$BR"; git reset -q --hard "origin/$BR"
OLD=$(date -u -d '91 minutes ago' +%Y-%m-%dT%H:%M:%SZ)
mkdir -p forge-combo29/tests_deepseek6_olditem
printf 'model: glm-5p3-flash\n%s\n' "$OLD" > forge-combo29/tests_deepseek6_olditem/CLAIM.txt
git add -A
GIT_COMMITTER_DATE="$(date -u -d '91 minutes ago' --rfc-2822)" GIT_AUTHOR_DATE="$(date -u -d '91 minutes ago' --rfc-2822)" git commit -q -m "old claim, 91 minutes ago"
git push -q origin "$BR" 2>/dev/null
bash "$R/claim.sh" tests_deepseek6_olditem "test claim T5"; echo "T5 rc=$?"
echo "== T6: an item with a report"
cd "$R/A"
git fetch -q origin "$BR"; git reset -q --hard "origin/$BR"
mkdir -p forge-combo29/tests_deepseek6_reported
echo x > forge-combo29/tests_deepseek6_reported/CLAIM.txt
echo report > forge-combo29/REPORT_deepseek6_reported.md
git add -A && git commit -q -m "reported item" && git push -q origin "$BR" 2>/dev/null
bash "$R/claim.sh" tests_deepseek6_reported "test claim T6"; echo "T6 rc=$?"
