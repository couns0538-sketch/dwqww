# Release state — Chess Engine Forge 6.2.0

Status: **strength release on top of 6.1.0; search refinements and thread voting**.

Changes relative to 6.1.0 (see `CHANGELOG.md`): quiet checks at the first
quiescence ply; a pawn-structure history for quiet move ordering;
history-aware quiet futility pruning and capture-history reductions; the
check extension removed; thread voting and pool-wide node budgets for
`Threads > 1`; check-aware move generation (about 3 % more nodes per second
than 6.1.0) and quiet-only generation in the picker; the tuning extractor
reads PGN `[FEN]` headers. Match records live in `validation/release-6.2.0/`.

Validation performed: GCC 13.3 Release with strict warnings as errors and GCC
ASan+UBSan, 4/4 CTest suites each; sanitizer-built engine exercised with four
threads through `go movetime`, `go depth`, `go infinite` + `stop`, `go nodes`
and `ucinewgame`; each search change measured on its own in 1000-game
fixed-node self-play (25,000 nodes per move, no adjudication) against 6.1.0;
the adopted set confirmed together at 3+0.03 (+17 +/- 22 Elo over 300 games,
LOS 94 %); five further parameter changes and one evaluation refit were
tested the same way and not adopted. Single-thread `bench` signatures are
unchanged by the threading and generation changes.

Not done for this release: opening book, tablebases, Windows runtime testing,
a separately measured Elo figure for thread voting (sanity-checked only).

---

# Release state — Chess Engine Forge 6.1.0

Status: **strength release on top of 6.0.0; adds multi-threaded search**.

Changes relative to 6.0.0 (see `CHANGELOG.md`): `Threads` option with Lazy
SMP; evaluation correction history extended from pawn structure to non-pawn,
minor, major and continuation keys; capture futility pruning;
selection-based move picking; POPCNT enabled in the default x86-64 build. Match records and the component A/B tests live in
`validation/release-6.1.0/`.

Validation performed: GCC 13.3 Release with strict warnings as errors and GCC
ASan+UBSan, 4/4 CTest suites each; sanitizer-built engine exercised with up
to four threads through every `go` mode; fixed-node self-play isolation tests
for each search change (1000 games at 25k nodes, 400 games at 100k nodes);
time-control matches against 6.0.0 and between thread counts (`Threads=2` vs
`Threads=1`: +81 +/- 40 Elo over 100 games at 5+0.05). Single-threaded the
release is at least as strong as 6.0.0 at blitz and stronger per node at
depth; see `validation/release-6.1.0/README.md` for the numbers and the
limits of what 300-game matches resolve. The single-thread `bench` signature
is unchanged by the threading code.

