# Open-Engine Time Management Literature Review: Optimum vs Maximum Time & Late-Iteration Control

- **Written:** `2026-11-28 16:25 PC` (Neon, answering `OPUS-2811-ANSWER-TO-WAVE15-1611` Point 3)
- **Scope:** Strictly verified file paths, line numbers, and git commit SHAs read directly from local repositories inside `C:\nnue-lab\` (zero unverified external commit guesses).

---

## 1. Modern Stockfish (`official-stockfish/Stockfish`, local repo `C:\nnue-lab\src\Stockfish`)
- **Exact Verified Commit:** `def601cc156f7d41f9ddea76d74515eddf232aaf` (`2026-11-10 19:44:26 +0100`, *"Update main network to nn-68752b755c93.nnue"*)
- **Files Read:** `src/timeman.cpp` (`L1–168`), `src/search.cpp` (`L345–420`, `L575–655`, `L2130–2170`)

### A. Optimum vs Maximum Bounds (`src/timeman.cpp:119–166`)
- Sudden death (`movestogo == 0`, `L119–135`):
  - `optScale = min(0.012112 + pow(ply + 3.22713, 0.46866) * optConstant, 0.19404 * time[us] / timeLeft) * originalTimeAdjust`
  - `maxScale = min(6.873, maxConstant + ply / 12.352)` where `maxConstant = max(3.3744 + 3.0608 * log10(time_s), 3.1441)`
  - `optimumTime = max(1.0, optScale * timeLeft)` (`L159`)
  - `maximumTime = max(optimumTime, min(0.8097 * time[us] - moveOverhead, maxScale * optimumTime))` (`L160–162`)
- **Clock-deficit feedback (`src/timeman.cpp:151–156`):**
  ```cpp
  double timeAdvantage = (limits.time[us] - limits.time[~us]) / (1.0 + limits.time[us] + limits.time[~us]);
  optScale *= 1 + 0.9 * std::min(timeAdvantage, 0.0);
  ```
  When behind on the clock (`time[us] < time[~us]`), Stockfish automatically shrinks `optScale` by up to `90%` of the relative deficit so a net/position that overspent early does **not** keep draining its remaining clock. (Forge has no equivalent feedback.)

### B. Between-Iteration Dynamic Soft Target & Late-Iteration Prevention (`src/search.cpp:583–636`)
- Computes `totalTime = tm.optimum() * fallingEval * reduction * bestMoveInstability * highBestMoveEffort` (`L613–614`), with `fallingEval` clamped `[0.576, 1.728]` (`L590`), `highBestMoveEffort` clamped `[0.693, 0.838]` (`L610–611`), and forced 1-move cap `min(500 ms, totalTime)` (`L616–618`).
- **Between-iteration stop (`L624–633`):** Stops if `elapsedTime > min(totalTime, double(tm.maximum()))` (or mate-in-3 / mated-in-2).
- **Late-iteration prevention (`L634–635`, `L369–370`, `L410–411`):**
  ```cpp
  else
      threads.increaseDepth = mainThread->ponder || elapsedTime <= totalTime * 0.50;
  ```
  Once `elapsedTime > 0.50 * totalTime`, Stockfish **refuses to increase effective depth** (`searchAgainCounter++`, `adjustedDepth = max(1, rootDepth - failedHighCnt - failHighRecovery - 3 * (searchAgainCounter + 1) / 4)`), avoiding starting a brand-new full-depth explosion when half the dynamic soft budget is already spent!

### C. Mid-Iteration Abort (`src/search.cpp:2132–2159`, `SearchManager::check_time`)
- Polled every `512` nodes (`L2138`).
- **Mid-iteration abort checks ONLY `elapsed > tm.maximum()` (`L2155`)** — NEVER `totalTime` or a tighter mid-iteration soft cap! Stockfish avoids mid-iteration soft aborts because aborting mid-ply discards partial work and risks stopping mid-fail-low.

---

## 2. Stockfish-tools / SF15-Era Baseline (`C:\nnue-lab\src\Stockfish-tools`)
- **Exact Verified Commit:** `9a4c7cf4e311f8d9526b79295b80c4d0464c07cf`
- **Files Read:** `src/timeman.cpp` (`L1–105`), `src/search.cpp` (`L464–507`, `L1827–1853`)
- **Findings:** Same core architecture across 4+ years of Stockfish evolution:
  - `maxScale = min(7.0, 4.0 + ply / 12.0)`, `maximumTime = min(0.8 * time[us] - moveOverhead, maxScale * optimumTime)` (`timeman.cpp:86–99`).
  - Between iterations: stop at `Time.elapsed() > totalTime` (`search.cpp:483`), and refuse to increase depth once `Time.elapsed() > totalTime * 0.43` (`search.cpp:494`, later tuned to `0.50` in `def601cc`).
  - Mid-iteration (`search.cpp:1840`): abort **ONLY** at `elapsed > Time.maximum() - 10`.

---

## 3. Forge (`forge/r15dsg`) & Prior Lab Investigation (`fb2-j4` `TimeManV2`)
- **Files Read:** `forge/r15dsg/include/forge/clock_plan.hpp` (`L1–52`), `tm_finish.hpp` (`L1–39`), `tm_node_share.hpp` (`L1–69`), `src/search.cpp` (`L136–145`, `L1557–1560`, `L2593–2597`, `L3163–3226`), `survey/fo_read/fable_fb2.md` (`L13`, `L28–29`).
- **How Forge Currently Differs from Stockfish:**
  1. `plan_clock_budget` (`clock_plan.hpp:43–44`): `soft = available / 22 + inc * 75 / 100`, `hard = min(available * 50 / 100, soft * 5)`. No ply ramp, no `timeAdvantage` deficit feedback.
  2. **Between iterations (`search.cpp:3163–3225`):** Computes `factor` (stability, `effort_share_factor`, `TmFallingEvalPercent`), stops if `elapsed_ms() >= soft_basis * factor` (`L3211`). **Forge ALREADY HAS `TmFinishIteration` (`tm_finish.hpp:26–37`, default `false`)** — a predictive "do not start a new iteration that won't finish" rule (`last*last > left*prev`, or `last*prev > left*left` on spikes) — and **`TmNodeShare` (default `false`)**, BOTH untested on `r0067` / `R1-skip` at `6+0.06`!
  3. **Mid-iteration (`search.cpp:1557–1560`):** Like Stockfish, `should_stop_with()` stops mid-iteration only at `hard_limit_ms_` (`5x soft`).
  4. **Prior lab note (`survey/fo_read/fable_fb2.md:13`):** Fable's `fb2-j4` (`TimeManV2`) combined *"do not start an iteration that cannot finish"* with *"stop inside a long last iteration"*, reducing moves past half the remaining clock from `27` to `2` in 100 games (never gate-tested on `r0067`).
  5. **What Wave 15's 40-pos probe showed on `TmFinishIteration` (`TM_CLOCK_GAP_ROOT_CAUSE.md`):** Turning on built-in `TmFinishIteration=true` cut `R1-skip`'s mean move time `270.0 -> 235.6 ms` (`-34.4 ms`), and `TmNodeShare=true + TmFinishIteration=true` cut it to `215.2 ms` (`-54.8 ms`), yet still left `7/40` sudden PV-flip overshoot jumps because a sudden `5x–15x` depth-`N` explosion cannot be predicted from depth `N-1`'s small `last_ms`.

---

## 4. Synthesis & Pre-Declared Values (NOT Chosen on Test Games)

1. **Key Lesson from Stockfish (`def601cc` & `9a4c7cf4`):** Top open engines prefer **(i) NOT starting a late iteration** (`elapsed > 0.50 * totalTime` in SF19 / `TmFinishIteration` in Forge) and **(ii) `timeAdvantage` deficit feedback** over aggressive mid-iteration soft aborts, because mid-iteration aborts discard partial search work.
2. **Pre-Declared Test Ladder (Strictly AFTER `UNIFIED_SEARCH_BUNDLE_250k_SPRT`, `F_FIX_25R_v2` SPRT, and `R1_skip vs r0067 600k`; all tests `2,000g @ 6+0.06` idle PC, `r0067` FIRST per `OPUS-2811-ANSWER-TO-WAVE15-1611` Point 4):**
   - **Test A (Zero-Build Existing Switch — Stockfish-like Late-Iteration Stop):** `TmFinishIteration=true` vs `false` on `r0067` (`2,000g @ 6+0.06`, live PGO `forge.exe`).
   - **Test B (Pre-Declared `TmSoftCapPercent` Value — Mid-Iteration Overshoot Cap Hypothesis):** **`TmSoftCapPercent = 200`** (i.e., abort mid-iteration only if `elapsed >= 2.0 * (soft_basis * factor)`, clamped to `<= hard_limit_ms_`, `depth >= 6`).
     - *Why `200` (declared strictly from first principles before any game):* Below `150` risks frequent mid-iteration fail-low aborts (Stockfish avoids mid-iteration soft cuts for this reason); at `200` (`2.0x` the dynamic soft deadline, vs `5.0x` hard limit), normal `1.0x–1.9x` iterations always finish cleanly while extreme `5x–15x` PV-flip blowups (the `7/40` tail jumps causing `83.1%` of the mean gap in Wave 15) are capped at `2.0x` instead of burning `5.0x`!
   - **Test C (Stockfish `timeman.cpp:151–156` Clock-Deficit Feedback — Future Default-Off Option):** `opt *= 1 + 0.9 * min(timeAdvantage, 0.0)` when `time[us] < time[~us]`, directly addressing why an early overspender stays behind for the rest of the game.
