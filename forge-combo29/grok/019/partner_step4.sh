#!/usr/bin/env bash
# Re-check a same-idea partner on a fresh base. Our harness, not theirs.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
DIR="forge-combo29/grok/$S"
BASE=6b98f2170a3210e71beed04bbd2553972c253ed7
python3 "$DIR/partner_pick.py" | tee "$DIR/partner_pick.txt"
PARTNER=$(awk '/^partner /{print $2}' "$DIR/partner_pick.txt")
echo "$PARTNER" > "$DIR/partner_id.txt"
if [ "$PARTNER" = "none" ]; then
  echo "NO_PARTNER" | tee "$DIR/partner_status.txt"
  exit 0
fi
found=0
for try in $(seq 1 11); do
  git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER"
  if git cat-file -e "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" 2>/dev/null; then
    found=1
    break
  fi
  echo "try $try no idea.patch.txt $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [ "$try" -eq 11 ]; then
    break
  fi
  sleep 60
done
if [ "$found" -ne 1 ]; then
  echo "NO_PATCH" | tee "$DIR/partner_status.txt"
  exit 0
fi
echo "HAS_PATCH $(git rev-parse FETCH_HEAD)" | tee "$DIR/partner_status.txt"
git archive --remote= 2>/dev/null || true
mkdir -p "$DIR/partner_src"
git archive FETCH_HEAD "forge-combo29/grok/$PARTNER" | tar -x -C "$DIR/partner_src" --strip-components=3
echo "extracted $(find "$DIR/partner_src" -type f | wc -l) files"
