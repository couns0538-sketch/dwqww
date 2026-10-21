# Forge23 SEE proof reuse: actual observer screen

Status: **promising exact-behavior opportunity, ready for separate candidate implementation**. No query was skipped, production code changed, speed measured or Elo demonstrated. Frozen source23: `1d3ed25bea2c8b781f7ee5a178af0f66061b3984`.

The fresh observer uses all77 verified frozen inputs, with explicit Board/search observation diffs, one diagnostic CMake target and two new observation/driver files (79 source files total). It keeps every original SEE call/result and search branch. Seven actual core objects were built once, serially, with the baseline `/usr/bin/g++-14`, Release `-O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto`. Complete source/build files remain at `/workspace/.cloud-setup/see-proof-reuse23-{source,release}` and are inventoried by `COMPLETE-OUTSIDE-ORIGINALS.json`; changed sources, baseline/observer binaries, cores and build records are also copied into this evidence directory.

The first PATH-based configure and dependent build could not spawn `cmake`; both FileNotFoundError records/empty streams remain intact. The shell attempting build after configure failed was a sequencing error, not an engine or compiler failure. Root cleared only the executable-path repair to the actual baseline CMake3.31.6 binary. Distinct attempt2 records show one actual configure and one actual compiler build, return0/closed owned groups. All actual engine/driver gates passed their first runs; no rescue, retry or reconstructed stream was used.

## Actual results

- Baseline/observer first UCI `bench 11`: **292545 nodes each**, entire stdout canonically identical after replacing only numeric `time`/`nps` fields.
- Eight legal fixtures at depth8, Threads1/Hash16/OwnBookfalse: one cold search followed by the same position with retained TT/history. All16 complete search-response sequences per engine match after the same two-field replacement, including depths, scores, nodes, PVs, hashfull and bestmoves. Original streams and exact sent commands are retained.
- Actual Board replay: **288 PV/bestmove rows,1378 legal moves,0 failures**.
- Actual Board SEE sweep: **391 legal full Move identities,140 positions,1,877,582 calls**, threshold[-2400,2400] step1. The76 named mirrored fixtures include existing pin/king/initial-Q/R/B/N/later-promotion cases;64 deterministic legal-play positions broaden ordinary captures. All569,037 tested `ge(0)=>ge(t<=0)` implications passed. Six EP rows,176 legal promotion rows and two pinned-illegal EP controls were observed. FEN/key/pawn-key/checkers/full key history remained unchanged after each sweep;68 existing known-gain rows agreed. No copied SEE oracle was used. This finite test supports, but cannot replace, the independent actual-algorithm monotonicity argument.

| Workload / consumer | Actual calls | Already proved true by GoodCaptures | Proven calls entering ordinary exchange | Exchange iterations within proven calls | Pinner iterations within proven calls |
|---|---:|---:|---:|---:|---:|
| bench11 noisy pruning |48191|12166|2804|4120|460|
| bench11 exact-zero extension |6545|1221|302|550|19|
| fixture noisy pruning |17437|3443|742|978|94|
| fixture exact-zero extension |4919|179|80|113|0|

Bench11 produced85261 GoodCaptures SEE calls and39179 successful returns. Its13387 proven repeated consumer calls are3.88% of all344945 observed SEE calls;3106 of those entered exchange analysis. The fixture run adds3622 duplicate queries,822 ordinary exchange entries/1091 iterations and30 promotion-helper iterations. These are **opportunities**, not measured savings: many duplicate queries take an early return, bookkeeping/code generation can offset saved work, and uninstrumented calibrated timing is still required. `proof_false`, stage/full-Move/Board-key scope faults and positive-threshold proof consumers were all0. The raw `Other.false_results` field is unobserved (placeholder0); only the three explicitly wrapped sites record answers.

Stage-derived proof is valid only immediately after the matching successful Main GoodCaptures return, before another `next()`; TT/QS/evasion/quiet/killer/counter/bad/none returns were exercised as negative controls with no proof leakage. The observer cross-checks stage against a cleared per-next diagnostic truth marker and full Move/key. Production can use the actual stage predicate without that extra mutable observer Boolean. Full Move identity includes promotion/flags. Main TT duplicates are skipped by GoodCaptures, so the marked move cannot enter same-move singular recursion before the extension consumer. Actual Board legality/check/SEE code is read-only in this scope.

The independent proof is preserved in `../next-search-screen-20261021/see-proof-independent.md`: ordinary attacker/occupancy order is threshold independent; parity of threshold recurrence makes false exits less likely and true exits more likely as threshold decreases. Castle/promotion-helper branches compare a threshold-independent scalar. This applies only to valid current Moves and defined arithmetic; an optimization must retain an explicit **actual consumer threshold<=0** guard and must not widen/retune the baseline multiplication domain. Exact-zero reuse needs no weaker-threshold inference.

## Commands and preservation

`prepare_observer.py`, the three observation diffs/header and `OBSERVER-SOURCE-INPUTS.json` bind actual instrumentation. `run_owned.py` and each `.status.json` retain exact compiler/build/bench/driver argv; `.stdin` files preserve UCI commands; `run_diagnostic.py` records the fixture corpus and normalization. The full threshold configuration, legal history, per-Move predicate digests/boundaries and replay rows remain in original stdout/TSV. All actual process groups closed; owned cleanup executes before evidence hashing/status persistence. No affinity was changed. `FIRST-PRESPAWN-FAILURES.md` preserves the failed approach and bounded repair.

`RESULT.json`, `PARITY.json`, `COMPLETE-OUTSIDE-ORIGINALS.json` and the final manifest bind source/compiler/core/engine/driver/raw results. Baseline source/core/exe originals and all77 current production inputs were rehashed unchanged after the diagnostic. Raw files are original producer outputs; hashes provide integrity, not independent authenticity or remote-publication proof.

Next: root may implement a separate minimal stage-derived proof getter, guarded noisy reuse and exact-zero extension reuse; add focused same-Board threshold-contract cases to the existing SEE unit group. Then freeze a new source, run all existing14 CTests across Release/ASan/TSan, full cold/warm search parity and Windows qualification. Use an uninstrumented calibrated hosted comparison for speed; equal-clock matches remain necessary for strength. Current23 remains the sole launched strength experiment.
