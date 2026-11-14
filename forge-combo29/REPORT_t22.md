# Task t22 Report: Search Inventory, Detailed Findings of What Was Wrong / Missing, and What Changed

## Overview

Task `t22` audited the entire search implementation in `forge-combo29/src/search.cpp` and `forge-combo29/include/forge/search.hpp` on top of `integrate/combo29-fixes` (`bf5574ee654a773f0ef3d06878707056b90cdad7`), catalogued every search technique and tuning parameter, identified concrete flaws / structural omissions in the search, and implemented three independent candidates behind default-off UCI `check` options (`ContHist4PlyRead`, `NonPawnCorrection`, and `LmrDeeperShallower`) without modifying evaluation or NNUE code.

With all three new UCI options at their default (`false`), the engine is bit-for-bit node-identical to `integrate/combo29-fixes`:
- `bench 11`: `312866` nodes
- `bench 13`: `862329` nodes
- `bench 16`: `3024920` nodes
- `go perft 5` (startpos): `4865609` nodes
- All 10 `scripts/check_pins.sh` depths (11, 13, 16, 20, 22 with `UseNNUE true` and `UseNNUE false`) match `combo29` exactly.

---

## 1. In Detail: What Was Found and What Was Wrong / Missing in the Base Search

Auditing `src/search.cpp` and `include/forge/search.hpp` revealed a well-structured PVS alpha-beta engine, alongside three specific architectural defects / gaps that directly informed the three candidates, plus several notable omissions documented in the full inventory:

### Finding A — Dead/Write-Only 4-Ply Continuation History Polluting Shared Tables (Bug / Asymmetry in `src/search.cpp`)

