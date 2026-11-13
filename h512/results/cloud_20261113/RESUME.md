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

## Also checked, no source change

- UBSan, then ASan+UBSan, on the 100000-ply test: 95960 checks, 0 failures, no diagnostic. `SANITIZERS.md`.
- Clang 18 codegen of the same refresh change: checksums and column counts match gcc. H1024 cold time dropped in every pair. H512 cold time did not clear the overlap. Numbers are in `REFRESH_BIAS.md`.
- The scorer check now also compares output bucket, both king keys, and the raw sum, and includes the near-bound weights. 520 python rows and 104 engine rows, 0 mismatches. `SCORER_PARITY.md`.
- The phase piece-count lookup is correct under Python precedence (256/256 byte values, 104 packed FENs). It was not changed. `PIECE_COUNT.md`. Do not rebuild the frozen selection or test shards.

## Done: AVX-512 VNNI output sum

`output_sum` uses `vpdpwssd` when the compiler defines `__AVX512VNNI__`. The portable `-march=x86-64-v4` build does not, and its `output_sum` is still `vpmullw` / `vpmaddwd` / `vpaddd`. Numbers, hashes, and the limits of the bench times are in `VNNI.md`. Scalar sum on the local H512 net stays `4558683`. Depth-12, depth-16, and H1024 depth-8 node counts match the madd binary. No Elo claim.

SonarCloud quality gate on pull request 9 passed for the commits before this one (0 new issues). That comment did not ask for a code change.

## Other agents, read after the first resume and not modified

- Correctness: `cursor/forge-correctness-20261113-e6b6` @ `13630f974e4b8e7a18da0c1e40fd4787dcd0a15b`. `forge-combo29/correctness/20261113/RESUME.md`. Capture buffer, UCI position parsing, perft stop, and a zero-node terminal root. It does not edit `nnue_v3`.
- Search strength: `cursor/forge-search-strength-20261113-9558` @ `d970a779acf072910a9a75e8c09b2e2138acda67`. `search_strength/CHECKPOINT.md`. A default-off enhanced-transposition counter. It does not edit `nnue_v3`.
- History index, same revision as above: `cursor/forge-history-index-20261113-712a` @ `b39453901cd47c654f94bb7ec0283fc7c7f0ceb0`.

## Done: refresh wrap, residual PSQT sample, b2 clip

The v3 cache can pass through 33 columns on a legal 32-piece pair (a knight on a2, then the start position) when every column is 1000 and the bias is 700. The intermediate sum is 33700. Wrapping int16 stores 32700, which is the int64 sum. The header no longer says every partial sum stays inside int16. The test requires the lanes to equal `700 + 1000 * pieces`. Piece order was not changed. Numbers: `REFRESH_WRAP.md`.

The same binaries compare the incremental runtime PSQT and the pawn-cache eval with `evaluate_uncached` for 8000 positions (40 castlings, 7 en passant, 71 promotions, 261 null moves, 0 mismatches). No eval code was changed.

`Model.clip` now clamps `b2` to `±131586 / (QA*QB)`, the last multiple whose rounded `QA*QB` value fits in int32. Torch is not installed here, so `clip()` was not executed. The constant check in `test_scorer_parity.py` passed, along with the existing 520-row scorer check.

v4 tests: 101066 checks, 0 failures. VNNI tests: 101115 checks, 0 failures. Walk totals are unchanged from `h512/results/step3/nnue_v3_tests_combo29.log`.

## Next, if this session continues

1. Do not repeat the fused both-perspective kernel unless the measurement is longer than the spread in `APPLY_BOTH.md`.
2. Do not retune the VNNI output kernel on this VM. A Zen 5 ThinLTO/PGO build is the remaining speed question, and it is not this machine. Clang 18 rewrites one of the two unrolled steps back to `vpmaddwd`; see `VNNI.md`.
3. Trainer numerics that need the real shards or a GPU stay blocked. Do not score test set 3. Equal-node games need candidate 3, which is not in this checkout.

Portable flags stay `-march=x86-64-v4` with `-ffp-contract=off`. Do not load an untrusted checkpoint with `torch.load`.
