# PREREG: planned counts and settings, written before the runs

Job fable4cpu, branch `fable52-cpu-20261110`, base `16833ecc03b425586f91f4c8834dea8807bf4c22`. A check passes only when its full planned count ran. A partial count is INCOMPLETE. A timeout, missing or cut-off output, or a non-zero exit is a failure, not "zero mismatches".

Times are Vienna. The PC's UTC clock runs 25,159 s ahead of github.com's Date header (measured at the clone), so Vienna = PC UTC - 25,159 s + 1 h.

## Fixed inputs

| Input | Identity |
|---|---|
| Lock exe (copy in `out\base\combo29_lock.exe`) | MD5 `c0051c99695f48bf93272d96fe7548c3`, SHA256 `e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e` |
| Source | clone at `16833ecc`, folder `forge-combo29/`; source manifest SHA256 `3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645` (equals the lock receipt) |
| Position file | `tests/fens_12k_v2.txt`, 12,000 positions, SHA256 `c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265` |
| Compiler | llvm-mingw clang 23.1.5, `clang++.exe` SHA256 `d05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970` |
| Net | the s198 h256 net built into the source (`src/nnue_weights.inc`); "net off" = `setoption name UseNNUE value false` |

## Pins (every build): planned 13

bench d11/13/16/20/22 net on = 312866 / 862329 / 3024920 / 12389307 / 34048354; net off = 375354 / 907205 / 2448617 / 13573040 / 24506465; perft startpos 5 = 4865609; kiwipete 4 = 4085603, 5 = 193690690. Threads 1; `bench` uses its own 16 MB table.

## C3 profile

Target: my lock-recipe build `c29ctl`. Workload `bench 22`, net on, single thread, CPU 12 with CPU 13 idle, two runs. Method: instruction-pointer samples of my own engine process at even steps of the thread's cycle counter, resolved with `llvm-symbolizer` including inlined code. Each sample goes to exactly one category, with this map fixed before the run. Rule added at 16:05, before the first profile run: the frames of a sample are walked from the innermost outwards and the first frame that names a listed function, or that was written in one of the engine's `.cpp` files, decides. Helper code inlined from headers (standard library, bit helpers, accessors) and the small helpers of `nnue.cpp` are thereby charged to the function they were inlined into. Samples outside the engine image or without a resolved frame are "Other".

| Category | Source functions |
|---|---|
| NNUE accumulator update | `nnue::update`, `nnue::dirty_pieces`, `Worker::record_move`, `Worker::record_null_move`, `add_feature`/`sub_feature` reached from `update` |
| NNUE accumulator refresh | `nnue::refresh`, `add_feature` reached from `refresh` |
| NNUE output layer | `nnue::evaluate` |
| Hand-crafted evaluation | everything in `eval.cpp`, `eval_params.cpp` |
| Transposition table | `TranspositionTable::*` |
| Move generation | `Board::generate_*`, `MovePicker::generate_*` |
| Move ordering | other `MovePicker::*`, sort helpers, history-score helpers |
| Make/unmake and legality | other `Board::*`, `bitboard.cpp` |
| Search own code | `Worker::*` not listed above, `Searcher::*` |
| Other | everything else, including unresolved addresses and runtime library code |

## C4 per candidate

- Pins: 13 with the flag at 0 and 13 with the flag at 1 = 26 planned.
- Harness comparison (separate evidence, see R2 in STATUS.md): 12,000 positions per configuration; configurations = flag 0 / flag 1 x net on / net off; 48,000 planned root comparisons, 0 differences required. Child positions are counted separately. A deliberately wrong update must be reported as different before any PASS is trusted. Amended at 16:20, before the first harness run: the planted fault is a wrong weight column in the capture update (the mover's column is subtracted twice and the captured piece's column not at all), in a private source copy `out\work\MUTANT_CAPTURE_COLUMN\b`. A mere change of the order of additions is not a valid planted fault here: every weight is a multiple of 1/4096 and the sums stay far below 2^24 of those units, so the float sums are exact and any order gives the same bits.
- Screening: one arm = one new process: `uci`, `isready`, `bench 20`, `quit` (net on, single thread, bench's own 16 MB table). Valid only if exit 0, nodes = 12,389,307 and CPU time / wall time >= 0.97. A = lock exe, B = candidate with the flag at 1, a fresh copy of the exe file for every arm, CPU 12 with CPU 13 idle, order A-B for odd pairs and B-A for even pairs, 1 warm-up pair discarded, 12 measured pairs. Metric: CPU cycles of the process per node; pair value = cycles(A) / cycles(B) - 1; result = median of the 12 pair values, with minimum and maximum. Null: lock against lock, same method, 12 pairs. Fewer than 10 valid pairs = INCONCLUSIVE. Below +2.0 % the candidate is stopped.
- Release comparison for a candidate at or above +2.0 %: 12,000 positions, `ucinewgame` before each, `go depth 12`, Threads 1, Hash 16; rows (depth, score, nodes, best move) against the lock exe; flag 0 / flag 1 x net on / net off = 48,000 planned.

## C5

- Setup: 7 sanitizer fault fixtures (3 ASan faults, 3 UBSan faults, 1 clean); instrumented exes must contain sanitizer symbols; checker self-tests with bad fixtures (wrong value, no output, timeout, non-zero exit, sanitizer report).
- ASan full bench: 10 runs (d11/13/16/20/22, net on and net off). PASS = 10 of 10 complete, node counts equal the pins, exit 0, no report. Build: lock switches, `-O1 -g -march=znver5 -ffp-contract=off -fno-fast-math -fsanitize=address`, no LTO, no PGO.
- UBSan full bench: the same 10 runs with `-fsanitize=undefined`; every report is listed.
- TSan, Threads 2-9: the compiler refuses `-fsanitize=thread` for this target; the refusal is logged; sub-item BLOCKED. Not a substitute: Threads 2..9 x 25 positions (positions 1-25) x `go nodes 300000`, Hash 64, on the ASan build, the UBSan build and the lock exe = 600 searches; checks: exit 0, a best move that is in the position's legal move list, no report.
- Determinism, Threads 1, lock exe, positions 1-2000, `go depth 13`, Hash 16, net on and net off:
  - cold (`ucinewgame` and `isready` before every position): 3 runs in 3 new processes; run 2 and run 3 against run 1 = 4,000 comparisons per net mode, 8,000 in all;
  - warm (one `ucinewgame` at the start, then no reset): 2 runs in 2 new processes = 2,000 comparisons per net mode, 4,000 in all;
  - reset check (positions 1-500: search, `ucinewgame`, search again, in one process) = 500 comparisons per net mode, 1,000 in all.
  - A row is depth, score, nodes, best move. Cold and warm rows are not compared with each other.
- Table stress: fixed script of 60 steps; step i applies operation i mod 12 from the list [Hash 1, Hash 2, Hash 16, Clear Hash, Hash 64, ucinewgame, Hash 256, Hash 1, Clear Hash + ucinewgame, Hash 1024 (ASan build: 256), Hash 3, UseNNUE false then true] and then searches 4 positions (positions 2001-2240 in order) with `go nodes 50000` = 240 searches per run. Lock exe: two runs in two new processes must give identical rows, 240 comparisons with the net on and 240 with the net off (the last operation is skipped in the net-off runs). ASan build: one run, no report, exit 0.
