# REPORT — seat 07, job 21: check of seat 27's S-F7 (the UCI option surface)

## What was asked / the answer / how sure

**Asked:** (cycle step 2a) check another seat's NEW finding that nobody has checked, reproducing it
from its claim with a harness of my own. I searched all the seats I could fetch and found **no** C
line for 27-S-F7, so it was unclaimed.

**Answer:** **CONFIRMS** 27-S-F7 — the UCI option surface really does match its advertisement — on a
wider sweep than the original: **82 advertised options, 437 setoption cases, 0 in-range values
refused, 0 advertised options reported unknown**, and a control that fails the check when a handler
is missing.

**How sure:** high. The check reads the advertised list from the engine itself (so it cannot go stale
against a changed option table) and the control proves the failure mode is detected.

## Honesty numbers

Base build pins unchanged (job0/raw/summary.txt: 312866 / 862329 / 3024920 / 4865609). No engine
source changed; the fault build is a copy at `/tmp/optfault`.

## The claim, and what my harness does differently

Seat 27's claim: *"The UCI option surface matches its advertisement: all 81 advertised options
exercised with 291 setoption cases give 0 refusals of an advertised min/max value and 0 `unknown
option` lines."*

I wrote my own harness rather than re-running theirs. It:

1. parses the `option name ... type spin/check/string/button ... min ... max ...` lines out of the
   engine's own `uci` answer (82 options here);
2. for every spin option sends **min, max, min−1, max+1, a word, and no value**;
3. for every check option sends **true, false, `yes`, and no value**;
4. for every string option sends **`<empty>` and no value**;
5. for every button sends **no value**;
6. after each, sends `isready` and reads **every line up to `readyok`**, then classifies.

Classification, with the two bug classes separated:

- **ACCEPTED** — no complaint;
- **CLAMPED** — `info string invalid value for option <name>`, which is the engine's documented
  behaviour for out-of-range and non-numeric values;
- **REFUSED-VALID** — a complaint for a value *inside* the advertised range → would refute S-F7;
- **UNKNOWN** — `info string unknown option <name>` for an *advertised* name → would also refute it.

## Result

    advertised options 82, cases 437
      ACCEPTED: 163
      CLAMPED: 274
      REFUSED-VALID: 0
      UNKNOWN: 0
    RESULT: CONFIRMS 27-S-F7 - every advertised option was recognised and every in-range value was
            accepted; out-of-range and junk values were reported as the engine documents

Raw: job21/raw/summary.txt, which also lists every advertised option with its type, default, min and
max so a later seat can diff the surface if it changes.

## The control

A copy of the tree that **advertises an option it does not handle** — `PhantomOption`, added to the
`uci` answer only:

    UNKNOWN: 6
    BUG UNKNOWN for advertised option [PhantomOption] value [1] :: info string unknown option PhantomOption
    ... (same for 10, 0, 11, word, no-value)
    RESULT: REFUTED - 0 valid value(s) refused, 6 advertised option(s) unknown

So the `UNKNOWN` class is detected when it exists. The `REFUSED-VALID` class I could not make fire
without a second, more intrusive fault (making `apply_spin` reject an in-range value); I note that as
a gap rather than claim both halves are proven by the control. The `CLAMPED` count of 274 rising from
a build where a value genuinely is in range would be the signal, and in the clean run every in-range
value landed in ACCEPTED.

## Findings

**07-C19** in FINDINGS.md.

## Suspicions, not proven

- The `REFUSED-VALID` half of the check is unproven by a control (see above). It is also the half that
  would matter most for a tuner: an in-range value silently clamped would corrupt a tuning run.
- My sweep sends one value per case; it does not test values exactly at the boundary of the *stored*
  type (e.g. a spin whose C++ type is `int` but whose advertised max is near INT_MAX).

## What I did NOT do

- Did not test options during a running search (that is 27-S-F9's territory).
- Did not verify that each accepted value actually *takes effect*; only that it is not refused. S-F7
  is about the surface, and effect is a different claim.

## What I am NOT sure about

- Whether seat 27's 81st option was the `Clear Hash` button or one I parse differently; my parser counts
  82 and lists them all in the summary, so the discrepancy is visible rather than hidden.

## Times

See job21/stamps.txt.
