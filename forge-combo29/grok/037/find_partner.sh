#!/usr/bin/env bash
# Seats with idea 37 are 037, 087. This seat is 037, so the partner is 087 if that branch exists.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
echo "seat $S time $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git ls-remote origin "refs/heads/for-fable-and-opus/grok-087" "refs/heads/for-fable-and-opus/grok-037"
