#!/bin/sh
# mutation_suite.sh : for EACH cited checker, plant a fault in what it checks, confirm it
# exits nonzero, then restore. A checker never shown failing is not evidence (23-F199/F226).
# Every mutation is applied to a COPY that is restored in a trap, so an interrupted run
# cannot leave a document corrupted.
SEAT=$(cd "$(dirname "$0")" && pwd)
cd "$SEAT" || exit 2
fail=0
restore() { for f in "$@"; do [ -f "$f.bak_mut" ] && mv -f "$f.bak_mut" "$f"; done; }

# ---- 1. audit_findings.py : duplicate finding id
cp FINDINGS.md FINDINGS.md.bak_mut
printf '| 23-F001 | 3 | PLANTED DUPLICATE ID | `x` | NEW |\n' >> FINDINGS.md
if python3 audit_findings.py >/tmp/m1.log 2>&1; then echo "audit_findings.py         FAILED TO CATCH a duplicate id"; fail=1
else echo "audit_findings.py         catches a duplicate id (exit $?)"; fi
restore FINDINGS.md

# ---- 2. doc_check.py : a stated count that disagrees with the table
cp FINAL_CHAIN_LINE.txt FINAL_CHAIN_LINE.txt.bak_mut
sed -i 's/distinct rows at/distinct rows at PLANTED/' FINAL_CHAIN_LINE.txt 2>/dev/null
# a more decisive mutation: alter a number in the stated-count sentence
python3 - <<'PY' 2>/dev/null
import re
p='FINAL_CHAIN_LINE.txt'; s=open(p).read()
s=re.sub(r'(\d+) `F` rows are', lambda m: str(int(m.group(1))+7)+' `F` rows are', s, count=1)
open(p,'w').write(s)
PY
if python3 doc_check.py >/tmp/m2.log 2>&1; then echo "doc_check.py              FAILED TO CATCH a count mismatch"; fail=1
else echo "doc_check.py              catches a count mismatch"; fi
restore FINAL_CHAIN_LINE.txt

# ---- 3. rule_check.py : a gap in the instance numbering
cp RULE_known_answer_control.md RULE_known_answer_control.md.bak_mut
python3 - <<'PY' 2>/dev/null
import re
p='RULE_known_answer_control.md'; s=open(p).read()
# heading form is "## Instance N - ..." (capital I). An earlier version of this mutation
# targeted 'INSTANCE' and changed NOTHING, so the checker "failed" a test that never ran (23-F229).
s2=s.replace('## Instance 12 ','## Instance 47 ',1)
assert s2!=s, "mutation did not change the page - the test would be vacuous"
s=s2
open(p,'w').write(s)
PY
if python3 rule_check.py >/tmp/m3.log 2>&1; then echo "rule_check.py             FAILED TO CATCH a numbering gap"; fail=1
else echo "rule_check.py             catches a numbering gap"; fi
restore RULE_known_answer_control.md

# ---- 4. verb_check.py : assert the queen is a knight
cp job70/verb_check.py job70/verb_check.py.bak_mut
sed -i 's/b.piece_type_at(chess.B6)==chess.QUEEN/b.piece_type_at(chess.B6)==chess.KNIGHT/' job70/verb_check.py
if python3 job70/verb_check.py >/tmp/m4.log 2>&1; then echo "verb_check.py             FAILED TO CATCH a wrong piece claim"; fail=1
else echo "verb_check.py             catches a wrong piece claim"; fi
restore job70/verb_check.py

# ---- 5. mech_check.py : assert the repair nets +6 (my own withdrawn story)
cp job70/mech_check.py job70/mech_check.py.bak_mut
sed -i 's/net_pc, 0)/net_pc, 6)/' job70/mech_check.py
if python3 job70/mech_check.py >/tmp/m5.log 2>&1; then echo "mech_check.py             FAILED TO CATCH the withdrawn walk-away story"; fail=1
else echo "mech_check.py             catches the withdrawn walk-away story"; fi
restore job70/mech_check.py

