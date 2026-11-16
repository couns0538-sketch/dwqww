#!/usr/bin/env bash
# claim.sh <item folder name> <subject> -- claim an item without ever overwriting a live claim.
# Steps a-f per file 10. Prints one line per step. Exit 0 = the item is yours.
set -u
ITEM="${1:?item folder name, e.g. tests_deepseek6_long31}"
SUBJECT="${2:?commit subject}"
BRANCH="for-fable-and-opus/deepseek6-work"
ROOT="$(git rev-parse --show-toplevel)"
MODEL="$(cat /tmp/ds6_model_name 2>/dev/null || echo unknown)"

echo "a: checking clean tree and up-to-date HEAD"
if [ -n "$(git status --porcelain)" ]; then
  echo "exit 2: uncommitted changes -- push your work first"; exit 2
fi
git fetch -q origin "$BRANCH" || { echo "exit 2: fetch failed"; exit 2; }
if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/$BRANCH)" ]; then
  echo "exit 2: HEAD differs from origin's branch (ahead or behind) -- push your work first"; exit 2
fi
REPORT="forge-combo29/REPORT_deepseek6_${ITEM#tests_deepseek6_}.md"
if git cat-file -e "origin/$BRANCH:$REPORT" 2>/dev/null; then
  echo "exit 3: already reported ($REPORT exists on the branch)"; exit 3
fi
CLAIM_PATH="forge-combo29/$ITEM/CLAIM.txt"
if git cat-file -e "origin/$BRANCH:$CLAIM_PATH" 2>/dev/null; then
  NEWEST=$(git log -1 --format=%ct "origin/$BRANCH" -- "forge-combo29/$ITEM")
  NOW=$(date -u +%s)
  AGE=$(( (NOW - NEWEST) / 60 ))
  if [ "$AGE" -lt 90 ]; then
    WHO=$(git show "origin/$BRANCH:$CLAIM_PATH" 2>/dev/null | head -1)
    echo "exit 3: live claim of ${WHO} (${AGE} min old)"; exit 3
  fi
  echo "c: the existing claim is ${AGE} min old -- lapsed, claiming over it is not needed: it is free"
fi
echo "d: writing the claim and pushing"
mkdir -p "$ROOT/forge-combo29/$ITEM"
{ echo "model: $MODEL"; date -u +%FT%TZ; } > "$ROOT/$CLAIM_PATH"
git add "$CLAIM_PATH"
git commit -q -m "$SUBJECT" || { echo "exit 2: commit failed"; exit 2; }
if ! git push -q origin "HEAD:$BRANCH" 2>/dev/null; then
  echo "e: push refused -- fetching to see who won"
  git fetch -q origin "$BRANCH"
  if git cat-file -e "origin/$BRANCH:$CLAIM_PATH" 2>/dev/null || git cat-file -e "origin/$BRANCH:$REPORT" 2>/dev/null; then
    git reset -q --hard "origin/$BRANCH"
    echo "exit 4: lost the race: take the next"
    exit 4
  fi
  git rebase -q "origin/$BRANCH" 2>/dev/null || { echo "exit 4: rebase failed"; git rebase --abort 2>/dev/null; exit 4; }
  if ! git push -q origin "HEAD:$BRANCH" 2>/dev/null; then
    echo "exit 4: second push refused"
    exit 4
  fi
fi
echo "f: verifying the claim on the branch"
git fetch -q origin "$BRANCH"
GOT=$(git show "origin/$BRANCH:$CLAIM_PATH" 2>/dev/null | head -1)
if [ "$GOT" != "model: $MODEL" ]; then
  git reset -q --hard "origin/$BRANCH"
  echo "exit 4: the branch's CLAIM.txt is not mine"
  exit 4
fi
echo "exit 0: $ITEM is mine ($MODEL)"
exit 0
