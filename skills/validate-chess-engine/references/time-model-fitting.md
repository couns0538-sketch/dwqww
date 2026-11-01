# Fitted time management from root-iteration logs

Use this workflow for a model that predicts whether the final completed root
iteration's best move differs from the current completed iteration. This is
an observable search outcome, not ground truth about the strongest chess move.

## Collection and labels

- Compile logging out by default. Emit only main-worker completed iterations,
  after aspiration has converged. Keep logging enabled for both collection arms
  if measuring its overhead; use the production logger-OFF build for final
  timing qualification.
- Attach stable game/search IDs in the runner and seal each search after its
  `bestmove`. Save the returned move, completion state and complete iteration
  count/index receipt. An interrupted later iteration may revise the returned
  move: count this discrepancy but retain the completed iterations. Dropping
  them selects away unstable searches. The target remains the last completed
  iteration; the returned move is audit metadata, never a model input.
- Use only information available at the current iteration: depth, move change,
  the existing best-move effort share, score/delta and elapsed/allocated time.
  State whether effort counts are cumulative or per iteration. Do not add root
  evaluations merely to obtain a new feature during a time-only experiment.
- Label each non-final iteration against that search's final completed move.
  Exclude the terminal iteration, whose label is zero by construction. Never
  count it as an easy model success. Count exclusions and raw/eligible rows.

## Fit and integer parity

Split by whole games before fitting. When reversed-color games share openings,
keep their pair IDs together. Fix the seed once, and do not retry split seeds
to improve AUC. A holdout containing one class is inadequate evidence; report
that condition and collect more data. The 20% group split need not contain
exactly 20% of rows because games differ in length.

Fit transformations using training data only, or declare bounded transforms
before collection. Report holdout AUC with average ranks for tied predictions,
class balance, log loss, and quantized AUC. AUC measures discrimination, not
probability calibration or playing strength. Probability calibration matters
when probability directly selects a time multiplier.

Report rows, searches, games and opening groups separately. Iterations from one
search are correlated; raw row count is not an independent effective sample
count. Report constant feature columns and feature ranges. Opening-group
separation does not establish absence of transpositions between partitions.

Mirror the engine's integer arithmetic exactly: signed division truncates
toward zero, including negative scores; define input/coefficient scales and
sigmoid table indexing. Log an exact quantized effort field so decimal text
rounding cannot move a feature across a quantization boundary. Reject fitted
coefficients outside tunable bounds rather than silently clipping them.

The Forge example implementation is `astra_r8/tmfit/fit_model.py`, with
`test_fit_model.py`. Its fixed transforms, Q10 inputs, Q12 coefficients and
Q10 sigmoid table are part of that candidate's contract, not universal tuned
constants. Run its synthetic tests separately from empirical fitting. Synthetic
reports must never be presented as measured engine evidence.

## Timing qualification

An average multiplier near one does not imply equal actual time usage. Search
stops are discrete, and the option changes the positions and iteration depths
encountered. Choose mapping parameters on a calibration set, freeze them, then
measure actual per-move/per-game clock usage on a separate smoke set. Preserve
both absolute means and the ratio, opening/seed identities, game lengths,
timeout/illegal counts, and aborts. Do not tune repeatedly against the reported
held-out smoke and call it held out.

Prove liveness with fresh-process interleaved OFF/ON clock searches on fixed
positions, multiple repeats, and medians. Record `go wtime/btime`, multiplier,
features, soft target and hard cap in the transcript. A fixed-depth bench can
prove search identity but cannot prove a time-only option is active.

Test low clocks and an absurd exposed coefficient/mapping intercept. Check
clamps, overflow safety, existing max-time cap, and external receipt time for
`bestmove`. Engine-reported search time does not include all protocol delay.
Run sanitizers over the ON path. Make incomplete runtime checks explicit.
Give a bounded sanitizer smoke its own success conditions: every requested
game/search ran with the option ON, real moves were exercised, and no illegal
moves, time losses, sanitizer diagnostics, or process failures occurred. Do not
reuse a 200-game time-normalization command with four games: its qualification
count cannot pass, and alternating OFF/ON also halves the intended ON coverage.
Recognize sanitizer SUMMARY, DEADLYSIGNAL, and leak reports during shutdown as
well as the first error line. Ensure standalone numeric test targets inherit
the sanitizer compile and link flags. Unit tests of a harness do not establish
that an instrumented engine actually ran cleanly.
Treat a hung `quit` that needs forced termination of the harness's own child
as a failed run even after cleanup succeeds. Parse option-rejection receipts
before `readyok`; advertising a coefficient is not proof its requested value
was accepted. Reserve the experiment switch, thread count, and hash size so
arbitrary extra options cannot silently override the comparison contract.

## Evidence and status

Bench-pin equality does not establish source-tree compatibility. Resolve the
exact lock commit or packaged source before generating a handoff patch. Compare
the source bytes, then check both `git apply --check -p1` and the intended patch
consumer on that tree. Git archive/export line-ending conversion can differ
from blob bytes; use blob hashes when auditing untouched algorithm regions.
When a candidate is ported to another base, preserve the earlier candidate and
its results under their original identity. Bind new results to the new base,
patch, resulting source, compiler flags and executable; never relabel evidence.

Retain immutable raw logs under the authorized scratch/storage budget. Commit
a deterministic 1% sample, exact row counts, source/executable/net/opening
hashes, fit seed, split IDs, complete commands and fit script hash. Seal raw
inputs before fitting and detect modifications during reads. Do not overwrite
previous fit outputs when retrying.

For parallel timing qualification, freeze the engine, coefficients, driver,
network, clock settings and opening assignments before launching any shard.
Use disjoint complete opening pairs with colors swapped. A short shard reports
PARTIAL clean evidence, never the full-game-count qualification result. The
parent must verify hashes, exact game/pair counts, unique opening assignments,
matching settings and modes, then recompute both time ratios from raw player
totals across all shards. Average neither shard ratios nor shard PASS labels.
Preserve every child failure and wait for owned children to clean up. Count
simultaneously active search threads across the entire job, including shards.

Record correctness, fitted prediction quality, equal-time behavior and playing
strength as separate conclusions. Keep the candidate UNPROVEN until the crew's
declared SPRT passes; a time-management acceptance also needs its longer-time
control confirmation. Never pool opening suites unless the accepted protocol
explicitly calls for it.
