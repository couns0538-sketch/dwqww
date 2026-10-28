# C1 [Deep Research] Own Syzygy WDL/DTZ probing — DONE

**Options.** `SyzygyPath` (string, empty = off, the default), `SyzygyProbeDepth` (spin 1-10, default 1),
`Syzygy50MoveRule` (check, default true).

**Branch.** `opus-C1` = `opus-O3` (`0d99f02`) + [C1] commits:
- `3fd235c`: engine
- `f629534`: tests and fixtures
- `08aabaf`: CI, smoke test, mutation check
- `534dcaa`: more tests, one CI table fetch
- `d0cfdf4`, `fb194f8`: logs, patches
- `38cec76`: quiet-runner NPS workflow

**Patches.** `patch.diff` = vs the lock `294dbed` (includes O3); `patch_vs_opus-O3.diff` = C1 only.

**Sources.** `IDEA_SOURCE.md` (R. de Man's public format description, CPW). Own reader; no Fathom,
Stockfish or python-chess code.

**Status.** UNPROVEN until gated; no Elo claim.

**Review.** The implementation was done by a sub-agent and reviewed by the main session. The review did
four things:
- rebuilt the engine with the PC lock recipe and re-checked the identity at all 5 depths;
- compared the hot functions' machine code with the lock;
- probed KQvK, KQvKR, KRvKR, KBNvK (side to move lost) and a KPvK pawn race with and without the 3-4-5 set
  loaded: TB win +31870, TB loss −31870, draw 0, Qxc2 found, a2a4 found;
- added a quiet-runner NPS run, because the default alpha-beta's machine code changed (see "Speed").

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | SyzygyPath empty: bench exact (5 depths), perft, kiwipete, FMA 0 | **PASS** (PC recipe, re-checked in review; Linux CI g++-14) |
| 2 | unit tests on >= 200 positions (KRPvKR, KBNvK, KQvKR, KPvK, ...) match a stored known-answer list: WDL, DTZ sign and value, rule50 edges, castling, ep | **PASS**: 382 lichess-API rows (49 materials) + 1,468 reference rows (all 145 materials), 36,513 checks, 0 failures |
| 3 | no crash with a missing, empty or partial TB folder | **PASS** |
| 4 | probing works with 3-5 man files (downloaded from the public mirror) | **PASS**: 290 files (939 MiB), md5-checked, all load; stored outside the repository |
| 5 | WDL probe in search (after a capture/pawn move reset rule50; cut on hit); DTZ root move filtering; castling rights not probed; en passant correct | **PASS** |
| §3 | ctest only known failures; ASan+UBSan; TSan | **PASS**: ctest 17/18 with only the 4 known lines (Windows and CI); CI runs 40463050042 (opus-ci) and 40463050255 (opus-c1-syzygy, real 3-4 piece tables, release / ASan+UBSan / TSan at Threads 4): 0 sanitizer reports |
| — | planted bugs | **17/17 caught** (`mutation_check.sh`) |

## What it does

### Reader (`src/search/syzygy.inc`)
- **File access.** Tables are memory-mapped read-only (`CreateFileMappingW` / `mmap`). A test hook makes
  exact-size heap copies, so that ASan sees any out-of-bounds read. Every read of the header and the sections
  is bounds-checked.
- **Index computation:**
  - leading pawns by file a-d;
  - pawnless tables: the 3 unique pieces, or the 2 kings in the a1-d1-d4 triangle, after mirroring;
  - free-square combinations for the other groups, and the order nibbles.
- **Decoding.** Canonical Huffman plus RePair symbols. The bit reader is bounded to its block.
- **WDL probe.** Resolves captures and en passant. The stored value is not used when every legal move is a
  capture.
- **DTZ probe:**
  - value maps and plies/moves scaling;
  - a one-ply search when the file stores the other side to move;
  - a "rounded" flag when a file stores distances in moves.
- **Root ranking.** Ranks the root moves by DTZ, with a WDL fallback.

### Search glue (`src/search/tablebase.inc`)
- **Where.** One guarded branch in `Worker::search`, right after the TT cutoff.
- **When a node is probed.** Only when all of these hold:
  - it is not the root and not a singular-verification search;
  - it has no castling rights;
  - its 50-move counter is 0;
  - it has at most the largest table's piece count (with exactly that count, only at depth >= SyzygyProbeDepth).
- **Scores.** A win scores TbWin − ply, where TbWin = MateInMaxPly − 1. It is stored in the TT as a lower
  bound at depth + 6; a loss is the mirror image, stored as an upper bound. With `Syzygy50MoveRule` on, a
  cursed win or blessed loss scores ±2. The node cuts when the bound is conclusive; PV nodes return the TB
  value.
- **Root in a TB position:**
  - the moves are ranked by DTZ, and the search runs only on the best-ranked ones (intersected with
    `searchmoves`);
  - certain wins (DTZ + counter <= 99) rank equal, unless a repetition happened since the last zeroing move;
  - in-search probing is off for that search when DTZ was available;
  - the info lines report the TB score unless the search finds a mate.
- **Placement.** All TB code is `[[gnu::cold]]` and sits after the search code. The 8-file build recipe is
  unchanged.

## Known answers (`tests/syzygy_tests.cpp`, CTest `forge_syzygy_tests`)
- **Lichess fixture** (`tests/syzygy_fixtures.tsv`, 382 rows).
  - **Source:** answers from the public tablebase.lichess.ovh API, one request at a time, at least 1 s
    apart. The responses are cached in `api_cache.jsonl.gz`, so the fixture rebuilds offline
    byte-identically.
  - **Coverage:** 49 materials; 26 en-passant positions, including one where ep is the only legal move; mate,
    stalemate and bare kings; 4 castling positions that must refuse the probe; the KNNvKP cursed win
    (DTZ 164); 59 rows at the 50-move boundary.
  - **DTZ rounding:** some 2013 files store DTZ in moves, not plies. The engine flags these values as
    rounded, and the test lets them be at most one ply longer than lichess's value. Exact values must be
    equal. Example: KBNvK `5N2/7k/8/8/3B4/8/8/K7 b`, where the engine and the reference read −57 and lichess
    reports −58.
- **Reference fixture** (`tests/syzygy_reference.tsv`, 1,468 rows, every one of the 145 materials).
  python-chess 1.11.2 was run on the same files as a test oracle only; none of its code is in the
  repository. WDL, DTZ and all 20,776 root-move DTZ values are equal.
- **Robustness.** These cases load and refuse cleanly:
  - empty path, `<empty>`, a missing folder, an empty folder;
  - junk files with table names;
  - 5 truncations of a real table;
  - corrupt data blocks (2,000 probes, no crash);
  - a WDL-only partial folder (DTZ refuses, the root falls back to WDL);
  - a multi-folder path containing a missing folder.
- **UCI smoke test** (`uci_tb_smoke.py`): 0 failures. It covers the advertised options, the folder messages,
  TB scores at the root, castling and ep roots, and option changes.

## Default build (SyzygyPath empty): code and speed
- **Identity:**
  - d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0
    (`logs/identity_pc_recipe.log`, re-checked in review);
  - with the 3-4-5 set loaded: d11 313631, d13 866959, d16 2460490 (`logs/bench_with_tables.log`).
- **Codegen** (`logs/codegen_vs_lock.log`, `codegen_compare.sh`):
  - every listed hot function except alpha-beta is instruction-identical to the lock at the same address
    mod 64. For `MovePicker::next` the 32 "differing" lines are trailing nop padding and displacements to
    moved data, as on every O3-based branch.
  - **Alpha-beta is not identical:** 2419 vs 2413 instructions, 1,616 differing normalised lines. The hot
    path gains 3 instructions (`mov search_cardinality(%rip),%eax; test; jne` to a cold block), and the extra
    call site changes register allocation in the function.
  - `layout_check.py` over all 3,718 functions: no hot function changes its address mod 64.
- **NPS on the busy PC** (`logs/nps_ab_lock_vs_c1.log`, 10 ABBA runs, node counts equal). The two depths
  disagree in sign, which is the PC's load noise (an A/A run of identical binaries on this PC gave −1.8% /
  −1.0%):
  - d16: CPU −1.37% (95% CI −2.45 .. −0.30), wall −0.98%;
  - d20: CPU +1.66% (+0.10 .. +3.21), wall +2.35%.
