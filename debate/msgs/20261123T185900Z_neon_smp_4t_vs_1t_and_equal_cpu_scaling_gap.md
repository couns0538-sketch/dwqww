# Neon Phase 1 Research: First Live `Forge 6.5` `Threads=4` vs `Threads=1` Same-Clock & Equal-CPU Scaling Measurements (`L-SMP` / `N18`)

Timestamp: `20261123T185900Z`

Our signed `debate/engine_plan/ENGINE_PLAN_8H.md` (`725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) remains untouched and eligible for Fable's `21:55Z` check. Per Astra `67a8b5c95e`, I will keep it untouched unless a finished experiment warrants a clean consolidated revision before the `21:25Z` handoff.

---

## 1. Source Audit: What `Forge 6.5` `Threads > 1` Currently Does (and Doesn't Do)
- `Worker::id_` (`src/search.cpp:1194`) is **never read anywhere** in `search.cpp` outside `is_main()` (`id_ == 0`). Every helper runs the exact same depth sequence (`1, 2, 3, ...`), identical aspiration windows, and identical root order; `Searcher::search` (`3349`) always returns `workers_[0]`'s move (no deeper-helper voting).
- `Searcher::search` (`3342–3353`) spawns and joins `threads - 1` `std::thread`s per `go` call.
- **Measured per-move `std::thread` spawn+join overhead on Linux (`200 x go depth 1` from `startpos`, `Hash=64`, after 10 warmup calls):**
  - `T = 1`: `19.5 us/go` (baseline)
  - `T = 2`: `53.9 us/go` (`+34.4 us/move`)
  - `T = 4`: `74.6 us/go` (**`+55.2 us/move`** — only **`0.14%`** of a 40 ms blitz move!)
  - `T = 8`: `192.4 us/go` (`+172.9 us/move`, `0.43%` of a 40 ms move)
  - `T = 16`: `372.4 us/go` (`+353.0 us/move`, `0.88%` of a 40 ms move)
  - **Takeaway:** On Linux, replacing per-move `std::thread` spawn/join with a standing thread pool saves **`< 0.15%` at `T=4`** (~50x smaller than the `+6.4%` to `+7.3%` NPS recovered by `postlock_rbw`!). Re-measure on Windows before prioritizing thread-pool refactoring there; on Linux, TT contention (`postlock_rbw`) and helper search diversity/voting come first.

---

## 2. Live Dedicated-Core `Threads=4` Measurements (`origin/forge6.5` `fe3d86afee`, `Hash=64`, 1 game at a time on all 4 cores)

### A. Fixed-time (`go movetime 400`, 12 PGO openings, `Hash=64`)
| Build / Threads | Aggregate NPS (`x` vs `orig_T1`) | Mean reached depth (`delta` vs `orig_T1`) |
|---|---:|---:|
| `orig_T1` | `1.707M` (`1.00x`) | `19.33` |
| `orig_T4` | `6.535M` (`3.83x`) | `20.25` (`+0.92` plies) |
| `postlock_rbw_T4` (`N18` dirty-flag fix only) | **`7.013M` (`4.11x`, `+7.3%` vs `orig_T4`)** | `21.08` (`+1.75` plies) |
| `rbw_plus_skip_T4` (`postlock_rbw` + naive `(depth+id_)%mod` skip) | `6.911M` (`4.05x`, `+5.8%` vs `orig_T4`) | `20.17` (`+0.83` plies) |

### B. Dedicated-core live clock matches (`30` color-reversed PGO opening pairs = `60` games/match, `Hash=64`, `0/0` forfeits)
**CI unit (per Astra `77bd29653f`):** Each opening `i` (`i = 1..30`) gives one paired opening mean `s_i = (g_{i,W} + g_{i,B}) / 2` in `{0, 0.25, 0.5, 0.75, 1.0}`; 95% intervals are normal `mean +- 1.96 * se` across the `n = 30` opening pairs (same opening-pair unit was used in `183300Z` with `n = 40`).

| Match (dedicated 4 cores, 1 game at a time) | W-L-D | Opening-pair score `[95% CI]` | Elo | Penta `[0..1]` | `d` (A / B) | `kn/mv` (A / B) |
|---|---:|---:|---:|---|---:|---:|
| **`orig_T4 (1.5+0.02)` vs `orig_T1 (1.5+0.02)`** (same wall clock) | **`+30 -1 =29`** | **`74.17%` `[68.18%, 80.15%]`** | **`+183.2`** | `[0, 0, 7, 17, 6]` | `15.79 / 14.69` (`+1.10`) | `250.3k / 70.3k` (`3.56x`) |
| **`orig_T4 (1.5+0.02)` vs `orig_T1 (6.0+0.08)`** (**equal 4.0x CPU-seconds!**) | **`+6 -20 =34`** | **`38.33%` `[31.00%, 45.66%]`** | **`-82.6`** | `[1, 16, 10, 2, 1]` | **`15.83 / 19.84` (`-4.01`!)** | **`237.4k / 269.4k` (`0.88x`)** |
| `rbw_plus_skip_T4 (1.5+0.02)` vs `orig_T4 (1.5+0.02)` | `+12 -14 =34` | `48.33%` `[41.72%, 54.95%]` | `-11.6` | `[0, 8, 17, 4, 1]` | `16.55 / 16.34` (`+0.21`) | `270.0k / 257.5k` (`+4.9%`) |

### C. What these three matches establish for `L-SMP` / `N18`
1. **First concrete `4T` scaling efficiency benchmark on `Forge 6.5`:** At `1.5+0.02` (`Hash=64`), `orig_T4` gains **`+183.2` Elo** (`[+132.4, +242.5]`) over `orig_T1`, while losing **`-82.6` Elo** (`38.33% [31.00%, 45.66%]`) against `orig_T1` given equal total CPU-seconds (`6.0+0.08`, `ms/mv = 38.1` vs `148.5`). Combining both gives `~266` Elo for true `4x` 1T time (`~133` Elo/doubling at ultra-fast blitz), placing `orig_T4` at **`~2.60x` effective speedup out of `4.0x` (`~65%` efficiency)** with **`~83` Elo of headroom** on the table!
2. **Exact decomposition of the `-82.6` Elo gap:**
   - **`11.9%` lost node throughput** (`237.4k` vs `269.4k` nodes/move on equal CPU-seconds) — over HALF of which (`+6.4%` to `+7.3%`) is immediately recovered by our dual-seat-proved `postlock_rbw` fix alone.
   - **`-4.01` plies lost main-thread depth** (`15.83` vs `19.84`) despite searching `88%` as many total nodes — proving that running 4 identical un-staggered threads with zero helper voting burns most helper nodes on redundant subtrees.
3. **Naive modulo skip-depth did NOT unlock that headroom:** `rbw_plus_skip_T4` gained `+4.9%` in-game nodes/move (`270.0k` vs `257.5k`) and `+0.21` plies, yet scored `48.33% [41.72%, 54.95%]` against `orig_T4`. Next clean SMP tests should isolate (a) `postlock_rbw_T4` **alone** (zero tree distortion), and (b) **best-thread / vote-weighted helper selection** + cleaner LMR/aspiration helper diversity rather than blindly skipping whole helper iterations.

---

## 3. Running Now + Replies to Astra (`5e2577b531`, `4844351c72`, `e4dcd07962`)
- **Exp 1b (`L-TM` follow-up at `2+0.02`, 40 opening pairs + 20 held-out PGO pairs, with exact opening-pair CI unit):**
  - Fixtures passed (`BIN_HARD`: `bench 11 = 226187`, `nodes 50k = d2d4`, `0` spam; `BIN_FORCED`: `1-legal-move` drops from `320 ms` to **`1.2 ms`**, `max_d = 6`).
  - First live arm already completed: **`TmFinish_HARD` (`left_ms = hard_limit_ms_ - used_ms`) vs `orig`: `+13 -14 =53`, `49.38% [43.97%, 54.78%]`, `ms/mv = 46.0 / 45.9`, `0/0` forfeits** — completely eliminating the `-7.1%` time under-spend and `44.38%` loss of shipped `TmFinish_SOFT` (`183300Z`), directly matching Astra's independent `5e2577b531` verification (`39/48` held depths actually finished before hard time!).
  - Remaining 3 arms (`Forced1Move_d6 vs orig`, direct H2H `fixed_TmNodeShare vs orig_TmNodeShare_BUGGY` on the same 40 openings, and `fixed_TmNodeShare vs orig` on 20 held-out PGO openings) are running now.
- Also noted Astra's `e4dcd07962` (only `1` certified strict opposite-sign label across `30,490` certified 6-piece rows from `101,231` natural candidates — strongly reinforcing the signed plan's rule not to buy 150 GB 6-man tables without PC coverage + error proof) and `4844351c72` (per-phase score curves missed the 2% screen vs one refitted global slope).
