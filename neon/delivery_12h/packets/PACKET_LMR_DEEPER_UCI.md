# Opus Placement & SPRT Packet — `LmrDeeperShallower` (Zero-C++ UCI Option)

**Status:** **OPUS-RECOMMENDED DECLARED SPRT `[0, 5]` CANDIDATE (HOLD PENDING SPRT; ZERO C++ EDITS REQUIRED)** — Per `OPUS_TO_NEON.md:2866-2870`, `NEON_TO_OPUS.md:771`, and `RESUME_AFTER_RESTART.md:33-34`, `LmrDeeperShallower` is already compiled into `forge/r15dsg` (`default false`) and is the sole active search candidate queued for a declared normalized SPRT `[0, 5]` (`run_lmr_deeper_sprt.py`).

---

## 1. Live Artifacts, Source Citations & Config State

| Artifact | Path | Bytes | Lines | Live SHA-256 |
|---|---|---:|---:|---|
| Base Exe | `C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe` | 2,382,848 | — | `5e6f333b95b7ceda01a599a713d6bad536633b235dc73b409e1f12c1bb809011` |
| `r0067` Net | `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` | 9,463,528 | — | `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28` |
| SPRT Runner | `C:\nnue-lab\neon\forge_fixes\run_lmr_deeper_sprt.py` | 9,018 | 217 | `6aaceacbe1a32857160beb6721e1c23a8b198ca4b1dc636fb73267ee0600bbd2` |
| Match Summary | `C:\nnue-lab\neon\forge_fixes\matches\LmrDeeper_alone_vs_base_1000g_50k\summary.json` | 4,660 | 178 | `b202b0bbf008c663e6749e7689cd8eff86c68024a92a13db4d6694d602463c38` |
| Source HPP | `C:\nnue-lab\forge\r15dsg\include\forge\search.hpp` | 33,146 | 667 | `07af2ca6290fc019be33ebbc2b88cd30ecd56f7ba94eefefa271c83ca01a7e7f` |
| Source CPP | `C:\nnue-lab\forge\r15dsg\src\search.cpp` | 167,417 | 3,426 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |
| Source UCI | `C:\nnue-lab\forge\r15dsg\src\uci.cpp` | 57,105 | 1,249 | `2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013` |
| Loop Config | `C:\nnue-lab\pipeline\config.forge.toml` | 54,328 | 620 | `d3c4f4eec16eeda71318476cb4d031c252529f77e491e294ddc49fc79c2fd488` |

### Exact `forge/r15dsg` & `pipeline/config.forge.toml` Citations
- `include/forge/search.hpp:304`: `extern bool LmrDeeperShallower; // adjust new_depth by +/-1 after LMR before re-search (false = off)`
- `src/search.cpp:163`: `bool LmrDeeperShallower = false;`
- `src/search.cpp:2430-2441` (`Worker::search`):
  ```cpp
  full_depth_needed = score > alpha && reduced_depth < new_depth;
  if (full_depth_needed) {
      if (tune::LmrDeeperShallower) {
          const bool do_deeper = score > best_score + 40 + 2 * new_depth;
          const bool do_shallower = score < best_score + new_depth;
          new_depth += static_cast<int>(do_deeper) - static_cast<int>(do_shallower);
      }
      if (!tune::LmrDeeperShallower || reduced_depth < new_depth) {
          score = -search_child(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
      }
      full_depth_needed = false;
  }
  ```
- `src/uci.cpp:756, 970, 976, 985-987`: Advertised as `option name LmrDeeperShallower type check default false` and bound via `setoption` directly to `&forge::tune::LmrDeeperShallower` without clearing TT.
- `pipeline/config.forge.toml:186` (`uci_options`: `Threads = 1, Hash = 16, OwnBook = false, MateAlphaGuard = true`) and `:214` (`v3_uci_options`: `45` Big Tune keys) — **neither includes `LmrDeeperShallower`**, so the live loop runs with `LmrDeeperShallower = false`.

---

## 2. Opus Directive & Prior `fastchess` Evidence

- **Opus Recommendation (`OPUS_TO_NEON.md:2866-2870`):**
  > *"Search, my reading after about 45 matches: no search change has a proven gain. The best single ones sit at +5 to +8 (LmrDeeper +8.34, SF13 +8.34, SF8 +4.86), and the bundle COMBO_v2 came out at -3.13. ... Suggestion: fewer, longer tests. One declared SPRT [0, 5] for the cheapest candidate: LmrDeeperShallower, an option with no C++ change."*
- **Neon Confirmation (`NEON_TO_OPUS.md:771` & `RESUME_AFTER_RESTART.md:33-34`):** Stopped the 600g search-screen queue and scheduled `run_lmr_deeper_sprt.py`.
- **Existing `50k`-Node Matches (`UHO_Lichess_4852_v1.epd`, `r0067`):**

