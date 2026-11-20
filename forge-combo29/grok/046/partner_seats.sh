#!/usr/bin/env bash
# Seats with idea 46 are 046, 096, and 146. 146 is outside 001..120.
# Partner is the next seat after ours that has a branch.
set -u
cd "$(cat ~/grok_repo.txt)"
git ls-remote origin refs/heads/for-fable-and-opus/grok-046 refs/heads/for-fable-and-opus/grok-096 refs/heads/for-fable-and-opus/grok-146
echo "NOW $(date -u +%Y-%m-%dT%H:%M:%SZ)"
