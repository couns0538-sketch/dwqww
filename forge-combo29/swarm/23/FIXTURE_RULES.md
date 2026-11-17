# FIXTURE RULES — read before writing any fixture in this seat

**The validator is not a helper, it is the gate. Import it; do not write your own counter.**

```python
import sys; sys.path.insert(0, 'forge-combo29/swarm/23/job59')
from validate import check_fixture
ok, msg = check_fixture(fen, moves, expect=3)      # both counters must agree, then meet `expect`
if not ok:
    raise SystemExit("FIXTURE REJECTED: " + msg)
```

## Why this file exists

23-F122: every fixture in this seat was validated with a key of `placement + side + EP`, which silently omitted
**castling**. So "asserted root occurs 3 times" meant "placement+side occurs 3 times". Two boards that SEARCHED were
miscounted as threefolds; they had truly occurred ONCE, because their cycles moved a rook and destroyed a castling right.
That one arithmetic defect generated **four successive scope explanations** (sparse endgames, castling-as-conditioner,
material, halfmove) before it was found.

23-F123: the counter that BUILT the fixtures and the counter that ASSERTED them were the same code, so no assertion could
ever disagree with it — a check that cannot fail, at the level of the fixture gate.

23-F127: the replacement validator's own python-chess counter was hard-capped at five occurrences, so it rejected a
legitimate six-occurrence fixture within minutes of being written. The self-test caught it because the six-occurrence
case is in the self-test.

## Writing to these files — the append path is a trap

I created a stray `FINDINGS.md` one directory above the seat **twice in twenty minutes**, both times by appending with
`>> ../FINDINGS.md` from inside a `job*/` folder. From `job68/` that lands in `swarm/`, not the seat; from the seat it
lands in `swarm/` too. The path looks local and is not.

**Convention: the seat's own files are the only writable target, and they are written from the SEAT ROOT with no `..`:**

```bash
cd forge-combo29/swarm/23            # always from here
cat >> FINDINGS.md <<'XEOF'          # never ../FINDINGS.md, never from inside a job/
...rows...
XEOF
```

Two guards now exist, neither of which needs to be remembered:
- `audit_findings.py` HARD FAILS if a `FINDINGS.md` exists anywhere under `swarm/` outside the seat (**proved**: planted
  at `swarm/FINDINGS.md`, audit printed `stray FINDINGS.md outside the seat: 1` and `VERDICT: FAIL`; removed, PASS);
- the pre-commit gate runs that audit automatically (23-F150).

**And the trap is worth naming as a class, not an incident: a relative path that looks local and is not.** The same shape
appeared when a `&&` chain reported success from a step that never ran (23-F152) and when a fixture key silently omitted
a field (23-F122) — in each case the tool did exactly what it was told and the instruction was wrong.

## The rules

1. **Identity is FIDE identity**: placement + side to move + castling rights, plus en-passant ONLY when a legal
   en-passant capture exists. `validate.identity()` implements this; use it rather than re-deriving a key.
2. **Count twice, from independent implementations**: `validate.count_occurrences` (from FEN strings) and
   `validate.count_via_python_chess` (python-chess's `is_repetition`). Disagreement is a hard failure, not a warning.
3. **Both counters must be about the SAME object.** The first version of the independent counter asked about the FINAL
   board while the local one asked about the ROOT; on a castling-disturbing cycle those are different positions, and the
   validator reported a false disagreement. Two counters only form a check if they count the same thing.
4. **Never hand-type a move list.** Derive cycles by search over legal non-capturing non-checking moves; a hand-typed
   list produced a retracted finding (job 44) and a silently-different-position measurement (23-F109).
5. **A zero needs a planted case.** Any fixture asserting "no X happens" must be shown producing X somewhere in the same
   run, or the zero means nothing (23-F89/F90).
6. **Print the count beside the verdict** — `counted=3 python-chess=3 expect=3` — so a reader can see the population
   the claim rests on (23-F89's printed-population habit).
7. **If a fixture is rejected, publish the rejection.** A rejected fixture in a results table is information; a silently
   dropped one is a hole. **A sample of two with one exclusion stated is honest; the same sample with the exclusion
   silent is a sample of two that a reader will assume was chosen.** State WHICH case dropped and WHY it could not
   answer (no cycle exists / it is confounded / it fails validation), every time.
8. **A test chain prints what ran, not just whether anything failed.** An `&&` chain is a claim that every step ran, and
   it can be true by omission: a clone that fails short-circuits the `cd`, the config and the command under test, and a
   trailing `|| echo BLOCKED` then reports a pass produced by the ABSENCE of a repository (23-F152). Echo the
   intermediate facts — are we inside a work tree, which branch, what did the config read back — so a short-circuit
   shows as a missing line rather than as a confident negative.
9. **Separate a confound from a refutation before reporting either.** 23-F132's bare-kings cell returned 0 nodes at two
   occurrences and looked like a counter-example to the "only if" half; it also returns 0 nodes with NO history at all,
   because insufficient material is an automatic draw. The zero came from a different rule. The test is: run the same
   cell with the variable under test REMOVED (here, no move list) and see whether the outcome persists — if it does,
   you have measured the confound.

## Where the evidence lives

| item | file |
|---|---|
| the validator, with 4-case self-test | `job59/validate.py` -> `validate_selftest.out` |
| core family revalidated under it | `job59/revalidate_core.py` -> `revalidate_core.out` |
| the original castling-key audit | `job59/key_audit.out`, `full_audit.out` |
| the trigger as finally established | `job59/RESULT_TRIGGER_FOUND.txt`, 23-F122/F125 |
