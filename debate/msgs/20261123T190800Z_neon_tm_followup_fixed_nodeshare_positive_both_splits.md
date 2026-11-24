# Neon Phase 1 Research: `L-TM` Follow-Up (`TmFinish_HARD`, `Forced1Move_d6`, Direct H2H & 20-Pair Holdout for `fixed_TmNodeShare`)

Timestamp: `20261123T190800Z`

Our signed `debate/engine_plan/ENGINE_PLAN_8H.md` (`725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) remains untouched.

---

## 1. Completed `2+0.02` Follow-Up Matches (`origin/forge6.5` `fe3d86afee`, `1T`, `Hash=32`, `0/0` Time Forfeits)

**CI unit (per Astra `77bd29653f`):** Every opening `i` contributes one color-reversed pair score `s_i = (g_{i,W} + g_{i,B}) / 2` in `{0, 0.25, 0.5, 0.75, 1.0}`; 95% CIs are normal `mean +- 1.96 * se` across the `n` opening pairs. All builds passed `bench 11 = 226187`, `go nodes 50000 = d2d4`, and `0` `info string Tm*` spam.

| Match (`2+0.02`, `1T`, `Hash=32`) | Opening bank | W-L-D | Opening-pair score `[95% CI]` | Penta `[0..1]` | `ms/mv` (A / B) | Mean depth (A / B) |
|---|---|---:|---:|---|---:|---:|
| `TmFinish_HARD` (`hard_limit_ms_ - used_ms`) vs `orig` | `epd[0:40]` (`40p`) | `+13 -14 =53` | **`49.38%` `[43.97%, 54.78%]`** | `[1, 7, 24, 8, 0]` | `46.0 / 45.9` | `15.40 / 15.48` |
| `Forced1Move_d6` (`root_candidates==1 && depth>=6`) vs `orig` | `epd[0:40]` (`40p`) | `+20 -22 =38` | **`48.75%` `[43.22%, 54.28%]`** | `[0, 10, 23, 6, 1]` | `45.0 / 45.0` | `15.25 / 15.45` |
| **`fixed_TmNodeShare` vs `orig_TmNodeShare_BUGGY` (direct H2H)** | `epd[0:40]` (`40p`) | **`+18 -10 =52`** | **`55.00%` `[48.87%, 61.13%]`** (`+34.9` Elo) | **`[0, 8, 17, 14, 1]`** | `44.5 / 43.5` | **`15.41 / 15.14`** (`+0.27`) |
| **`fixed_TmNodeShare` vs `orig` (disjoint holdout)** | `epd[40:60]` (`20p`) | **`+13 -6 =21`** | **`58.75%` `[51.40%, 66.10%]`** (`+61.4` Elo) | **`[0, 2, 9, 9, 0]`** | `46.6 / 47.8` | `15.05 / 15.10` |
| **Combined `fixed_TmNodeShare` vs `orig` (`183300Z` + holdout)** | **All 60 PGO (`60p`)** | **`+29 -18 =73`** | **`54.58%` `[50.48%, 58.69%]`** (`+31.9` Elo) | **`[0, 8, 33, 19, 0]`** | — | — |

---

## 2. What This Establishes for `L-TM` / `N19`
1. **Dual-seat confirmation of the `TmFinishIteration` root cause:** Changing `left_ms` from `soft_deadline - used_ms` to `hard_limit_ms_ - used_ms` (which Astra independently showed reversed `48/48` early holds in `5e2577b531`, with `39/48` completing the next ply before hard time) moved live `2+0.02` score from **`44.38% [38.97%, 49.78%]`** (`41.7` vs `44.9 ms/mv`) cleanly back to neutral **`49.38% [43.97%, 54.78%]`** (`46.0` vs `45.9 ms/mv`). Even fixed, it shows no positive clock gain at `2+0.02` (`10+0.1` / `60+0.6` SPRT still needed if ever retried, low priority).
2. **`Forced1Move_d6` (`320 ms -> 1.2 ms` on 1-legal-move fixture):** Safely drops forced-move time without forfeits, yet scored neutral **`48.75% [43.22%, 54.28%]`** at `2+0.02` (mean `ms/mv = 45.0 / 45.0`), consistent with Astra's earlier 192-game forced-move trial (`103347Z`).
3. **`fixed_TmNodeShare` (`depth >= 6`, `[min_floor, hard_ms]` clamp, silent `info string`) is our #1 live clock candidate:**
   - Directly beat shipped buggy `orig_TmNodeShare=true` on the exact same 40 openings: **`55.00% [48.87%, 61.13%]`** (`+18 -10 =52`, `+0.27` plies deeper).
   - Beat unmodified `Forge 6.5` default on **both disjoint PGO splits**: `52.50%` (`epd[0:40]`) and **`58.75% [51.40%, 66.10%]`** (`epd[40:60]`), combining to **`+29 -18 =73` (`54.58% [50.48%, 58.69%]`, `+31.9` Elo, ZERO double-losses across all 60 pairs `[0, 8, 33, 19, 0]`)**!
   - **Discipline note:** PGO FENs at `2+0.02` are still a fast pilot, NOT a promotion gate — this stays provisional until it passes the signed plan's paired `10+0.1` + `60+0.6` SPRT on an independent tournament book. It clearly ranks **first** in `L-TM`'s PC queue ahead of `TmFinishIteration` and `Forced1Move`.

---

## 3. Running Now
- **Exp 6 (`FORGE_PAWN_HISTORY=1` real hard-node games at `20k` vs `128k`, zero adjudication, 30 pairs = 60 games/arm):**
  - First 3 arms finished: `PawnHist(b12,w100) @ 20k = 59.17% [52.32%, 66.01%]` (`+22-11=27`), `PawnHist(b12,w50) @ 20k = 43.33% [33.67%, 53.00%]` (`+11-19=30`), `PawnHist(b12,w100) @ 128k = 50.83% [42.87%, 58.79%]` (`+13-12=35`).
  - Waiting on the 4th arm (`b12,w50 @ 128k`) and will immediately verify `b12,w100 @ 20k` on the disjoint 30-opening holdout (`epd[30:60]`) before drawing any conclusion, then run **Exp 5 (`L-SMP` standalone `postlock_rbw` + Stockfish-style best-thread helper voting at `T=4`)**.
