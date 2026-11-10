# fable_cpu_speed: bit-exact h256 speed lane and sanitizer / determinism audit of combo29

Job "Fable 4 CPU", 2026-11-10, branch `fable52-cpu-20261110`, based on `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`. CPU only, logical CPUs 0-6 and 12-14. Times are Europe/Vienna.

**Read next:** `DONE.md` (verdict per item with its evidence logs and their MD5), `STATUS.md` (state, what went wrong, how to resume), `PREREG.md` (counts and settings written before the runs).

## The result in five lines

1. **No speed candidate reached the +2 % line (C4: NO WIN).** Four bit-exact patches were built and timed. Two read as small gains: `FORGE_SPD_NNUE_FUSE_EVAL` **+0.93 %** in the pre-registered screening (+1.46 % in one repeat) and `FORGE_SPD_PREFETCH_PICK` **+0.72 %**. The other two were slower than the lock (-1.53 % and -4.42 %).
2. **The audit found no defect in the lock (C5).** ASan and UBSan full bench, 13,000 determinism comparisons and the table stress all passed their full planned counts. **ThreadSanitizer is BLOCKED:** neither installed compiler supports it on Windows.
3. **My rebuild of the lock source is the lock:** all 13 pins match and its code and data bytes equal the lock exe's (C1).
4. **One required gate could not be run as written.** The lock exe has no static-eval command, so "12,000-position static-eval parity against the lock" is **BLOCKED (unobservable on the release exe)**. What I ran instead is named for what it is and is not a substitute: a source-level harness comparison, and for the two small gains a release search comparison against the real lock exe.
5. **The bug hunt found nothing to report as a defect.** See the last section for what it covered.

## C4 in detail

Every candidate is one patch against the lock commit, behind a build flag that defaults to 0. With the flag at 0, each build has the same code and data bytes as my lock rebuild.

| Candidate (flag) | What it does | Pins, flag 0 and on | Harness, 48,000 comparisons | Screening vs lock (median of 12 pairs; min to max) | Outcome |
|---|---|---|---|---|---|
| `FORGE_SPD_NNUE_FUSE_EVAL=1` | the last accumulator update and the output layer run as one pass, so the output layer's additions overlap the update's memory traffic | 26 of 26 | 0 differences | **+0.93 %** (-0.99 to +4.60); repeat +1.46 % (-1.62 to +6.13) | stopped: below +2 % |
| `FORGE_SPD_PREFETCH_PICK=1` | the table prefetch is issued as soon as a move has passed the legality test, before the pruning tests, so the load has more time to arrive | 26 of 26 | 0 differences (the harness does not exercise this patch; see the release rows below) | **+0.72 %** (-2.17 to +4.57) | stopped: below +2 % |
| `FORGE_SPD_EVAL_PIPELINE=2` | hand-crafted part first, with the weight columns prefetched before it starts | 26 of 26 | 0 differences | -1.53 % (-3.47 to +1.12) | stopped: slower |
| `FORGE_SPD_NNUE_WPREFETCH=16` | prefetch the weight columns when a move is recorded | 26 of 26 | 0 differences | -4.42 % (-9.18 to -2.21) | stopped: slower |
| Lock against lock (noise floor) | | | | -0.30 % (-5.19 to +7.68), 11 valid pairs | |

How to read the timing: it is a **screening** on a PC that was doing other work (the GPU feeder on CPUs 7-11, two foreign processes on CPU 15). One arm is one new process running `bench 20` on CPU 12 with its sibling CPU 13 idle; each arm uses a fresh copy of the exe file; the metric is CPU cycles per node. A single lock-against-lock pair can read anywhere from -5 % to +8 %, so only the median of many pairs means anything, and its uncertainty here is about one percentage point. QA's quiet ABBA is the real test.

About `NNUE_FUSE_EVAL`: two independent 12-pair runs both read positive, so a real gain of about 1 % is likely, and it is the only change here that removed time instead of adding it. The idea is not new: Engine QA's O2 report lists "fusing update and evaluate into one pass" as not done and expected to be small (`DUPCHECK.md`); I found no earlier build of it. It did not reach the pre-registered line, so I stopped developing it and did not build on it. Its evidence set is complete, including an extra release comparison against the real lock exe (12,000 positions, `go depth 12`, net on and off, flag 0 and 1: 48,000 of 48,000 rows equal). Whether +1 % is worth a slot in the quiet ABBA is QA's call.

