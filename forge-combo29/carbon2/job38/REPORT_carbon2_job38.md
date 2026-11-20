# REPORT — `carbon2` — Job 38

- **Top-Line Summary:**
  - **(1) Step 0:** `PASS (1 == 1)` — `exe B` (`6b98f2170a3210e71beed04bbd2553972c253ed7`, `g++` 13.3.0 Release, `sha256 = e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`): `bench 11` `PASS (312866 == 312866)`, `bench 13` `PASS (862329 == 862329)`, `bench 16` `PASS (3024920 == 3024920)`, `go perft 5` `PASS (4865609 == 4865609)`, `S14` on `O` (`200` FENs, `d12`) `PASS (9500069 == 9500069)`, `S14` on `G` (`353` FENs, `d12`) `PASS (18466239 == 18466239)`.
  - **(2) Prediction Graded (`prediction_job38.txt`, committed alone in `879b2dc11` at `2026-11-20T12:30:07+00:00`):** **`2/4` HIT** — `(1)` `A1` `031` switch-on `O` rows equal seat's committed rows: predicted `yes`, measured `yes` (`10937472 == 10937472`, `0/200` differ) **HIT**; `(2)` `A3` `s10_variant` match Elo vs off: predicted `0.0` (`[-15.0, +15.0]`), measured `-33.08 +/- 10.12 Elo` **MISS**; `(3)` Part B twin pairs with equal switch-on `O` rows: predicted `0`, measured `1` (`S32: 024 vs 074`) **MISS**; `(4)` Part C first patch read has at least one finding: predicted `no`, measured `no` (`024` `S32` is `CLEAN`) **HIT**.
  - **(3) Part A (`S10` — seats `031` and `081`, plus `s10_variant.patch.txt`):**
    - **A1:** Both `031` and `081` apply cleanly, pass all four honesty numbers, match `exe B` `200/200` on `O` and `353/353` on `G` with `IdeaS10=false`, and match their own committed switch-on `O` rows `200/200` (`031`: `10937472 == 10937472`, `195 == 195` differ from base, `0 == 0` differ from `P_on_O_d12.nodes.txt`; `081`: `9542904 == 9542904`, `10 == 10` differ from base, `0 == 0` differ from `O_p_on_d12.nodes.txt`).
    - **A2:** `031` shrinks `best_score` at `src/search.cpp:2154-2157` (`768/1024`) **without checking `(alpha, beta)`** (corrupting fail-highs `>= beta` and fail-lows `<= alpha`), and runs its 2-ply wide-window probe (`lo..hi` width `60`) on the **outer node's own `SearchStack* ss`** (`src/search.cpp:1615`), clobbering `ss->killers`, `ss->raw_eval`, `ss->tt_pv` (forced `true`), `ss->static_eval`, and `ss->pv` / `ss->pv_length`.
    - **A3:** `s10_variant.patch.txt` restricts the shrink to `orig_alpha < best_score && best_score < beta` (`orig_alpha` saved before `alpha` is raised inside the move loop) and runs the probe on a dedicated `shuffle_stack_`. Proofs all pass (`O` on sum `11,389,229`, `148/200` differ from base). In `1,106` games (`nodes=20000`, `Threads=1`, `Hash=16`, `S14`, `OG553.epd`), **`s10_variant` scores `258-363-485` (`-33.08 +/- 10.12 Elo`)** vs **`031` at `183-493-430` (`-100.06 +/- 11.96 Elo`)** — recovering **`+66.98 Elo`** by fixing the fail-high/fail-low shrink and stack-frame clobbering, while remaining `-33.08 +/- 10.12 Elo` behind switch-off because `031`'s remaining gates (`defender_holds` tautologically true when `stm == winner`, `|eval| >= 80` without pawn-structure check, and `2`-ply probe cost) still misclassify ordinary winning positions as shuffles.
  - **(4) Part B (Five Twin Pairs across 10 Seats):** All `10` seats pass `git apply --check`, all four numbers, `off == base` on `O` (`9500069 == 9500069`), and `0/200` differences vs each seat's own committed switch-on `O` rows. **`1/5` twin pair is EQUAL** (`S32`: `024` `9,547,450` == `074` `9,547,450`, `0/200` differ); **`4/5` twin pairs are DIFFERENT** (`200/200` differ on each: `B1` `030` `10,081,213` vs `080` `9,748,678`; `K4` `043` `8,983,632` vs `093` `8,921,190`; `B8` `028` `9,718,009` vs `078` `9,295,189`; `S13` `016` `9,722,445` vs `066` `9,656,004`).
  - **(5) Part C (Line-by-Line Hunk Audit):** Audited in required order: Patch 1 = Seat `024` (`IdeaS32`, `14` hunks) -> **`CLEAN`**; Patch 2 = Seat `030` (`IdeaB1`, `11` hunks) -> **`CLEAN`**.
- **Timeline (`stamps.txt` & `git log`):**
  - Job 38 fetched: `Fri Nov 20 12:23:40 PM UTC 2026` (claim pushed at `Fri Nov 20 12:24:26 PM UTC 2026`)
  - Step 0 commit `f61323f18`: `2026-11-20T12:28:56+00:00` (`step0_raw.txt` finished `Fri Nov 20 12:28:38 PM UTC 2026`)
  - Prediction commit `879b2dc11` (alone): `2026-11-20T12:30:07+00:00`
  - Part A commit `44aa19a23`: `2026-11-20T13:02:31+00:00`
  - Part B commit `cacde56ee`: `2026-11-20T13:08:02+00:00`
  - Part C commit `2c9feaa9e`: `2026-11-20T13:10:05+00:00` (Minute 46 — 33 minutes before Minute 80 hard stop `1:43:40 PM UTC`)

---

## WHAT THIS CANNOT SEE

The PC's engine (r15d with the speed work), the PC's net and settings, Windows; strength at the PC's node counts; a
1,106-game match carries about +/- 10 Elo.

---

## (1) Step 0 — Base Engine `exe B` (`6b98f2170a3210e71beed04bbd2553972c253ed7`)

Built from `6b98f2170a3210e71beed04bbd2553972c253ed7` (`forge-combo29/`) in Release with `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` (`libstdc++`, CMake `3.28.3`; exact flags in `forge-combo29/carbon2/job38/builds.txt`; raw verification in `step0_raw.txt`, `B_O_d12.nodes.txt`, `B_O_d12.meta`, `B_G_d12.nodes.txt`, `B_G_d12.meta`):

