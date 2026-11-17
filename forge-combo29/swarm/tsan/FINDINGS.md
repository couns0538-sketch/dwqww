# ThreadSanitizer run at Threads 4 — races only, no timings

## The flag line

`g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`, engine `forge-combo29` at audit base `6b98f217`, CMake 3.28.3.
Configure:

```
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 \
      -DCMAKE_CXX_FLAGS="-fsanitize=thread -fno-omit-frame-pointer -g \
        -ffile-prefix-map=<source tree>=/src -ffile-prefix-map=<build dir>=/build" \
      -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=thread"
```

which expands to:

```
CXX_FLAGS = -fsanitize=thread -fno-omit-frame-pointer -g -ffile-prefix-map=<src>=/src -ffile-prefix-map=<build>=/build -O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4
LINK      = /usr/bin/g++ -fsanitize=thread -fno-omit-frame-pointer -g -O3 -DNDEBUG -fsanitize=thread <objs> -o forge
```

TSan runtime `libtsan.so.2` from `libtsan2 14.2.0-4ubuntu2~24.04.1`, 21 undefined `__tsan_*` symbols,
`ldd` resolves `libtsan.so.2 => /lib/x86_64-linux-gnu/libtsan.so.2`.

**Engine binary sha256 `889a9b467d77a8210e38f981ef8c00d1f77e8f8b4faaf9ae19406373c0751cfa`.**

**On reproducibility, because a hash that moves is not a hash.** The obvious flag set (`-fsanitize=thread
-fno-omit-frame-pointer -g`) produces a binary whose sha256 **changes with the checkout path and the build
directory**, because `-g` embeds both. Verified: the same source built in two build directories under the same
checkout gave `21189c77…` and `bbe13ccc…`; the same source in a different checkout gave `df59381e…`. **So the
two `-ffile-prefix-map` flags are part of the flag line, not a convenience** — with them the build is
byte-reproducible across paths (two builds of the same tree in different directories both produce
`889a9b46…`, and the mutant builds below reproduce identically). The quoted hash is the reproducible one.

**clang 18 cannot link a sanitized binary on this VM and was not used.** `/usr/bin/clang++ -fsanitize=thread`
fails during CMake's compiler probe with:

```
ld: cannot find /usr/lib/llvm-18/lib/clang/18/lib/linux/libtsan-x86_64.a: No such file or directory
ld: cannot find /usr/lib/llvm-18/lib/clang/18/lib/linux/libtsan_cxx-x86_64.a: No such file or directory
ld: cannot find -lstdc++: No such file or directory
```

TSan **was** available through g++ 13.3.0, so nothing was substituted: the requested instrument is the one
that ran.

**Result: 147 driven searches at `Threads 4`, zero ThreadSanitizer reports of any kind, in processes whose
exit was observed.**

## 0. The trap in this seat's own driver, and the fix

The brief warns that **a sanitizer which reports at exit cannot be read to `bestmove`**. This seat's first
driver had exactly that bug: `close()` sent `quit` then called `wait()` **without reading the pipe again**, so
anything written after `quit` was lost. The first clean run was produced that way and has been **discarded and
replaced**, not relabelled.

The bug was not hypothetical. On the planted-race build, the same driver, the child prints *after* `quit`:

```
ThreadSanitizer: reported 25 warnings
```

and exits **66**. The old driver read `bestmove`, sent `quit`, and never saw either. The fixed driver drains
stdout to EOF **before** reaping and records `drained_to_eof` and the real `exit_code`.

`evidence/drain_selftest.log` proves the fix and the failure: a fake engine that emits a race report only on
`quit` is caught by the fixed driver (**1 report**) and missed by a deliberately naive driver (**0 reports**),
`DRAIN_SELFTEST_PASS`.

Consequence for the result: **every clean row in `evidence/exit_observation.json` reports `exit_code 0` with
`post_quit_lines 0`** (`EXIT_OBSERVED_FOR_ALL`). The process was read until it closed its own stdout and then
exited successfully. A build that hid a race exits **66**, as both planted builds do — so exit status is an
independent second signal that agrees with the empty race count.

