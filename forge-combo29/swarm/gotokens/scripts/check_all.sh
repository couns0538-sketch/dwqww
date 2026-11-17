#!/usr/bin/env bash
# Run every check this seat's FINDINGS.md can be held to.
#
# Two independent verifiers, because they check different objects:
#   verify_claims.py   -- figures against the JSONL/JSON evidence, plus
#                         markdown table shape
#   verify_anchors.py  -- the source lines the document cites still contain
#                         the constructs the document says they do
#
# Both have been proved able to fail (see FINDINGS.md "How the figures here are
# checked"); a clean run here means "the cited figures and anchors match", not
# "the prose is correct".
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
rc=0
echo "== claims =="
python3 scripts/verify_claims.py || rc=1
echo
echo "== source anchors =="
python3 scripts/verify_anchors.py || rc=1
echo
if [ "$rc" -eq 0 ]; then echo "ALL CHECKS PASS"; else echo "CHECKS FAILED"; fi
exit "$rc"
