# REPORT — seat 07, job 19: the time manager's pure functions, and three void controls

## What was asked / the answer / how sure

**Asked:** finish the area-7 read; the time manager is the remaining file in the area's order.

**Answer:** every property the time manager's two headers claim **holds**, checked directly because
these functions are pure — plus `plan_clock_budget`'s invariants, under UBSan, with both a property
control and a working sanitizer control. The interesting part of this job is that my UBSan control
took **three failed attempts** before it could fire at all; each failure would have let me report a
meaningless "no UB".

**How sure:** high for the properties (they are exhaustively checked over grids and proven failable),
high that UBSan would catch an overflow in this code (control fires), and therefore reasonably high
that no overflow occurs on these paths for the inputs tested.

## Honesty numbers

Base build pins unchanged from job0: 312866 / 862329 / 3024920 / 4865609. This job touches no engine
source and does not re-measure search; it needs no pins of its own.

## Result

    tm_finish: monotonicity checked 1000, extreme inputs 12
    node share: 560 grid cases checked for N2/N3
    node share scale: 0% -> 1500, 50% -> 1000, 100% -> 500 (want 1500/1000/500)
    clock plan: 420 cases satisfied 1 <= soft <= hard <= available
    clock plan at the parse ceiling 36028797018963967: soft 28823037615171173 hard 28823037615171173

    ALL TIME-MANAGER PROPERTIES HELD (0 failure(s))

Raw: job19/run.txt.

## What was checked, and why each property matters in play

| property | source claim | why it matters |
|---|---|---|
| `iteration_will_not_finish(_, _, 0)` → true | "A budget that is already used up cannot hold another iteration" | otherwise the engine starts an iteration it cannot finish and may lose on time |
| non-positive durations → false | "A non-positive duration is not a measurement" | otherwise a fast first iteration makes the estimate nonsense |
| monotonic in the remaining budget (1,000 cases) | implied by the estimate being compared to `remaining_ms` | a non-monotonic stop rule can stop *later* with *less* time |
| node-share scale 0/50/100 % → 1500/1000/500 | the header's documented linear scale | the time budget would silently shift if this drifted |
| `effort_share_factor` = 1.0 with node share on | "TmNodeShare applies that share itself, so this piece stays 1" | otherwise the share is applied twice and the budget is wrong |
| `1 ≤ soft ≤ hard ≤ available` (420 cases) | the header's stated bounds | soft > hard would make the stop rule contradictory; hard > available loses on time |
| parse ceiling produces sane limits | `kMaxClockMs = int64_max / 256` chosen so products fit | a GUI sending a huge clock must not overflow |

## The three void UBSan controls (the honest part)

The first proof required is that UBSan in *this* build really reports a signed overflow. Three attempts
failed to demonstrate that, each for a different reason:

1. `(void)(last_ms * last_ms);` — the value was unused, so **-O2 deleted the multiply entirely**;
   UBSan had nothing to report.
2. `if (overflow_probe >= 1000000LL) return (overflow_probe * 4) != 0;` — 4 × 10⁶ does **not** overflow
   int64; the control returned a wrong value, not an overflow. (It did produce 99 property failures,
   which is a different signal.)
3. `if (overflow_probe > 1000000000000LL)` — the guard was above anything my own grid produces
   (max 10⁶), so the branch was **never reached**.

Only after fixing all three did the control fire:

    /tmp/tm_ub/forge/tm_finish.hpp:33:32: runtime error: signed integer overflow:
        1000000 * 100000000000000 cannot be represented in type 'long int'

I also verified independently that this UBSan build reports overflow at all, with a two-line program
(`/tmp/ubctl.cpp`): `runtime error: signed integer overflow: 4611686018427387904 * 4`.

**Why this matters:** had I stopped at attempt 1, "zero UBSan lines" would have meant nothing, which is
exactly the trap the brief warns about. The lesson is a third variant for the swarm: a sanitizer
control must be (a) reachable by the test's own inputs and (b) not optimised away.

## Property control (C1)

Changing the node-share midpoint from 500 to 400 in a copy of `tm_node_share.hpp`:

    FAIL N4 100% share must give 1/2 of soft, got 400
    node share scale: 0% -> 1400, 50% -> 900, 100% -> 400 (want 1500/1000/500)
    PROPERTIES VIOLATED (3 failure(s))

So the property assertions are failable, not vacuous.

## Findings

**07-C16** in FINDINGS.md.

## Suspicions, not proven

- `iteration_will_not_finish` mixes 64-bit and `unsigned __int128` arithmetic; the 128-bit path avoids
  the overflow the comment worries about, and my extreme-input cases do not trip UBSan, but I did not
  prove the 128-bit reasoning algebraically.
- `plan_clock_budget`'s `hard = std::min(available * hard_percent / 100, soft * hard_soft_multiple)`
  can exceed `soft`, which is intended; I checked the bounds but not whether the *chosen* numbers are
  the ones the tuner wants.

## What I did NOT do

- Did not test the time manager inside a real search beyond job11's nine clock controls (which is the
  behavioural side of the same file).
- Did not verify the tunables' advertised min/max against the UCI option table.

## What I am NOT sure about

- Whether the grids cover the pathological combinations a hostile GUI could send (e.g. `movestogo`
  near INT_MAX together with a huge clock). `movestogo` is clamped to 50 in the plan, which I read but
  did not fuzz.

## Times

See job19/stamps.txt.