- `exe B` `sha256`: `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`
- No-option `bench 11` (fresh process): `PASS (312866 == 312866)`
- No-option `bench 13` (fresh process): `PASS (862329 == 862329)`
- No-option `bench 16` (fresh process): `PASS (3024920 == 3024920)`
- No-option `go perft 5` (fresh process): `PASS (4865609 == 4865609)`
- `S14` (`Threads=1, Hash=16, NullThreatVerify=true, EvasionOrdering=true, BadCapLmr=true`) on `O` (`opening_200.epd`, `d12`, fresh `ucinewgame` per FEN):
  - Position count: `PASS (200 == 200)`
  - Node sum: `PASS (9500069 == 9500069)`
  - Position 1 nodes: `PASS (41311 == 41311)`
  - Position 2 nodes: `PASS (24872 == 24872)`
  - Position 3 nodes: `PASS (28574 == 28574)`
- `S14` on `G` (`gated_353.epd`, `d12`, fresh `ucinewgame` per FEN):
  - Position count: `PASS (353 == 353)`
  - Node sum: `PASS (18466239 == 18466239)`

---

## (2) Prediction Graded (`prediction_job38.txt`, commit `879b2dc11`)

Committed **alone** in `879b2dc115bdc64055291c546ebbab16b9fc3db4` (`2026-11-20T12:30:07+00:00`) before Part A's first measuring run, and never edited afterwards:

| # | Question | Pre-Committed Prediction | Measured Result | Grade |
|---:|---|---|---|---|
| `(1)` | `A1`: rebuild of seat `031` gives its committed switch-on `O` rows (`yes` / `no`) | `yes` | `yes` (`10937472 == 10937472`, `0/200` differ vs `P_on_O_d12.nodes.txt`) | **HIT** |
| `(2)` | `A3`: match Elo of `031`'s variant vs switch off (wrong outside range) | `0.0 Elo` (wrong outside `[-15.0, +15.0] Elo`) | `-33.08 +/- 10.12 Elo` (`258-363-485` in `1,106` games; outside `[-15.0, +15.0]`) | **MISS** |
| `(3)` | `Part B`: of the `5` twin pairs, how many have equal switch-on `O` rows (`0` to `5`) | `0` | `1` (`S32`: `024` `9,547,450` == `074` `9,547,450`, `0/200` differ) | **MISS** |
| `(4)` | `Part C`: first patch read has at least one finding (`yes` / `no`) | `no` | `no` (Patch 1 read in Part C, `024` `IdeaS32`, has `0` findings -> `CLEAN`) | **HIT** |

- **Score:** **`2/4` HIT**.
  - Why `(2)` missed: fixing `031`'s out-of-window shrink and stack clobbering recovered **`+66.98 Elo`** (`-100.06` -> `-33.08 Elo`), proving those two defects caused two-thirds of `031`'s Elo loss, but `031`'s remaining trigger gates (no pawn-structure check, `|eval| >= 80` cp, `2` non-pawn plies, `defender_holds` tautologically `true` whenever `stm == winner`, and a `2`-ply wide-window search per interior PV node) still fire on `148/200` openings (`+19.9%` nodes on `O`) and cost `-33.08 +/- 10.12 Elo` at `20,000` nodes/move.
  - Why `(3)` missed: static diff reading noted `024` added child-to-parent `hash_proof` bubbling (`best_score >= beta && (ss + 1)->hash_proof`) while `074` recorded direct TT returns only, overlooking before measurement that `null_score = -search(ss + 1, ..., -beta, -beta + 1)` reaches `null_score >= beta` **only when `ss + 1` fails low** (`best_score <= -beta < beta_child`), so `024`'s bubbling condition is mathematically unreachable on every null-move cutoff.

---

## (3) Part A — `S10`: One Idea, Two Seats (`031` and `081`), `-100` Elo Between Them

### A1. Rebuild and Verification of Seats `031` and `081` (`partA_proofs_raw.txt`)

- **Seat `031` (`grok-031:forge-combo29/seats/031/idea.patch.txt`, `sha256 = 6d1a6f3f8644eb34fa4a2dbb3e89baf17f04cbcbdfab97e10cf27cda7216e685`):**
  - `git apply --check` (from repo root on `6b98f217`): `PASS (0 == 0)`
  - No-option `bench 11`: `PASS (312866 == 312866)`
  - No-option `bench 13`: `PASS (862329 == 862329)`
  - No-option `bench 16`: `PASS (3024920 == 3024920)`
  - No-option `go perft 5`: `PASS (4865609 == 4865609)`
  - `S14` + `IdeaS10=false` on `O`: sum `PASS (9500069 == 9500069)`, positions differing from `exe B`: `PASS (0 == 0)` (`031_off_O_d12.nodes.txt`)
  - `S14` + `IdeaS10=false` on `G`: sum `PASS (18466239 == 18466239)`, positions differing from `exe B`: `PASS (0 == 0)` (`031_off_G_d12.nodes.txt`)
  - `S14` + `IdeaS10=true` on `O` (`031_on_O_d12.nodes.txt`):
    - Node sum vs known `10,937,472`: `PASS (10937472 == 10937472)`
    - Positions differing from `exe B` vs known `195`: `PASS (195 == 195)`
    - Node sum vs `031`'s committed `P_on_O_d12.nodes.txt`: `PASS (10937472 == 10937472)`
    - Positions differing from `031`'s committed `P_on_O_d12.nodes.txt`: `PASS (0 == 0)` (**EQUAL** on all `200/200` rows; binary `sha256` also matches `031`'s `P_on_O_d12.meta`).

- **Seat `081` (`grok-081:forge-combo29/seats/081/idea.patch.txt`, `sha256 = 8430a8b654d504f7e69d11b1dc3daf73854fa5e2c9a477cc893c7eb1dddf80bc`):**
  - `git apply --check` (from repo root on `6b98f217`): `PASS (0 == 0)`
  - No-option `bench 11`: `PASS (312866 == 312866)`
  - No-option `bench 13`: `PASS (862329 == 862329)`
  - No-option `bench 16`: `PASS (3024920 == 3024920)`
  - No-option `go perft 5`: `PASS (4865609 == 4865609)`
  - `S14` + `IdeaS10=false` on `O`: sum `PASS (9500069 == 9500069)`, positions differing from `exe B`: `PASS (0 == 0)` (`081_off_O_d12.nodes.txt`)
  - `S14` + `IdeaS10=false` on `G`: sum `PASS (18466239 == 18466239)`, positions differing from `exe B`: `PASS (0 == 0)` (`081_off_G_d12.nodes.txt`)
  - `S14` + `IdeaS10=true` on `O` (`081_on_O_d12.nodes.txt`):
    - Node sum vs known `9,542,904`: `PASS (9542904 == 9542904)`
    - Positions differing from `exe B` vs known `10`: `PASS (10 == 10)` (indices `[34, 37, 61, 81, 106, 111, 121, 122, 133, 177]`)
    - Node sum vs `081`'s committed `O_p_on_d12.nodes.txt`: `PASS (9542904 == 9542904)`
    - Positions differing from `081`'s committed `O_p_on_d12.nodes.txt`: `PASS (0 == 0)` (**EQUAL** on all `200/200` rows).

