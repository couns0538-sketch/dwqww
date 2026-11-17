#!/bin/sh
# Run every checker over this seat's deliverables. Exit 0 only if all pass.
#
# Each member is proved able to fail INDEPENDENTLY, because a gate claim is only as broad
# as the number of its members individually shown to fail (findings §6). The proofs are
# the *_proof.sh / fixture scripts next to each checker, not this file.
#
# Usage: sh gate.sh            (from the seat root, or anywhere: it anchors to this file)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
SRC=${FORGE_SRC:-/home/ubuntu/work/base/forge-combo29}
SEAT=$(cd "$HERE/.." && pwd)
fail=0
ran=0

check() {
  name=$1; shift
  ran=$((ran + 1))
  if "$@" > /tmp/gate_$name.log 2>&1; then
    echo "PASS  $name"
  else
    echo "FAIL  $name   (see /tmp/gate_$name.log)"
    tail -5 /tmp/gate_$name.log | sed 's/^/        /'
    fail=1
  fi
}

check citations    python3 "$HERE/check_citations.py" "$SEAT/FINDINGS.md" "$SRC"
check numbers      python3 "$HERE/check_numbers.py"   "$SEAT/FINDINGS.md" "$SEAT/evidence"
check doc          python3 "$HERE/check_doc.py"       "$SEAT/FINDINGS.md"
check doc-fixtures sh "$HERE/doc_fixtures/run.sh"
check sign-selftest python3 "$HERE/sign_test.py" --selftest
check tsan-probe   python3 "$HERE/tsan_run.py" probe

echo
echo "checks run: $ran  (expected 6)"
if [ "$ran" -ne 6 ]; then
  echo "GATE INCOMPLETE: a member did not run"
  exit 2
fi
[ $fail -eq 0 ] && echo "GATE: PASS" || echo "GATE: FAIL"
exit $fail
