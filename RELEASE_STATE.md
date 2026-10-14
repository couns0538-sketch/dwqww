# Release state — Chess Engine Forge 6.4.0

Status: **strength release; first shipped neural network (residual NNUE,
+86 Elo at fixed nodes and +45 Elo at 10+0.1 over 6.3.0), validated against
Stockfish 19 at UCI_Elo 3000**.

Against Stockfish 19 with `UCI_LimitStrength=true UCI_Elo=3000` (one thread,
Hash 64, 8moves_v3 openings) the shipped binary scored 52.5 % over 100 games
at 20+0.2 (35W 30L 35D, +17 +/- 53 Elo); 6.3.0 scored 50.0 % (33W 33L 34D)
and 6.2.0 51.5 % (35W 32L 33D) under the same conditions, differences inside
the noise of 100 games. Match records live in `validation/release-6.0.0/`.

Engine change relative to 6.3.0 (see `CHANGELOG.md`): the evaluation is now
the hand-crafted score plus a residual 768 -> 128x2 SCReLU network trained
with the new `--residual` trainer mode on 13.4M self-play positions with pure
search-score targets; the net improves the validation loss by 6 % over the
hand-crafted evaluation and won 62.1 % of 500 games at 20k nodes/move
(209W 88L 203D) and 56.5 % of 200 games at 10+0.1 (49W 23L 128D) against the
6.3.0 release. Five search constants were tested by fixed-node SPRT and
rejected (`FutilityBase=80`+`FutilityMultiplier=130` 50.20 %,
`SeeQuietMultiplier=18` 50.50 %, `QsSeeMargin=80` 50.00 %,
`HistoryPruneMultiplier=3000` 49.93 %, `NullMoveEvalDivisor=150` 49.16 %);
the search constants are those of 6.3.0. Every run is recorded in
`validation/release-6.0.0/EXPERIMENTS.md` with its games in
`all-match-pgns.zip`. Validation performed for this release: GCC Release
build, `forge_tests` and 4/4 CTest suites, the matches above, and the
time-control match against the reference opponent. The `bench 11` signature
of the shipped binaries is 417491 nodes; all six static builds (Linux and
Windows, x86-64-v2/v3 and Zen 4, compiled with `-ffp-contract=off`) were
executed, the Windows ones under Wine, and report the same signature.

Not done for this release: tablebases, native Windows testing, a quantised
(integer) network evaluation (the float network costs about 15 % of the nodes
per second), larger or longer-trained nets (every residual run reached its
best validation loss within the first two epochs on the available 13.4M
positions).

---

# Release state — Chess Engine Forge 6.3.0

Status: **incremental strength release; search constants retuned by SPRT
(+16 Elo at fixed nodes over 6.2.0), validated against Stockfish 19 at
UCI_Elo 3000**.

Against Stockfish 19 with `UCI_LimitStrength=true UCI_Elo=3000` (one thread,
Hash 64, 8moves_v3 openings) the shipped binary scored 50.0 % over 100 games
at 20+0.2 (33W 33L 34D, 0 +/- 54 Elo); 6.2.0 scored 51.5 % (35W 32L 33D)
under the same conditions, a difference well inside the noise of 100 games.
Match records live in `validation/release-6.0.0/`.

Engine change relative to 6.2.0 (see `CHANGELOG.md`): late-move pruning keeps
one more quiet move per depth (`LmpBase=4`) and the history bonus grows faster
and saturates later (`HistoryBonusQuadratic=20`, `HistoryBonusMax=2048`);
the combination was accepted by a fixed-node SPRT (20k nodes/move, elo0=0,
elo1=5) after 3670 games at 52.37 %, LLR 2.97. Four other search constants
(`SingularMargin=1`, `ProbcutDepth=4`, `LmrHistoryDivisor=4000`,
`RfpMargin=60`), two new pawn-structure evaluation terms with a retuned table,
and a second NNUE net were tested and rejected; every run is recorded in
`validation/release-6.0.0/EXPERIMENTS.md` with its games in
`all-match-pgns.zip`. Validation performed for this release: GCC Release
build, `forge_tests` and 4/4 CTest suites, the SPRTs above, and the
time-control match against the reference opponent. The `bench 11` signature
of the shipped binaries is 344040 nodes; all six static builds (Linux and
Windows, x86-64-v2/v3 and Zen 4) were executed, the Windows ones under Wine.

Not done for this release: tablebases, NNUE weights (the trainer ships; the
nets so far overfit and lose to the tuned hand-crafted evaluation), native
Windows testing.

---

# Release state — Chess Engine Forge 6.2.0

Status: **strength release; roughly level with Stockfish 19 at UCI_Elo 3000 in
measured single-threaded matches**.

Against Stockfish 19 with `UCI_LimitStrength=true UCI_Elo=3000` (one thread,
Hash 64, 8moves_v3 openings) the pre-release build scored 47.75 % over 200
games at 10+0.1 (66W 75L 59D) and the shipped binary scored 51.5 % over 100
games at 20+0.2 (35W 32L 33D). Match records live in `validation/release-6.0.0/`.

Engine changes relative to 6.1.0 are described in `CHANGELOG.md`: embedded
engine-generated opening book with Polyglot support, cutoff-count LMR (SPRT
+21 Elo), material correction history, new evaluation terms and a retuned
table, a lazy move picker, and a falling-evaluation time extension. Validation
performed for this release: GCC Release build, `forge_tests` and 4/4 CTest
suites (C++ tests, match-tool tests, UCI regression, ponder regression),
fixed-node SPRTs for each search change, a time-control A/B of the time
manager, and time-control matches against the reference opponent. The
`bench 11` signature of the shipped binaries is 340241 nodes; the Linux and
Windows x86-64-v2/v3 builds were executed (Windows under Wine) and the Zen 4
(`znver4`) builds were 4.

Not done for this release: tablebases, NNUE weights (the trainer ships, the
nets so far lose to the tuned hand-crafted evaluation), native Windows
testing.

---

# Release state — Chess Engine Forge 6.1.0

Status: **strength release; beats Stockfish 19 at UCI_Elo 2800 in measured matches**.

The reference opponent is Stockfish 19 with `UCI_LimitStrength=true` and
`UCI_Elo=2800`, whose skill scale is anchored to CCRL blitz ratings. Match
records live in `validation/release-6.0.0/`. The 5.31.0 baseline scored 10.0 %
(1W 17L 2D over 20 games at 10+0.1); 6.0.0 scored 69.0 % over 200 games at
10+0.1 and 82.5 % over 100 games at 30+0.3; 6.1.0 scores 75.0 % over 200 games
at 10+0.1 with one thread, and adds a `Threads` option (75 % against its own
single-threaded build with four threads).

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