### A2. Reading of `031` and `081` Against `IDEAS.md` (`partA_A2_analysis.txt`)

`IDEAS.md` (`fable/50-agent-engine-ideas:engine-ideas/50-agents/IDEAS.md:148-155`):
> *"In quiet nodes where the pawn score has stayed large and almost flat while both sides only shuffle, run a short probe that forbids pawn moves and captures for the side that is supposed to be winning. If that probe cannot change the score, and the defender has a shuffle or a repetition, shrink the node toward equality. No second evaluation function and no list of fortress shapes."*

1. **Concept Mapping (`031` vs `081`):**
   - **"the pawn score" (and "large"):**
     - `031` (`src/search.cpp:1575-1584`): Never computes a pawn-structure score; uses full `ss->static_eval` (`|eval| >= IdeaS10_Margin = 80` cp).
     - `081` (`src/eval.cpp:659-683`, `src/search.cpp:1635-1643`): Exposes `Evaluator::pawn_structure_cp(board)` from the classical evaluator's cached `pawn_cache_` (tapered by phase) and requires both `|eval| >= 25` and `|pawn_cp| >= 25` with matching sign.
   - **"flat":**
     - `031` (`src/search.cpp:1575-1582`): `|ss->static_eval - (ss - 2)->static_eval| <= IdeaS10_Flat` (`40` cp).
     - `081` (`src/search.cpp:1634, 1661-1662, 1798-1799`): `board.halfmove_clock() >= 4`, 1-ply restricted probe within `|probe - eval| <= 40` cp, and `s10_pull` pulls only search scores within `|score - s10_eval_before| <= 40` cp.
   - **"shuffle":**
     - `031` (`src/search.cpp:1585-1591`): Only the last `2` plies `(ss - 1)` and `(ss - 2)` must be non-none, non-capture, non-promotion, non-pawn moves.
     - `081` (`src/search.cpp:1564-1568, 1634, 1637-1639`): `halfmove_clock() >= 4` AND all `4` plies `(ss - 1)..(ss - 4)` must be non-none, non-capture, non-promotion, non-pawn moves.
   - **"the probe":**
     - `031` (`src/search.cpp:1606-1620, 1463, 1506-1509, 1711, 1898-1901`): Recursive `Worker::search(board, ss, IdeaS10_Probe=2, best_score - 30, best_score + 30, false)` with `shuffle_suppress_ = true` disabling non-PV TT cutoffs and skipping captures, promotions, and pawn moves for `shuffle_winner_`; triggers when `lo < probe < hi`.
     - `081` (`src/search.cpp:1572-1602, 1645-1662`): Non-recursive 1-ply loop (`restricted_quiet_score`) over the pawn-ahead side's legal non-capture, non-promotion, non-pawn moves (passing via null move first if `winner != stm`), scoring children by `-static_evaluate(board, child_ss)` on a fresh child frame.
   - **"the defender holds":**
     - `031` (`src/search.cpp:1592-1605`): True on repetition; if `stm == defender`, true if the defender has **any** legal non-capture, non-promotion, non-pawn move (almost always true); if `stm == winner`, checks `shuffle_move(ss - 1)`, which is **already guaranteed true by line `1591`** (tautologically `true` whenever `stm == winner`!).
     - `081` (`src/search.cpp:1604-1628`): Requires the defender (via null move if `defender != stm`) to have a legal quiet piece move that **reverses `(ss - 2)`** (`from == prev.to && to == prev.from`) or **immediately repeats** the position.

2. **Where the Shrink Is Applied & Answers on `031`'s Shrink and Stack Frame:**
   - **Where applied & to which scores:**
     - `081` (`wt_081/forge-combo29/src/search.cpp:1789, 1793, 1826, 1868, 1885, 1919, 2098, 2242`): Gated to `!pv_node && !root_node && !in_check && excluded.is_none()`; shrinks `ss->static_eval` (`896/1024`) before pruning, re-verifies every cutoff (`pulled >= beta` / `pulled < alpha`) before returning on razoring/NMP/ProbCut/multi-cut, and at `2242` shrinks `best_score` only if `|best_score - s10_eval_before| <= 40`.
     - `031` (`wt_031/forge-combo29/src/search.cpp:2154-2157`, helper at `1567-1622`): Applied at the end of `Worker::search` (`best_score = best_score * 768 / 1024`) **unconditionally on `(alpha, beta)` and `pv_node`**.
   - **Does `031` shrink scores outside `(alpha, beta)`?** **YES.** `shrink_shuffle_score` at `src/search.cpp:2155` checks neither `alpha` nor `beta`:
     - When `best_score >= beta` and `best_score > 0` (including zero-window fail-highs `beta = alpha + 1`, e.g. `beta = 200, best_score = 220`), multiplying by `768/1024` drops `best_score` to `165 <= alpha < beta`, destroying the beta cutoff (`2160`), storing `BoundUpper` (`2177`), and returning a fail-low!
     - When `best_score <= alpha` and `best_score < 0` (including zero-window fail-lows, e.g. `alpha = -200, beta = -199, best_score = -220`), multiplying by `768/1024` raises `best_score` toward `0` to `-165 >= beta`, fabricating a false beta cutoff (`2160`), storing `BoundLower` (`2177`), and returning a bogus fail-high!
   - **Does `031`'s probe use the outer node's own stack frame?** **YES.** `src/search.cpp:1615` calls `search(board, ss, tune::IdeaS10_Probe, lo, hi, false)` passing `ss` directly, with `hi - lo = 60 > 1` so `pv_node == true` inside the probe (`1625`).
   - **Every field of `ss` read by the outer node (and its parent caller) after `shrink_shuffle_score` returns (`wt_031/forge-combo29/src/search.cpp`):**
     1. `ss->killers` (`src/search.cpp:2162` -> `update_quiet_stats` at `1388-1391`): read/shifted if `best_score >= beta` on a quiet move; mutated if the probe took a quiet cutoff at `ss`.
     2. `ss->raw_eval` (`src/search.cpp:2180` / `2182`): stored into TT; overwritten by the probe at `1726-1728`.
     3. `ss->tt_pv` (`src/search.cpp:2180` / `2182`): stored into TT; **unconditionally overwritten to `true`** by the probe at `1675` (`ss->tt_pv = pv_node || ...`) because the probe's `hi - lo = 60 > 1` sets `pv_node = true` even on non-PV outer nodes.
     4. `ss->static_eval` (`src/search.cpp:2189-2191`): read in the correction-history guard and passed to `update_correction`; overwritten by the probe at `1722-1729`.
     5. `ss->pv` and `ss->pv_length` (read by the parent caller on child `ss == ss_parent + 1` at `src/search.cpp:2128-2129` right after `return best_score` when `pv_node` and `score > alpha`): zeroed at `1638` and overwritten at `2127-2129` with the 2-ply restricted shuffle line.

