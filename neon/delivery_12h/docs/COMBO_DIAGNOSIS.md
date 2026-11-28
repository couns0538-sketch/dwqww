# `V3P_SF_COMBO_v1` Blowup Diagnosis & Clean Combo Verification (`M_A2`)

## 1. Executive Summary

`V3P_SF_COMBO_v1` (`728`-line union of `V3P + SF4b1 + SF4a + SF6 + SF8 + SF1`) blew up `B4+r0067` `bench 13` from `632,195` (`base_r15dsg`) to `773,964` (`+22.4%`) and scored **`-0.35 [-12.79, +12.10] Elo`** (`244-245-511`, `z=-0.055`) over `1,000` fastchess games (`50k` nodes) despite `SF8` solo scoring `+17.97 Elo` (`bench 13 = 542,701`, `-14.2%`) and `SF6` solo scoring `+10.43 Elo`.

Two distinct, code-verified root causes explain the regression:

1. **`SF4a_sf_rule50_damping.patch` (`+20.4%` B4 d13 / `-32.7%` FULL d13 / `+0.58 Elo` solo):** Unconditionally removes `EvalRule50Damp` (`false` by default in `forge/r15dsg`), shrinking `static_eval` on every reversible ply (`score - score * clock / 189`) and forcing `rule50_score_for_this_clock()` to `return true;`. This breaks `improving` comparisons across plies (`ss` vs `ss - 2`), destabilizes NMP/RFP/futility/EvalSwing, and leaks `clock=0` TT bounds into `clock>0` nodes.
2. **`SF6 + SF8` LMR Collapse (`+42.7%` B4 d13: `565,442 -> 806,766`; `+55.2%` d11 / `+24.3%` d13 under live `FULL` 49-option config):**
   - `SF8` enables `cont4/2` unconditionally and adds `cont6/4`, raising max quiet history from `49,152` to `61,440` (`+25%` ceiling, `+35–50%` typical positive scores on ordered quiets).
   - `SF6` switches `ReductionTable` to `1024`-scale fixed point, removes the integer deadzone (`history / LmrHistoryDivisor`), adds `!quiet` capture-history LMR (`-1` ply max), and truncates downward (`r_fp >> 10`) with **zero rounding/centering offset**.
   - **Empirical M_A2 isolation proves** that removing `!quiet` capture-history LMR alone (`SF4b1_SF6b_quiet_only_SF8_combo`) only trims `B4+r0067` `bench 13` from `806,766` to `777,867` (`+23.0%` over base) and leaves `FULL` d11 inflated at `272,020` (`+46.1%` over `SF4b1_SF8`). Even scaling the divisor by `3/2` **without** a rounding bias (`scaled_0`: `r_fp >> 10`) still blows up `B4+r0067` `bench 13` to **`780,335` (`+23.4%`)** because near-boundary `B4` table entries (`q(2,2)=1.068`, `q(3,3)=1.399`, `q(5,5)=2.027`) immediately drop 1 full ply on tiny positive `SF8` history.
   - **Fix (`SF6b_scaled` = `scaled_256`):** Quiet-only fractional LMR (`!quiet` caphist branch removed) + `/(tune::LmrHistoryDivisor * 3 / 2)` + `+256` rounding bias (`int r = r_fp >= 0 ? ((r_fp + 256) >> 10) : -((-r_fp) >> 10);`) preserves exact `r15dsg` reductions at `history = 0` while completely eliminating the blowup:
     - `SF4b1_SF6b_scaled_SF8_combo` / `V3P_SF4b1_SF6b_scaled_SF8_combo`:
       - Default `bench 11/13`: `309,401 / 729,443` (`-15.4%` vs base `862,329`)
       - `B4+r0067` `bench 11/13`: `191,512 / 566,308` (`-10.4%` vs base `632,195`, matching `SF4b1_SF8` `565,442`)
       - `FULL` (49-opt match config) `bench 11/13`: `163,489 / 459,684` (`-20.2%` vs base `576,076`, `-6.1%` vs `SF4b1_SF8` `489,595`)
       - `FULL + LmrDeeperShallower=true`: `193,901 / 519,866` (`-2.5%` vs base+DS `533,003`)

