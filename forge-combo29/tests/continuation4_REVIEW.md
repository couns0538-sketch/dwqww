# Four-ply continuation history experiment

Status: **UNPROVEN search-changing experiment**, not a demonstrated fix, speedup,
or strength improvement. Production checkpoint: `d2e99a1`.

## Opt-in contract

- Build with `-DFORGE_EXPERIMENT_CONTINUATION4=1`. Its source default is zero.
- In that build, set UCI `Continuation4Weight` from 0 to 100. It defaults to 0.
  With `FORGE_EXPOSE_TUNABLES` defined, UCI advertises the experiment option.
  A macro-zero build neither advertises nor accepts this experimental tunable.
- The option is appended after all existing tunables in the parameter table
  and after every existing advertised option, including Clear Hash.
  Resolve options by name, never by a table index.
- A weight of 100 adds exactly the stored four-ply continuation-history value.
  A weight of 50 adds half that value, with signed integer division truncating
  toward zero. Existing four-ply updates remain at half the update bonus.
- Missing stack context, sentinel entries, null predecessors, and null history
  pointers contribute nothing. This matches the existing update eligibility.
- Weight zero preserves the existing main/one-ply/two-ply arithmetic and order.
  The locked constants, NNUE, datasets, and history-update rules are unchanged.

The extra term is used both by the fast move-picker scorer and by
`Worker::quiet_history`, including the `FORGE_SEARCH_SPEED2=0` path. It can
therefore change move ordering, history pruning, and history-based LMR. It is
not merely a move-order cosmetic change.

## Reproduction

On an x86-64-v4 CPU with GCC 14:

```sh
CXX=g++-14 bash tests/continuation4_check.sh /tmp/forge-continuation4-repro
```

The script builds the 2×2 matrix of `FORGE_SEARCH_SPEED2=0/1` and
`FORGE_EXPERIMENT_CONTINUATION4=0/1`, using strict floating-point flags. Other
new review switches remain at their default values. It runs:

1. Internal helper tests for zero/positive weight, signed truncation, null and
   sentinel context, and the fast scorer's original sum plus the new term.
2. All official depth 11/13/16/20/22 pins with NNUE on/off and startpos perft 5
   for every build at weight zero.
3. Fixed-depth T1 comparisons over the existing 128-FEN fixture, comparing
   depth, nodes, score, PV, and bestmove with NNUE on/off in both speed modes.
4. Weight-50 and weight-100 searches on 32 FENs, with NNUE on/off in both speed
   modes; every returned PV move is replayed against Forge legal generation.
5. Experiment-only option exposure, accepted nonzero values, range clamping,
   malformed-value rejection, and recovery of baseline search after reset to 0.

Legal-PV validation uses Forge's own board implementation, not an independent
chess oracle. These are finite correctness/equivalence screens, not exhaustive
search proofs. Positive-weight search differences are expected and do not show
better play. Any adoption requires separate controlled strength testing; no
container timings qualify as a speed result.

## Observed receipt (2026-11-10)

All four full pin suites passed. All 512 weight-zero exact result comparisons
passed. At weights 50/100, 256 searches completed; 170 differed from weight
zero, establishing that the experiment actually ran. All 128 corresponding
positive-weight speed-path comparisons matched. The validator replayed 1,382
legal PV plies. Helper, UCI exposure, clamping/rejection, and reset tests passed.

`continuation4_results.json` records binary/fixture hashes and comparison
counts; `continuation4_pins.txt` records the four complete pin summaries. The
four engine binaries were frozen from production checkpoint `d2e99a1`, before
the subsequent default-off TT API-depth fix. Rebuilding a later checkpoint can
produce different binary hashes without changing these expected results.

The new option advertisement test was first run against the pre-experiment
binary and failed because the option was absent, then passed for both
experiment-build scorer variants. No additional experimental search options
were enabled during this screen. Full-engine aggregate checks are coordinated
separately; this receipt covers this experiment only.

## Append-only option follow-up (2026-11-10)

`Continuation4Weight` is last in the tunable table and is advertised after
`Clear Hash`, so the entire legacy advertised option sequence is an unchanged
prefix. The advertisement defers the experimental parameter by its name;
production `setoption` also resolves `parameter.name`, never an index. A
repository-wide audit found no positional parameter lookup requiring conversion.

The focused regression first failed on the original prepended experiment and
on the intermediate table-only append (which still shifted Clear Hash). It
then passed with the full append fix in both `FORGE_SEARCH_SPEED2` modes: all
52 tunables were changed and restored independently by name, and depth-11 pins
remained 312866 with NNUE and 375354 without it. The helper test additionally
finds the experiment by name and checks that its iterator is the table's final
entry. This follow-up does not change the experiment's search behavior:
nonzero weight still changes ordering, LMR, and pruning, with strength unproven.

Focused command (baseline and experiment built with the same speed mode):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tests/continuation4_option_order.py BASELINE EXPERIMENT
```
