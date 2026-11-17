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
   dropped one is a hole.

## Where the evidence lives

| item | file |
|---|---|
| the validator, with 4-case self-test | `job59/validate.py` -> `validate_selftest.out` |
| core family revalidated under it | `job59/revalidate_core.py` -> `revalidate_core.out` |
| the original castling-key audit | `job59/key_audit.out`, `full_audit.out` |
| the trigger as finally established | `job59/RESULT_TRIGGER_FOUND.txt`, 23-F122/F125 |