**What was wrong in base (`bf5574ee`)**:
In `Worker::update_continuation` (`src/search.cpp:943-950` on base):
```cpp
void Worker::update_continuation(SearchStack* ss, Piece piece, int to, int bonus) {
    for (const int back : {1, 2, 4}) {
        const SearchStack* previous = ss - back;
        if (previous->continuation == nullptr || previous->current_move.is_none()) continue;
        apply_history((*previous->continuation)[static_cast<std::size_t>(piece)][static_cast<std::size_t>(to)],
                      back == 4 ? bonus / 2 : bonus);
    }
}
```
Every time a quiet move fails high (`update_quiet_stats`, lines 966 & 971) or beats `alpha` in a reduced LMR search (`search`, line 1431), the engine writes continuation bonuses and maluses into **one single shared 4D table** `ContinuationHistory` (`[13][64][13][64]`) for `ss - 1` (opponent's previous move), `ss - 2` (own previous move), **and `ss - 4` (own move two turns ago, weighted by `bonus / 2`)**.

However, when reading continuation history to score quiet moves, prune quiet moves, and adjust LMR reductions:
1. `MovePicker::QuietScorer` (`src/search.cpp:614-632` on base, active when `FORGE_SEARCH_SPEED2=1`) only fetched `cont1 = (ss - 1)->continuation` and `cont2 = (ss - 2)->continuation`.
2. `quiet_history_sum` (`src/search.cpp:179-187` on base) only summed `main + cont1 + cont2`.
3. `Worker::quiet_history` (`src/search.cpp:921-935` on base, used for shallow history pruning at line 1335, LMR reduction adjustment at line 1421, and non-`SPEED2` builds) also only read `ss - 1` and `ss - 2`.

Because Forge uses a **single unified `[prev_piece][prev_to][piece][to]` table** (not separate tables per ply offset), writing 4-ply-back associations into `continuation_history_` while never reading `(ss - 4)->continuation` had two negative effects:
1. All 4-ply continuation updates performed work and dirtied cache lines on every quiet cutoff and malus loop, yet 4-ply continuation context (`ss - 4`) was completely ignored when ordering moves, pruning bad quiet moves, or computing LMR depth adjustments.
2. Worse, because `(ss - 4)` is a same-side move (just like `(ss - 2)`), its half-weight updates modified the exact same `PieceToHistory` slices read by `(ss - 2)` without the search ever consulting `(ss - 4)` when that move actually occurred 4 plies earlier.

### Finding B — Static-Eval Correction History Blind to Piece Placement / King Safety (`src/search.cpp:802-870`)

**What was wrong / missing in base (`bf5574ee`)**:
In `Worker::corrected_eval` (`src/search.cpp:852-859` on base) and `Worker::update_correction` (`src/search.cpp:861-870` on base), static evaluation error `(best_score - static_eval)` was tracked in only two tables:
1. `correction_history_`, indexed by `board.pawn_key() & (CorrectionSize - 1U)` (pawn positions only).
2. `material_correction_`, indexed by `material_key(board) & (CorrectionSize - 1U)` (total piece counts per type/color only, ignoring squares).

That corrected `static_eval` drives almost every forward-pruning decision in Forge:
- Quiescence stand-pat and delta/futility base (`src/search.cpp:1036-1052`)
- Razoring (`src/search.cpp:1203`)
- Reverse futility pruning (`src/search.cpp:1209`)
- Null-move pruning gate and eval reduction (`src/search.cpp:1214-1220`)
- ProbCut SEE margin `probcut_beta - ss->static_eval` (`src/search.cpp:1260`)
- Child quiet futility pruning (`src/search.cpp:1331`)
- Improving flag (`ss->static_eval > (ss - 2)->static_eval`, `src/search.cpp:1195-1197`)

Whenever a position has a systematic evaluation error caused by **piece placement rather than pawn structure or material count** — for example, an exposed king after castling rights are lost or pieces swarm the kingside, trapped rooks/bishops, or an entrenched knight outpost while pawns stay fixed — every sibling node with the same pawn structure blends incompatible king/piece placements into one `pawn_key` bucket, washing out the correction signal. Base Forge had no non-pawn piece-placement correction history at all.

### Finding C — Flat, Unadjusted Post-LMR Re-Search Depth (`src/search.cpp:1422-1428`)

**What was wrong / suboptimal in base (`bf5574ee`)**:
In the LMR block of `Worker::search` (`src/search.cpp:1422-1428` on base):
```cpp
const int reduced_depth = std::clamp(new_depth - r, 1, new_depth);
score = -search(board, ss + 1, reduced_depth, -alpha - 1, -alpha, true);
full_depth_needed = score > alpha && reduced_depth < new_depth;
if (full_depth_needed) {
    score = -search(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
    full_depth_needed = false;
}
```
When a reduced zero-window search (`reduced_depth < new_depth`) failed high (`score > alpha`), Forge discarded the magnitude of `score` and unconditionally re-searched at the exact nominal `new_depth` (and then again at `new_depth` with full window `(-beta, -alpha)` on PV nodes if `score > alpha`).
- If the reduced search barely cleared `alpha` (e.g., `score < best_score + new_depth`), it still paid the full cost of a `new_depth` re-search even when `r == 1` meant `new_depth - 1 == reduced_depth`.
- Conversely, if a late move crushed the reduced search far above `best_score` (`score > best_score + 40 + 2 * new_depth`), signaling a sharp tactical refutation or missed threat, it received no extra ply in the confirmation search or PV search.
- Careful detail noticed while inspecting `src/search.cpp:1410`: `best_score` starts the move loop at `-Infinite` (`-32001`), **not** at `alpha`. However, LMR only executes when `move_count > 1` (or `> 2` at root, line 1412), so at least move 1 has already completed without aborting and raised `best_score` to a real search score (`>= -MateValue`), making `best_score + 40 + 2 * new_depth` and `best_score + new_depth` well-defined and free of overflow on every LMR move.

### Finding D — Other Notable Gaps Observed During the Full Audit (Not Selected to Stay Within the 3-Candidate Cap)

1. **Pawn History (`absent`)**: Quiet move ordering uses butterfly `[side][from][to]` plus `[prev_piece][prev_to][piece][to]` continuation history, with no `[pawn_key][piece][to]` table to remember quiet piece maneuvers tied to specific pawn structures.
2. **Capture-History LMR Adjustment (`absent`)**: Noisy moves enter LMR (`Reductions.noisy[d][m]` at line 1413), and `history` already holds `capture_history_value(board, move)` for captures at line 1323, yet line 1421 (`if (quiet) r -= ...`) only adjusts `r` for quiet moves; good/bad capture history never adjusts noisy LMR reductions.
3. **Quiet Checks in Quiescence (`partly`)**: When `qsearch` enters with `in_check == true`, `MovePicker` uses `EvasionTT` / `EvasionGenerate` and searches all legal check evasions (returning `mated_in(ply)` if `move_count == 0`). When `in_check == false`, `qsearch` only generates captures and promotions (`Mode::Quiescence` -> `generate_captures`), never quiet checking moves at ply 0 of quiescence.
4. **6-Ply Continuation History & Continuation Correction History (`absent`)**: Continuation history stops at `back = 4` (with `back = 6` absent), and correction history has no move-pair/continuation-indexed table.
5. **VM Toolchain Issue Encountered at `Start` (`environment`)**: On this Ubuntu 24.04 cloud VM, `/etc/alternatives/c++` pointed to `/usr/bin/clang++` (Clang 18.1.3), which selected `/usr/lib/gcc/x86_64-linux-gnu/14` as its GCC installation directory even though only `libstdc++-13-dev` (`g++ 13.3.0`) was installed (`gcc/14` had no `libstdc++.so` / headers). Consequently, plain `cmake` failed compiler detection with `/usr/bin/ld: cannot find -lstdc++`. Invoking CMake with `CXX=g++` resolved this cleanly.

---

## 2. Detailed Breakdown of What Changed on `carbon/t22-search-candidates`

Total engine diff across `include/` and `src/` is **71 insertions and 9 deletions** (80 changed lines total for all three candidates combined; rule 5 allows up to 150 changed lines per candidate):

### A. `forge-combo29/include/forge/search.hpp` (`+5 / -0`)
1. Declared three `bool` flags in `namespace forge::tune` (lines 268–270):
   - `extern bool ContHist4PlyRead;`
   - `extern bool NonPawnCorrection;`
   - `extern bool LmrDeeperShallower;`
2. Added two per-worker correction history tables on `class Worker` (lines 352–353):
   - `std::unique_ptr<CorrectionHistory> non_pawn_white_correction_;`
   - `std::unique_ptr<CorrectionHistory> non_pawn_black_correction_;`

### B. `forge-combo29/src/search.cpp` (`+53 / -9`)
1. **Default-off option definitions** (`lines 73–75`):
   - Initialized `ContHist4PlyRead = false`, `NonPawnCorrection = false`, `LmrDeeperShallower = false`.
2. **Candidate 1 — `ContHist4PlyRead`** (`lines 181–191`, `616–640`, `952–972`):
   - Extended `quiet_history_sum(...)` (under `#if FORGE_SEARCH_SPEED2`) with `const PieceToHistory* cont4` and added `if (cont4 != nullptr) score += (*cont4)[p][move.to] / 2;`.
   - Updated `MovePicker::QuietScorer` to initialize `cont4` to `(ss - 4)->continuation` when `tune::ContHist4PlyRead && ss != nullptr && !(ss - 4)->current_move.is_none()`, and `nullptr` otherwise (`stack_` starts search at `&stack_[4]`, so `ss - 4` is always in bounds even at `ply == 0`, where `(ss - 4)->current_move.is_none()` is `true`).
   - Updated `Worker::quiet_history(...)` in both `#if FORGE_SEARCH_SPEED2` and `#else` compilation paths to add `(*(ss - 4)->continuation)[piece][move.to] / 2` under the identical guard, keeping `FORGE_SEARCH_SPEED2=0` and `FORGE_SEARCH_SPEED2=1` bit-identical.
3. **Candidate 2 — `NonPawnCorrection`** (`lines 790–792`, `806–807`, `823–832`, `880–884`, `897–900`):
   - Allocated `non_pawn_white_correction_` and `non_pawn_black_correction_` in `Worker::Worker` and zeroed both in `Worker::clear()` (ensuring `ucinewgame` resets all state deterministically).
   - Added `non_pawn_key(const Board& board, Color color)`, a fast SplitMix-style hash over `board.pieces(color, type)` bitboards for `Knight` through `King` (`type = 2..6`).
   - In `Worker::corrected_eval`: when `tune::NonPawnCorrection` is `true`, looks up `np_w` and `np_b` for `[side][key & (CorrectionSize - 1U)]` and adds `(np_w + np_b) / 2` to `correction` prior to `correction / CorrectionGrain`.
   - In `Worker::update_correction`: when `tune::NonPawnCorrection` is `true`, updates both tables using the same `apply` helper (`diff * weight / 256` clamped to `[-CorrectionLimit, CorrectionLimit]`) as pawn and material correction history.
4. **Candidate 3 — `LmrDeeperShallower`** (`lines 1419`, `1463–1470`):
   - Changed `new_depth` from `const int` to `int` so post-LMR adjustments propagate into both the zero-window re-search and any subsequent PV full-window re-search.
   - Inside `if (full_depth_needed)` after the reduced LMR search beats `alpha`: when `tune::LmrDeeperShallower` is `true`, computes `do_deeper = score > best_score + 40 + 2 * new_depth` and `do_shallower = score < best_score + new_depth`, adjusts `new_depth += int(do_deeper) - int(do_shallower)`, and only runs the zero-window full-depth re-search if `reduced_depth < new_depth`.

### C. `forge-combo29/src/uci.cpp` (`+13 / -0`)
1. Advertised all three options in the `uci` response (`lines 184–186`):
   - `option name ContHist4PlyRead type check default false`
   - `option name NonPawnCorrection type check default false`
   - `option name LmrDeeperShallower type check default false`
2. Parsed `setoption name <Option> value <true|false>` (`lines 299–308`), emitting `info string invalid value for option <Name>` on malformed values (matching `Ponder`, `OwnBook`, and `UseNNUE`).

### D. `forge-combo29/tests_t22/` (New Test Files)
1. `forge-combo29/tests_t22/search_candidates_test.cpp`:
   - Verifies default-off parity (`bench 11` = 312866, `bench 13` = 862329, `perft 5` = 4865609).
   - Builds 200 diverse legal positions from 25 opening/middlegame/endgame seed FENs via deterministic pseudo-random legal rollouts.
   - For each candidate (`ContHist4PlyRead`, `NonPawnCorrection`, `LmrDeeperShallower`): enables only that option, verifies `bench 13` produces a different non-zero node count than 862329, runs 200 searches to `depth = 10` (clearing every 25 searches so history/correction tables exercise both cross-search accumulation and clean resets), and verifies every returned `best_move` is non-null, passes `board.is_legal(best_move)`, and appears in `board.legal_moves()`.
   - Resets all three options to `false` at the end and confirms `bench 13` returns to `862329`.
2. `forge-combo29/tests_t22/uci_candidates.txt`:
   - Plain UCI command script exercising `uci`, baseline `bench 11`/`13`/`16`, `go perft 5`, toggling each candidate option on and off through UCI `setoption`, and checking `bench 11` and `bench 13` node counts.

---

## 3. Search Inventory Table

Line numbers below list the original `integrate/combo29-fixes` (`bf5574ee`) line numbers first, followed by post-t22 line numbers where shifted in `src/search.cpp` / `include/forge/search.hpp`.

| Search Technique | Status (in base `bf5574ee`) | Line Numbers (`bf5574ee` -> `t22`) | Tuning Options (`forge::tune`) |
|---|---|---|---|
| Aspiration windows | present | `src/search.cpp:51, 93, 1661-1682` (`-> 51, 96, 1705-1726`); `include/forge/search.hpp:245` | `AspirationDelta` |
| Principal-variation search (PVS) | present | `src/search.cpp:1121, 1411, 1423, 1426, 1435, 1437-1439` (`-> 1158, 1448, 1460, 1463-1470, 1479, 1481-1483`) | (none) |
| Null-move pruning and verification | present (verification at `depth >= 14`) | `src/search.cpp:25-28, 77-80, 1213-1251` (`-> 25-28, 80-83, 1250-1288`); `include/forge/search.hpp:220-223, 299, 378-379` (`-> 220-223, 302, 383-384`) | `NullMoveMinDepth`, `NullMoveBase`, `NullMoveDepthDivisor`, `NullMoveEvalDivisor` |
| Reverse futility pruning (RFP) | present | `src/search.cpp:29-31, 81-82, 1208-1212` (`-> 29-31, 84-85, 1245-1249`); `include/forge/search.hpp:224-226` | `RfpDepth`, `RfpMargin`, `RfpImproving` |
| Futility pruning (quiet moves) | present (child futility on `lmr_depth`) | `src/search.cpp:35-37, 84-85, 1329-1334` (`-> 35-37, 87-88, 1366-1371`); `include/forge/search.hpp:230-232` | `FutilityDepth`, `FutilityBase`, `FutilityMultiplier` |
| Futility pruning (captures) | partly (implemented, default off: `CaptureFutilityBase = 0`) | `src/search.cpp:69-71, 106-107, 1340-1345` (`-> 69-71, 109-110, 1377-1382`); `include/forge/search.hpp:264-266` | `CaptureFutilityBase`, `CaptureFutilityMultiplier`, `CaptureFutilityDepth` |
| Razoring | present | `src/search.cpp:32-34, 82-83, 1202-1207` (`-> 32-34, 85-86, 1239-1244`); `include/forge/search.hpp:227-229` | `RazorDepth`, `RazorBase`, `RazorMultiplier` |
| Late-move reductions (LMR) and adjustments | partly (log-product tables for quiet & noisy; adjusted by `tt_pv`, `!improving`, `cut_node`, `tt_capture && quiet`, `gives_check`, `in_check`, child `cutoff_count`, quiet `history`; no capture-history LMR term; post-LMR deeper/shallower re-search adjustment absent in base, added behind `LmrDeeperShallower`) | `src/search.cpp:21-24, 55, 57, 75-76, 97, 99, 133-155, 1412-1433` (`-> 21-24, 55, 57, 78-79, 100, 102, 136-158, 1449-1477`); `include/forge/search.hpp:216-219, 249, 251` | `LmrQuietBase`, `LmrQuietDivisor`, `LmrNoisyBase`, `LmrNoisyDivisor`, `LmrHistoryDivisor`, `LmrCutoffThreshold` (+ `LmrDeeperShallower`) |
| Late-move pruning (LMP / move-count pruning) | present | `src/search.cpp:38, 86, 157-159, 1327` (`-> 38, 89, 160-162, 1364`); `include/forge/search.hpp:233` | `LmpBase` |
| History pruning (quiet moves) | present | `src/search.cpp:39-40, 86-87, 1335` (`-> 39-40, 89-90, 1372`); `include/forge/search.hpp:234-235` | `HistoryPruneDepth`, `HistoryPruneMultiplier` |
| Static-exchange pruning of captures | present (in MovePicker good/bad split, qsearch, and main search) | `src/search.cpp:43, 50, 89, 93, 464, 1069, 1346-1348` (`-> 43, 50, 92, 96, 468, 1106, 1383-1385`); `include/forge/search.hpp:237, 244` | `SeeNoisyMultiplier`, `QsSeeMargin` |
| Static-exchange pruning of quiet moves | present | `src/search.cpp:42, 88, 1336` (`-> 42, 91, 1373`); `include/forge/search.hpp:236` | `SeeQuietMultiplier` |
| Main history (butterfly `[side][from][to]`) | present (gravity updates + PV non-cutoff bonus) | `src/search.cpp:52-54, 94-96, 161-168, 179-187, 614-633, 921-935, 965, 970, 1477-1479` (`-> 52-54, 97-99, 164-171, 182-192, 618-640, 952-972, 1002, 1007, 1521-1523`); `include/forge/search.hpp:246-248, 274, 343` (`-> 246-248, 277, 346`) | `HistoryBonusQuadratic`, `HistoryBonusLinear`, `HistoryBonusMax` |
| Capture history (`[moved_piece][to][victim_type]`) | present | `src/search.cpp:680-693, 937-941, 975-989, 1323` (`-> 687-700, 974-978, 1012-1026, 1360`); `include/forge/search.hpp:277, 344` (`-> 280, 347`) | `HistoryBonusQuadratic`, `HistoryBonusLinear`, `HistoryBonusMax` |
| Continuation history (`[prev_piece][prev_to][piece][to]`) | partly (`update_continuation` writes plies 1, 2, and 4 back, with ply 4 at `bonus / 2`, but `quiet_history` / `QuietScorer` only read plies 1 and 2 back in base; ply 6 absent; fail-low bonus default off; 4-ply read added behind `ContHist4PlyRead`) | `src/search.cpp:72, 107, 179-187, 614-633, 921-950, 966, 971, 1431, 1480-1485` (`-> 72, 110, 182-192, 618-640, 952-987, 1003, 1008, 1475, 1524-1529`); `include/forge/search.hpp:267, 275-276, 300, 345` (`-> 267, 278-279, 303, 348`) | `HistoryBonusQuadratic`, `HistoryBonusLinear`, `HistoryBonusMax`, `FailLowContinuationBonus` (+ `ContHist4PlyRead`) |
| Countermove heuristic & killers | present (2 killers per ply + `[prev_piece][prev_to]` countermove) | `src/search.cpp:438-444, 477-490, 955-963` (`-> 442-448, 481-494, 992-1000`); `include/forge/search.hpp:278, 290, 346` (`-> 281, 293, 349`) | (none) |
| Pawn history (quiet move ordering indexed by pawn structure) | absent | — | (none) |
| Correction history | partly (pawn-hash correction history and material-count-hash correction history present; non-pawn piece-placement correction history absent in base, added behind `NonPawnCorrection`; continuation/minor-piece correction histories absent) | `src/search.cpp:58, 100, 802-810, 852-870, 1036, 1186, 1496-1502` (`-> 58, 103, 812-833, 874-901, 1073, 1223, 1540-1546`); `include/forge/search.hpp:252, 279-282, 347-348` (`-> 252, 282-285, 350-353`) | `MaterialCorrectionWeight` (+ `NonPawnCorrection`) |
| Singular extensions (single, double, negative, multi-cut) | present (single `+1`, double `+2` capped at `<= 6` along path on non-PV, multi-cut return `singular_beta` when `singular_beta >= beta`, negative `-2` if `tt_score >= beta` and `-1` if `cut_node`) | `src/search.cpp:44-45, 90, 1128-1129, 1354-1376, 1381` (`-> 44-45, 93, 1165-1166, 1391-1413, 1418`); `include/forge/search.hpp:238-239, 289, 296` (`-> 238-239, 292, 299`) | `SingularDepth`, `SingularMargin` |
| ProbCut | present (qsearch pre-filter followed by `depth - 4` search) | `src/search.cpp:47-48, 91-92, 1252-1286` (`-> 47-48, 94-95, 1289-1323`); `include/forge/search.hpp:241-242` | `ProbcutDepth`, `ProbcutMargin` |
| Internal iterative reductions (IIR) | present (`--depth` when `!in_check && depth >= IirDepth && tt_move.is_none() && (pv_node || cut_node)`) | `src/search.cpp:46, 91, 1290` (`-> 46, 94, 1327`); `include/forge/search.hpp:240` | `IirDepth` |
| Hash-table cutoffs in quiescence | present (non-PV exact/lower/upper TT cutoffs + static eval bound refinement + stand-pat/end-of-qsearch stores) | `src/search.cpp:1009-1025, 1037-1050, 1108-1114` (`-> 1046-1062, 1074-1087, 1145-1151`) | (none) |
| Mate-distance pruning | present | `src/search.cpp:130-131, 1140-1143` (`-> 133-134, 1177-1180`) | (none) |
| Check extensions | present (`+1` when `gives_check && depth >= CheckExtensionDepth && !root_node && see_ge(move, 0)`) | `src/search.cpp:56, 98, 1377-1380` (`-> 56, 101, 1414-1417`); `include/forge/search.hpp:250` | `CheckExtensionDepth` |
| Checks in quiescence | partly (full check evasions generated when already `in_check`; quiet checking moves when not in check are absent) | `src/search.cpp:435-437, 514-538, 1029-1031, 1056-1062, 1106` (`-> 439-441, 518-542, 1066-1068, 1093-1099, 1143`) | (none) |
| Delta / futility pruning in quiescence | present (`futility_base = static_eval + QsFutilityMargin`, prunes non-checking non-promotions where `futility_base + capture_value <= alpha`) | `src/search.cpp:49, 92, 1052, 1064-1068` (`-> 49, 95, 1089, 1101-1105`); `include/forge/search.hpp:243` | `QsFutilityMargin` |
| Hash-table ageing and replacement | present (5-bit generation incremented in `new_search()`, refreshed on TT probe hit, 4-way cluster replacement minimizing `depth - 4 * relative_age`, overwrite policy on store, 50-move `score_usable` guard) | `src/search.cpp:270-406, 1794` (`-> 274-410, 1838`); `include/forge/search.hpp:75-102, 127-132` | (none; `Hash` UCI option sets size) |
| Time management (best-move stability, node share, score swings) | present (soft/hard budget, stability scale at 0 / >=3 / >=6 stable iterations, root best-move node-effort fraction scale, falling-eval extension, minimum factor clamp) | `src/search.cpp:59-68, 101-105, 1530-1556, 1708-1740` (`-> 59-68, 104-108, 1574-1600, 1752-1784`); `include/forge/search.hpp:254-263, 350-352, 361-363` (`-> 254-263, 355-357, 366-368`) | `TmSoftDivisor`, `TmIncrementPercent`, `TmHardPercent`, `TmHardSoftMultiple`, `TmStableFactor`, `TmSemiStableFactor`, `TmUnstableFactor`, `TmEffortBase`, `TmFallingEvalPercent`, `TmMinFactorPercent` |

---

## 4. Candidate Reference Cards for Match Testing

None of the owner's previously rejected candidates (`EvalOptimism`, `RfpReturnBlend`, enhanced transposition cutoffs, `LmrCapVictim`, `NullMoveMinDepth=2`, `CaptureFutilityBase=300`, `FailLowContinuationBonus`, `SingularMargin=1`, `ProbcutDepth=4`, `LmrHistoryDivisor=4000`, `RfpMargin=60`, or refreshing a hash entry's age on a hit) were used.

