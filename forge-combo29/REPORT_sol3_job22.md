# sol3 Job 22 — Native sanitizer checks

## (1) Step 0 — plain engines passed

Linux cloud, Case A. The retained r15d and kF executables and
synthetic net768 matched their pinned SHA-256 values. With PC20,
Threads 1 and Hash 16, each fresh-process pair gave bench 11
at 882,074 nodes and bench 13 at 4,275,906. Every net run printed
`info string NNUE v3 active:` and `checksum 30ab43b4ba5db5f3`.
[Plain hashes and raw pins](sol3/job22/stage0)

## (2) Step 1 — build flags and known answers

I built with GCC 14.2.0 (Debian 14.2.0-19), CMake 4.2.3
and the matching Debian `libasan.so.8`, `libubsan.so.1` and
`libtsan.so.2` runtimes. Each build kept the original engine
defines and `-march=x86-64-v4`, with `NDEBUG` removed.
I verified the effective flags on all nine compilation units
per arm. The compile-time overrides stayed in scratch.

| Builds | Effective sanitizer flags | PC20 + net768 known pins |
| --- | --- | --- |
| AU-r15d, AU-kF | `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=undefined` | Both 882,074 / 4,275,906 |
| T-r15d, T-kF | `-O1 -g -fsanitize=thread` | Normal T-r15d startup returned `uciok`, exit 0 |
| C-AU, C-UB | Same AU flags on scratch controls | See control runs |
| C-T | Same T flags on scratch control | See control runs |

C-UB is the requested second compilation of C-AU after removing
its first fault. All seven compilation invocations completed.
The AU pins used fresh independent processes and matched the
plain results for both depths.
[Build readback](sol3/job22/build/build_readback.txt) · [AU pins](sol3/job22/known) · [TSan startup](sol3/job22/T-startup)

## (3) Step 2 — all positive controls reported

The same UCI harness was used for the controls and clean runs.
C-AU and C-UB used W1 position 1, PC20, Threads 1, Hash 16,
net768 and depth 9. Each exited 1 after its expected report.

| Control | Detected result | First source site |
| --- | --- | --- |
| [C-AU](sol3/job22/controls/C-AU/engine.stderr.txt) | `ERROR: AddressSanitizer: heap-buffer-overflow` | `Worker::search`, `src/search.cpp:2629` in C-AU |
| [C-UB](sol3/job22/controls/C-UB/engine.stderr.txt) | `runtime error: signed integer overflow` | `Worker::search`, `src/search.cpp:2629` in the UB-only copy |
| [C-T](sol3/job22/controls/excerpts.txt) | All five W1 starts at Threads 2 named `forge::SanitizerControlNodes` in a TSan data-race report | The planted counter is in `src/search.cpp:96` and is incremented in quiescence and alpha-beta at `1776,1926` |

The first C-T process ran `go nodes 50000` at W1 position 1 and
kept reporting the deliberate race at different recursive stacks.
I interrupted that process after it emitted 9,669 warning headers
and 117,539,575 stderr bytes. GitHub rejected that single file at
its size limit. I preserved the complete byte stream in numbered
text parts and verified their concatenation against the original
SHA-256. The oversized checkpoint was unpublished. The succeeding
push used the numbered files.

Each of W1 positions 1–5 then got a fresh C-T process with Threads 2,
Hash 16, PC20 + net768 and its own `go nodes 50000`. The runtime halted on its first report, so each control
exited 66 before bestmove. Each first report named the same planted
counter. The clean T runs keep their non-halting runtime setting.
[Original C-T receipt](sol3/job22/controls/C-T/stderr_parts.receipt.txt) · [Numbered raw stream](sol3/job22/controls/C-T/stderr_parts) · [First 30 lines per control diagnostic](sol3/job22/controls/excerpts.txt) · [Control patches and gate](sol3/job22/controls)


## (4) Prediction graded

All four AU rows had exactly 0 distinct reports. Both T processes
had 0, within the declared 0–2 range. This grades the six declared
rows against complete engine stderr files.
[Pre-run prediction](sol3/job22/prediction.md) · [Counted reports](sol3/job22/clean/diagnostics.json)

## (5) Step 3 — six complete engine processes