## 1. The clean negative

| Case | What it drives | Runs | Answered | Node counts |
| --- | --- | ---: | ---: | --- |
| A | `go depth 12`, `ucinewgame` between every search | 40 | 40/40 | 0 – 9,590,202 |
| B | `go nodes 200000`, `ucinewgame` between every search | 40 | 40/40 | 0 – 198,762 |
| C | `setoption Hash` mid-session, search before and after | 20 | 20/20 | 8,739 – 231,394 |
| D | `Clear Hash` between searches | 20 | 20/20 | 2,965 – 148,683 |
| E | MultiPV 4 (control: documented single-threaded) | 10 | 10/10 | 4,903 – 129,921 |
| F | Drawn-root bail, KvK (control: thread-invariant) | 1 | 1/1 | 0 (by design) |
| G | `go infinite` then `stop` with 4 workers live | 8 | 8/8 | n/a (stopped) |
| H | `setoption Threads` 1/4/2/8 mid-session | 8 | 8/8 | 28,720 – 262,932 |

147 searches, all answering with a `bestmove` (`evidence/tsan_run.json`, transcript
`evidence/tsan_run.rawlog`). The case-A maximum of 9,590,202 is one position — `Q6k/8/7P/8/5p2/8/5K2/8 b`,
which searched to `seldepth 29` and reported `mate -6` — not a typo and not a parsing artifact. The same
position reached 2.6M nodes on an earlier build of the same source, which is the Threads-4 node-count
instability quantified in §5, not anything about the sanitizer. The transcript was scanned for text beyond the marker this seat expected —
`ThreadSanitizer`, `WARNING`, `SEGV`, `data race`, `SUMMARY`, `DEADLYSIGNAL`, `==…==ERROR` — **every count 0**.
No suppression file exists on the host and none was set; the only `TSAN_OPTIONS` were
`halt_on_error=0 history_size=4`, chosen so a race would be *printed and the run continued* rather than
aborting the search.

**Classification: there are no reports to classify.** No race on a search table, none on a counter, none on
initialisation, none benign-looking. The rest of this file is why the empty table means something.

## 2. Proof the runner is live — three separate proofs

**(a) Two threads, one global, off the search path.** A `plantrace` command starts two `std::thread`s that
`++` a file-scope `unsigned long` with no synchronisation. TSan reports it **and names the object**:
`Location is global '(anonymous namespace)::g_planted_counter' of size 8 at 0x55aec4345820`
(`evidence/planted_a_global.txt`, mutant sha256 `b065465d…`). Proves TSan is linked, running and printing.

**(b) The unsynchronised increment on the engine's OWN search threads.** This is the proof that matters, since
(a) only shows we can make a race ourselves. A `++` was planted inside `Worker::should_stop()` — the path the
main worker and every helper traverse on every node check. One `go depth 12` at `Threads 4` then produced
**13–24 race reports** (count varies with interleaving; the *report* is stable) at that site, with the stack
naming the real helper threads:

```
WARNING: ThreadSanitizer: data race
  Read of size 8 ... by thread T1:
    #0 forge::Worker::should_stop()  /src/src/search.cpp:1298
    #1 forge::Worker::search(Board&, SearchStack*, int, int, int, bool)  /src/src/search.cpp
    #2 forge::Worker::search(Board, SearchLimits const&, bool, const std::vector<Worker*>&)
    #3 operator()  /src/src/search.cpp            <- the Searcher::search helper lambda
```

(`evidence/planted_b_hotpath.txt`, mutant sha256 `07282fb8…`.) Frame `#3` is the helper-thread launch in
`Searcher::search`. **TSan therefore observed the engine's actual worker threads running the actual search
body** — the exact population the clean negative is about. Both planted builds are separate trees and
separate binaries; the engine under test has no such edit.

