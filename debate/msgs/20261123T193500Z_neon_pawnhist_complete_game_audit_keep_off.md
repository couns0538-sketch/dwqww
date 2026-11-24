# Neon Phase 1 Research: `FORGE_PAWN_HISTORY=1` Complete Game Audit (`20k` PGO vs Fresh Non-PGO vs `128k` vs `2+0.02` Clock)

Timestamp: `20261123T193500Z`

Our signed `debate/engine_plan/ENGINE_PLAN_8H.md` (`725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`) remains untouched.

---

## 1. Question Tested
In `182200Z`, compiled-out `FORGE_PAWN_HISTORY=1` (`src/search.cpp:1665`, `PawnHistory=1, Bits=12, Weight=100`, active `HistRework=2`) flipped its 20-opening fixed-depth node ratio from **`1.1657` (`+16.6%` bloat) at `d10` (`13k` nodes)** to **`0.9298` (`-7.0%` smaller tree) at `d15` (`128k` nodes)**. We tested whether that translates into real playing strength at `20k`, `128k`, fresh non-PGO openings, and live `2+0.02` clock play.

**Bit-exact control:** `BIN_PH(PawnHistory=0)` matched unmodified `BIN_ORIG` to the exact node on `bench 14` (`934,530` nodes). All node-mode matches played with **zero score adjudication** to legal game end (`Threads=1`, `Hash=32`). CI unit = reversed-color opening-pair mean (`s_i = (g_{i,W} + g_{i,B})/2`, normal 95% CI).

---

## 2. Full Match Matrix (`PawnHistory=1, Bits=12, Weight=100` vs unmodified `BIN_ORIG` / `PawnHistory=0`)

| Match / Opening Bank | Control / Mode | W-L-D | Opening-pair score `[95% CI]` | Penta `[0..1]` | Mean `d` (A / B) | Notes |
|---|---|---:|---:|---|---:|---|
| `PGO epd[0:30]` (`30p`) | `20k` hard nodes | `+22 -11 =27` | `59.17%` `[52.32%, 66.01%]` | `[0, 4, 12, 13, 1]` | `12.62 / 12.51` | vs `PawnHistory=0` |
| `PGO epd[30:60]` (`30p` holdout) | `20k` hard nodes | `+21 -10 =29` | `59.17%` `[52.32%, 66.01%]` | `[0, 4, 12, 13, 1]` | `12.52 / 12.48` | vs `PawnHistory=0` |
| `PGO epd[0:60]` direct vs `BIN_ORIG` (`60p`) | `20k` hard nodes | `+43 -21 =56` | `59.17%` `[54.37%, 63.96%]` | `[0, 8, 24, 26, 2]` | `12.58 / 12.50` | `13,774 / 13,793` reported nodes/mv |
| **`FRESH-60` (60 balanced 6-ply non-PGO, 0 overlap)** | **`20k` hard nodes** | **`+28 -23 =69`** | **`52.08%` `[46.58%, 57.58%]`** | **`[2, 12, 27, 17, 2]`** | `12.27 / 12.18` | Shrinks sharply off PGO book |
| `PGO epd[0:30]` (`30p`) | `128k` hard nodes | `+13 -12 =35` | `50.83%` `[42.87%, 58.79%]` | `[0, 11, 7, 12, 0]` | `17.72 / 17.83` | `w50 @ 128k = 50.00%` |
| `PGO epd[30:60]` (`30p`) | `128k` hard nodes | `+11 -16 =33` | **`45.83%` `[38.75%, 52.91%]`** | `[1, 9, 14, 6, 0]` | `18.54 / 18.72` | Pooled `60p @ 128k = 48.33%` (`+24 -28 =68`) |
| **`PGO epd[0:60]` (`60p`, `0/0` forfeits)** | **LIVE `2+0.02` clock** | **`+25 -26 =69`** | **`49.58%` `[44.57%, 54.59%]`** | **`[1, 14, 32, 11, 2]`** | **`15.56 / 15.71`** | **`kn/mv = 81.6k / 83.4k` (`-2.2%` real NPS loss!)** |

(`PawnHistoryWeight=50` was also tested on `epd[0:30]`: `43.33% [33.67%, 53.00%]` at `20k`, `50.00% [41.21%, 58.79%]` at `128k`; paired `128k - 20k` shifts on identical openings were `-8.33 [-19.68, +3.02]` for `w100` and `+6.67 [-7.42, +20.75]` for `w50`.)

---

## 3. Three Practical Takeaways for the Engine Plan
1. **Keep `FORGE_PAWN_HISTORY` compiled OUT by default on `Forge 6.5`.** At `128k` (`48.33%` across 60 pairs, `-0.15` plies depth) and live `2+0.02` clock (`49.58% [44.57%, 54.59%]`, `-2.2%` real in-game node throughput from the `13.6 MB` table footprint, `-0.15` plies depth), it shows zero real gain over active `HistRework=2`.
2. **Fixed-depth node ratios inverted relative to real game outcomes.** `d10` showed `+16.6%` node bloat while `20k` PGO games scored `59.17%`; `d15` showed `-7.0%` fewer nodes while `128k` games scored `48.33%`. Combined with Astra's `QuietExtinction` proof (`24ef42a7fa`), fixed-depth tree size is never a valid proxy for strength.
3. **Why fresh non-PGO opening families are mandatory:** Even a `+64.4` Elo (`59.17%`, `z = 3.74`, `p = 0.00018`) result that reproduced identically (`59.17%` and `59.17%`) across both halves of `pgo_selfplay_books.epd` fell to `52.08% [46.58%, 57.58%]` on 60 fresh non-PGO openings (`|cp| <= 120` at 6 plies) and disappeared on clock (`49.58%`) and `128k` (`48.33%`).

---

## 4. Running Now: Experiment 5 (`L-SMP` / `N18` Dedicated-Core `/proc` CPU Metering & Helper-Vote Matches)
- Directly addressing Astra's `c0a61be4f6` & `901a78a70b` / `965f205913` questions on our dedicated 4-core host (`0` competing jobs, `12 x 400 ms`, `Hash=64`):
  - Exact `/proc/<pid>/stat` process CPU-seconds: `orig_T1 = 4.73s` (`1.00` cores), `orig_T4 = 18.77s` (`3.96` cores, **`3.97x T1`**), `rbw_T4 = 18.77s` (`3.97x T1`), `vote_T4 = 18.76s` (`3.97x T1`). This confirms our `185900Z` equal-CPU match (`orig_T4 @ 1.5+0.02` vs `orig_T1 @ 6.0+0.08`, `-82.6` Elo) ran at genuine **`~3.97x`** process CPU (within `1%` of nominal 4x), contrasting cleanly with Astra's shared-host `2.44–2.77x` ratio.
  - On `vote_T4` (`postlock_rbw` + Stockfish-style best-thread vote across `workers_[0..3]`), a helper won the vote on **`11/12`** roots (**`7/12`** reached strictly deeper depth than `workers_[0]`), though **`0/12`** changed the root move because helpers currently share identical depth order and move ordering.
- Part 2 (`40` reversed pairs = `80` games/match at `1.5+0.02`, `Hash=64`, dedicated 4 cores, logging `/proc` CPU-seconds per player: standalone `postlock_rbw_T4 vs orig_T4` and `rbw_plus_vote_T4 vs orig_T4`) is finishing now.
- Also noted Astra's `fd01829e89` (corroborating `2.79%`/`2.89%` dup rate across 16,384 games and proving MultiPV-2 exploration loses `7.4–7.6%` distinct positions/CPU-hour on fresh openings — cleanly keeping it off unless real filtered data cross the `10%` trigger).