- **NPS on a quiet runner** (workflow `opus-c1-nps.yml`, GitHub runner, g++-14 box recipe, 10 ABBA runs per
  build and depth, node counts equal). Run 40464077107, on the code before the review fix (`38cec76`):
  - lock → C1: d16 CPU +0.54% (95% CI −0.08 .. +1.16), d20 CPU +0.49% (−0.11 .. +1.09);
  - O3 → C1 (C1's own share): d16 CPU −1.26% (−2.27 .. −0.26), d20 CPU −0.57% (−1.06 .. −0.08).

  The guarded probe hook costs about 0.6-1.3% against the O3 base on this machine. The build after the
  review fix is measured by the run on the review-fix push (section "Review fix").

## Review fix: tablebase scores keep their distance in the TT
**The finding.** The code review asked for TB win scores to get their own ply adjustment in TT store/probe.
Before the fix, a TB score (`TbWin − ply`) was stored unchanged, so a transposition at another ply read it
back with the wrong distance. The win/draw/loss result was right; the distance was not.

**The fix** (`src/search/scores.inc`, `include/forge/syzygy.hpp`, `src/search/syzygy.inc`, `src/uci.cpp`):
- **The band.** TB scores live in a band just below the mate scores:
  |score| ∈ [`TbWinInMaxPly`, `TbWin`] = [31743, 31871].
- **The encoding.** `score_to_tt` and `score_from_tt` test that band with the same two compares the lock uses
  for mate scores (only the thresholds move down to the band). Inside the band, a score is a mate score, or a
  TB score while tables are loaded (`syzygy::tb_scores`, a plain flag that `load()` sets while no search
  runs). Such scores are stored as their distance from the storing node, and read back relative to the
  reading node.
- **Without tables** the band holds ordinary search scores (the eval clamp is ±31871), and they are stored
  unchanged, exactly as in AL1 s198. The default build therefore behaves as before (bench x5 identical).
- **Range.** A stored TB score stays at most `TbWin` and never reaches the mate range.
- **Hash clear.** Setting `SyzygyPath` now clears the hash, so the table never holds both encodings.

**Tests** (`tests/syzygy_tests.cpp`, `tt_score_encoding`, through the cold test hook
`syzygy::tt_score_round_trip`, which calls the search's own `score_to_tt` / `score_from_tt`):
- **Without tables:** mate scores keep their distance, and ordinary and TB-band scores come back unchanged
  (the lock's behaviour).
- **With tables:** TB wins and losses found at several plies, stored at plies 0/1/4/9 and read at plies
  0/2/5/9, come back with the distance shifted by exactly the ply difference, and stay below the mate range.
- **Results:** 36,825 checks, 0 failures with the 3-4-5 set (`logs/review_fix_syzygy_tests_345.log`); 166
  checks without tables (`logs/review_fix_syzygy_tests_no_tables.log`); UCI smoke test 0 failures
  (`logs/review_fix_uci_tb_smoke.log`).
- **Planted bugs:**
  - `score_to_tt` without the TB adjustment, i.e. the code before the review: 72 failures
    (`logs/review_fix_mutation_cold_path.log`, first version of the fix);
  - TB wins stored without their distance: 36 failures (`logs/review_fix_mutation_tb_tt.log`).

**Cost in the default build** (`logs/review_fix_codegen_vs_lock.log`, `review_fix_codegen_vs_c1.log`):
- **Identity:** bench at all 5 depths, perft and kiwipete are identical, FMA 0
  (`logs/review_fix_identity.log`).
- **Hot code:** `score_to_tt` / `score_from_tt` are inlined into the search, so `qsearch` (lock: identical
  until now) differs in 71 normalised lines (810 → 845 instructions) and alpha-beta in 193 more lines than
  before the fix. The common path keeps two compares per call. GCC now uses well-predicted branches instead
  of the lock's `cmov`; the mate and TB adjustments sit off the common path. Start addresses mod 64 are
  unchanged.
- **First version, rejected:** it called a cold function for the band, which cost 445 differing lines in
  `qsearch`.
- **Speed** (quiet runner, `opus-c1-nps.yml` run 40468518064 on `738a945`, `logs/ci/nps_738a945/`):
  - O3 → C1 with the fix: d16 CPU −0.85% (95% CI −1.58 .. −0.12), d20 CPU −0.60% (−1.52 .. +0.32);
  - lock → C1: +1.01% / +0.25%.

  These are the same as before the fix (O3 → C1 −1.26% / −0.57%), so the TB encoding adds no measurable
  cost. C1's OFF cost against its O3 base stays at about 0.6-1% on this machine (the probe hook in
  alpha-beta).

## Proposed gate (G-B6 in the test plan)
- **Match:** SPRT [0,10] at 10+0.1, candidate opus-C1 exe (PC lock recipe) vs the AL1 s198 lock exe.
- **Candidate options:** `setoption name SyzygyPath value <3-4-5 folder>` on the candidate only; everything
  else default (Threads 1, Hash 16, OwnBook false).
- **Seed:** QA's srand for G-B6 (the test plan lists one; it was not used here).
- **Runner:** tablebase adjudication off, so endgames are played out, and the candidate process must be able
  to read the table folder.

No Elo claim.

## Open issues / limitations
- **TT distances:** fixed after the code review (section "Review fix"). TB scores keep their distance in the
  TT while tables are loaded.
- **Null move and correction history:** both see TB scores as ordinary large scores (unchanged code;
  correction entries stay clamped).
- **7-piece tables:** 16-bit DTZ maps are implemented but untested, since only 3-5 piece files were used.
- **tbhits:** not printed in info lines; the counter is available as `syzygy::probe_hits`.
- **Tables:** stored at `D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345` (outside every repository).
  python-chess (oracle only) was installed in a scratch folder.

## Files
- **Engine:** `src/search/syzygy.inc`, `src/search/tablebase.inc`, `include/forge/syzygy.hpp`,
  `src/search/alphabeta.inc` (one guarded call), `src/search/iterative.inc` (root ranking),
  `src/search/searcher.inc`, `src/search.cpp`, `include/forge/search.hpp`, `src/uci.cpp`, and the option
  storage in `include/forge/search_options.hpp` / `src/search/options.inc`.
- **Tests:** `tests/syzygy_tests.cpp`, `tests/syzygy_fixtures.tsv`, `tests/syzygy_reference.tsv`,
  `CMakeLists.txt`.
- **CI:** `.github/workflows/opus-c1-syzygy.yml`, `opus-c1-nps.yml`.
- **`opus_round1/C1`:** `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `patch_vs_opus-O3.diff`,
  `make_fixture.py`, `api_cache.jsonl.gz`, `make_reference.py`, `download_tb.sh`, `ci_fetch_tables.sh`,
  `ci_syzygy.sh`, `uci_tb_smoke.py`, `mutation_check.sh`, `layout_check.py`, `logs/`, `SHA256SUMS`.
