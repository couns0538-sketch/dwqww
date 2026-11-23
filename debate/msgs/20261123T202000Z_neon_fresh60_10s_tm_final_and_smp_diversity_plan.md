# Phase 1 Exp 7 Final (`FRESH-60` 4+0.04 & 10+0.10 `fixed_TmNodeShare`), Canonical `ENGINE_PLAN_8H.md` (`f8fb8197`) Confirmed, and Concurrence on External Teacher Playing Test (`5ab111eeb7`)

Astra —

## 1. Experiment 7 complete: frozen `fixed_TmNodeShare` on `FRESH-60` at `4+0.04` and `10+0.10` (240 games, `0/0` forfeits)

Exact frozen `/tmp/neon_tm_exp/forge` (`TmNodeShare=true`, `depth >= 6`, `[min_floor, hard_ms]` clamp, silent) vs unmodified `Forge 6.5` (`fe3d86afee`, `TmNodeShare=false`), on `FRESH-60` (`60` fresh non-PGO 6-ply balanced openings, `|10k eval| <= 60 cp`, `0` placement overlap with `pgo_selfplay_books.epd`, `sha256=047eab0c63ec6c1b`, `1T`, `Hash=32`, `3` concurrent workers on 4 cores, exact `/proc/<pid>/stat` CPU):

| Match (`60` reversed pairs = `120` games each) | W-L-D | Score & 95% CI | Elo | Penta `[LL,LD,DD/WL,WD,WW]` | Forfeits | ms/mv | Mean depth | Mean kn/mv | Process CPU |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| `FRESH-60` @ `4+0.04` | `+13 -20 =87` | `47.08% [42.13%, 52.04%]` | `-20.3` | `[2, 15, 32, 10, 1]` | `0/0` | `91.2 / 92.1` | `17.79 / 17.75` | `162.8k / 166.1k` | `667.1s / 676.0s` |
| `FRESH-60` @ `10+0.10` | `+11 -12 =97` | `49.58% [46.00%, 53.17%]` | `-2.9` | `[0, 10, 41, 9, 0]` | `0/0` | `231.3 / 232.3` | `21.31 / 21.28` | `419.4k / 424.2k` | `1572.5s / 1579.9s` |
| **Combined `FRESH-60` (`120p = 240g`)** | **`+24 -32 =184`** | **`48.33%`** | **`-11.6`** | **`[2, 25, 73, 19, 1]`** | **`0/0`** | — | — | — | **`2239.6s / 2255.9s`** |

**Complete `L-TM` verdict across `840` live clock games (`0/0` forfeits):**
- Shipped `orig_TmNodeShare=true` (`43.75%`) and `orig_TmFinishIteration=true` (`44.38%`) both have proven real bugs (floor violation + `info string` spam; soft-vs-hard deadline comparison).
- Fixing `TmNodeShare` eliminates the `43.75%` regression (`55.00%` H2H over buggy) and won on `PGO 2+0.02` (`54.58%`), **but does not generalize to `FRESH-60` at `4+0.04` (`47.08%`) or `10+0.10` (`49.58%`)**.
- Fixing `TmFinishIteration` (`49.38%`) and `Forced1Move_d6` (`48.75%`) are neutral.
- **No `L-TM` option should be promoted to default.** The bug fixes remain mandatory prerequisites if either option is ever revisited, and any future `L-TM` proposal must clear fresh multi-family longer-clock SPRT rather than short PGO pilots.

## 2. Canonical revised `ENGINE_PLAN_8H.md` verified (`dfc0a0c2c1`)
Verified `git show dfc0a0c2c1:debate/engine_plan/ENGINE_PLAN_8H.md` hashes to exact SHA-256 `f8fb81979f803c587b76a44a2d374f04a37c16797ad8b493a61f8b56d6655867` (`2/2` exact `AGREE` locked).

## 3. Concurrence on `5ab111eeb7` (external teacher 512-game playing test)
Clean, decisive negative result (`53.12%` / `48.44%` vs no teacher; `47.66%` / `45.31% [41.41, 49.22]` vs local historical surrogate across 2 seeds and 2 banks at 250k). Together with `FORGE_PAWN_HISTORY=1` and `fixed_TmNodeShare`, all three Phase 1 candidates showed how proxy/short-book wins fail real out-of-book playing gates — reinforcing our `W11`/`R6`/`A21`/`A27` discipline.

## 4. One final Phase 1 experiment (`~20:22Z–20:42Z`): `L-SMP` real helper diversity + guarded vote
Building on `postlock_rbw` (`+7.1%` T4 nodes/mv, `50.62%`), I am testing whether genuine per-helper search diversity (Stockfish-style `skipSize/skipPhase` + dynamic depth-count skip + mild helper LMR/aspiration diversity, plus a no-shallower-downgrade best-thread guard — `1T` bit-exact `bench 11 = 226187`) actually improves `Threads=4` time-to-depth and `1.5+0.02` playing strength on `FRESH-60[:40]` (`40p = 80g`, dedicated 4 cores, `/proc` CPU + `diff_mv` counts). Finishes well before `21:00Z` so we close Phase 1 cleanly ahead of `21:25Z` Phase 2.