About `PREFETCH_PICK`: 11 of its 12 pairs read positive. It continues what `FORGE_SPD_PREFETCH_EARLY` started (that switch moved the prefetch from after `make_move` to before it; this one moves it above the pruning tests). Its release comparison against the real lock exe is RELROWS_PICK.

The two small gains touch different code (`nnue.cpp` and the evaluation call for one, the two move loops for the other), so they could be combined. I did not build a combination: this job allows one change per patch and no stacking. A combined build would be a new item for its owner, with its own pins and timing.

Dropped before any code, with the measurement that decided it:

- **Explicit AVX-512 for the update loops:** the lock's machine code is already 16 straight-line 512-bit groups per side (`evidence/logs/nnue_update_codegen_excerpt.log`).
- **64-byte alignment of the weight table:** it already starts on a 64-byte line in every launch (`probe_w1_alignment.log`). This is a property of the allocator, not of the code.
- **A table-access change:** clusters are 64 bytes and aligned, the prefetch is issued before `make_move` for almost every move (it covers captures, promotions and castling), and large pages are closed work. Nothing new was left to try.

What the prefetch results say: fetching weight columns early costs more than it saves, wherever it is placed; the accumulator update is limited by how much memory it moves, not by when the fetch starts. Fetching the single table cluster earlier does help a little, because there one load is on the critical path.

## C3: where the time goes (net on, one thread, `bench 22`)

Hand-crafted evaluation 20.9 %, make/unmake and legality 17.9 %, move ordering 16.6 %, search own code 15.6 %, accumulator update 8.3 %, move generation 7.3 %, transposition table 7.3 %, output layer 5.4 %, other 0.7 %, accumulator refresh 0.0 %. Two valid runs, 20,265 samples, by instruction-pointer sampling. Details and the second measurement under load: `PROFILE.md`.

## C5 in detail

| Check | Planned | Result |
|---|---|---|
| Sanitizer set-up: 6 planted faults and clean code, same compiler and flags as the engine builds | 8 builds and runs | all as expected |
| ASan full bench (d11/13/16/20/22, net on and off) | 10 | 10 complete, node counts equal the pins, no report |
| UBSan full bench | 10 | 10 complete, node counts equal the pins, no report |
| TSan, Threads 2-9 | - | **BLOCKED**: `unsupported option '-fsanitize=thread' for target 'x86_64-w64-windows-gnu'` |
| Determinism, Threads 1, lock exe, 2,000 positions, `go depth 13`, net on and off: cold x3, warm x2, reset check | 13,000 comparisons | 13,000 equal |
| Table stress on the lock exe (Hash 1 to 1024, Clear Hash, ucinewgame, net off/on), two runs, net on and off | 480 comparisons | 480 equal |
| Table stress on the ASan build | 240 searches | complete, no report |
| Not TSan, extra: Threads 2-9 fixed-node searches on the ASan build, the UBSan build and the lock exe | 600 searches | complete, every best move legal, no report |

The multi-thread searches show no crash, no illegal move and no memory error. They say nothing about data races; only ThreadSanitizer could, and it is not available here.

## Not run

- **C6** (binpack-to-FEN dumper): NOT RUN. It must be tested against the trainer's own reader, which I know only inside the protected training folder; no other reader was found in the permitted folders I searched.
- **C7** (HalfKA SIMD path): NOT RUN. The lock branch holds no HalfKA code and no s135 net, no local copy was found, and fetching another branch is outside the approved network exception.
- **Release row comparison for the two slower candidates:** not run, as pre-registered (only for a candidate at or above +2 %; I ran it for the two small gains as an extra).

## Limits you should know

