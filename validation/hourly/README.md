# Forge 6.4 improvement work

User authorization, 19 October 2026: inspect `couns0538-sketch/dwqww`, improve
Forge 6.4, preserve code and all experiment evidence, and deliver an update
after each hourly development cycle. Source changes and isolated experiments
are authorized. Work is on `forge/6.4-hourly-20261019`.

## Verified starting point

- Engine branch: `cursor/engine-strength-overhaul-66cc`.
- Baseline commit: `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`.
- Release ZIP SHA-256:
  `98d2ff2c523a25931897794bad3c39d40398799b8907d51596dad3e326a2ba9d`.
- All 51 source, build, test and tool files compared with that ZIP are identical.
- The complete original match archive contains 44 PGNs and 76,047 games.
  Every PGN matches the immutable match branch at
  `f481fc5afc6bf13b730fe5853fbefaeeb6047162` by Git blob hash and byte length.
- Forge 6.4 versus Stockfish 19 with the reported 3000 limiter setting is
  **100 games**, W35/L30/D35, 20+0.2. The 1,120 Stockfish games combine versions,
  settings and time controls. Original 6.x console/config/training logs are
  absent; do not reconstruct or present substitutes as originals.

The inherited `SOURCE_PROVENANCE.json` and several 5.x support documents are
historical. They do not describe all 6.4 features or authenticate 6.x runner
binaries. Use the new manifest and original source evidence.

## First experiment

`20261019-tt-tag-independent-bits`: repair overlap between transposition-table
bucket-index bits and verification-tag bits. Multiply-high indexing needs a
low-32-bit tag; the portable modulo path retains its high-32-bit tag.

The new regression fails 12 checks against the unchanged baseline library.
The repaired candidate passes it and all four existing Release CTest suites.
Both binaries retain the short `bench 11` signature of 417491. That does not
promise universal search identity: eliminating an erroneous TT hit can change
a search. This is a correctness repair whose strength effect requires testing.

The experiment does not repair SMP races, rule-50 eligibility or inherent
partial-tag collisions. It does not change pruning, evaluation, the network,
time management or version numbering. Read `STATE.json` and the latest run
records for current acceptance status.

## Operating procedure

Recovery commands, from the repository root:

```sh
python3 tools/match/restore_hourly_artifacts.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/match/run_hourly_sprt.py --prepare-only
PYTHONDONTWRITEBYTECODE=1 python3 tools/match/run_hourly_sprt.py
```

`ARTIFACTS.json` authenticates the encoded archive pieces, complete archives and
every extracted file. The runtime archive retains the exact three executed
Linux binaries and runner license notices. Full upstream runner source remains
identified by immutable official commit
`ebfd64cb7fac80d4822c50b07dca4fe934779d21` in its provenance record. The recovery
archive retains all 30 raw A/A files including complete UCI traces. Earlier
large binary-upload attempts did not complete; the smaller encoded transport
is explicit and independently hash-checked. Never count an attempted upload
as a successful save.

The restoration helper also recreates the exact selected opening permutation
from the tracked original book and frozen protocol, with a hash check. For a
continuation, restore the latest full match archive first, including its native
checkpoint, cumulative PGN and prior immutable result/log files. Source and
runner paths may be rebased only through the reviewed driver. A native terminal
SPRT cannot be resumed. First natural tranche is 100 pairs, then cumulative
200, 300, and so on; this is one test up to its fixed 10,000-pair maximum.

The 19 October native recovery check passed: a two-round A/A run resumed to four
rounds matched the uninterrupted four-round control in pair IDs, positions,
colors, moves, results and native statistics. This verifies natural checkpoint
recovery, not arbitrary interruption or playing strength.

1. Recover this branch and the latest completed checkpoint. Inspect upstream
   changes without replacing the verified baseline with another project or a
   newer filename. Preserve all original branches and raw evidence.
2. Check the work lease and actual owned jobs before starting. Do not duplicate
   a live implementation or overlap benchmarks with another CPU workload.
   A fresh remote lease from an active foreground run means report its saved
   status rather than launch a competing experiment. Do not signal a PID from
   another process namespace.
3. Finish validation of the current candidate before stacking another change.
   Use one bounded hypothesis, reproduce defects first, review substantial
   patches independently, and preserve rejected/inconclusive ideas with their
   evidence and a condition for revisiting them.
4. Correctness and strength are separate decisions. Use a preregistered,
   equal-clock fastchess SPRT for a stronger-engine claim. Require actual
   native H1 acceptance, not positive score, fewer nodes or budget exhaustion.
   Preserve small demonstrated improvements. Do not broadly remove selective
   search to force all warm/cold scores to agree.
5. Record exact source, network, compiler, binary, runner and opening hashes;
   commands, resource allocation, raw stdout/stderr, PGNs, native statistics,
   tests, failures and reviews. Save before long steps and before ending.
   Commit these artifacts on this work branch with a checked expected head.
6. Send an update every cycle, including a blocked or inconclusive cycle:
   what changed, evidence, current decision, saved artifact links and next step.
   Do not invent work during unavailable execution or usage intervals. Do not
   force a release/version increment because the timer fired.

Use the actual available CPU allocation. The user's Windows data-generation
reservation of logical CPUs 12–15 is not the numbering of this cloud machine.
Do not claim physical Ryzen or Windows validation from Linux tests.

## Ranked remaining investigations

These are hypotheses unless accompanied by a reproducer in a later run.

1. Complete the TT-tag candidate's equal-clock strength assessment.
2. Defer move-picker direct-check masks until quiet/evasion scoring needs them;
   require exact per-position search results and credible paired timing.
3. Attribute root search effort to stable move identities across iterative
   deepening and aspiration passes; verify accounting and equal-clock strength.
4. Reproduce high-halfmove-clock qsearch TT reuse with controlled entries.
5. Design coherent publication of shared TT entries for SMP; the existing
   non-atomic fields are a separate issue from this tag correction.
6. Fuse NNUE accumulator passes while preserving each lane's floating-point
   operation order; retain `-ffp-contract=off` and output-layer summation order.
7. Reproduce the loaded external-book bypass of `OwnBook=false`.
8. Validate NNUE checkpoint dimensions, training/inference K metadata, requested
   load failures and save errors before new training runs.
9. Make unspecified single-config CMake builds use Release, and refresh current
   provenance documentation without rewriting historical evidence.

Consult the archived 6.x experiment ledger before retesting old search
constants or neural architectures. A source change or new hypothesis must
explain why an earlier rejected idea is worth revisiting.