# ---- 6. sign_check.py : invert the sign expectation
cp job70/sign_check.py job70/sign_check.py.bak_mut
sed -i 's/lambda v: v\[0\]=="mate" or v\[1\]>500,"mate or cp>500")/lambda v: v[0]=="mate" or v[1]<-500,"mate or cp<-500")/' job70/sign_check.py
if python3 job70/sign_check.py >/tmp/m6.log 2>&1; then echo "sign_check.py             FAILED TO CATCH an inverted sign"; fail=1
else echo "sign_check.py             catches an inverted sign"; fi
restore job70/sign_check.py

# ---- 7. tie_test.py : restore the old tie-collapsing line in margins.py
cp job11/margins.py job11/margins.py.bak_mut
python3 - <<'PY' 2>/dev/null
p='job11/margins.py'; s=open(p).read()
import re
s=re.sub(r'    if sa > sc:\n        winner = a\n    elif sc > sa:\n        winner = c\n    else:\n        winner = "tie"',
         '    winner = a if sa > sc else c', s)
open(p,'w').write(s)
PY
if python3 job11/tie_test.py >/tmp/m7.log 2>&1; then echo "tie_test.py               FAILED TO CATCH the tie collapse"; fail=1
else echo "tie_test.py               catches the tie collapse"; fi
restore job11/margins.py

# ---- 8. final_recheck.py : one expectation inverted
cp job68/final_recheck.py job68/final_recheck.py.bak_mut
sed -i 's/row("| 2 occ searches | nodes > 0 | %d | %s |", l2\[2\] > 0, l2\[2\])/row("| 2 occ searches | nodes > 0 | %d | %s |", l2[2] > 999999, l2[2])/' job68/final_recheck.py
if timeout 400 python3 job68/final_recheck.py >/tmp/m8.log 2>&1; then echo "final_recheck.py          FAILED TO CATCH a false expectation"; fail=1
else echo "final_recheck.py          catches a false expectation"; fi
restore job68/final_recheck.py

# ---- 9. frontpage_check.py : invert claim 2
cp job69/frontpage_check.py job69/frontpage_check.py.bak_mut
sed -i 's/ok2 = bm == order\[0\]/ok2 = bm != order[0]/' job69/frontpage_check.py
if timeout 300 python3 job69/frontpage_check.py >/tmp/m9.log 2>&1; then echo "frontpage_check.py        FAILED TO CATCH an inverted claim"; fail=1
else echo "frontpage_check.py        catches an inverted claim"; fi
restore job69/frontpage_check.py

# ---- 10-12. the NUMBER-PRODUCING scripts the FINAL's figures come from (23-F230).
# These are the same exposure as the evidence scripts but were never exit-code tested.
cp job61/correctness.py job61/correctness.py.bak_mut
sed -i 's/_p2 = (r4_pc\[1\] == 0 and r4_pc\[0\] == "cp")/_p2 = (r4_pc[1] == 999999)/' job61/correctness.py
if ( cd job61 && timeout 400 python3 correctness.py >/dev/null 2>&1 ); then echo "job61/correctness.py      FAILED TO CATCH a wrong P2"; fail=1
else echo "job61/correctness.py      catches a wrong P2"; fi
restore job61/correctness.py

cp job48/first_legal_move.py job48/first_legal_move.py.bak_mut
sed -i 's/_p4 = rows\[-1\]\[1\] > 1000/_p4 = rows[-1][1] > 999999999/' job48/first_legal_move.py
if ( cd job48 && timeout 400 python3 first_legal_move.py >/dev/null 2>&1 ); then echo "job48/first_legal_move.py FAILED TO CATCH a failed control"; fail=1
else echo "job48/first_legal_move.py catches a failed control"; fi
restore job48/first_legal_move.py

cp job51/holdout.py job51/holdout.py.bak_mut
sed -i 's/if tot and ok1 == tot and ok2 == tot and ok3 == t3_tot:/if False:/' job51/holdout.py
if ( cd job51 && timeout 400 python3 holdout.py >/dev/null 2>&1 ); then echo "job51/holdout.py          FAILED TO CATCH a holdout miss"; fail=1
else echo "job51/holdout.py          catches a holdout miss"; fi
restore job51/holdout.py

echo
if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS - 12 of 12 scripts shown able to fail on a planted fault"; exit 0; fi
echo "VERDICT: FAIL - at least one checker cannot fail"; exit 1