### A3. Variant (`s10_variant.patch.txt`) Proofs and `1,106`-Game `fastchess` Matches

- **Design of `s10_variant.patch.txt`:** Starts from `031`'s patch and changes **only** the two defects asked in A3:
  1. Captures `const int orig_alpha = alpha;` right before the move loop (`src/search.cpp:1872`, because `alpha` is mutated in-place inside the move loop via `alpha = score;`) and calls `shrink_shuffle_score` at `src/search.cpp:2165` **only when `orig_alpha < best_score && best_score < beta`**.
  2. Allocates `std::unique_ptr<std::array<SearchStack, MaxPly + 8>> shuffle_stack_;` per `Worker`, copies the read-only `4`-ply history prefix `(ss - 4)..(ss - 1)` into `(*shuffle_stack_)[0..3]` plus `ply` and `static_eval` into `probe_ss = &(*shuffle_stack_)[4]`, and runs the probe on `probe_ss` so the outer node's `stack_` is completely untouched.
- **Proofs on `s10_variant.patch.txt` (`sha256 = 85e7b8bb3ff75e090489a1bd48bc9fbc4481856d51cdf35d70cc84908f9ef290`, `partA_proofs_raw.txt`):**
  - `git apply --check` (repo root on `6b98f217`): `PASS (0 == 0)`
  - No-option `bench 11`: `PASS (312866 == 312866)`
  - No-option `bench 13`: `PASS (862329 == 862329)`
  - No-option `bench 16`: `PASS (3024920 == 3024920)`
  - No-option `go perft 5`: `PASS (4865609 == 4865609)`
  - `S14` + `IdeaS10=false` on `O`: sum `PASS (9500069 == 9500069)`, differ from `exe B`: `PASS (0 == 0)` (`s10_variant_off_O_d12.nodes.txt`)
  - `S14` + `IdeaS10=false` on `G`: sum `PASS (18466239 == 18466239)`, differ from `exe B`: `PASS (0 == 0)` (`s10_variant_off_G_d12.nodes.txt`)
  - `S14` + `IdeaS10=true` on `O` (`s10_variant_on_O_d12.nodes.txt`): sum = **`11,389,229`**, **`148/200`** positions differ from `exe B` (`195/200` differ from `031`).
- **`1,106`-Game `fastchess` Matches (`nodes=20000`, `Threads=1`, `Hash=16`, `S14`, `OG553.epd`, `-rounds 553 -games 2 -concurrency 3`):**

| Match (`on` vs `off`, same binary) | Games | W - L - D | Points (%) | Elo (`+/-` 95% CI) | nElo (`+/-` 95% CI) | Ptnml(0-2) | Raw File |
|---|---:|---|---|---|---:|---|---|
| **`s10_variant` (`IdeaS10=true` vs `false`)** | `1106` | **`258 - 363 - 485`** | `500.5 (45.25%)` | **`-33.08 +/- 10.12`** | `-67.38 +/- 20.48` | `[18, 135, 340, 54, 6]` | `fastchess_s10_variant.txt` |
| **Seat `031` (`IdeaS10=true` vs `false`)** | `1106` | **`183 - 493 - 430`** | `398.0 (35.99%)` | **`-100.06 +/- 11.96`** | `-180.98 +/- 20.48` | `[64, 208, 257, 22, 2]` | `fastchess_031.txt` |

---

## (4) Part B — Five Twin Pairs Across Ten Seats (`partB_raw.txt`, `partB_readings.txt`)

Every one of the `10` seats was built in a fresh worktree at `6b98f2170a3210e71beed04bbd2553972c253ed7`. Per-seat honesty and reproducibility checks (`partB_raw.txt`):

| Pair | Seat | `git apply --check` | `bench 11` | `bench 13` | `bench 16` | `perft 5` | `S14 off` on `O` vs `exe B` | `S14 on` on `O` vs Seat's Committed Rows |
|---|---|---:|---|---|---|---|---|---|
| `B1` | `030` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (10081213 == 10081213)`, diff `PASS (0 == 0)` |
| `B1` | `080` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (9748678 == 9748678)`, diff `PASS (0 == 0)` |
| `S32` | `024` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (9547450 == 9547450)`, diff `PASS (0 == 0)` |
| `S32` | `074` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (9547450 == 9547450)`, diff `PASS (0 == 0)` |
| `K4` | `043` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (8983632 == 8983632)`, diff `PASS (0 == 0)` |
| `K4` | `093` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (8921190 == 8921190)`, diff `PASS (0 == 0)` |
| `B8` | `028` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (9718009 == 9718009)`, diff `PASS (0 == 0)` |
| `B8` | `078` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (9295189 == 9295189)`, diff `PASS (0 == 0)` |
| `S13` | `016` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (9722445 == 9722445)`, diff `PASS (0 == 0)` |
| `S13` | `066` | `PASS (0 == 0)` | `PASS (312866 == 312866)` | `PASS (862329 == 862329)` | `PASS (3024920 == 3024920)` | `PASS (4865609 == 4865609)` | `PASS (9500069 == 9500069)`, diff `PASS (0 == 0)` | `PASS (9656004 == 9656004)`, diff `PASS (0 == 0)` |

### Twin-Pair Switch-On `O` Comparison (`200` FENs, `d12`, `S14`)

| Pair | Seats `(A, B)` | Sum `A` | Sum `B` | Positions Differing (`A` vs `B`) | Verdict | First 3 Differing Positions (`pos#: A vs B`, FEN in `opening_200.epd`) |
|---|---|---:|---:|---:|---|---|
| **`B1`** | `030` vs `080` | `10,081,213` | `9,748,678` | **`200 / 200`** | **DIFFERENT** | `#1: 12481 vs 17841`; `#2: 31753 vs 25977`; `#3: 31668 vs 43905` |
| **`S32`** | `024` vs `074` | `9,547,450` | `9,547,450` | **`0 / 200`** | **EQUAL** | None (`PASS (9547450 == 9547450)`, `PASS (0 == 0)`) |
| **`K4`** | `043` vs `093` | `8,983,632` | `8,921,190` | **`200 / 200`** | **DIFFERENT** | `#1: 23741 vs 24693`; `#2: 21846 vs 26341`; `#3: 35911 vs 35070` |
| **`B8`** | `028` vs `078` | `9,718,009` | `9,295,189` | **`200 / 200`** | **DIFFERENT** | `#1: 17283 vs 24947`; `#2: 17878 vs 29945`; `#3: 31115 vs 39302` |
| **`S13`** | `016` vs `066` | `9,722,445` | `9,656,004` | **`200 / 200`** | **DIFFERENT** | `#1: 19900 vs 26526`; `#2: 22525 vs 19210`; `#3: 42778 vs 49901` |

