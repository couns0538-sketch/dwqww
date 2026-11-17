# Validation — Chess Engine Forge 5.31.0

Immediate baseline: 5.30.0 archive SHA-256 `fd2f0d249b78bc353bc3a439464be0c4aec7a01eb1664f2c923f985aef74d0d7`. Exact source ZIP CRC and 890-entry SHA-256 manifest verified; native strict baseline repro returns 53 and 54 in the depth-9 boundary windows while no-LMR reference returns 54 and 55. New test harness fails exactly two depth-9 assertions on the unchanged baseline.

Final candidate: GCC 14.2 Release, Clang 17 Release, Clang 17 Debug ASan+UBSan, C++20 -Werror (plus -Wall -Wextra -Wpedantic -Wconversion -Wshadow); each passes engine, match-tool, UCI, ponder regression (4/4). GCC/Clang/sanitizer extended UCI each passed 30 cases including handshake/readiness, finite/infinite/stop/ponder, searchmoves, mate, options, clocks, TT, transactional positions. Perfts start d6=119060324, Kiwipete d4=4085603, CPW position3 d5=674624.

Baseline/candidate freshly rebuilt identically GCC 14.2 -O3 with 7 CPU0-pinned AB/BA pairs on AMD EPYC 9V74 shared VM. Shallow 908968 nodes each, median 490.824/480.926 ms; deep 11713955/12911443 nodes, aggregate median 7841.932/8458.033 ms. Best moves and scores are unchanged in all eight benchmark cases; no speed/Elo conclusion. No A/B Fastchess or SPRT was run for this narrow correctness fix.

Windows binary built with pinned llvm-mingw toolchain (outer ZIP SHA-256 `7b021b4b9717936751f6437317ed7defa628ac83a1726f8fb315ea0fd1813af3`, contained tar.xz SHA-256 `8c843b8878f25c822afd37864e435beda65e2abe030543ed70915aeb1ecd16de`); Zen4 -O3/ThinLTO/znver4 and static C++ runtime, PE32+ AMD64. PE architecture/subsystem/imports/checksum checked; Windows/Wine runtime and physical Ryzen 7950X3D not available. Frozen-source re-extraction rebuild and verification logs are in the separate release evidence bundle.

---

# Validation — Chess Engine Forge 5.30.0

## Current immediate baseline and direct reproduction

Archive 5.29.0 SHA-256: `8de2079347384e029f8819ed71b98b5aae1fbbb5ac8e870fe1e604c52a330944`.
Verified ZIP CRC and 842/842 frozen source-file manifest entries. Baseline GCC, Clang and
Clang ASan+UBSan each pass 4/4 CTest groups. Baseline reproducer on
`4r2k/8/8/8/8/8/8/4K3 w - - 0 1`, `go depth 1 searchmoves a1a8` prints
`info depth 1 score mate 0 ...` and `bestmove 0000`, although White has legal moves.
The new process regression fails on the baseline as expected. The corrected candidate reports
`info string searchmoves restriction has no legal root moves`, `score cp 0`, and `bestmove 0000`.

## Strict builds, sanitizers, perft and protocol

GCC 14.2 and Clang 17 with C++20 `-O3 -Wall -Wextra -Wpedantic -Wconversion -Wshadow
-Werror` compile successfully; Clang 17 `-O1 -g1` with ASan+UBSan and identical warnings
also passes. All 4 CTest groups pass in each configuration: native engine tests,
match-tool tests, full UCI and pondering regressions. No observed sanitizer errors.
Reference perft from clean baseline and candidate: start d6=119060324,
Kiwipete d4=4085603, CPW position3 d5=674624. Candidate also passes Clang and
sanitizer reference perft. New regressions validate in-check/quiet empty restriction,
real mate/stalemate, warm/cold TT, board history/clock immutability, non-empty
restricted root, and interrupted legal fallback.

## Paired search diagnostics (not Elo)

Three CPU0-pinned interleaved repetitions, fresh unchanged 5.29.0 versus candidate,
GCC 14.2 `-O3`, 32 MiB hash, identical conditions on AMD EPYC 9V74 shared virtual host.
Shallow: 908968 nodes both; median baseline 490.388 ms, candidate 498.947 ms (+1.75%).
Deep: 11713955 nodes both; baseline 7863.258 ms, candidate 7718.584 ms (-1.84%).
All eight per-position depth, node, score, best move and full PV signatures match.
Small, opposing timing shifts on a shared host are noise diagnostics, not a speed or
playing-strength claim. Binary SHA-256 and raw results are retained in the evidence archive.

## Match-tool calibration and strength limitations

Pinned external Fastchess binary SHA-256:
`b1a7c834110144db23cb95a446ea1546c9b2333ab3508e6ac49eb26e1a2f5dff`.
Four pairs / eight games of identical unmodified 5.29.0, 5000 nodes per move,
colors swapped, four distinct MIT positions, CPU0, normal terminations,
4W/0D/4L, pentanomial [0,0,4,0,0], score 50%. This was a tool calibration,
NOT an A/B strength test. A/B Elo was not attempted for this UCI correctness fix.
No superhuman/super-GM result is demonstrated.

## Windows Zen 4 delivery

Pinned LLVM-MinGW toolchain GitHub Actions artifact ZIP SHA-256
`7b021b4b9717936751f6437317ed7defa628ac83a1726f8fb315ea0fd1813af3`,
contained archive SHA-256
`8c843b8878f25c822afd37864e435beda65e2abe030543ed70915aeb1ecd16de`.
Clang 24.0.0git UCRT, C++20, -O3, ThinLTO, -march=znver4, -mtune=znver4,
-static, -pthread, and strict Werror. PE32+ AMD64 Windows CUI header and UCRT/kernel
imports checked, timestamp zero, PE checksum verified and binary SHA-256 retained.
Native Windows and Wine unavailable: NOT WINDOWS-RUNTIME-TESTED.

