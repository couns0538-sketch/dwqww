#!/usr/bin/env bash
# One fetch of the partner seat. Prints HAS_PATCH, NO_PATCH, or NO_PARTNER.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
cd "$REPO"
DIR="forge-combo29/grok/$S"
python3 "$DIR/partner_pick.py" | tee "$DIR/partner_pick.txt"
PARTNER=$(awk '/^partner /{print $2}' "$DIR/partner_pick.txt")
echo "$PARTNER" > "$DIR/partner_id.txt"
if [ "$PARTNER" = "none" ]; then
  echo "NO_PARTNER" | tee "$DIR/partner_status.txt"
  exit 0
fi
git fetch -q --depth 1 origin "for-fable-and-opus/grok-$PARTNER"
echo "fetched $(git rev-parse FETCH_HEAD) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
if git cat-file -e "FETCH_HEAD:forge-combo29/grok/$PARTNER/idea.patch.txt" 2>/dev/null; then
  rm -rf "$DIR/partner_src"
  mkdir -p "$DIR/partner_src"
  git archive FETCH_HEAD "forge-combo29/grok/$PARTNER" | tar -x -C "$DIR/partner_src" --strip-components=3
  echo "HAS_PATCH $(git rev-parse FETCH_HEAD)" | tee "$DIR/partner_status.txt"
  find "$DIR/partner_src" -type f -printf '%f\n' | sort | tee "$DIR/partner_files.txt"
else
  echo "NO_PATCH" | tee "$DIR/partner_status.txt"
fi