All 5 new M_A2 binaries pass `perft 5 == 4865609` across all 4 option sets, `v3_parity` `0/200` diffs across `8/8` king buckets and `8/8` output buckets (with planted `king_map[2]` bug detected `7/200`), and `SF4b1` search-vs-`uci eval` separation (`KRN-KR` `uci eval = 39`, `go depth 1 = 10 cp` vs base `54 cp`).

---

## 2. Exact Patch Diff Inventory (`V3P_SF_COMBO_v1` & M_A2 Clean Patches)

### 2.1 Existing Combo Composition (`C:\nnue-lab\neon\forge_fixes\patches\`)

`V3P_SF_COMBO_v1.patch` (`728` lines) is the exact union of 6 patches against `forge/r15dsg/`:

| Component Patch | Lines in `COMBO_v1` | Files & Exact Hunks |
|---|---:|---|
| `V3P_pairwise_psqt.patch` | `1–494` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`: adds `FlagPairwise=4`, `FlagPsqt=8`, `MaxHidden=1536`, `MaxPsqt=16*QA*QB`, `psqt` accumulators/cache/AVX2+AVX512+scalar pairwise kernels. Bit-identical on standard V3 (`!pairwise && !has_psqt`). |
| `SF4b1_v3_endgame_scale.patch` | `495–545, 705–713` | `include/forge/eval.hpp:51`, `src/eval.cpp:511-543`, `src/search.cpp:3422`: adds `scale_v3_eval` (pawnless `<=1` minor ahead + OCB damping) ONLY in `Worker::static_evaluate_v3`. |
| `SF4a_sf_rule50_damping.patch` | `546–558, 714–728` | `include/forge/search.hpp:363-371` (removes `!tune::EvalRule50Damp`, changes `/ 100` to `score - score * clock / 189`), `src/search.cpp:285-293` (forces `rule50_score_for_this_clock()` to `return true;`). **BLOWUP CAUSE #1.** |
| `SF6_lmr_fractional_caphist.patch` | `559–600, 675–704` | `src/search.cpp:294-320, 2405-2425`: `1024`-scale `ReductionTable`, `reduction_fp`, quiet LMR `history * 1024 / LmrHistoryDivisor` + `!quiet` caphist LMR + downward `r_fp >> 10` truncation. **BLOWUP CAUSE #2 (with `SF8`).** |
| `SF8_conthist_6ply.patch` | `601–656` | `src/search.cpp:893-936, 1617-1628, 1705-1713`: unconditional `cont4/2` + `cont6/4` (`ss->ply >= 2`) in `QuietScorer`, `Worker::quiet_history`, and `Worker::update_continuation`. |
| `SF1_quiet_checks_tail.patch` | `657–674` | `src/search.cpp:2272, 2290`: replaces `skip_quiets = true` in LMP/quiet futility with `picker.close_quiet_tail()`. |

### 2.2 New Clean M_A2 Patches (`C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\patches\`)

All generated via `git diff` against unmodified `C:\nnue-lab\forge\r15dsg\`:

1. **`SF4b1_SF8.patch`** (`123` lines): Exact `SF4b1` + `SF8` (no `V3P`, no `SF4a`, no `SF1`, no `SF6`).
2. **`SF6b_quiet_only.patch`** (`76` lines): Standalone `SF6b` keeping `1024`-scale `ReductionTable`, `reduction_fp`, `reduction() = reduction_fp(...) >> 10`, and quiet-only fractional LMR (`r_fp -= std::clamp(history * 1024 / tune::LmrHistoryDivisor, -2048, 2048);`), removing the `!quiet` capture-history LMR branch.
3. **`SF4b1_SF6b_quiet_only_SF8_combo.patch`** (`196` lines): `SF4b1 + SF8 + SF6b_quiet_only` (isolates `!quiet` caphist LMR vs quiet fractional LMR on `SF4b1+SF8`).
4. **`SF4b1_SF6b_scaled_SF8_combo.patch`** (`196` lines): `SF4b1 + SF8 + SF6b_quiet_scaled` (`history * 1024 / (tune::LmrHistoryDivisor * 3 / 2)` for quiets only + `int r = r_fp >= 0 ? ((r_fp + 256) >> 10) : -((-r_fp) >> 10);`).
5. **`V3P_SF4b1_SF6b_scaled_SF8_combo.patch`** (`694` lines): Clean `V3P_pairwise_psqt` + `SF4b1 + SF6b_scaled + SF8` ready for `G2` Pairwise+PSQT nets.

---

## 3. Verified Deterministic `bench 11 / 13` Matrix

Option sets tested (single-threaded, `r0067` = `C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`):
- **Default**: factory UCI defaults (HCE, no `r0067`).
- **`B4+r0067`**: `NNUEArchFile=cand.fnn3`, `NNUEArch=true`, `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true`.
- **`FULL`**: all 49 options from `pipeline/config.forge.toml` (`uci_options` + `v3_uci_options` + `NNUEArchFile` + `NNUEArch=true`), matching fastchess match conditions.
- **`FULL + DS`**: `FULL` + `LmrDeeperShallower=true`.

### 3.1 Existing Binaries (`C:\nnue-lab\neon\forge_fixes\builds\`)

| Executable | Default (`d11 / d13`) | `B4+r0067` (`d11 / d13`) | `d13` vs Base (`B4`) | `FULL` (`d11 / d13`) | `d13` vs Base (`FULL`) | `FULL + DS` (`d11 / d13`) |
|---|---:|---:|---:|---:|---:|---:|
| `base_r15dsg.exe` | `312,866 / 862,329` | `187,930 / 632,195` | `0.0%` | `218,410 / 576,076` | `0.0%` | `225,025 / 533,003` |
| `v3p_engine.exe` | `312,866 / 862,329` | `187,930 / 632,195` | `0.0%` | `218,410 / 576,076` | `0.0%` | `225,025 / 533,003` |
| `SF1_quiet_checks_tail.exe` | `353,777 / 958,576` | `214,513 / 658,655` | `+4.2%` | `205,140 / 514,456` | `-10.7%` | `267,410 / 606,912` |
| `SF4a_sf_rule50_damping.exe` | `293,202 / 863,278` | `206,111 / 760,916` | **`+20.4%`** | `173,749 / 387,885` | **`-32.7%`** | `208,917 / 462,545` |
| `SF4b1_v3_endgame_scale.exe` | `312,866 / 862,329` | `176,165 / 656,345` | `+3.8%` | `213,589 / 522,455` | `-9.3%` | `238,407 / 552,229` |
| `SF6_lmr_fractional_caphist.exe` | `331,231 / 971,962` | `221,678 / 652,860` | `+3.3%` | `187,527 / 493,256` | `-14.4%` | `227,077 / 622,982` |
| `SF8_conthist_6ply.exe` | `343,542 / 865,115` | `212,619 / 542,701` | **`-14.2%`** | `203,395 / 567,326` | `-1.5%` | `225,524 / 560,660` |
| `V3P_SF4b1_SF8.exe` | `343,542 / 865,115` | `233,585 / 565,442` | **`-10.6%`** | `186,160 / 489,595` | **`-15.0%`** | `221,320 / 551,204` |
| `V3P_SF4b1_SF6_SF8.exe` | `362,992 / 650,074` | `232,844 / 806,766` | **`+27.6%`** | `288,913 / 608,811` | **`+5.7%`** | `176,079 / 427,451` |
| `V3P_SF_COMBO_v1.exe` | `390,478 / 905,984` | `252,988 / 773,964` | **`+22.4%`** | `228,517 / 565,604` | `-1.8%` | `242,074 / 505,443` |

### 3.2 New M_A2 Clean Builds & Isolation Probes (`streamA_search\builds\`)

| Executable / Probe | Default (`d11 / d13`) | `B4+r0067` (`d11 / d13`) | `d13` vs Base (`B4`) | `FULL` (`d11 / d13`) | `d13` vs Base (`FULL`) | `FULL + DS` (`d11 / d13`) |
|---|---:|---:|---:|---:|---:|---:|
| **`SF4b1_SF8.exe`** | `343,542 / 865,115` | `233,585 / 565,442` | **`-10.6%`** | `186,160 / 489,595` | **`-15.0%`** | `221,320 / 551,204` |
| **`SF6b_quiet_only.exe`** | `313,259 / 869,179` | `224,944 / 670,590` | `+6.1%` | `188,062 / 470,018` | `-18.4%` | `256,599 / 516,524` |
| **`SF4b1_SF6b_quiet_only_SF8_combo.exe`** | `400,153 / 876,044` | `227,817 / 777,867` | **`+23.0%`** | `272,020 / 556,962` | `-3.3%` | `181,635 / 538,762` |
| *(probe)* `SF4b1+SF8+SF6b_scaled_0` (`*3/2`, `+0` bias) | `284,880 / 600,855` | `225,849 / 780,335` | **`+23.4%`** | `190,436 / 542,201` | `-5.9%` | `213,632 / 473,058` |
| *(probe)* `SF4b1+SF8+SF6b_scaled_512` (`*3/2`, `+512` bias) | `272,154 / 709,924` | `172,439 / 500,283` | `-20.9%` | `130,330 / 398,864` | `-30.8%` | `190,430 / 474,758` |
| **`SF4b1_SF6b_scaled_SF8_combo.exe`** (`*3/2`, `+256` bias) | `309,401 / 729,443` | `191,512 / 566,308` | **`-10.4%`** | `163,489 / 459,684` | **`-20.2%`** | `193,901 / 519,866` |
| **`V3P_SF4b1_SF6b_scaled_SF8_combo.exe`** (`*3/2`, `+256` bias) | `309,401 / 729,443` | `191,512 / 566,308` | **`-10.4%`** | `163,489 / 459,684` | **`-20.2%`** | `193,901 / 519,866` |

*(Non-PGO builds of `SF4b1_SF8` and `V3P_SF4b1_SF6b_scaled_SF8_combo` match PGO builds bit-for-bit on deterministic node counts and match `V3P_SF4b1_SF8` / `SF4b1_SF6b_scaled_SF8_combo` identically on `r0067`.)*

---

## 4. Code-Level Root Cause Analysis

### 4.1 `SF4a`: Unconditional Rule50 Damping & TT Clock Leak
- `forge/r15dsg/include/forge/search.hpp:363-371` gates rule50 eval damping behind `if (!tune::EvalRule50Damp || halfmove <= 0) return score;` (`EvalRule50Damp` defaults `false` at `search.cpp:164`).
- `SF4a` removes `!tune::EvalRule50Damp` and damps `score - score * clock / 189` unconditionally on every `static_eval` (`search.cpp:2023`, `1820`), while replacing `rule50_score_for_this_clock()` (`search.cpp:287-291`) with `return true;`.
- Consequence:
  1. Positive evals decay `~0.53%` per reversible ply, so `ss->static_eval` (at `clock = hmc`) drops below `(ss - 2)->static_eval` (at `clock = hmc - 2`), falsely flipping `improving` (`search.cpp:2033`) to `false` in quiet middlegames/endgames and distorting NMP (`2094, 2102`), RFP, futility, and `EvalSwingMult=15`.
  2. TT entries written at `clock = 0` (`100%` eval) are reused at `clock = 12+` (`~93.6%` eval), injecting inconsistent bounds and corrupting `update_correction` (`search.cpp:2531`).
  3. On `B4+r0067` this causes `+20.4%` expansion (`760,916`), while under `FULL` (`FutilityBase=12`, `NullMoveMinDepth=2`) it collapses the tree by `-32.7%` (`387,885`), yielding `+0.58 Elo` (`z=+0.07`) noise.

### 4.2 `SF6 + SF8` LMR Interaction & Empirical Isolation (`SF6b_quiet_only` vs `SF6b_scaled`)
1. **`SF8` shifts quiet history upward:** Removing `tune::ContHist4PlyRead &&` on `cont4/2` and adding `cont6/4` (`search.cpp:893-936, 1617-1628, 1705-1713`) increases max `quiet_history` from `49,152` to `61,440` (`+25%` ceiling) and raises ordered quiet history scores by `~35–50%`. Under integer LMR (`SF8` solo), `|history| < 6000` (or `< 6721` in `FULL`) still truncates to `0`, shrinking `bench 13` (`-14.2%` B4, `-1.5%` FULL).
2. **`SF6` removes the deadzone AND truncates downward (`r_fp >> 10`):**
   - `SF6` stores `floor(q * 1024)` in `ReductionTable`:
     - Under `B4` (`LmrQuietBase=85, LmrQuietDivisor=220`): `q(2,2) = 1.068 -> 1094`, `q(3,3) = 1.399 -> 1432`, `q(5,5) = 2.027 -> 2075`.
     - Under `FULL` (`LmrQuietBase=132, LmrQuietDivisor=176`): `q(3,3) = 2.006 -> 2054`.
   - Because `r = r_fp >> 10` truncates downward with **no centering/rounding offset** (unlike Stockfish's `r += 697` base offset at `Stockfish/src/search.cpp:1352`), a tiny positive history (`> 45` in `FULL` at `q(3,3)`, or `> 410` in `B4` at `q(2,2)`) drops `r` by a full ply (`2 -> 1` or `1 -> 0`), while negative history rarely crosses upward.
3. **Empirical isolation proves why both scaling AND `+256` rounding bias are required:**
   - Removing only `!quiet` caphist LMR (`SF4b1_SF6b_quiet_only_SF8_combo`) leaves `B4+r0067` d13 at `777,867` (`+23.0%` vs base, vs `806,766` with caphist) and `FULL` d11 at `272,020` (`+46.1%` vs `SF4b1_SF8` `186,160`). Thus caphist LMR only accounted for `~29k` of the `+241k` `B4` jump.
   - Scaling the divisor by `* 3 / 2` WITHOUT `+256` (`probe_scaled_0`: `r_fp >> 10`) STILL blows up `B4+r0067` d13 to `780,335` (`+23.4%`)!
   - Adding `+256` (`+0.25` ply rounding bias: `(r_fp + 256) >> 10`) with `* 3 / 2` divisor (`SF4b1_SF6b_scaled_SF8_combo`) leaves `history=0` reductions untouched relative to `r15dsg` (`1.068+0.25=1.318 -> 1`, `1.723+0.25=1.973 -> 1`, `2.027+0.25=2.277 -> 2`) while requiring meaningful positive history (`> ~2,600–3,200` on `q(2,2)`/`q(5,5)`) to reduce a full ply — eliminating the blowup completely (`B4` d13 `566,308` `-10.4%`, `FULL` d13 `459,684` `-20.2%`).
   - By contrast, `+512` (`probe_scaled_512`) rounds `q(4,4)=1.723` up to `2` even at `history=0`, overly compressing `FULL` (`398,864`, `-30.8%`). Hence `+256` + `* 3 / 2` is the clean surgical balance.

---

## 5. `LmrDeeperShallower=true` Interaction & Live Match Post-Mortem

- `LmrDeeperShallower` is already implemented in `forge/r15dsg/src/search.cpp:2432-2439` (defaults `false` at `search.cpp:163`).
- On `V3P_SF4b1_SF8`, enabling `LmrDeeperShallower=true` **inflates** `bench 13` by `+30.6%` under `B4+r0067` (`565,442 -> 738,447`) and `+12.6%` under `FULL` (`489,595 -> 551,204`).
- **Completed match `V3P_SF4b1_SF8_LmrDeeper_vs_base_1000g_50k` (`summary.json`):**
  - `1,000` games (`50k` nodes, `concurrency=6`, `UHO_Lichess_4852_v1.epd`, `seed=202611311`, `551.7s`):
  - `W-L-D = 251-242-507`, `ptnml=[16, 124, 210, 135, 15]`, **`Elo = +3.13 +/- 13.33 [-10.21, +16.48]`**, `z = +0.46`, `LOS = 67.72%`.
- Because `LmrDeeperShallower=true` dilated `V3P_SF4b1_SF8`'s tree (`489,595 -> 551,204` under `FULL`) and diluted `SF8`'s `+17.97 Elo` gain down to `+3.13 Elo`, **Neon should match clean `SF4b1_SF8` / `V3P_SF4b1_SF8` and `SF4b1_SF6b_scaled_SF8_combo` / `V3P_SF4b1_SF6b_scaled_SF8_combo` with `LmrDeeperShallower=false` (default) FIRST**, and only test `LmrDeeperShallower=true` separately if desired.

---

## 6. Correctness Verification (`perft 5`, `v3_parity`, `SF4b1` Separation)

All 5 new M_A2 executables passed every verification check (sequential, 1 thread):

1. **`perft 5 == 4865609`:** Passed on all 5 M_A2 exes across Default, `B4+r0067`, `FULL`, and `FULL+DS` (`20/20` runs, `0` UCI option refusals).
2. **`v3_parity` (200 `val.plain` FENs, `r0067` `cand.fnn3`, `8/8` KB `[0..7]`, `8/8` OB `[0..7]`):**
   - `SF4b1_SF8.exe`: `0/200` diffs (`bad_planted_bug = 7` on `king_map[2]` mutation)
   - `SF6b_quiet_only.exe`: `0/200` diffs (`bad_planted_bug = 7`)
   - `SF4b1_SF6b_quiet_only_SF8_combo.exe`: `0/200` diffs (`bad_planted_bug = 7`)
   - `SF4b1_SF6b_scaled_SF8_combo.exe`: `0/200` diffs (`bad_planted_bug = 7`)
   - `V3P_SF4b1_SF6b_scaled_SF8_combo.exe`: `0/200` diffs (`bad_planted_bug = 7`)
3. **`SF4b1` Search-vs-`uci eval` Separation (`r0067`):**
   - `KRN-KR` (`8/4k3/8/4r3/8/3R4/2N1K3/8 w - - 0 1`): `uci eval` = `39` on all binaries; `go depth 1` = `54 cp` (`base_r15dsg`, `SF6b_quiet_only`) vs **`10 cp`** (`SF4b1_SF8`, `SF4b1_SF6b_quiet_only_SF8_combo`, `SF4b1_SF6b_scaled_SF8_combo`, `V3P_SF4b1_SF6b_scaled_SF8_combo`); `go depth 6` = `32 cp` (`base`) vs `4–8 cp` (`SF4b1` builds).
   - `KBN-KB` (`8/8/3k4/8/3b4/8/2BNK3/8 w - - 0 1`): `uci eval` = `6` on all binaries; `go depth 1` = `33 cp` (`base`) / `34 cp` (`SF6b_quiet_only`) vs **`5–7 cp`** (`SF4b1` builds).
4. **Standalone unit test (`tests\test_sf6b_combo.py`):** Ran cleanly (`Ran 4 tests ... OK`, exit code `0`).

---

## 7. Copy-Paste Match Commands for Neon Main Agent

> **Note:** M_A2 builds in `streamA_search\builds\` are non-PGO (matching `base_r15dsg.exe` non-PGO bit-for-bit on fixed-node `50k` matches; for `6+0.06` clock matches later, rebuild winner with `build_fast.py --pgo`). Keep `LmrDeeperShallower=false` (default) on all initial screening matches.

### 7.1 `run_net_match.py` Screening Commands (`1,000` games, `50k` nodes, `LmrDeeper=false`)

1. **Clean `SF4b1_SF8` (isolate `SF4b1 + SF8` without `LmrDeeperShallower=true`):**
```powershell
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\run_net_match.py --name SF4b1_SF8_vs_base_1000g_50k --cand-exe C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\builds\SF4b1_SF8.exe --base-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe --cand-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --base-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --games 1000 --nodes 50000 --concurrency 6 --seed 202611315
```

2. **Existing `V3P_SF4b1_SF8` with `LmrDeeper=false` (re-check without `LmrDeeperShallower=true`):**
```powershell
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\run_net_match.py --name V3P_SF4b1_SF8_noDeeper_vs_base_1000g_50k --cand-exe C:\nnue-lab\neon\forge_fixes\builds\V3P_SF4b1_SF8.exe --base-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe --cand-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --base-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --games 1000 --nodes 50000 --concurrency 6 --seed 202611316
```

3. **Clean `SF4b1_SF6b_scaled_SF8_combo` vs `base_r15dsg`:**
```powershell
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\run_net_match.py --name SF4b1_SF6b_scaled_SF8_vs_base_1000g_50k --cand-exe C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\builds\SF4b1_SF6b_scaled_SF8_combo.exe --base-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe --cand-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --base-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --games 1000 --nodes 50000 --concurrency 6 --seed 202611317
```

4. **V3P-enabled `V3P_SF4b1_SF6b_scaled_SF8_combo` (on `r0067`, or swap `--cand-net` to `G2` Pairwise+PSQT `.fnn3`):**
```powershell
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\run_net_match.py --name V3P_SF4b1_SF6b_scaled_SF8_vs_base_1000g_50k --cand-exe C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\builds\V3P_SF4b1_SF6b_scaled_SF8_combo.exe --base-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe --cand-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --base-net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 --games 1000 --nodes 50000 --concurrency 6 --seed 202611318
```

### 7.2 Raw `fastchess.exe` Command Template (`V3P_SF4b1_SF6b_scaled_SF8_combo` vs `base_r15dsg`, `1,000` games, `50k` nodes)

```powershell
C:\nnue-lab\tools\fastchess\fastchess-windows-x86-64\fastchess.exe -engine cmd=C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\builds\V3P_SF4b1_SF6b_scaled_SF8_combo.exe name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.MateAlphaGuard=true option.LmrQuietBase=132 option.LmrQuietDivisor=176 option.LmrNoisyBase=25 option.LmrNoisyDivisor=336 option.LmrHistoryDivisor=6721 option.NullMoveBase=5 option.LmpBase=13 option.HistoryPruneMultiplier=1945 option.HistoryBonusQuadratic=49 option.HistoryBonusLinear=90 option.HistoryBonusMax=2429 option.SingularDepth=6 option.IirDepth=5 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=true option.DrawJitter=2 option.NullMoveMinDepth=2 option.NullMoveDepthDivisor=4 option.NullMoveEvalDivisor=184 option.RfpDepth=6 option.RfpMargin=84 option.RfpImproving=37 option.RazorDepth=3 option.RazorBase=182 option.RazorMultiplier=379 option.FutilityDepth=8 option.FutilityBase=12 option.FutilityMultiplier=59 option.HistoryPruneDepth=2 option.SeeQuietMultiplier=15 option.SeeNoisyMultiplier=83 option.SingularMargin=3 option.ProbcutDepth=7 option.ProbcutMargin=168 option.QsFutilityMargin=123 option.AspirationDelta=16 option.CheckExtensionDepth=3 option.LmrCutoffThreshold=9 option.MaterialCorrectionWeight=48 option.CaptureFutilityBase=45 option.FailLowContinuationBonus=41 option.EvalSwingMult=15 option.NNUEArchFile=C:/nnue-lab/runs/forge/r0067/train/cand.fnn3 option.NNUEArch=true -engine cmd=C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe name=base option.Threads=1 option.Hash=16 option.OwnBook=false option.MateAlphaGuard=true option.LmrQuietBase=132 option.LmrQuietDivisor=176 option.LmrNoisyBase=25 option.LmrNoisyDivisor=336 option.LmrHistoryDivisor=6721 option.NullMoveBase=5 option.LmpBase=13 option.HistoryPruneMultiplier=1945 option.HistoryBonusQuadratic=49 option.HistoryBonusLinear=90 option.HistoryBonusMax=2429 option.SingularDepth=6 option.IirDepth=5 option.NonPawnCorrection=true option.CuckooRep=true option.HistRework=2 option.TtPruneV2=true option.CorrHistV2=true option.DrawJitter=2 option.NullMoveMinDepth=2 option.NullMoveDepthDivisor=4 option.NullMoveEvalDivisor=184 option.RfpDepth=6 option.RfpMargin=84 option.RfpImproving=37 option.RazorDepth=3 option.RazorBase=182 option.RazorMultiplier=379 option.FutilityDepth=8 option.FutilityBase=12 option.FutilityMultiplier=59 option.HistoryPruneDepth=2 option.SeeQuietMultiplier=15 option.SeeNoisyMultiplier=83 option.SingularMargin=3 option.ProbcutDepth=7 option.ProbcutMargin=168 option.QsFutilityMargin=123 option.AspirationDelta=16 option.CheckExtensionDepth=3 option.LmrCutoffThreshold=9 option.MaterialCorrectionWeight=48 option.CaptureFutilityBase=45 option.FailLowContinuationBonus=41 option.EvalSwingMult=15 option.NNUEArchFile=C:/nnue-lab/runs/forge/r0067/train/cand.fnn3 option.NNUEArch=true -each proto=uci nodes=50000 -openings file=C:/nnue-lab/tools/book/UHO_Lichess_4852_v1.epd format=epd order=random -srand 202611318 -rounds 500 -games 2 -repeat -concurrency 6 -recover -ratinginterval 40 -pgnout file=C:\nnue-lab\neon\forge_fixes\matches\V3P_SF4b1_SF6b_scaled_SF8_vs_base_1000g_50k\games.pgn min=true -autosaveinterval 0 -log file=C:\nnue-lab\neon\forge_fixes\matches\V3P_SF4b1_SF6b_scaled_SF8_vs_base_1000g_50k\fastchess.log level=warn
```
