# Resume: Forge NNUE evaluation, 2026-11-13

Branch: `cursor/forge-nnue-eval-20261113-22cc`, cut from `fable/standalone-h512-20261111` @ `efb2ff960037087299332bc6a44baea69441a17a`. Do not push this work onto `main`, `lock/combo29-20261110` (`16833ecc03b425586f91f4c8834dea8807bf4c22`), or the Fable branch.

## Done in the first checkpoint

`refresh_from_pieces` rebuilds a king-bucket cache entry from `b1` when the diff has more columns than the new position has pieces. Evidence, commands, and the limits of that evidence are in `REFRESH_BIAS.md` in this directory.

Verified here, on synthetic nets only:

- Unit walk matches `h512/results/step3/nnue_v3_tests_combo29.log` (100000 plies, 0 mismatches) plus new far-cache and near-bound checks. 95960 checks, 0 failures.
- Speed-tool checksums and bench nodes match the previous object (depth 12: 309106, depth 16: 21116907, H1024 depth 8: 27556).
- Cold refresh of two positions that share a king bucket uses fewer columns and less time (H512 about 235-255 ns down to 191-199 ns; H1024 about 826-831 ns down to 611-628 ns, pinned).
- Depth-16 search bench time stays inside the baseline's own spread. No Elo claim. No claim that search NPS changed.

## Do not repeat

- H512 phase 1 and phase 2 training arms in `h512/REPORT.md` and `h512/REPORT_PHASE2.md`. Candidate 3 is the net those reports kept. The 1024-unit pilot lost to it on the user's clock (M9, -5.9 Elo).
- Scoring or tuning on test set 3. It was built and left untouched.
- The v2 refresh-from-bias NPS comparison. The history index already records no search-NPS change for that bit. This checkpoint only measured the v3 form, and only the microbench moved.

## Blocked on this machine

- No candidate-3 `.fnn3`, no lock exe, no `.pos` shards, no ROCm/torch, no AMD GPU. `h512/train/train_h512_gpu.py` cannot run.
- A loss or a synthetic-bench delta is not a match. Equal-node games need the user's nets and a match harness that is not here.

## Other agents, revisions actually read

- Repository history index: `cursor/forge-history-index-20261113-712a` @ `b39453901cd47c654f94bb7ec0283fc7c7f0ceb0` (2026-11-13 12:01:17 +0000). Read `docs/history-index/findings/NNUE.md` and the NNUE section of `docs/history-index/HANDOFF.md` from that commit. Their work is an index of reports, not an engine patch. The v2 shortcut note above is from that file.
- Engine correctness (`bc-5fe8fb40-acdb-4ad4-a70c-6afae1dde6b6`) and the Fable-branch investigation (`bc-2d3bd137-243e-4385-9831-aaafe1b19558`) had no published branch name when this note was written. Nothing of theirs was edited.

## Done after the first checkpoint

- Fused both-perspective `apply_changes` was bit-exact and was not kept. The walk-time delta was smaller than the run spread. Numbers: `APPLY_BOTH.md`.
- `centipawns()` is the integer formula `score_net_numpy` uses. `h512/train/test_scorer_parity.py` compares it with `fable_nnue_v3.evaluate` (416 rows, 0 mismatches, 253 negative) and, when given the engine tool, with that tool (104 rows, 0 mismatches). No test-set file was read.
- `as_i32` rejects a `b2` that does not fit in int32. In-range values, including the int32 extremes, keep the previous little-endian bytes. `export_net` no longer casts to int32 before that check. Torch is not installed here, so the export function itself was not executed.

## Next, if this session continues

1. Do not repeat the fused both-perspective kernel unless the measurement is longer than the spread in `APPLY_BOTH.md`.
2. A VNNI output kernel (`__AVX512VNNI__`) is at most the ~25 ns `output_sum` on H512. It will not show up in `bench 16` unless something else changes. Measure `output_sum_ns` only, and keep it only if that number moves and the scalar sum stays `4558683` on the local H512 net.
3. Trainer numerics that need the real shards or a GPU stay blocked. Do not score test set 3.

Portable flags stay `-march=x86-64-v4` with `-ffp-contract=off`. Do not load an untrusted checkpoint with `torch.load`.
