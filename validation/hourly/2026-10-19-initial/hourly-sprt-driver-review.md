# Independent review: frozen hourly TT-tag SPRT harness

## Outcome

No remaining blocker was found for preparing the protocol and launching the first natural 100-pair tranche. No engine or strength match was launched in this review. The driver changed before protocol preparation: it now checks and records the **final** native LLR, rejecting a final NaN/Inf even if an earlier LLR was finite. The prior check searched for any finite-looking LLR line and could miss this evidence failure.

The new helper still leaves statistical decisions to fastchess. It recognizes the pinned runner's native `SPRT (...) completed - H0/H1 was accepted` messages, rejects conflicting terminal messages, and records the finite final LLR without recalculating Elo or the stopping rule.

## Reviewed evidence

- `tools/match/run_hourly_sprt.py`, `tools/match/pgn_stats.py`.
- Saved `forge-fastchess-resume-review.md`, actual pinned-runner `--help` output, and real natural 2-round -> 4-round A/A checkpoint/PGN fixtures.
- Official pinned source `ebfd64cb7fac80d4822c50b07dca4fe934779d21`, preserved inside `runtime-reproduction.zip`; output format in `app/src/matchmaking/output/output_fastchess.hpp` and the stopping message in `app/src/matchmaking/tournament/roundrobin/roundrobin.cpp`.
- `app/third_party/chess.hpp` removes invalid or legally uncapturable EP targets when reading FEN (the `setFenInternal`/`isEpSquareValid` path). This accounts for source EP target -> PGN dash normalization.

## Checks

The committed review script launches no engines. It exercises the real saved 8-game A/A fixture and observed native JSON schema; rejects changed clocks, binary paths, engine counts, SPRT model, opening start, adjudication, UCI options, WDL and pentanomial counts; recognizes H0/H1 output; rejects conflicting decisions, missing LLR and nonfinite final LLR. It also confirms that its completed input checkpoint was not modified. See `hourly-sprt-driver-review-tests.json` for every check and exact driver digest.

## Continuation invariants

The driver freezes binary, opening, checker and driver identities before any strength game. A continuation verifies the previous final evidence hashes and complete paired PGN prefix before changing only recognized absolute paths. Original checkpoints and previous per-tranche logs remain immutable. Native config is read before the larger cumulative `-rounds` override, and `stats=true` is retained. Affinity, strict mode and fresh trace paths are reapplied. Incomplete/failed attempts or native H0/H1 outcomes cannot be resumed automatically. Terminal outcomes retain orphan PGNs and reconcile native statistics against complete pairs; natural exhaustion requires every round through the cap exactly twice, with swapped colors and the same starting FEN.

## Practical limits

- PGN checking is bookkeeping, not a second chess-legality implementation. The allowed EP-to-dash normalization is deliberately broader than proving EP legality anew; safety of that normalization relies on the pinned runner identity and exact source opening hash. All other first-four-field FEN components must agree. This is not a reason to change the opening protocol after games start.
- The tests use previously completed fixed-node A/A fixtures solely to verify schema and bookkeeping. They provide no playing-strength result.
- The old `hourly-sprt-driver-validation.json`, if retained, describes an earlier driver revision. The new review result records the post-fix digest. Freeze `protocol.json` only after these edits.
- After a natural tranche, snapshot/persist the checkpoint, PGNs and logs before continuing; do not substitute scheduled interruption for natural completion.

