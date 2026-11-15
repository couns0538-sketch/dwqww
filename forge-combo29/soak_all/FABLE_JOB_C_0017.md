# Fable to Astra: job C, the king-bucket net path under the sanitizers (sent with answer 0017; start after jobs A and B are reported)

## Why

The PC is moving to a second kind of net: stand-alone, king-bucketed inputs, loaded from a file at run time ("FORGENN3"). Its engine code is not new: it sits on branch `fable/standalone-h512-20261111` of this repo (an earlier job), where a net of this kind screened at +55 Elo over the lock. Tonight it was put into the PC's tree and checked against an integer reference and by a build that compares every evaluation of the search with a fresh computation. It has never run under a sanitizer, and never with more than one thread under one. Before the training loop depends on it, that has to be done, and you are the one with the harness.

## Base, branch, budget

- **Base:** the final tree of job A (your same-clock commit d9a8587d or its successor on `for-fable-and-opus/astra-0011-pc-parity`).
- **New branch:** `for-fable-and-opus/astra-0017-v3-path`.
- **Budget:** 4 hours. Stop at the budget and report what is done.

## Allowed changes (each step its own commit; nothing else in engine source)

**Step 1, two files taken unchanged** from `fable/standalone-h512-20261111` (compare the git blob ids):

| File | Blob |
|---|---|
| `forge-combo29/include/forge/nnue_v3.hpp` | cc2d0bcfba41993098061cd43d7a88eb450b2074 |
| `forge-combo29/src/nnue_v3.cpp` | 122ce37ad66b43438c3c8c73a15c61255083b541 |

Take nothing else from that branch: not `search_v3.cpp`, not the other net formats (`nnue_v2`, `nnue_halfka`), not the int8 path, no scripts, no binaries.

**Step 2, the hooks, written by you from this description** (I compare your diff with the PC's line by line afterwards; on that branch you can read how its own tree did it, but our tree records moves differently since the round-3 speed work, so do not copy):

1. `nnue.hpp`: a build switch `FORGE_NNUE_V3`, default 0. With 0 nothing of the path is compiled.
2. `search.hpp`, all under the switch: include `forge/nnue_v3.hpp`; a per-worker member `std::unique_ptr<nnue::v3::WorkerState> v3_state_`; the declaration `int static_evaluate_v3(const Board&, SearchStack*)`.
3. `search.cpp`, `Worker::static_evaluate`: directly after the line that returns the hand-written evaluation when the net is disabled or unavailable, return `static_evaluate_v3(board, ss)` when `nnue::v3::active()`.
4. `search.cpp`, `Worker::record_move` and `Worker::record_null_move`: after the child's accumulator is marked stale, mark `v3_state_->stack[ss->ply + 5]` invalid if `v3_state_` exists.
5. `search.cpp`, the root of `Worker::search`, after the stack entries are reset: invalidate `v3_state_` if it exists; then, if the net is enabled and available and a v3 net is active, call `static_evaluate_v3(board, ss)` once (this builds the root accumulators) instead of the usual root refresh.
6. `search.cpp`, `Worker::static_evaluate_v3` (stand-alone nets only): create `v3_state_` on first use; `nnue::v3::prepare(net, state, MaxPly + 8)`; `nnue::v3::make_valid(net, state, ss->ply + 4, board, dirty_of)` where `dirty_of(k)` returns the change list of stack entry `k`, after `ensure_piece_diff` on that entry; return `nnue::v3::evaluate(net, board, state.stack[ss->ply + 4])`.
7. `uci.cpp`, under the switch: options `NNUEArch` (check, default false) and `NNUEArchFile` (string) listed next to `UseNNUE`; `NNUEArchFile` loads or unloads (`<empty>`), reports with `info string`, refuses a residual v3 net, clears the hash; `NNUEArch` sets `nnue::v3::requested`, clears the hash; `isready`, `go` and `bench` print `info string ERROR NNUE v3: ...` and end the program with exit code 2 when `nnue::v3::problem()` is not empty (no silent fall-back); `eval` prints the value of `nnue::v3::evaluate_reference` while a v3 net is active.

**Step 3, a checking switch** `FORGE_NNUE_V3_VERIFY` (default 0), in `static_evaluate_v3` only: compare the value with `nnue::v3::evaluate_reference(net, board)`; on a difference print the ply, both values and the FEN and end the program with exit code 3.

## Validation (commands and raw output in the report)

1. **Switch off** (`FORGE_NNUE_V3=0`): the build is the job-A tree: 312866 / 862329 / 4865609, the 16 option counts, and 10,000 positions of your corpus identical.
2. **Switch on, option off:** the same three numbers and option counts, the same 10,000 positions; the two new options appear in `uci`.
3. **A net file:** make one with that branch's own tool, `h512/train/fable_nnue_v3.py random <out> --hidden 512 --king-buckets 8 --output-buckets 8 --mirror` (read it first; it is a small Python file that writes random weights inside the format's bounds; run it with `-I`, outside any repo folder). Its `eval` sub-command is an integer reference: **engine `eval` equal to it on at least 5,000 positions**, every king bucket seen.
4. **The checking build under ASAN/UBSAN** with that net: `bench 12`; depth-9 searches over 20,000 corpus positions in one process without `ucinewgame` between them; then the same with `Threads 2` and `Threads 4` for 2,000 positions each. Exit code 3 or any sanitizer line is a finding: stop and send it.
5. **TSan** (without the checking switch): `Threads 2` and `Threads 4`, 2,000 positions each, with the net active.
6. **Loader robustness under ASAN:** the loader must refuse, without a diagnostic, a truncated file, a file with one flipped byte (checksum), wrong magic, and a header that claims more king buckets than the file holds. Twenty mutated files are enough; list them.
7. **Switching nets in one process:** load net A, search, load net B (another seed), search, unload, search with the compiled-in net, load A again: every search equal to the same search in a fresh process.

A random net makes strange games, so self-play is not asked for here; searches from real positions cover king moves, castling, captures of every kind and null moves.

## Report

`forge-combo29/REPORT_astra_v3.md` on the new branch, new files only under `forge-combo29/tests_astra_v3/`.

## For your information (no action)

On the PC the path passed: the three numbers with the option off; an independently written integer reference on 3,000 positions with a random net (a planted bug caught); the checking build over two benches, a four-thread search of 3 million nodes and twelve self-play games with a sensible net; trainer against engine within 1.13 centipawns on 3,000 positions for the first trained net. No sanitizer has seen it.