*(For the 4 differing pairs, positions `#1`, `#2`, and `#3` are all among the `200/200` differing positions: `#1 = rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4`, `#2 = rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4`, `#3 = rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3`.)*

### Readings of the Differing Pairs (and Note on Equal Pair `S32`) (`partB_readings.txt`)

- **`B1` (`030` vs `080` vs `BREAKTHROUGHS.md` lines `9-29`):** `BREAKTHROUGHS.md` asks for a cheap board-placement quiet-move ordering prior inside the quiet-move band that fades down as quiet history accumulates (`"A static piece-square bonus does not test this idea"`). Seat `030` (`src/search.cpp:289-330`) implements a classical board-attack delta `2 * popcount(att & enemy) + popcount(att & enemy_king_zone)` from `move.from` to `move.to` without touching `nnue.*`, faded solely by `main_history[us][from][to]` (`delta * 96 * 1024 / (1024 + 4 * |main_h|)`). Seat `080` (`src/nnue.cpp:502-562`, `src/search.cpp:585-652`) reads *"where it would live: the network"* by materialising the node's NNUE accumulator and computing a 16-lane first-order linear Taylor delta (`clamp(x,0,1)^2 * w2` dotted with the move's `DirtyPieces` `w1` columns), faded against the combined `quiet_history + threat_quiet_bonus` sum (`Fade = 1024, Scale = 32, Cap = 4000`).
- **`S32` (`024` vs `074` — why EQUAL `200/200`):** Both seats record a direct TT cutoff's depth on `SearchStack` in `search` and `qsearch` and require reduced null-move verification (`depth < 14`) when `(ss + 1)` returned on a TT bound shallower than `depth - Slack` (`Slack = 0`). Seat `024` also attempts to bubble `(ss + 1)->hash_proof` up on `best_score >= beta` (`src/search.cpp:1558, 2138`), whereas `074` checks direct TT cutoffs only; because `null_score = -search(ss + 1, ..., -beta, -beta + 1)` reaches `>= beta` **only when `ss + 1` fails low** (`best_score <= -beta < beta_child`), `024`'s `best_score >= beta` bubbling never fires on `ss + 1` for any null cutoff, making both builds identical (`9,547,450`) across all `200` openings.
- **`K4` (`043` vs `093` vs K4 job text in `043/DESIGN.txt` & `093/idea_design.txt`):** Both seats implement the exact same RFP guard and formula (`if (tune::IdeaK4 && (ss - 1)->static_eval != ValueNone && (ss - 3)->static_eval != ValueNone && (ss - 1)->static_eval < (ss - 3)->static_eval) rfp_margin -= IdeaK4_Shrink;`). They differ solely in their chosen default spin value: `043` picked `IdeaK4_Shrink = 32` (allowing `d=1` improving RFP margin `72 - 40 - 32 = 0`), while `093` picked `IdeaK4_Shrink = 24` (keeping `d=1` improving RFP margin positive at `8`).
- **`B8` (`028` vs `078` vs `BREAKTHROUGHS.md` lines `159-178`):** Both seats add a `[side 2][victim 7][attacker 7][role 5]` `int16_t` table (`Weight = 1024`) into `QuietScorer::score` and `Worker::quiet_history`. Seat `028` (`IdeaB8_Swing = 40`) includes `King` as a threatened victim, requires `mover_worth < enemy_worth` for counter-threat role `4`, updates both `from` and `to` bits in slider occupancy (`src/search.cpp:189`), and updates the role table **only after a quiet beta cutoff** (`best_score >= beta`) with full `history_bonus(depth)`. Seat `078` (`IdeaB8_Swing = 48`) scans only `Knight..Queen` victims, allows any counter-attack worth more than `victim_value` regardless of `mover_worth`, clears only `move.from` in `attacks_after_quiet`, and updates the role table **immediately after every searched quiet move inside the move loop** (`history_bonus(max(1, depth)) / 2`) even when that move fails low.
- **`S13` (`016` vs `066` vs `IDEAS.md` lines `459-467`):** `IDEAS.md` credits a quiet piece move (`[side][from][to]`) when a pawn move a few plies later with unchanged pawn structure *"raised the score"*, using the table for quiet piece ordering and up to `1`-ply LMR relief. Seat `016` reads *"raised the score"* as a **beta cutoff** (`best_score >= beta`, `+1` bonus depth if quiet and `> beta + 100`) and uses `IdeaS13_ReduceDivisor = 1024`, whereas Seat `066` reads *"raised the score"* as **beating entry `alpha`** (`best_score > alpha_at_moves`, which also fires on interior PV improvements below `beta`), compares `(earlier + 1)->break_pawn_key == board.pawn_key()`, and uses a `4x` weaker divisor `IdeaS13_LmrDivisor = 4096`.

---

## (5) Part C — Line-by-Line Hunk Audit (`partC_line_by_line.txt`)

Ordered per `FABLE_TO_carbon2_38.md` lines `114-115`: (1) one build from each EQUAL twin pair in Part B -> **Seat `024` (`IdeaS32`)**; (2) **`030`'s `B1`** (not among the equal pairs).

### Patch 1: Seat `024` (`IdeaS32` — `seats/024/idea.patch.txt`, `14` hunks)

