#!/bin/sh
# Proof-of-need for check_doc.py: three fixtures that MUST fail and one that MUST pass.
# Run from this directory. Exit 0 only when all four behave as labelled.
cd "$(dirname "$0")" || exit 2
fail=0
for f in bad_fragment.md bad_repeat.md bad_endash.md; do
  python3 ../check_doc.py "$f" >/dev/null 2>&1
  if [ $? -eq 0 ]; then echo "FAIL: $f passed but must fail"; fail=1; else echo "ok: $f fails as required"; fi
done
python3 ../check_doc.py good.md >/dev/null 2>&1
if [ $? -eq 0 ]; then echo "ok: good.md passes as required"; else echo "FAIL: good.md failed but must pass"; fail=1; fi
[ $fail -eq 0 ] && echo "PROOF OF NEED: PASS" || echo "PROOF OF NEED: FAIL"
exit $fail