| Candidate UCI Option | Match Runner Option Line | `bench 11` (Off / On) | `bench 13` (Off / On) | Origin / Reference |
|---|---|---|---|---|
| `ContHist4PlyRead` | `option.ContHist4PlyRead=true` | `312866` / `335384` | `862329` / `989877` | Direct audit of read/write asymmetry in `src/search.cpp` + Chess Programming Wiki (*Continuation History*) |
| `NonPawnCorrection` | `option.NonPawnCorrection=true` | `312866` / `293735` | `862329` / `775585` | Chess Programming Wiki (*Correction History* — non-pawn piece-placement correction) |
| `LmrDeeperShallower` | `option.LmrDeeperShallower=true` | `312866` / `336538` | `862329` / `813907` | Chess Programming Wiki (*Late Move Reductions* — post-LMR re-search depth adjustment) |

---

## 5. Commands Run and Full Outputs

*Environment note*: On this Ubuntu 24.04 cloud VM, `/usr/bin/c++` pointed to `clang++-18` while only `libstdc++-13-dev` (`g++ 13.3.0`) headers/libraries were installed alongside a bare `gcc-14` directory stub, causing default `cmake` without `CXX=g++` to fail CMake's compiler link check (`cannot find -lstdc++`). Setting `CXX=g++` builds cleanly with GNU 13.3.0. In addition, the VM CPU does not have AVX-512, so `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` was used as specified in `Start`.