**(c) The 4 threads are real, sampled from the OS.** `Threads 4` peaks at **6 OS threads** during a search
(`/proc/<pid>/status` `Threads:`, sampled every 10 ms: `[1, 3, 4, 5, 6]`). MultiPV 4 peaks at **3**, the same
as `Threads 1` — confirming, in the same instrument, that MultiPV really runs single-threaded, which is what
makes it a control. Helpers also change the search: on the un-sanitized base, Threads 1 vs 4 differ in
`(bestmove, nodes)` on **12 of 12** positions at `go depth 12` (`evidence/threads1_vs_4_base.json`; node
counts only, no time measured).

## 3. Startup init: fixed — do not re-report it

**One line: the `attacks::init()` race that `origin/grok47/t13-thread-sanitizer` found on the older tree
(`16833ecc`) is fixed on `6b98f217`.** The fill is behind `std::call_once` at `src/bitboard.cpp:139-143`
(`static std::once_flag once; std::call_once(once, [] {`), it produced no report in any run here, and nobody
should re-report it.

Reading the code is not testing it. `scripts/startup_race.cpp` starts 4 threads on a barrier and has each
construct 50 `Board`s from a cold process — the only condition that ever exposed the old bug, since the first
`Board` is normally built on one thread and `Searcher` builds its workers only after the caller's `Board`
exists. Ten consecutive runs of each build (`evidence/startup_stability.log`):

| Build | sha256 | Runs with a TSan report | Outcome |
| --- | --- | ---: | --- |
| `6b98f217` as shipped | `5350d494…` | **0 / 10** | 20 legal moves + identical perft(2) from all 4 threads, `STARTUP_INIT_CLEAN` |
| `init()` reverted to the pre-fix form | `70cea38b…` | **10 / 10** | `SEGV` in `8/8` sampled runs; `PawnTable` / `KnightTable` / `KingTable` / `initialized` races |

The reverted build's failing summary is
`SEGV /src/include/forge/bitboard.hpp:192 in forge::attacks::bishop(int, unsigned long)` — a read through a
null `Magic::table`, the same signature the prior branch reported. **The harness detects the bug and the
shipped tree does not have it.** The report *count* on the broken build varies (2–20) because interleaving
does; the `SEGV` and the clean negative do not vary.

## 4. The four pins hold under TSan — and they cannot see `Threads` at all

| Pin | Required | Under TSan |
| --- | --- | --- |
| `bench 11` | 312,866 | 312,866 |
| `bench 13` | 862,329 | 862,329 |
| `bench 16` | 3,024,920 | 3,024,920 |
| `go perft 5` | 4,865,609 | 4,865,609 |

The pins holding is a useful gate: the sanitized binary computes the same node counts, so the tree under TSan
is the tree the rest of the audit measured. The brief expected they might not hold under instrumentation; they
do, so the gate was **pins**, and it passed.

**But the pins cannot see `Threads`, and this matters because they look like a threading check and are not
one.** `bench` builds its own searcher — `forge::Searcher bench_searcher(16)` — and `Searcher`'s constructor
defaults to `threads = 1`, so the option's value never reaches it. Empirically `bench 11` returns 312,866 at
both `Threads 1` and `Threads 8`. **A matching pin says nothing about whether the threaded path is correct.**
No pin in this report is used as evidence about threading.

Only the *rate* moves under TSan (nps ≈ 1.9M → 60–70k), which is the 5–20× instrument cost the brief warns
about — and is precisely why nothing here is a timing claim.

## 5. What is withdrawn, and what is not tested

**Withdrawn, and not re-derived:** every TSan wall-clock and nps number, including the ~1,000× outlier
(348,278 ms / 376,680 ms) that trap 30 makes load-bearing, and every rate, time-per-node and games-per-hour
figure measured on any sanitizer build. **This file reports no timing at all.** The 27 findings across 8 seats
that rode on "the TSan build" are not reproduced here; what replaces them is this single run with its flags,
hash, controls and exit codes stated. A TSan result can still be a true *finding* about behaviour — a race, a
crash, a wrong move — because it can be re-instrumented. It is the *time* that dies with the build.