All rows used PC20, Hash 16, MultiPV 1 and the pinned standalone
net768 (active checksum `30ab43b4ba5db5f3`, AVX-512). W1 is the
Job 19 fixture. Both A workloads used Threads 1. Each B workload
used a single process with Threads 1, 2, 4, then 1 for the games.
The B rows list the one process exit and report count across all
three phases.

| Build | Part and limits | Searches / bestmove lines | Nodes | Engine exit | Report blocks / distinct |
| --- | --- | ---: | ---: | ---: | ---: |
| [AU-r15d-d9](sol3/job22/clean/AU-r15d-d9) | A, W1 1–200, depth 9 | 200 / 200 | 4,097,080 | 0 | 0 / 0 |
| [AU-r15d-games](sol3/job22/clean/AU-r15d-games) | A, W1 201–210, 10 games, softnodes 2000 | 458 / 458 | 1,950,742 | 0 | 0 / 0 |
| [AU-kF-d9](sol3/job22/clean/AU-kF-d9) | A, W1 1–200, depth 9 | 200 / 200 | 4,097,080 | 0 | 0 / 0 |
| [AU-kF-games](sol3/job22/clean/AU-kF-games) | A, W1 201–210, 10 games, softnodes 2000 | 458 / 458 | 1,950,742 | 0 | 0 / 0 |
| [T-r15d](sol3/job22/clean/T-r15d) | B, nodes 50000 / infinite then stop / 4 games at softnodes 2000 | 72 + 18 + 343 = 433 / 433 | 2,256,725 + 51,979 + 1,444,459 | 0 | 0 / 0 |
| [T-kF](sol3/job22/clean/T-kF) | B, nodes 50000 / infinite then stop / 4 games at softnodes 2000 | 72 + 18 + 343 = 433 / 433 | 2,293,268 + 46,397 + 1,444,459 | 0 | 0 / 0 |

The depth-9 totals sum the last `info depth` node counts. Every
A depth-9 node count and bestmove matched its corresponding
plain Job 19 row, 200 per build. Both A game runs produced the
same 458 moves across ten legal games, with seven checkmates
and three claimable threefold draws. The game counts use the
final consumed-node marker. The B fixed-node and timed-stop
counts use the last `info depth` node count and can omit work in
an unfinished iteration. B spreads the fixed and timed-stop
searches across W1 1–90 in blocks of 30 per thread setting. Its
four games use W1 positions 211–214.

All six clean engine stderr streams are empty. There are zero
distinct clean reports to excerpt. Separate audit code replayed
the command schedules and game legality from the captured UCI
streams, checked all net activation and artifact hashes, and
reconstructed the counted search labels.
[Raw run directories](sol3/job22/clean) · [Result readback](sol3/job22/clean/results.json) · [Transcript audit](sol3/job22/clean/transcript.audit.json)

For each B process the harness scheduled all 18 stops for 100 ms
after the corresponding `go infinite` command. The observed
elapsed from the stamped go write to the stamped stop write was
100.157–125.202 ms for T-r15d and 100.296–166.897 ms for T-kF.
[r15d stop receipts](sol3/job22/clean/T-r15d/infinite.tsv) · [kF stop receipts](sol3/job22/clean/T-kF/infinite.tsv)

## Facts

The two T game tables are byte-identical. The four games per build
produced 343 legal moves, ending in three checkmates and one claimable
threefold draw. Both processes had already run all three thread-count
blocks before starting those games.
[T-r15d game table](sol3/job22/clean/T-r15d/games.tsv) · [T-kF game table](sol3/job22/clean/T-kF/games.tsv) · [Independent raw diagnostics and game recount](sol3/job22/clean/independent.audit.json)

## Suspicions

The timed stops exercise different scheduler interleavings across
runs. In this sample the stop sends sometimes landed after the target
deadline. A race that needs a different interleaving could escape these
clean runs.

## What I did not do

I did not change the tracked engine source. The fault controls were
built in scratch from the published text patches. I did not run the
Windows toolchain or compare playing strength.

## What I am not sure about

These runs do not establish coverage of every branch inside the
thread hand-off. The two builds' last-info totals do not show exactly
how much work their fixed-node and timed-stop searches consumed.

## What this check cannot see

> The PC's compiler (clang 23 for Windows), its net, its exe with a profile; code that your positions and games do not reach; mistakes a checker cannot report (the address checker does not see a read inside an allocated block).