| Hunk | File & Applied Lines (`+` lines) | What It Does | Switch-Off Path Different? | Every Index & Bound | Read Before Written? | Non-Per-Thread State Written by Search? | Cost Per Node When On |
|---:|---|---|---|---|---|---|---|
| 1 | `include/forge/search.hpp:300-306` (`+303`) | Declares `extern bool IdeaS32` in `forge::tune`. | No (declaration only). | None. | None. | Written only by UCI `setoption`, never by search. | `0` |
| 2 | `include/forge/search.hpp:410-421` (`+413..418`) | Adds `bool hash_proof = false; int hash_proof_depth = 0;` to `SearchStack`. | No (8 bytes/frame; unread when off). | None (`stack_` is `MaxPly + 8 = 136`). | Default-initialized to `false`, `0`. | None (`stack_` is per-`Worker`). | `0` (storage) |
| 3 | `src/search.cpp:100-107` (`+103..104`) | Defines `IdeaS32 = false`, `IdeaS32_Slack = 0`. | No (`default false`). | None. | Static init before `main()`. | Written only by UCI `setoption`. | `0` |
| 4 | `src/search.cpp:147-153` (`+150`) | Registers spin `IdeaS32_Slack` (`0..64`) in `tune::parameters()`. | No (parameter table only). | None. | Initialized at line `104`. | Static descriptor table; search never writes `IdeaS32_Slack`. | `0` |
| 5 | `src/search.cpp:1417-1424` (`+1420..1421`) | Clears `ss->hash_proof = false; ss->hash_proof_depth = 0;` at `qsearch` entry. | No: 2 dead stores to fields unread while `IdeaS32 == false`; search path unchanged. | `ss` in `&stack_[4 .. MaxPly + 4]` (`0..135`). | Writes before any read in `qsearch`. | None (`ss` is per-`Worker`). | 2 scalar stores / `qsearch` node |
| 6 | `src/search.cpp:1457-1468` (`+1460..1465`) | On non-PV `qsearch` TT cutoff, if `IdeaS32`, records `hash_proof = true` and `tte.depth`. | No (`if (tune::IdeaS32)`). | `ss` in `&stack_[4 .. MaxPly + 3]`. | `tte.depth` valid (`tt_hit == true`). | None (`ss` is per-`Worker`). | 1 branch + 2 stores on `qsearch` TT cutoff |
| 7 | `src/search.cpp:1553-1564` (`+1556..1561`) | At `qsearch` exit, bubbles `(ss + 1)->hash_proof` on `best_score >= beta`. | No (`tune::IdeaS32` short-circuits). | `ss + 1` in `&stack_[5 .. MaxPly + 4]` (`<= 132 < 136`). | Stand-pat `>= beta` returned at `1486`; `best_score >= beta` here came from `qsearch(ss + 1)` which ran Hunk 5. | None (`ss`, `ss + 1` per-`Worker`). | 1-3 branches at `qsearch` exit |
| 8 | `src/search.cpp:1571-1578` (`+1574..1575`) | Clears `ss->hash_proof = false; ss->hash_proof_depth = 0;` in `Worker::search` after `depth <= 0` `qsearch` handoff. | No: 2 dead stores to unread fields when off; search path unchanged. | `ss` in `&stack_[4 .. MaxPly + 4]`. | Writes before any read in `search`. | None (`ss` is per-`Worker`). | 2 scalar stores / `search` node |
| 9 | `src/search.cpp:1659-1668` (`+1662..1665`) | On non-PV `search` TT cutoff, if `IdeaS32`, records `hash_proof = true` and `tt_depth`. | No (`if (tune::IdeaS32)`). | `ss` in `&stack_[4 .. MaxPly + 3]`. | `tt_depth = tt_hit ? tte.depth : -1` (`1617`), `tt_hit` true. | None (`ss` is per-`Worker`). | 1 branch + 2 stores on `search` TT cutoff |
| 10 | `src/search.cpp:1745-1757` (`+1748..1754`) | On null cutoff (`null_score >= beta`), sets `shallow_hash = IdeaS32 && (ss + 1)->hash_proof && (ss + 1)->hash_proof_depth < depth - IdeaS32_Slack` and requires verification when `depth < 14 && shallow_hash`. | No (`tune::IdeaS32` short-circuits `&&`). | `ss + 1` in `&stack_[5 .. MaxPly + 4]`. | `search(board, ss + 1, ...)` just ran at `1737` (initializing `ss + 1` via Hunk 8 or Hunk 5). | None (`ss + 1` per-`Worker`). | 1-3 scalar checks per null fail-high + reduced verification search when shallow |
| 11 | `src/search.cpp:2134-2144` (`+2137..2141`) | At `search` exit, bubbles `(ss + 1)->hash_proof` on `best_score >= beta`. | No (`tune::IdeaS32` short-circuits). | `ss + 1` in `&stack_[5 .. MaxPly + 4]`. | `best_score >= beta` came from the breaking `search(ss + 1)` call (`2091`). | None (`ss`, `ss + 1` per-`Worker`). | 1-3 branches at `search` exit |
| 12 | `src/search.cpp:2372-2379` (`+2375..2376`) | Clears `hash_proof` & `hash_proof_depth` across `stack_` at root start. | No (unread when off). | Range-for over `stack_[0..135]`. | Write-only. | None (`stack_` is per-`Worker`). | `272` stores / `go` |
| 13 | `src/uci.cpp:222-228` (`+225`) | Prints `option name IdeaS32 type check default false`. | No (`uci` listing). | None. | None. | `std::cout` in `uci_loop`. | `0` |
| 14 | `src/uci.cpp:391-399` (`+394..396`) | Handles `setoption name IdeaS32 value true|false`. | No (`setoption` only). | None. | `value_text` parsed in `uci_loop`. | Mutates `tune::IdeaS32` in `uci_loop` outside search. | `0` |

- **Verdict for Patch 1 (Seat `024`, `IdeaS32`):** **`CLEAN`**

### Patch 2: Seat `030` (`IdeaB1` — `seats/030/idea.patch.txt`, `11` hunks)

