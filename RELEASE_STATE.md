# Release state — Chess Engine Forge 6.0.0

Status: **strength release; measured gain over 5.31.0**.

The 5.x line kept raising pruning thresholds whenever a zero-window search disagreed with a
full-depth reference, which left the engine without usable late-move reductions below depth 10,
without null-move pruning below depth 6, and without reverse futility, futility or late-move
pruning. 6.0.0 adopts the standard selective-search toolkit (see CHANGELOG.md) and a
position-indexed transposition table. Evaluation, move generation, UCI, pondering and the
match tooling are unchanged.

Evidence: fastchess, 5+0.05, Hash 32, `tools/openings/forge-10000.epd`, 100 games, candidate
search versus the unchanged 5.31.0 binary: W88 D7 L5, +413 +/- 111 Elo. Strict GCC
`-Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror` release build and GCC ASan+UBSan
build pass all 4 CTest groups. Reference perfts are unchanged (move generation untouched).

Known limits: single-threaded, hand-crafted evaluation without king-attack terms, no opening
book, tablebases or NNUE. The next measurable items are evaluation (piece-square tables, king
safety, passed-pawn interaction with kings), continuation/capture history, and TT aging.

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
