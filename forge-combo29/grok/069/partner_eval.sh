#!/usr/bin/env bash
# STEP 4. Find the next seat with this idea, build that patch, prove it.
# Usage: partner_eval.sh
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
LOG="$D/partner_eval.log"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
exec > >(tee -a "$LOG") 2>&1
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Idea 19 seats, in number order. Partner is the next one after us that has a branch.
order=(019 069 119)
next=()
seen=0
for n in "${order[@]}"; do
  if [ "$seen" -eq 1 ]; then next+=("$n"); fi
  if [ "$n" = "$S" ]; then seen=1; fi
done
for n in "${order[@]}"; do
  if [ "$n" = "$S" ]; then break; fi
  next+=("$n")
done
echo "candidate_order ${next[*]}"

partner=""
for n in "${next[@]}"; do
  if git ls-remote --heads origin "for-fable-and-opus/grok-$n" | grep -q "grok-$n"; then
    partner=$n
    break
  fi
done
echo "partner=${partner:-none}"
if [ -z "$partner" ]; then
  echo "NO_PARTNER"
  exit 0
fi
echo "$partner" > "$D/partner_seat.txt"

have_patch() {
  git cat-file -e "FETCH_HEAD:forge-combo29/grok/$partner/idea.patch.txt" 2>/dev/null
}

git fetch -q --depth 1 origin "for-fable-and-opus/grok-$partner" || { echo "FAIL fetch"; exit 2; }
echo "fetched $(git rev-parse FETCH_HEAD) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
deadline=$((SECONDS + 600))
while ! have_patch; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "NO_PATCH_AFTER_WAIT"
    exit 0
  fi
  echo "waiting for idea.patch.txt $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  sleep 60
  git fetch -q --depth 1 origin "for-fable-and-opus/grok-$partner" || true
done
git show "FETCH_HEAD:forge-combo29/grok/$partner/idea.patch.txt" > "$D/partner.patch.txt"
echo "patch_bytes $(wc -c < "$D/partner.patch.txt")"
# Their own O depth-12 rows, if they committed any TSV whose name suggests it.
git ls-tree -r --name-only FETCH_HEAD "forge-combo29/grok/$partner" > "$D/partner_files.txt"
echo "their files:"
cat "$D/partner_files.txt"