| Hunk | File & Applied Lines (`+` lines) | What It Does | Switch-Off Path Different? | Every Index & Bound | Read Before Written? | Non-Per-Thread State Written by Search? | Cost Per Node When On |
|---:|---|---|---|---|---|---|---|
| 1 | `include/forge/search.hpp:304-312` (`+307..309`) | Declares `IdeaB1`, `IdeaB1_Scale`, `IdeaB1_Fade` in `forge::tune`. | No (declarations). | None. | None. | Mutated only by UCI `setoption`. | `0` |
| 2 | `src/search.cpp:104-112` (`+107..109`) | Defines `IdeaB1 = false`, `IdeaB1_Scale = 96`, `IdeaB1_Fade = 4`. | No (`default false`). | None. | Static init before `main()`. | Read-only during search. | `0` |
| 3 | `src/search.cpp:148-154` (`+151`) | Registers spins `IdeaB1_Scale` (`0..500`) and `IdeaB1_Fade` (`0..64`). | No (parameter table). | None. | Initialized in Hunk 2. | Static metadata; search never writes spins. | `0` |
| 4 | `src/search.cpp:282-336` (`+285..333`) | Defines `fading_board_prior(board, move, main_history)` (attack + king-zone delta faded by `1024 / (1024 + Fade * |h|)`). | No (uncalled when `IdeaB1 == false`). | `move.from, move.to` in `0..63`; `us, them` in `0..1`; `their_king >= 0` -> `0..63` into `KingZoneMask[64]`; `Knight/King/Bishop/Rook` tables `0..63` with magic `m.mask`; `denom >= 1024`; `|delta * Scale * 1024| <= 12,800,000 << INT_MAX`. | All locals initialized; `attacks::init()` runs in `Board` ctor. | None (pure read of `board`, const attack tables, and `tune::IdeaB1_*`). | 2 attack lookups + 4 `popcount`s + 1 int div per scored quiet move |
| 5 | `src/search.cpp:850-856` (`+853`) | Adds `fading_board_prior` in `QuietScorer::score` (`FORGE_SEARCH_SPEED2`) when `tune::IdeaB1` is true. | No (`if (tune::IdeaB1)`). | `side` in `0..1`, `move.from` in `0..63`, `move.to` in `0..63` into `(*main_history_)[2][64][64]`. | `main_history_` zero-initialized on `Worker` ctor and `clear()`. | None (`main_history_` is per-`Worker`). | 1 Hunk-4 call / quiet move |
| 6 | `src/search.cpp:984-993` (`+987..990`) | Adds `fading_board_prior` in `generate_quiets` (`!FORGE_SEARCH_SPEED2` branch 1) when `IdeaB1` is true. | No (inactive `#else`, and `if (tune::IdeaB1)`). | `[0..1][0..63][0..63]`. | `main_history_` zero-initialized. | None (`main_history_` per-`Worker`). | 1 Hunk-4 call / quiet move (if non-SPEED2) |
| 7 | `src/search.cpp:1010-1019` (`+1013..1016`) | Adds `fading_board_prior` in `generate_quiets` (`!FORGE_SEARCH_SPEED2` branch 2) when `IdeaB1` is true. | No (inactive `#else`, and `if (tune::IdeaB1)`). | `[0..1][0..63][0..63]`. | `main_history_` zero-initialized. | None (`main_history_` per-`Worker`). | 1 Hunk-4 call / quiet move (if non-SPEED2) |
| 8 | `src/search.cpp:1050-1060` (`+1053..1057`) | Adds `fading_board_prior` on quiet evasions (`!FORGE_SEARCH_SPEED2`; `SPEED2` uses Hunk 5 at line `1050`) when `IdeaB1` is true. | No (`if (tune::IdeaB1)`). | `[0..1][0..63][0..63]`. | `main_history_` zero-initialized. | None (`main_history_` per-`Worker`). | 1 Hunk-4 call / quiet evasion |
| 9 | `src/uci.cpp:229-235` (`+232`) | Prints `option name IdeaB1 type check default false`. | No (`uci` listing). | None. | None. | `std::cout` in `uci_loop`. | `0` |
| 10 | `src/uci.cpp:404-410` (`+407`) | Adds `name == "IdeaB1"` to check-option guard in `uci_loop`. | No (`setoption` only). | None. | `name` initialized in `uci_loop`. | None during search. | `0` |
| 11 | `src/uci.cpp:415-422` (`+418..419`) | Sets `target = &forge::tune::IdeaB1` in `uci_loop`. | No (`setoption` only). | None. | Non-null `target`. | Mutates `tune::IdeaB1` in `uci_loop` outside search. | `0` |

- **Verdict for Patch 2 (Seat `030`, `IdeaB1`):** **`CLEAN`**

---

## Facts (Proved by Committed Artifacts)