## Source-freeze promotion gate

Source ZIP is frozen after documentation and regression integration. Source hash manifest
excludes the manifest itself to avoid recursive hashing. Re-extraction, manifest verification,
fresh GCC and Clang strict builds, CTest and perft plus independent repeat Windows cross-build
must pass before declaring this release validated. Post-freeze logs, source ZIP hash and
Windows executable hashes are retained externally in the release evidence archive.

---

# Historical validation — Forge 5.29.0 (retained unchanged below)

# Validation — Chess Engine Forge 5.29.0

## Immediate validated baseline

Untouched 5.28.0 source ZIP SHA-256: `0fb9dca23fa56d4708601e8d8157c8b1831fb0880509931a628aa0b3c2dc3261`.
ZIP CRC and all 818 source-manifest hashes verify. Fresh GCC 14.2 executable
`8994c2c9cc8d3222d1569cf015c97fe30493d28dd14fbb42eb2edd16ff8ba37c`
and Clang 17 executable
`3bf7de1b22bcde79ed1583a72fdde6dc2da524e1feb9ef38a4610dc3acd7812c`
reproduce the frozen baseline hashes. Both passed 3/3 CTest; ASan+UBSan passed 3/3.
Extended baseline UCI/perft passed.

## Ponder feature and direct tests

Only `include/forge/search.hpp` (`SearchLimits`/atomic hit timestamp), `src/search.cpp`
(`Searcher::should_stop`/`Searcher::search`), and `src/uci.cpp` (UCI grammar/options,
search worker publication, predicted PV reply) modify engine behavior. A new
`tools/ponder_regression.py` is registered in CTest by `CMakeLists.txt`.

New feature regression cases check Ponder advertisement, legal PV predicted replies,
pre-hit publication suppression, `ponderhit` timed conversion, terminal/checkmate roots,
`stop` while pondering, explicit zero-node limit, 16 immediate-hit races, side clocks,
option disable, invalid input and subsequent ordinary searches. An independent 40-case
protocol simulation records 20 hits, 20 misses, all legal predicted/played moves and no
hangs. Untouched 5.28.0 fails the initial feature regression, as expected.

## Strict builds / reference perft / UCI

GCC 14.2 `-O3` and Clang 17 `-O3`, both `-Wall -Wextra -Wpedantic -Wconversion
-Wshadow -Werror`: engine, match-tool, UCI and ponder tests pass (4/4 CTest each).
Clang 17 ASan+UBSan at `-O1 -g1` and the same strict warnings also pass 4/4,
no observed sanitizer findings. The original extended UCI regression passes under both
GCC and Clang, including handshake/readiness, finite, infinite-stop, searchmoves,
mate, options, transactional-position, explicit zero limits and historical protections.
Perft: start d6=119060324; Kiwipete d4=4085603; CPW position3 d5=674624.

## Four paired fixed-depth comparisons

Identical GCC `-O3`, 32 MiB hash, 1 search thread, CPU0 affinity, alternating execution
order, four full repetitions. Shallow baseline/candidate each search 908968 nodes;
median sum of four positions 550.152 / 547.746 ms (-0.44%). Deep baseline/candidate each
search 11713955 nodes; median 8254.920 / 8132.491 ms (-1.48%). Every per-position
score, best move and node count is equal. Timing variability precludes a throughput
improvement claim. Pondering was disabled in these deterministic benchmarks.

## Fastchess safety sample / strength limitation

Pinned upstream Fastchess alpha 1.8.2, commit a281cafd608f044ec152dabd8f5e379dac0a6b47,
SHA-256 `facc8910c98328058dea4d4f537da5f64f44b43b2ed8a66ed5049e220081c633`.
16-game identical-binary A/A: 50%. A/B: 30 color-swapped pairs at `0.2+0.002`,
fixed MIT opening corpus, seed 2026100908, equal 32 MiB hash and Move Overhead 10,
one thread and CPU0 affinity. 60 normally terminated games: candidate 27 W / 6 D /
27 L (50%); pentanomial `[4,3,16,3,4]`. SPRT at 30-pair cap inconclusive.
**This Fastchess build does not implement GUI pondering; the A/B match ran with pondering
OFF. It is a safety control, not a measurement of the practical pondering benefit.**
No Elo gain, external calibrated strength ladder or superhuman claim is supported.

## Windows and remaining risk

Windows x86-64 LLVM-MinGW Clang 24.0.0git, UCRT, flags `-O3 -flto=thin
-march=znver4 -mtune=znver4 -static -pthread`, strict warnings,
zero COFF timestamp. Exact toolchain outer ZIP SHA-256
`7b021b4b9717936751f6437317ed7defa628ac83a1726f8fb315ea0fd1813af3`
and contained tar SHA-256
`8c843b8878f25c822afd37864e435beda65e2abe030543ed70915aeb1ecd16de`.
PE32+ x86-64 Windows CUI, imports, checksum, static C++ linkage and bitwise repeat-build
are validated. No native Windows/Wine runtime is available: **NOT Windows-runtime-tested**.

Outstanding: actual ponder-on tournament match and quantified Elo effect; Threads/Lazy SMP,
legally curated OwnBook, coefficient-robust evaluation regressions, proven deep selective
search issues, repetition-history fingerprint collision and external strength ladder.
