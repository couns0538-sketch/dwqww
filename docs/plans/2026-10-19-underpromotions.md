# Unapplied underpromotion candidate

Base source: `166ebac895ef5f304c99deaa8c55dd070b941c1d`. Repository source was only read. No patch was applied, and no compilation, CTest, UCI driver, engine, game or benchmark was run. Source-derived expected outcomes below are unverified until the frozen experiment has finished.

## Scope and implementation

The main picker obtains promotions through captures-only/noisy generation, then excludes all promotions from its quiet list. That generator currently emits queen promotions alone. Remove its R/B/N guard, retaining the existing Q/R/B/N ordering. Both ordinary captures and all quiet promotions remain noisy; legal filtering and move ordering are unchanged. This also exposes all promotion choices to quiescence. The header comment is updated to describe that contract. No SEE, TT rule-50, search parameter or evaluation change is included.

## Apply and validate tests first, after the frozen SPRT audit

1. Preserve the frozen SPRT source, binaries, inputs, protocol, logs and decision. Do not apply either patch or start validation until that run and its statistical audit have concluded. Use the existing isolated checkout; do not create a worktree.
2. From `/workspace/dwqww`, inspect `underpromotions-tests.patch`, then apply only it with `git apply /workspace/.cloud-setup/experiments/underpromotions-tests.patch`. Rebuild the existing relevant Linux targets in the external build directory and run `forge_tests` plus the UCI driver against that uncorrected engine. Preserve commands, exit codes and logs. The board noisy-generation counts, searched underpromotion PV checks, winning-rook score and UCI assertion must fail for the missing promotions, not a parse/build/runtime error. The previous queen-only expectation is intentionally replaced by the four-choice contract.
3. Apply only `underpromotions-implementation.patch`. Rebuild the same targets and rerun the failing checks; then run all four required CTest suites. The root suite already contains stalemate, mate, rule-50 and ponder/deadline regressions. Keep passed/failed/unrun outcomes distinct.
4. Once Linux correctness passes, create a separate immutable candidate/checkpoint and reproduce Windows Release build/core/UCI/ponder checks with the established flags and floating-point contract. Do not overwrite the existing release or accepted binaries. Any search/performance or strength experiment needs new frozen source, binaries, openings and stopping rule; changed nodes are expected from a move-completeness correction. No Elo or native Ryzen claim follows from these tests.

## Regression intent

- Board: white `1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1` and black `4k3/8/8/8/8/8/p7/1R2K3 b - - 0 1` each provide four legal quiet and four legal capture promotions, one per Q/R/B/N type. Exact per-type counts detect omissions and duplicates.
- Search: `8/k1P5/2K5/8/8/8/8/8 w - - 0 1` and its rank/color mirror. Each restricted Q/R/B/N root search must visit a child and return the allowed move as its PV head, with the hash cleared between choices. This rejects the old fallback-only success. Queen promotion stalemates (score zero); rook promotion leaves a legal king move and material advantage (score greater than 100 cp). Bare bishop/knight draws still require an actual searched PV. After clearing the hash again and removing the root restriction, each color must choose its rook promotion at depth one, with that move at the PV head and score greater than 100 cp. This adds ordinary-play choice coverage beyond forced selection; its expected move remains to be confirmed in the future red/green run.
- Process UCI: the existing fallback-only knight assertion is replaced by the rook fixture at depth one, requiring the selected move, an actual depth-one PV containing it, and a positive centipawn score greater than 100.

`underpromotions.patch` is the combined review artifact. Apply either that combined patch OR the two split patches, never both. The split artifacts exist to preserve the tests-first sequence.

## Static review completed

All three patch artifacts pass non-mutating `git apply --check` against the base checkout. `git diff --exit-code` and tracked-file status confirm repository source remains unchanged. A second read-only reviewer confirmed fixture legality, both-color promotion counts, correct mirrored root moves, queen stalemate versus the rook's legal Ka6/Ka3 reply, and that PV plus child-node assertions reject fallback-only results. These checks do not substitute for the required future red/green build and runtime validation.
