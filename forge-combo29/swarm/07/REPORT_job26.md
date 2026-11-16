# REPORT — seat 07, job 26: the PC r15 build, verified against its own numbers

## What was asked / the answer / how sure

**Asked:** fetch `handoff/fable-opus-combo29-all-20261114`, read `FABLE_TO_swarm_5.md` before the next
step, build the PC's engine from the patch it carries in a SEPARATE copy with
`-DFORGE_MATE_ALPHA_GUARD=1`, and check the bench numbers it must give.

**Answer:** built and **all eight published numbers match exactly**, in all three regimes the file
distinguishes. Patch sha256 verified before use.

**How sure:** very high — the numbers are exact integer matches in a fresh process per line, and the
file itself tells us a mismatch would mean a wrong regime, so I checked all three.

## Patch provenance

    source:  forge-combo29/soak_all/FABLE_TO_swarm_5.md on handoff/fable-opus-combo29-all-20261114
    block:   the fenced diff, from its first `diff` line to its last line
    bytes:   2319 lines
    sha256:  d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a
    expected prefix per file 5: d6bd72c531f785f4   -> MATCH

Applied in a **separate worktree** (`/agent/repos/pcbase`, base `6b98f217`) so the copy I build the
base engine from is untouched, exactly as instructed. `patch -p1` reported **11 files** and no rejects.

Build: `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1` with g++ 13.3.0,
`-j4`. The flag is required: without it `MateAlphaGuard` does not exist and PC20 would print
`unknown option`.

## Results (Threads 1, Hash 16, one fresh process per line)

| settings | check | got | published | |
|---|---|---|---|---|
| none (no setoption at all) | bench 11 | 312866 | 312866 | OK |
| none | bench 13 | 862329 | 862329 | OK |
| none | bench 16 | 3024920 | 3024920 | OK |
| none | go perft 5 | 4865609 | 4865609 | OK |
| S14 (14 settings) | bench 11 | 242796 | 242796 | OK |
| S14 | bench 13 | 656517 | 656517 | OK |
| PC20 (S14 + 6) | bench 11 | 278024 | 278024 | OK |
| PC20 | bench 13 | 587276 | 587276 | OK |

No `unknown option`, `invalid value` or `ERROR` line appeared in any regime, which is the second thing
file 5 asks to be checked (every option name must exist in the exe's own `uci` list).

Raw: job26/raw/pc_pins.json.

## Why the three-regime check matters

File 4 records that the pins are **default-option** numbers while the known node sums are taken **under
S14**, and that seat 10 saw a false mismatch by mixing them. File 5 adds a third regime, PC20. So the
same build legitimately gives three different bench-13 values (862329 / 656517 / 587276) and all three
are correct in their own regime. Checking only one would have left the others unproven, and a reader
could easily think one of them is a bug.

## Findings

**07-C21** in FINDINGS.md.

## Suspicions, not proven

- The S14 bench 11 figure here (242796) matches the number seat 10 measured on the **base** tree, which
  suggests the S14 settings dominate that measurement; I did not test why they coincide.
- PC20's six extra options are all exercised for existence, but only `MateAlphaGuard` and `OwnBook`
  are boolean/simple; `HistRework` takes 0..3 and I set 2 as specified without testing other levels.

## What I did NOT do

- Did not test the new search options' behaviour (CuckooRep, HistRework, TtPruneV2, CorrHistV2) beyond
  confirming the engine accepts them and that PC20 reproduces its numbers.
- Did not touch evaluation-dependent results; the PC plays with its own trained net which is not shared
  (file 5), so the built-in evaluation remains, and file 2's rule 2 applies.

## What I am NOT sure about

- Whether any of the PC patch's FORGE_FIX_* switches other than the defaults documented are on in this
  build. I built exactly as instructed and the pins match, so the configuration is the intended one.

## Times

See job26/stamps.txt.