1. Base `6b98f2170a3210e71beed04bbd2553972c253ed7` built in Release with `g++ 13.3.0` (`libstdc++`) produces `sha256 = e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, matching all four honesty numbers (`312866`, `862329`, `3024920`, `4865609`) and `S14` node totals `O = 9,500,069` and `G = 18,466,239` (`step0_raw.txt`).
2. Every one of the `12` seat patches tested in Parts A and B (`031, 081, 030, 080, 024, 074, 043, 093, 028, 078, 016, 066`) reproduces its seat's own committed `S14` switch-on `O` node rows with **`0/200` differences** (`partA_proofs_raw.txt`, `partB_raw.txt`).
3. Seat `031` shrinks `best_score` outside `(alpha, beta)` (`wt_031/forge-combo29/src/search.cpp:2154-2157`) and passes the outer node's `SearchStack* ss` into its wide-window 2-ply probe (`src/search.cpp:1615`), scoring **`-100.06 +/- 11.96 Elo`** (`183-493-430`) vs switch-off at `20,000` nodes/move (`fastchess_031.txt`).
4. Fixing only those two defects in `s10_variant.patch.txt` (`orig_alpha < best_score && best_score < beta` plus dedicated `shuffle_stack_`) raises match performance by **`+66.98 Elo`** to **`-33.08 +/- 10.12 Elo`** (`258-363-485` in `1,106` games, `fastchess_s10_variant.txt`).
5. Across the `5` twin pairs in Part B, **`1` pair is EQUAL** (`S32`: `024` and `074` both give `9,547,450`, `0/200` differ) because `024`'s `best_score >= beta` `hash_proof` bubbling cannot trigger on a null-move fail-low child (`ss + 1`), while **`4` pairs are DIFFERENT** on `200/200` `O` positions (`B1`, `K4`, `B8`, `S13`).
6. Line-by-line hunk audits of `024`'s `IdeaS32` (`14` hunks) and `030`'s `IdeaB1` (`11` hunks) found zero switch-off path divergences, zero out-of-bounds indices, zero read-before-write values, and zero search-written shared state (`partC_line_by_line.txt`).

---

## Suspicions (Separate from Facts)

1. `s10_variant.patch.txt` still loses `-33.08 +/- 10.12 Elo` at fixed `20,000` nodes/move primarily because `031`'s remaining `defender_holds` check (`src/search.cpp:1595-1603`) is tautologically `true` whenever `stm == winner` (`shuffle_move(ss - 1)` was already checked at line `1591`) and almost always `true` when `stm == defender` (any legal quiet non-pawn move), causing the `2`-ply wide-window probe (which increments `nodes_`, counting against the `20,000`-node budget) and `0.75x` PV score shrink to fire in ordinary non-fortress middlegames (`148/200` openings on `O`).
2. In Seat `024` (`IdeaS32`), Hunks 7 and 11 (`best_score >= beta && (ss + 1)->hash_proof`) appear to have been intended to propagate shallow TT proofs up the null-move subtree, but because alpha-beta negates bounds at each ply, propagating a proof for a parent null cutoff would have needed upper-bound (`best_score <= alpha`) all-node tracking across *every* move at `ss + 1`, not beta-cutoff tracking.

---

## Read and Not Tested (Separate from Facts and Suspicions)

1. In Seat `066` (`IdeaS13`, read in Part B), `credit_quiet_before_break` checks `(earlier + 1)->break_pawn_key == board.pawn_key()`, where `break_pawn_key` is written in `Worker::search` (`line 1697`) but **not** in `Worker::qsearch`. If `earlier` at `ss - 2` searched a move at `depth - 1 <= 0` that went straight into `qsearch(ss - 1)`, `(ss - 1)->break_pawn_key` retains whatever `pawn_key` was left on `ss - 1` by an earlier sibling subtree rather than the position after `earlier`. We read this in `066`'s diff during Part B but did not construct a targeted test or audit `066` in Part C because Part C's ordered list contained only `024` (`S32`) and `030` (`B1`).
2. In Seat `078` (`IdeaB8`, read in Part B), `attacks_after_quiet` clears `move.from` in `occ_without_mover` without setting `move.to` when testing post-move slider attacks (`RoleAttackThreat` / `RoleCounterThreat`), so a slider moving onto a ray can appear to X-ray through its own destination square (`move.to` is excluded only by not holding an enemy piece, while squares beyond `move.to` are not blocked by `move.to`). Read in Part B; not tested in isolation.

---

## What I Did Not Do

- Did not run `fastchess` matches on Seat `081` or on the Part B twin pairs (not requested by `FABLE_TO_carbon2_38.md`).
- Did not run `G` (`gated_353.epd`) switch-on rows for Part B seats (`FABLE_TO_carbon2_38.md` Part B specifies `O` (`200` positions, depth `12`) for the `10` twin builds).
- Did not audit a third patch in Part C because the ordered specification (*"the builds of the pairs whose twin rows were EQUAL in Part B (one of each pair), then 030's B1 if not among them"*) yielded exactly two patches (`024` `S32`, then `030` `B1`).
- Did not touch any engine source file in `/agent/repos/dwqww`, create any pull request, or modify any branch other than `for-fable-and-opus/carbon2-work`.

---

## What I Am Not Sure About

- Whether `s10_variant.patch.txt` would still lose Elo if `probe` nodes were excluded from `nodes_` or if tested under wall-clock time control instead of fixed `nodes=20000`, versus how much of the `-33.08 Elo` comes from distorting interior PV scores in non-fortress positions vs spending `~20%` of the fixed `20,000`-node budget inside `IdeaS10_Probe` sub-searches.
- Whether `043` (`IdeaK4_Shrink = 32`) vs `093` (`IdeaK4_Shrink = 24`) measurably differs in match play beyond the `+/- 10 Elo` noise bar of `1,106` games.

---

## Model Name

`Gemini 4 Carbon`

---

## Pre-Commit Repository & Directory Listing (`git status --short && ls -R forge-combo29/carbon2/job38`)

```text
 M forge-combo29/carbon2/job38/stamps.txt
?? forge-combo29/carbon2/job38/REPORT_carbon2_job38.md
forge-combo29/carbon2/job38:
016_off_O_d12.nodes.txt
016_off_O_d12.nodes.txt.meta
016_on_O_d12.nodes.txt
016_on_O_d12.nodes.txt.meta
024_off_O_d12.nodes.txt
024_off_O_d12.nodes.txt.meta
024_on_O_d12.nodes.txt
024_on_O_d12.nodes.txt.meta
028_off_O_d12.nodes.txt
028_off_O_d12.nodes.txt.meta
028_on_O_d12.nodes.txt
028_on_O_d12.nodes.txt.meta
030_off_O_d12.nodes.txt
030_off_O_d12.nodes.txt.meta
030_on_O_d12.nodes.txt
030_on_O_d12.nodes.txt.meta
031_off_G_d12.nodes.txt
031_off_G_d12.nodes.txt.meta
031_off_O_d12.nodes.txt
031_off_O_d12.nodes.txt.meta
031_on_O_d12.nodes.txt
031_on_O_d12.nodes.txt.meta
043_off_O_d12.nodes.txt
043_off_O_d12.nodes.txt.meta
043_on_O_d12.nodes.txt
043_on_O_d12.nodes.txt.meta
066_off_O_d12.nodes.txt
066_off_O_d12.nodes.txt.meta
066_on_O_d12.nodes.txt
066_on_O_d12.nodes.txt.meta
074_off_O_d12.nodes.txt
074_off_O_d12.nodes.txt.meta
074_on_O_d12.nodes.txt
074_on_O_d12.nodes.txt.meta
078_off_O_d12.nodes.txt
078_off_O_d12.nodes.txt.meta
078_on_O_d12.nodes.txt
078_on_O_d12.nodes.txt.meta
080_off_O_d12.nodes.txt
080_off_O_d12.nodes.txt.meta
080_on_O_d12.nodes.txt
080_on_O_d12.nodes.txt.meta
081_off_G_d12.nodes.txt
081_off_G_d12.nodes.txt.meta
081_off_O_d12.nodes.txt
081_off_O_d12.nodes.txt.meta
081_on_O_d12.nodes.txt
081_on_O_d12.nodes.txt.meta
093_off_O_d12.nodes.txt
093_off_O_d12.nodes.txt.meta
093_on_O_d12.nodes.txt
093_on_O_d12.nodes.txt.meta
B_G_d12.nodes.txt
B_G_d12.nodes.txt.meta
B_O_d12.nodes.txt
B_O_d12.nodes.txt.meta
builds.txt
fastchess_031.txt
fastchess_s10_variant.txt
j38_harness.py
partA_A2_analysis.txt
partA_proofs_raw.txt
partB_raw.txt
partB_readings.txt
partC_line_by_line.txt
prediction_job38.txt
REPORT_carbon2_job38.md
run_partA_match.py
run_partA_proofs.py
run_partB.py
run_step0.py
s10_variant_off_G_d12.nodes.txt
s10_variant_off_G_d12.nodes.txt.meta
s10_variant_off_O_d12.nodes.txt
s10_variant_off_O_d12.nodes.txt.meta
s10_variant_on_O_d12.nodes.txt
s10_variant_on_O_d12.nodes.txt.meta
s10_variant.patch.txt
stamps.txt
step0_raw.txt
```