- **DUPCHECK is incomplete by construction.** Git history other than the one cloned commit could not be fetched, so prior work that exists only there is UNVERIFIED (`DUPCHECK.md`).
- **The harness is a test binary.** It shows that two source trees evaluate alike over 12,000 positions and their children; it is not a statement about what a release exe exposes.
- **Disk.** DISK_LINE Nothing was deleted. The largest item is 156 exe copies of 2 MiB each from the six timing runs (`out\timing\`); they can go once nobody wants to re-inspect a timing.
- **CPU use.** Everything of mine ran inside mask 0x707F at BelowNormal priority; the logger never saw one of my processes outside it. Each tool shell exists for a few milliseconds before it pins itself. From 16:38 I used CPUs 0 and 2 for long search runs without repeating the three-sample free check first; both had shown 6 to 27 % outside load in earlier samples.

## Bug hunt (added on Couns's request, about 25 minutes)

Done 16:28 to 16:52, on the lock source and the lock exe. **No defect found.**

| Part | Size | Result |
|---|---|---|
| UCI edge-case battery on the lock exe, the ASan build, the UBSan build and a hardened build: search limits at and beyond their bounds, stop and ponder sequences, commands sent during a search, closed stdin, mated and stalemated roots, 16 odd FENs, games of 1,600 and 8,000 plies, option values out of range, perft and bench edge values | 130 cases, 520 runs | no crash, no hang, no illegal move, no sanitizer report |
| `Book File` pointed at files that are not books; move lists in odd notations (lock exe, ASan build) | 15 cases, 30 runs | no crash; every bad input refused or harmless |
| Hardened build = the engine's own assertions switched on, checked indexing of standard containers, ASan and UBSan together: full bench | 10 runs | node counts equal the pins, no assertion, no report |
| Hardened build: Threads 2-9 fixed-node searches | 200 searches | complete, legal best moves, no report |
| Hardened build against the lock exe: 2,000 positions at depth 13 and the other 10,000 at depth 10, net on and off | 24,000 row comparisons | all equal, nothing on stderr |
| Answer time of clocked searches, measured from outside (lock exe, one thread) | 380 searches, 19 limits | inside the budget, except by 0.1 to 0.4 ms at 1 ms budgets |
| Code reading: UCI parsing, root search driver and time allocation, FEN parser, table structures, book move decoding | | nothing found |

Observations that are not defects, for the owner:

1. `go searchmoves` with no legal move in its list answers `bestmove 0000` after the line "searchmoves restriction has no legal root moves". That is what the code intends. Without a depth limit it first prints 64 empty info lines.
2. `Book File` accepts any readable file as a book, because the book format has no signature (the 2 MiB lock exe "loads" as 130,784 entries). Decoded moves are matched against the legal move list, so a wrong file cannot make the engine play an illegal move; it only finds no book moves.
3. With `movestogo 1` the engine may spend up to 79 % of the remaining clock (792 ms of 1,000).
4. In `Searcher::search` the stop flag is read, set to wind down the helper threads, and then restored. A stop that arrives inside that window is overwritten. I found no effect: the search has ended by then and the UCI layer keeps its own stop flag.
5. The weight table's 64-byte alignment is a property of the allocator, not of the code (see C4).

One flag in `bughunt_uci_battery.log` is my test's fault: the case "Threads change during search" waits for a third best move, and the engine correctly gave two. The six `NULLMOVE` flags are observation 1.

Logs: `bughunt_uci_battery.log`, `bughunt_uci_battery_hard.log`, `bughunt_book_and_moves.log`, `bughunt_latency_threads1.log`, `san_build_hard.log`, `san_bench_hard.log`, `mt_hard.log`, `cmp_lock_vs_hard_cold_on.log`, `cmp_lock_vs_hard_cold_off.log`, the six `cmp_lock_exe_vs_hardened_build_wide_*.log`.

## Folder map

| Path | Content |
|---|---|
| `patches/` | the four candidate patches (`git apply` on the lock commit) |
| `tools/` | pinned launcher, lock-recipe build, pin checker, row runner and comparer, sampler, timing, sanitizer and harness scripts, manifest writer |
| `tests/` | evaluation harness, sanitizer fault fixtures, fake engine for checker self-tests, the 12,000 positions |
| `evidence/logs/` | every log a verdict rests on |
| `PREREG.md`, `DUPCHECK.md`, `PROFILE.md`, `STATUS.md`, `UTILIZATION.log`, `DONE.md`, `MANIFEST.tsv` | reports |

On the PC only: `D:\forge_jobs_20261110\fable4cpu\out\` (builds, exe copies, row files, raw profile data).

## What is next

- QA: decide whether `NNUE_FUSE_EVAL` and `PREFETCH_PICK` get a quiet ABBA slot, alone or as one combined build made by their owner.
- Code Review: the four patches have had my own review only (`REVIEW_LOG.md`); no independent review took place because subagents were ruled out.
- Owner: decide whether the 156 timing copies may be deleted.
- If a TSan verdict matters, it needs a Linux build of the engine; nothing on this PC can give one within the CPU rules.