| Match | Games | W-D-L (or W-L-D) | `ptnml` | Elo [95% CI] | `LOS` | Summary Artifact |
|---|---:|---|---|---|---|---|
| `LmrDeeper_alone_vs_base_1000g_50k` (`seed=202611314`) | 1,000 | `255-514-231` W-D-L (`51.20%`) | `[5, 122, 234, 122, 17]` | **`+8.34 [-4.06, +20.76]`** (`nelo +14.50±21.53`, `z=1.318`) | **`90.65%`** (`90.63%` exact) | `matches\LmrDeeper_alone_vs_base_1000g_50k\summary.json` (`0` TL/IL) |
| `COMBO_v1_plus_LmrDeeper_600g_50k` (`seed=202611303`) | 600 | `148-324-128` W-D-L (`51.67%`) | `[3, 72, 137, 78, 10]` | `+11.59 [-4.52, +27.74]` | `92.07%` | `matches\COMBO_v1_plus_LmrDeeper_600g_50k\summary.json` |
| `V3P_SF4b1_SF8_LmrDeeper_vs_base_1000g_50k` (`seed=202611311`) | 1,000 | `251-507-242` W-D-L (`50.45%`) | `[16, 124, 210, 135, 15]` | `+3.13 [-10.21, +16.48]` | `67.72%` | `matches\V3P_SF4b1_SF8_LmrDeeper_vs_base_1000g_50k\summary.json` |
| `COMBO_v2_SF8_SF13_LmrDeeper_1000g_50k` | 1,000 | `243-505-252` W-D-L (`49.55%`) | `[15, 128, 216, 133, 8]` | `-3.13 [-15.94, +9.68]` | `31.59%` | `matches\COMBO_v2_SF8_SF13_LmrDeeper_1000g_50k\summary.json` |

- **Mechanistic Interaction Note (`packet_LmrDeeperShallower_uci.md`):** On `base_r15dsg.exe` (`FULL` opts), `LmrDeeperShallower=true` trims `bench 13` (`576,076 -> 533,003`, `-7.48%`). On bloated `COMBO_v1`, `do_shallower` skipped redundant re-searches (`+11.59` Elo), whereas on already-compressed `V3P_SF4b1_SF8`, `do_deeper` inflated `B4 bench 13` (`565,442 -> 738,447`, `+30.6%`) and diluted the gain to `+3.13` (`COMBO_v2` dropped to `-3.13`).

---

## 3. `run_lmr_deeper_sprt.py` Specification & `MateAlphaGuard` Omission Caveat

- **Execution State:** Not yet run (`matches\SPRT_LmrDeeperShallower_0_5_50k` does not exist).
- **Declared SPRT Settings (`run_lmr_deeper_sprt.py:78-163`):**
  - `--name SPRT_LmrDeeperShallower_0_5_50k`, `--exe builds/base_r15dsg.exe`, `--net runs/forge/r0067/train/cand.fnn3`, `--nodes 50000` (or `--tc 6+0.06` with `CLOCK_MATCH_RUNNING` lockfile + `timemargin=50`), `--max-rounds 2000` (`4,000` max games), `--concurrency 8`, `--seed 202611601`, `elo0=0.0, elo1=5.0, alpha=0.05, beta=0.05, model=normalized`.
  - Writes pre-match declaration `declaration_{name}.json` before game 1; never pools with prior `1,000g` run.
- **CRITICAL CONFIG CAVEAT (`run_lmr_deeper_sprt.py:59-75`):**
  - `load_live_uci_options()` reads `cfg["engine"]["v3_uci_options"]` (`45` keys) + `NNUEArch=true` + `NNUEArchFile` + `LmrDeeperShallower`, **omitting** `cfg["engine"]["uci_options"]` (`Threads = 1, Hash = 16, OwnBook = false, MateAlphaGuard = true` at `config.forge.toml:186`).
  - While `Threads=1`, `Hash=16`, `OwnBook=false` match engine defaults, **`MateAlphaGuard` defaults to `false` instead of `true`!** (Whereas `LmrDeeper_alone_vs_base_1000g_50k/summary.json:57` and `pipeline/nnloop/engine.py` explicitly set `MateAlphaGuard = true`). Before running `run_lmr_deeper_sprt.py`, Neon/Opus should either merge `[engine].uci_options` into `load_live_uci_options()` or document the `MateAlphaGuard=false` deviation in the declaration.

---

## 4. Zero-C++ Placement & Rollout Plan (Conditional on `H1_ACCEPTED` + Clock Check)

1. **Gate:** Do NOT place until `SPRT_LmrDeeperShallower_0_5_50k` accepts `H1` (`[0, 5]`, `alpha=beta=0.05`) AND a GPU-idle clock check (`6+0.06` or `10+0.1` with `CLOCK_MATCH_RUNNING`) clears `LCB > -10`.
2. **Zero-C++ Placement (`pipeline/config.forge.toml:214`):** Backup `config.forge.toml` first; append `, LmrDeeperShallower = true` inside `[engine] v3_uci_options` (`45 -> 46` keys) and validate via `pipeline.nnloop.common.load_config` (`assert cfg['engine']['v3_uci_options']['LmrDeeperShallower'] is True`).
3. **Zero-C++ Revert:** Restore `config.forge.toml` from backup (or remove `, LmrDeeperShallower = true`); `src/search.cpp:163` defaults back to `false` with zero C++ rebuild.
4. **Compatibility Warning:** Orthogonal to `V3P` and Round 12–14 patches syntactically, but **do not** stack blindly with compressed-tree LMR patches (`SF8`) without re-testing the combined binary.