Not done for this release: opening book, tablebases, Windows runtime testing,
thread voting for the best move (the main thread's result is used).

---

# Release state — Chess Engine Forge 6.0.0

Status: **strength release; beats Stockfish 19 at UCI_Elo 2800 in measured matches**.

The reference opponent is Stockfish 19 with `UCI_LimitStrength=true` and
`UCI_Elo=2800`, whose skill scale is anchored to CCRL blitz ratings. Match
records live in `validation/release-6.0.0/`. The 5.31.0 baseline scored 10.0 %
(1W 17L 2D over 20 games at 10+0.1); 6.0.0 scores well above 50 %.

Engine changes relative to 5.31.0 are described in `CHANGELOG.md`. Validation
performed for this release: GCC Release build, GCC ASan+UBSan build, 4/4 CTest
suites (C++ tests, match-tool tests, UCI regression with the three reference
perfts 119060324 / 4085603 / 674624, ponder regression), a 15-position tactical
suite, fixed-node self-play A/B tests for each search change, and time-control
matches against the reference opponent.

Not done for this release: multi-threaded search, opening book, tablebases,
Windows runtime testing.

---

# Release state — Chess Engine Forge 5.31.0

Status: **validated depth-9 LMR bound-correctness release, no demonstrated Elo gain**.

Immediate validated baseline: immutable 5.30.0 source ZIP SHA-256 `fd2f0d249b78bc353bc3a439464be0c4aec7a01eb1664f2c923f985aef74d0d7`; ZIP CRC and all 890 existing source SHA-256 manifest entries verified. No newer validated source or demonstrably active implementation was observed in the accessible Library/process inventory before promotion; remote work cannot be excluded. The original 5.30.0 files remain unchanged.

The only engine behavior change raises the quiet late-move-reduction floor in `Searcher::alpha_beta` from depth >=9 to depth >=10. On `rn1qkb1r/p1p1ppp1/1p1pbn2/7p/3P4/2N1PN2/PPP1BPPP/R1BQK2R w KQkq - 0 1`, direct depth-9 windows [53,54] and [54,55] previously fail low at 53/54; no-LMR and 5.31.0 return 54/55. Tests include the adjacent boundary and exact board/Zobrist/reversible-history state restoration. No other move ordering, TT, null pruning, qsearch, evaluation, UCI grammar or threading change.

GCC 14.2/Clang 17 Release C++20 -O3 strict -Werror plus Clang 17 ASan+UBSan pass all 4 CTest groups. All extended UCI/ponder checks pass, and reference perfts are exact 119060324, 4085603, 674624. Seven interleaved CPU0 paired GCC benchmarks preserve shallow total 908968 nodes; deep total 11713955 → 12911443 nodes, and all best moves/scores. Shared-VM timing changes are diagnostics only; no speed or Elo improvement or controlled opponent-strength result is claimed.

Windows x86-64/Zen4 PE is cross-compiled with pinned LLVM-MinGW Clang 24, `-O3 -flto=thin -march=znver4 -mtune=znver4`, static C++ runtime and checksum verification. **NOT WINDOWS-RUNTIME-TESTED** (native Windows and Wine unavailable).

Unresolved: depth-10+ LMR reduction/bound risk, depth-6+ verified null/zugzwang contexts, 64-bit repetition-history fingerprint collision possibility, and no controlled strength/Elo or physical Ryzen performance estimate.

---

# Release state — Chess Engine Forge 5.30.0

Status: **validated restricted-root correctness release, no demonstrated Elo gain**.

Immediate validated baseline: complete immutable `chess-engine-forge-5.29.0.zip` SHA-256
`8de2079347384e029f8819ed71b98b5aae1fbbb5ac8e870fe1e604c52a330944`.
ZIP CRC and all 842 source manifest entries verified against the extracted actual archive.
Previous 5.29.0 remains preserved and available without alteration.
No demonstrably active overlapping implementation was found in the accessible local artifacts;
this does not guarantee no unseen remote development exists.

Exactly one engine behavioral change: when a requested `searchmoves` restriction excludes all
legal root moves but the actual position has a legal move, Forge returns a distinct no-result
status (`SearchInfo.restricted_root_empty=true`), `score cp 0`, empty PV and `bestmove 0000`.
Unchanged 5.29.0 produced `score mate 0` on the in-check nonmate at
`4r2k/8/8/8/8/8/8/4K3 w - - 0 1` with `go depth 1 searchmoves a1a8`.
Actual root mate/stalemate classification occurs before restriction; root TT bound isolation,
legal restricted fallback under interruption, all earlier search/ponder logic are retained.

Fresh strict GCC/Clang release and Clang ASan+UBSan tests each pass 4/4 CTest suites, including
new tests; required reference perfts match 119060324, 4085603, 674624.
Three CPU0-pinned interleaved baseline/candidate benchmarks preserve 908968/11713955
shallow/deep nodes, scores, best moves and complete PVs; median times shift +1.75% / -1.84%.
Fastchess pinned 4-pair/8-game same-binary baseline calibration 4W/0D/4L (50%) with
all normal terminations. This correctness release does not claim an Elo win and has no A/B
SPRT. No calibrated external strength ladder or superhuman evidence exists.

Windows: LLVM-MinGW Clang 24 / UCRT pinned toolchain, x86-64 PE, Ryzen 9 7950X3D Zen 4
flags `-O3 -flto=thin -march=znver4 -mtune=znver4`, static C++ linkage, PE header/imports,
checksum, deterministic repeat builds. **CROSS-COMPILED / PE-VERIFIED / NOT WINDOWS-RUNTIME-TESTED**.

Next diagnostics (hypotheses, not changes made in 5.30): depth-9+ LMR against a frozen
full-window/boundary reference, depth-6+ null verification, bit-exact evaluation
parameterization and licensed held-out tuning. See `engine-improvement-log.md`.
