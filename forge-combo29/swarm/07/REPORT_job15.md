# REPORT — seat 07, job 15: transposition-table invariants, and a second kind of blind control

## What was asked / the answer / how sure

**Asked:** continue the area-7 read (the transposition table is one of the eight files in the area's
order), prioritising what shows in normal play.

**Answer:** four TT invariants that must hold for correct play **all hold**: 2,000 store-then-probe
round trips return the exact stored payload; a key differing only in its high 32 bits does not get
another key's payload; `resize()` and `clear()` leave no stale hits. Getting to this result required
catching a **second kind** of blind control, new tonight: a fault planted in a header but compiled
into only the test file, while the code under test kept using its old object file.

**How sure:** high, once the control was rebuilt correctly (it then reports 15 failures).

## Honesty numbers

Base build: 312866 / 862329 / 3024920 / 4865609 (job0/raw/summary.txt). No engine source changed.

## The invariants and why each matters in play

| # | invariant | what breaks in play if it fails |
|---|---|---|
| 1 | store(K) then probe(K) returns the same score/depth/bound/rule-50 clock | a search remembers the wrong score for a position → wrong best move |
| 2 | a key differing only above 32 bits must not return the other key's payload | two distinct positions share a verdict → illegal or losing move |
| 3 | `resize()` must not leave a hit from the old allocation | a hash resize mid-game (GUI option) would serve stale scores |
| 4 | `clear()` must empty the table | `ucinewgame`/`Clear Hash` would keep the previous game's scores |

`TTEntry` is 16 bytes with a 32-bit verification key (`static_assert(sizeof(TTEntry) == 16)`), so
invariant 2 is about the engine's *own* tag derivation being self-consistent, not about collisions
being impossible.

## Result

    1. store-then-probe: 2000/2000 hits
    2. high-32 variant missed, as expected
    3. probe after resize: miss
    4. probe after clear: miss
    occupied-after-clear hashfull: 0
    ALL TT INVARIANTS HELD (0 failure(s))

Raw: job15/tt_run.txt.

## The control, and the mistake in my first attempt

**Attempt 1 (blind).** I planted a constant `verification_key` in `/tmp/inc_tt/forge/search.hpp`,
built the probe with `-I/tmp/inc_tt`, and linked the **pre-built** `build-rel/.../search.cpp.o`.
Result: "ALL TT INVARIANTS HELD". That is meaningless: the translation unit that implements
`probe`/`store` was compiled against the *real* header, so the fault could not reach the table.

**Attempt 2 (valid).** Recompile `search.cpp` itself against the faulty header, then link:

    FAIL rule50 clock mismatch for key 18339545375304548980
    ... FAILURES (15 failure(s))

The specific failure is diagnostic: with a constant tag, every entry in a cluster matches, so a probe
returns another position's rule-50 clock. That is exactly the mechanism invariant 1 is meant to
catch, and the probe catches it.

**Lesson for the swarm (now two variants):**
1. (from 07-C10) plant the fault in the file the code actually lives in — the legality shortcut is
   inline in `board.hpp`, so a `board.cpp` fault is unreachable;
2. (from this job) a header-planted fault requires recompiling **every dependent translation unit**,
   not just the test file; linking stale `.o` files silently defeats the control.

## Findings

**07-C12** in FINDINGS.md.

## Suspicions, not proven

- The replacement policy (`store_body`'s `admit` rule and the probe's depth-minus-age choice) I read
  but did not test for fairness or for whether a deep entry can be evicted by a shallow newer one
  more often than intended. That affects strength, not correctness, and needs a benchmark, not an
  invariant.
- `score_usable`'s fifty-move horizon logic is exercised indirectly by invariant 1's clock checks but
  not probed at its boundaries (clocks 89/90/99/100).

## What I did NOT do

- Did not test TT behaviour under multiple threads (area 4's territory) or under `FORGE_SPD_TT_NOTLS=1`
  (the build uses 0 for this probe; the shipped CMake defines 1, so the lock-free owner path is
  **not** what I probed — stated plainly, this test covers the locked path only).
- Did not test hashfull's sampling accuracy (seat 27's S-F3 concerns that).

## What I am NOT sure about

- Whether the shipped `FORGE_SPD_TT_NOTLS=1` path has the same invariants. My probe deliberately used
  the locked build so that a failure would be unambiguous; the owner path skips `lock_stripe` and
  deserves its own probe.

## Times

See job15/stamps.txt.