### A. Initial `Start` Baseline Verification (before any changes)

Command:
```bash
CXX=g++ cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Output:
```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Configuring done (0.4s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 171 nps 1829625
info string bench depth 13 nodes 862329 time 449 nps 1920554
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

Baseline `bench 16` check:
```bash
git rev-parse HEAD && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 16\nquit\n' | ./build/forge
```
Output:
```text
bf5574ee654a773f0ef3d06878707056b90cdad7
info string bench depth 16 nodes 3024920 time 1497 nps 2020654
```

### B. Post-Change Release Build, Rule 7 Numbers, `bench 16`, `uci` Listing, and Candidate Node Counts

Command:
```bash
rm -rf build && CXX=g++ cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j && ./build/forge < forge-combo29/tests_t22/uci_candidates.txt
```

Output:
```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
id name Chess Engine Forge 6.4.24 candidate
id author OpenAI
option name Hash type spin default 32 min 1 max 2048
option name Threads type spin default 1 min 1 max 256
option name Move Overhead type spin default 10 min 0 max 1000
option name Ponder type check default false
option name OwnBook type check default true
option name Book File type string default <empty>
option name Book Depth type spin default 30 min 0 max 100
option name Book Variety type spin default 30 min 0 max 100
option name UseNNUE type check default true
option name NnueFile type string default <empty>
option name ContHist4PlyRead type check default false
option name NonPawnCorrection type check default false
option name LmrDeeperShallower type check default false
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name QsSeeMargin type spin default 40 min 0 max 500
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name TmSoftDivisor type spin default 22 min 5 max 80
option name TmIncrementPercent type spin default 75 min 0 max 150
option name TmHardPercent type spin default 60 min 10 max 95
option name TmHardSoftMultiple type spin default 5 min 1 max 20
option name TmStableFactor type spin default 60 min 20 max 150
option name TmSemiStableFactor type spin default 80 min 20 max 150
option name TmUnstableFactor type spin default 140 min 50 max 300
option name TmEffortBase type spin default 155 min 100 max 250
option name TmFallingEvalPercent type spin default 100 min 0 max 400
option name TmMinFactorPercent type spin default 45 min 10 max 100
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
option name CaptureFutilityDepth type spin default 6 min 0 max 15
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name Clear Hash type button
uciok
info string bench depth 11 nodes 312866 time 168 nps 1862297
info string bench depth 13 nodes 862329 time 448 nps 1924841
info string bench depth 16 nodes 3024920 time 1487 nps 2034243
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
info string bench depth 11 nodes 335384 time 174 nps 1927494
info string bench depth 13 nodes 989877 time 522 nps 1896316
info string bench depth 11 nodes 293735 time 156 nps 1882916
info string bench depth 13 nodes 775585 time 415 nps 1868879
info string bench depth 11 nodes 336538 time 178 nps 1890662
info string bench depth 13 nodes 813907 time 416 nps 1956507
info string bench depth 13 nodes 862329 time 444 nps 1942182
```

### C. Full `check_pins.sh` Verification (depths 11, 13, 16, 20, 22 with NNUE on and off + perft 5)

Command:
```bash
bash forge-combo29/scripts/check_pins.sh ./build/forge
```

Output:
```text
net-on : 312866 862329 3024920 12389307 34048354
net-off: 375354 907205 2448617 13573040 24506465
perft5 : 4865609
PINS MATCH combo29
```

### D. `tests_t22/search_candidates_test.cpp` (Release Build)

Command:
```bash
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp forge-combo29/tests_t22/search_candidates_test.cpp -pthread -o /tmp/t22_test_release && /tmp/t22_test_release
```

Output:
```text
defaults bench11 312866 bench13 862329 perft5 4865609
candidate ContHist4PlyRead bench13_on 989877 bench13_off 862329
candidate ContHist4PlyRead searches 200 depth 10 legal_ok 1 total_nodes 3932164
candidate NonPawnCorrection bench13_on 775585 bench13_off 862329
candidate NonPawnCorrection searches 200 depth 10 legal_ok 1 total_nodes 3828541
candidate LmrDeeperShallower bench13_on 813907 bench13_off 862329
candidate LmrDeeperShallower searches 200 depth 10 legal_ok 1 total_nodes 3871269
defaults_after bench13 862329
PASS t22 search_candidates_test
```

### E. `tests_t22/search_candidates_test.cpp` (Built with `-fsanitize=address,undefined`)

Command:
```bash
g++ -std=c++20 -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=all -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp forge-combo29/tests_t22/search_candidates_test.cpp -pthread -o /tmp/t22_test_san && /tmp/t22_test_san
```

Output:
```text
defaults bench11 312866 bench13 862329 perft5 4865609
candidate ContHist4PlyRead bench13_on 989877 bench13_off 862329
candidate ContHist4PlyRead searches 200 depth 10 legal_ok 1 total_nodes 3932164
candidate NonPawnCorrection bench13_on 775585 bench13_off 862329
candidate NonPawnCorrection searches 200 depth 10 legal_ok 1 total_nodes 3828541
candidate LmrDeeperShallower bench13_on 813907 bench13_off 862329
candidate LmrDeeperShallower searches 200 depth 10 legal_ok 1 total_nodes 3871269
defaults_after bench13 862329
PASS t22 search_candidates_test
```

### F. Full UCI Binary Built with `-fsanitize=address,undefined` Running `tests_t22/uci_candidates.txt`

Command:
```bash
g++ -std=c++20 -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=all -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/src/*.cpp -pthread -o /tmp/forge_san && /tmp/forge_san < forge-combo29/tests_t22/uci_candidates.txt
```

Output:
```text
id name Chess Engine Forge 6.4.24 candidate
id author OpenAI
option name Hash type spin default 32 min 1 max 2048
option name Threads type spin default 1 min 1 max 256
option name Move Overhead type spin default 10 min 0 max 1000
option name Ponder type check default false
option name OwnBook type check default true
option name Book File type string default <empty>
option name Book Depth type spin default 30 min 0 max 100
option name Book Variety type spin default 30 min 0 max 100
option name UseNNUE type check default true
option name NnueFile type string default <empty>
option name ContHist4PlyRead type check default false
option name NonPawnCorrection type check default false
option name LmrDeeperShallower type check default false
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name QsSeeMargin type spin default 40 min 0 max 500
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name TmSoftDivisor type spin default 22 min 5 max 80
option name TmIncrementPercent type spin default 75 min 0 max 150
option name TmHardPercent type spin default 60 min 10 max 95
option name TmHardSoftMultiple type spin default 5 min 1 max 20
option name TmStableFactor type spin default 60 min 20 max 150
option name TmSemiStableFactor type spin default 80 min 20 max 150
option name TmUnstableFactor type spin default 140 min 50 max 300
option name TmEffortBase type spin default 155 min 100 max 250
option name TmFallingEvalPercent type spin default 100 min 0 max 400
option name TmMinFactorPercent type spin default 45 min 10 max 100
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
option name CaptureFutilityDepth type spin default 6 min 0 max 15
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name Clear Hash type button
uciok
info string bench depth 11 nodes 312866 time 1582 nps 197766
info string bench depth 13 nodes 862329 time 4420 nps 195097
info string bench depth 16 nodes 3024920 time 14762 nps 204912
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
info string bench depth 11 nodes 335384 time 1711 nps 196016
info string bench depth 13 nodes 989877 time 5137 nps 192695
info string bench depth 11 nodes 293735 time 1652 nps 177805
info string bench depth 13 nodes 775585 time 4155 nps 186663
info string bench depth 11 nodes 336538 time 1715 nps 196232
info string bench depth 13 nodes 813907 time 4224 nps 192686
info string bench depth 13 nodes 862329 time 4430 nps 194656
```

### G. Non-`FORGE_SEARCH_SPEED2` Build Path Verification

Command:
```bash
g++ -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=0 -DFORGE_SPD_NO_ZERO_MOVELISTS=0 -DFORGE_SEARCH_SPEED2=0 -DFORGE_SPD_PREFETCH_EARLY=0 -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 -I forge-combo29/include forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp forge-combo29/src/book.cpp forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp forge-combo29/tests_t22/search_candidates_test.cpp -pthread -o /tmp/t22_test_nospeed2 && /tmp/t22_test_nospeed2
```

Output:
```text
defaults bench11 312866 bench13 862329 perft5 4865609
candidate ContHist4PlyRead bench13_on 989877 bench13_off 862329
candidate ContHist4PlyRead searches 200 depth 10 legal_ok 1 total_nodes 3932164
candidate NonPawnCorrection bench13_on 775585 bench13_off 862329
candidate NonPawnCorrection searches 200 depth 10 legal_ok 1 total_nodes 3828541
candidate LmrDeeperShallower bench13_on 813907 bench13_off 862329
candidate LmrDeeperShallower searches 200 depth 10 legal_ok 1 total_nodes 3871269
defaults_after bench13 862329
PASS t22 search_candidates_test
```

### H. Existing Regression Tests (`tests_t1`, `tests_t3`, `tests_t6`, `tests_t8`)

Commands and outputs:
```text
$ /tmp/t1_test
in_check 0
losing_captures 68
bestmove d3b1
nodes 176

$ /tmp/t3_test
clock_parse_test passed

$ /tmp/t6_test
fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
depth 1 score 1 move d2d4 nodes 26
depth 2 score 49 move d2d4 nodes 54
depth 3 score 18 move e2e4 nodes 215
span depth 2 nodes 54 -> depth 3 nodes 215
nodes 55 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 75 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 95 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 115 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 135 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 155 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 175 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
nodes 195 depth 2 score 49 move d2d4 finished-score 49 finished-move d2d4 PASS
fen 8/8/8/8/4k3/8/3R4/4K3 w - - 0 1
depth 1 score 409 move e1f2 nodes 32
depth 2 score 432 move e1f2 nodes 58
depth 3 score 419 move e1e2 nodes 160
span depth 2 nodes 58 -> depth 3 nodes 160
nodes 59 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 71 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 83 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 95 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 107 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 119 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 131 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 143 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
nodes 155 depth 2 score 432 move e1f2 finished-score 432 finished-move e1f2 PASS
PASS fixed-node score and move agree

$ /tmp/t8_convert /tmp/t8_lock.nnue && /tmp/t8_test /tmp/t8_lock.nnue
wrote /tmp/t8_lock.nnue hidden 256
ok load converted net
ok startpos eval matches built-in net
ok kiwipete eval matches built-in net
ok converted file is non-empty
ok load shifted bias
ok shifted bias changes an evaluation
ok empty path restores built-in net
ok restored eval matches built-in net
ok bad magic keeps the current net
ok eval unchanged after bad magic
ok wrong version keeps the current net
ok wrong hidden size keeps the current net
ok truncated file keeps the current net
ok oversized file keeps the current net
ok missing file keeps the current net
ok eval unchanged after rejected files
PASS
```

---

## 6. What Could Not Be Verified

1. **Playing strength (Elo) and SPRT match results**: Can only be measured by self-play / gauntlet matches on the owner's PC.
2. **Windows Clang ThinLTO + PGO (`znver5`, AVX-512 / BMI2 `PEXT` + `ZMM`) build and hardware throughput**: This Linux cloud VM lacks AVX-512 and the Windows `llvm-mingw` clang 23.1.5 toolchain, so builds used Linux `g++ 13.3.0` with `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`.
3. **Clang compilation on this VM**: `clang++-18` is installed without a matching `libstdc++-14-dev` or `libc++-dev` package, so C++ compilation on this VM used `g++ 13.3.0`.