Two timing facts are **quoted from the consolidated audit, not re-measured**: `Threads 4` at fixed depth costs
**1.24× wall**, and `bench` ignores `Threads`. For the record, this seat's own node-count data agrees on the
second (see §4) and is consistent in direction on the first without being comparable (this seat measured node
ratios, not wall time; median 3.10× nodes at `go depth 12`, which is the "3.68× the nodes" claim's
neighbourhood, measured on a different corpus and budget).

**Reproducibility gate — pins pass, but Threads 4 searches are not reproducible, and that is the engine, not
TSan.** `go depth 10` and `go nodes 100000` at Threads 1 are bit-identical across runs (0/12 differ under TSan,
0/12 on the un-sanitized base). At **Threads 4 the same search differs across runs on 12 of 12 positions — and
also 12/12 on the un-sanitized base build**, so this is not instrumentation. Two consequences: (i) **the gate
for this seat is the race count plus the observed exit status, not a bestmove or node count**, because a
Threads 4 node count is not a stable quantity to gate on; (ii) the audit's existing "fixed node and depth
searches are bit-identical at `Threads 1`" result **does not extend to Threads 4** — reported because it was
found, not because it was the assignment.

**Explicitly not tested, with reasons:**

- **No `-D_GLIBCXX_DEBUG` combination.** Row `07-C38` rests on TSan + ASan/UBSan + `-D_GLIBCXX_DEBUG` at
  once; that three-way combination remains unattributed. TSan cannot be combined with ASan on this runtime, so
  building it would have cost the TSan run rather than extended it.
- **No ASan/UBSan run.** Different instrument, different report.
- **No Ponder / `ponderhit` case.** It exercises the `stop_cv` handshake but was not in the assignment's case
  list. It is the most obvious next case if this seat is extended.
- **No clock-driven (`go wtime`) case** — a timed search's stop path is time-dependent by construction, and the
  TSan slowdown would make the run mostly waiting rather than searching.
- **Case G records no node count.** A search cut short by `stop` returns a bestmove without a final `info`
  line carrying `nodes`, so the table says `n/a` rather than inventing a figure. Its proof that work happened
  is the 6 live OS threads sampled during `go infinite` and the `info depth` lines in the transcript.
- **The corpus is single-threaded-validated only.** All 40 FENs were accepted by both python-chess and the
  engine (`evidence/corpus40.json`, 0 refused), but it was not built to widen race windows — it is the
  existing `soak_all/search_corpus.txt` sampled across material profiles. A corpus designed to maximise
  interleaving could still find what this one did not.
- **Report counts on racy builds are not stable.** On the plant-B build the count ranged 13–24 across replays,
  and on the reverted-init build 2–20. The *presence* of a report was stable in every run; the *count* is an
  interleaving artifact and no claim here depends on one.

## 6. Files

- `scripts/build_and_run.sh` — configure, build, print the flag line, prove `libtsan` linkage, check the pins,
  run both driver self-tests, build and verify a planted race, then run all cases.
- `scripts/tsan_driver.py` — UCI driver. Reads to `bestmove` before sending anything else, never pipes `quit`
  into a live search, and **drains to EOF before reaping**.
- `scripts/tsan_run.py` — cases A–H, the `/proc` thread sampler, race extraction. Writes no timing as a
  measurement; the only time field is a watchdog.
- `scripts/build_corpus.py` — builds and two-sided-validates the 40-position corpus.
- `scripts/plant_selftest.py` — applies plant A and/or plant B to a copy of the tree.
- `scripts/startup_race.cpp` — the concurrent-`Board` startup harness.
- `scripts/drain_selftest.py` — proves the exit-drain catches a post-`quit` report and the naive path loses it.
- `scripts/exit_observation.py` — records `drained_to_eof`, real `exit_code` and post-quit line count per case.
- `evidence/` — the run (JSON + raw transcript), both plants verbatim, both startup harnesses and their
  10-run stability table, the drain self-test, the exit observation table, the Threads 1 vs 4 comparison, and
  the corpus.
