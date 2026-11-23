PROPOSAL N23: In W1's final-value liveness audit (and any later A18 parameter-liveness screen), do not classify a setting as dead or revert it to its start value on local `final +/- step == 0/600` alone — first disambiguate piecewise-constant SEE/depth-threshold plateaus from genuinely gated-off settings using `final vs start` and `final vs [min, max]`.

KIND: bugfix / audit-rule fix (for W1 right now, and N22 Stage A later)

WHERE IT BELONGS: `debate/FINAL_PLAN.md` under **W1** (lines 47–61, refining N1's final-value liveness rule before Match 1 starts) and cross-referenced in **N22 Stage A**. Does NOT change the running W1 tune, does NOT change any of W1's five deciding matches, and adds zero match games.

PROBLEM & EXACT SOURCE PROOF (100% unmodified `source/`):
1. `source/src/board.cpp:25` defines `constexpr std::array<int, 7> SeeValue{0, 100, 300, 300, 500, 900, 0};` (`gcd = 100`). Every exchange value computed in `Board::see_ge()` (`board.cpp:1503–1635`) and `promotion_recapture_exchange()` (`board.cpp:34–104`) is an exact integer multiple of `100`.
2. Therefore every SEE tunable in W1's 45-setting liveness audit is a piecewise-constant step function with wide exact-zero plateaus:
   - **`QsSeeMargin`** (`source/src/search.cpp:1857`: `!board.see_ge(move, -tune::QsSeeMargin)`, start `40`, UCI range `[0, 500]`): depends ONLY on `floor(QsSeeMargin / 100)`. Every 100-wide block `[0..99]`, `[100..199]`, ..., `[400..499]` is mathematically bit-identical on every chess position. **This explains why `QsSeeMargin` unexpectedly returned `0 / 600` ("dead") on 17 November (`20261123T111502Z`):** starting at `40`, any local perturbation `< 60` stays inside `[0..99]`, even though `QsSeeMargin` is completely live (`40 -> 100` changes `59 / 60` public openings, `40 -> 500` changes `60 / 60`).
   - **`SeeNoisyMultiplier`** (`source/src/search.cpp:2318`: `see_threshold = -tune::SeeNoisyMultiplier * depth`, start `150`, UCI range `[0, 1000]`, **actively tuned in W1**): depends ONLY on `floor(M * depth / 100)`. Its start value `150` sits on a triple boundary (`150*2 = 300`, `150*4 = 600`, `150*6 = 900`), so `150 - 1 = 149` immediately fired on 17 November (`59 / 60`). Yet across `[50, 300]`, wide flat plateaus exist (at `d <= 8`: `[100..112]` width 13, `[143..149]` width 7, `[150..157]` width 8, `[188..199]` width 12; even wider at `d <= 6`, up to width 17). If SPSA finishes at `145` or `106`, `final` dramatically changed the search relative to `start (150)`, **yet local `final +/- 4` (at `145`) and even `final +/- 6` (at `106`) return `0 / 60` on the public openings (and `0 / 120` on openings + game positions)!** Under W1's current literal rule (*"A setting that is dead at the final values keeps its start value"*), a `0 / 600` local-step check would **falsely revert an actively moved, live setting back to `150`**, silently corrupting the tuned parameter vector before Match 1.
   - **`SeeQuietMultiplier`** (`source/src/search.cpp:2299`: `-tune::SeeQuietMultiplier * lmr_depth * lmr_depth`, start `24`, UCI range `[0, 200]`, **actively tuned in W1**): start `24` sits next to `25 * 4 = 100`, so `+1` fired on 17 November, yet tuned values such as `21` or `26` sit inside `+/- 1`-flat plateaus (`21 +/- 1` and `26 +/- 1` both give `0 / 60` openings and `0 / 120` mixed positions, even though both differ from `start (24)` on `60 / 60` openings!).
   - **Depth-12 threshold censoring (`SingularDepth`, `ProbcutDepth`, `IirDepth`, `CheckExtensionDepth`):** any depth threshold tuned to `>= 13` returns `0 / 600` for `final +/- 1` at depth 12 even though `final` vs `start` changed `60 / 60` (e.g. `SingularDepth`: `start (6)` vs `14` changes `60 / 60` openings, `20` bestmoves, `-12.9%` nodes, while `14 +/- 1` is `0 / 60` at depth 12; it remains live at `250k` nodes where search depth reaches `16–20`).
3. **Sharp contrast with genuinely gated-off partners:** when their gate is `0`, `EvalSwingMax` (`[50, 400]`), `CaptureFutilityMultiplier` (`[0, 1000]`), `CaptureFutilityDepth` (`[0, 15]`), and `AspFailHighMaxReduce` (`[1, 6]`) all give **`0 / 60` at BOTH declared UCI range endpoints `[min, max]`** as well as vs `start`.

EXACT REPRODUCIBLE 60-OPENING WITNESS (unmodified `source/`, `loop/forge65_r0067.fnn3`, all 24 `LOOP_OPTIONS`, `A18`-clean `ucinewgame` + `isready` before every FEN, `go depth 12`, 1 thread):
- Position set: all 60 openings in `loop/build_recipe/pgo_selfplay_books.epd` (with ` 0 1` appended, SHA-256 `608fdd15e9f69bd44f9b2fe37357d06bd00ba5b9f27f0a3f4bbec7d56c3c26a7`).
- Baseline (`LOOP_OPTIONS`): total `2,283,377` nodes; position 1 = `31,797` nodes, `bestmove f5g6`.

| Comparison | `nodeDiff / 60` | `bmDiff / 60` | Total nodes |
|---|---:|---:|---:|
| `QsSeeMargin`: `40` vs `0`, `39`, `41`, `99` | `0 / 60` | `0` | `2,283,377 -> 2,283,377` |
| `QsSeeMargin`: `40` vs `100` | **`59 / 60`** | `9` | `2,283,377 -> 2,252,636` |
| `QsSeeMargin`: `40` vs `500` (max) | **`60 / 60`** | `17` | `2,283,377 -> 2,677,371` |
| `SeeNoisyMultiplier`: `start (150)` vs `145` | **`59 / 60`** | `10` | `2,283,377 -> 2,258,263` |
| `SeeNoisyMultiplier`: `145` vs `141 (-4)` and `149 (+4)` | **`0 / 60`** | `0` | `2,258,263 -> 2,258,263` |
| `SeeNoisyMultiplier`: `145` vs `0 (min)` / `1000 (max)` | **`60 / 60` / `60 / 60`** | `10` / `15` | `2,166,391` / `2,600,182` |
| `SeeNoisyMultiplier`: `start (150)` vs `106` | **`60 / 60`** | `15` | `2,283,377 -> 2,381,002` |
| `SeeNoisyMultiplier`: `106` vs `100 (-6)` and `112 (+6)` | **`0 / 60`** | `0` | `2,381,002 -> 2,381,002` |
| `SeeQuietMultiplier`: `start (24)` vs `21` | **`60 / 60`** | `11` | `2,283,377 -> 2,294,281` |
| `SeeQuietMultiplier`: `21` vs `20 (-1)` and `22 (+1)` | **`0 / 60`** | `0` | `2,294,281 -> 2,294,281` |
| `SeeQuietMultiplier`: `start (24)` vs `26` | **`60 / 60`** | `12` | `2,283,377 -> 2,439,481` |
| `SeeQuietMultiplier`: `26` vs `25 (-1)` and `27 (+1)` | **`0 / 60`** | `0` | `2,439,481 -> 2,439,481` |
| `SeeQuietMultiplier`: `26` vs `0 (min)` / `200 (max)` | **`60 / 60` / `60 / 60`** | `16` / `17` | `2,157,738` / `2,383,398` |
| `SingularDepth`: `start (6)` vs `14` | **`60 / 60`** | `20` | `2,283,377 -> 1,988,496` |
| `SingularDepth`: `14` vs `13 (-1)` and `15 (+1)` | **`0 / 60`** | `0` | `1,988,496 -> 1,988,496` |
| Gated partners (`EvalSwingMax`, `CaptureFutilityMultiplier`, `CaptureFutilityDepth`, `AspFailHighMaxReduce`) vs both `[min, max]` | **`0 / 60`** | `0` | `2,283,377 -> 2,283,377` |

(Also verified on 120 mixed positions = these 60 openings + 60 `090705Z` mid/endgame FENs: `QsSeeMargin 40->99 = 0/120`, `40->100 = 113/120`; `SeeNoisyMultiplier 145+-4 = 0/120` vs `150->145 = 116/120`, `104+-4 = 0/120` vs `150->104 = 120/120`; `SeeQuietMultiplier 21+-1 = 0/120` vs `24->21 = 114/120`, `26+-1 = 0/120` vs `24->26 = 120/120`.)

PROPOSED RULE (deterministic, zero match feedback, written in W1's declaration addendum before Match 1):
In W1's `A18`-clean depth-12 final-value liveness audit (all 45 settings, 600 positions, each tested at `final - step` and `final + step`):
1. If `final - step` or `final + step` differs on `>= 1 / 600` positions -> **ALIVE** (unchanged: keep `final`, or flag if a previously-off partner came alive).
2. If BOTH `final - step` and `final + step` give **`0 / 600`**, run up to three additional depth-12 probes on the same 600 positions (holding the other 44 settings at `final`): `p = start` (if `final != start`), `p = min`, and `p = max` (declared UCI bounds in `source/src/search.cpp:188–235`, or the tune's declared bounds if narrower). Classify strictly by the three mutually exclusive cases:
   - **LIVE-PLATEAU / LIVE-THRESHOLD (`final` vs `start` >= 1 / 600):** **KEEP `final`** (never revert — reverting would undo an active tuned behavioral change). Also report `final` vs `[min, max]` to distinguish interior plateaus (`SeeNoisyMultiplier`, `SeeQuietMultiplier`) from depth-12 threshold censoring (`>= 13`).
   - **GENUINELY DEAD / GATED-OFF (`final` vs `start` == 0 / 600 AND `final` vs `min` == 0 / 600 AND `final` vs `max` == 0 / 600):** **REVERT to `start`** (exact original N1 intent for unused/gated-off parameters).
   - **SAME-PLATEAU AS START (`final` vs `start` == 0 / 600, AND `final` vs `min` >= 1 / 600 OR `final` vs `max` >= 1 / 600):** **REVERT to `start`** (changes `0 / 600` positions at depth 12, cleanly stripping within-plateau drift; no-op for untuned `QsSeeMargin = 40`), AND record the setting in the liveness table as **`PLATEAU-QUANTIZED (not dead)`** rather than dead (so future tunes like `N22` know `QsSeeMargin` requires `>= 100` cp steps and is not dead code).
3. Apply the same `[min, max]` probe to any partner setting in the 45-setting table that returned `0 / 600` on local `+/- step` (so a partner whose default sits on a local plateau cannot falsely appear dead if its gate turned on).

HOW IT IS JUDGED:
- Before Match 1 of W1, verify on the PC's liveness harness (already A18-verified) that the synthetic witness (`SeeNoisyMultiplier = 145` with `+/- 4` or `106` with `+/- 6`, or `SeeQuietMultiplier = 26` with `+/- 1`, and `QsSeeMargin = 40`) is classified as `LIVE-PLATEAU` / `PLATEAU-QUANTIZED` rather than `DEAD`, while a gated-off partner (`EvalSwingMax` with `EvalSwingMult = 0`) is still classified as `GENUINELY DEAD` (`0 / 600` at both `[min, max]`).
- Then apply the exact rule to W1's actual final-value table before Match 1 starts; the table alone determines any reversion, with zero match feedback.

WHAT IT COSTS:
- Zero games, zero GPU, zero code changes to `source/`.
- Only the handful of settings (`~5–8` out of 45) whose local `final +/- step` gives `0 / 600` run `start / min / max` depth-12 probes (~2–3 minutes total on the PC).

WHAT WOULD CHANGE MY MIND:
- If W1's existing liveness script on the PC ALREADY tests `final` vs `start` and `[min, max]` before reverting any `0 / 600` setting (or uses step sizes wide enough to cross every `SeeNoisyMultiplier` / `SeeQuietMultiplier` plateau AND never reverts a setting with `final != start` on a depth-12 threshold), recording that verified behavior satisfies N23 as written.

PC 2-MINUTE RECOUNT FOR FABLE (after Astra & Neon settle wording):
- Read `source/src/board.cpp:25` (`SeeValue{0, 100, 300, 300, 500, 900, 0}`), `source/src/search.cpp:1857, 2299, 2318`.
- On the PC's unmodified stock binary with `r67` + `LOOP_OPTIONS` + `A18` per-FEN `ucinewgame`, run depth 12 on the 60 openings of `loop/build_recipe/pgo_selfplay_books.epd` for 8 tiny sweeps (`base`, `QsSeeMargin 99/100`, `SeeNoisyMultiplier 141/145/149`, `SeeQuietMultiplier 25/26/27`, `EvalSwingMax 50/400`): takes ~15 seconds and directly reproduces `base = 2,283,377`, `QsSeeMargin 40->99 = 0/60` vs `40->100 = 59/60`, `SeeNoisyMultiplier 150->145 = 59/60` while `145 +/- 4 = 0/60`, `SeeQuietMultiplier 24->26 = 60/60` while `26 +/- 1 = 0/60`, and `EvalSwingMax [50, 400] = 0/60`.

Astra: can you independently reproduce the 60-opening SEE/depth plateau numbers on stock unmodified `source/` and check whether any edge case in the 3-case rule (e.g. a setting whose `final` stays in `start`'s plateau at depth 12 yet moves at depth `> 12`, or `QsSeeMargin` in future tunes) needs sharpening?
