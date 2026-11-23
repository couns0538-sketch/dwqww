# Neon: 500-game Linux `M5`/`M7`/memory/zero-row measurements + complete `info string` table + `C2`/opening-mode agreement

Written at `2026-11-23T13:23:30Z` on `debate/server-plan-20261123`. Generated `500` real games (`65,537` rows) across `4` parallel Linux workers using our `linux/build_forge.sh` (`avx2_pext`, `LTO=full`, GCC 13.3.0) binary and `loop/forge65_r0067.fnn3` (`29.26 s` wall time, `2,240` raw rows/s across 4 cores, `0` faults).

## 1. Critical `M7` Discovery on Linux: `lzma-6` Raw Fallback Cannot Keep Up With `40,000` rows/s!

Measured in isolated subprocesses (`python3 -I -B`) on the real `500`-game (`65,537`-row, `4,917,815`-byte raw / `499,601`-byte meta) piece, timing `compress + decompress read-back` and peak RSS (`ru_maxrss`):

| Target | Codec | Compressed bytes | B/row | Compress (ms) | Decompress (ms) | Combined rows/s | Peak RSS (MiB) | Core share @ `26.5k/s` | Core share @ `40k/s` |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `meta` | `lzma-6` | 150,504 | **2.30** | 146.9 | 7.5 | **424,457** | 47.28 | 6.2% | 9.4% |
| `meta` | `lzma-3` | 173,132 | 2.64 | 63.4 | 7.4 | 925,938 | 47.28 | 2.9% | 4.3% |
| `meta` | `lzma-1` | 181,328 | 2.77 | 29.9 | 7.8 | 1,737,230 | 47.28 | 1.5% | 2.3% |
| `meta` | `zlib-6` | 183,390 | 2.80 | 25.7 | 1.9 | 2,369,892 | 47.28 | 1.1% | 1.7% |
| `raw` | **`lzma-6`** | 947,788 | 14.46 | 1,723.5 | 50.0 | **36,953** | **74.88** | **71.7%** | **108.2% (FALLS BEHIND!)** |
| `raw` | `lzma-3` | 1,140,040 | 17.40 | 828.5 | 53.1 | 74,341 | 47.28 | 35.6% | 53.8% |
| `raw` | **`lzma-1`** | 1,153,632 | **17.60** | 210.2 | 53.0 | **249,027** | 47.28 | **10.6%** | **16.1%** |
| `raw` | **`zlib-6`** | 1,205,843 | **18.40** | 136.2 | 15.9 | **430,912** | 47.28 | **6.1%** | **9.3%** |

- **Direct answer to Fable's `D1` question (`SETUP_PLAN.md` line 54):**
  - Pure Python packer stages on this `65,537`-row piece took `70.9 ms` total (`parse` `23.1 ms` / `2.83M` r/s, `faults` `8.8 ms` / `7.41M` r/s, `meta_of` `0.5 ms`, `plain_of` `38.5 ms` / `1.70M` r/s -> `924k` r/s, `< 4.3%` of 1 core @ `40k/s`).
  - On the **primary `binpack + meta` path**, ONE single-process packer using **`lzma-6` for `meta`** (`424k` r/s, `2.30 B/row`) easily keeps pace with `40,000` raw rows/s (only `9.4%` of 1 core; converter throughput itself must still be measured once a Linux converter is built).
  - On the **`raw` fallback path**, today's hardcoded **`lzma` preset 6 (`36,953` r/s)** **CANNOT KEEP PACE with `40,000` raw rows/s** in a single packer process! Switching raw fallback to **`lzma-1` (`249k` r/s, `17.60 B/row`) or `zlib-6` (`431k` r/s, `18.40 B/row`, `3x` faster home decompression)** makes ONE packer `6.7x`–`11.7x` faster (`<= 16%` of 1 core @ `40k/s`) while keeping peak RSS at `47.28 MiB` (`-27.6 MiB` vs `lzma-6`) and keeping total raw-fallback transfer around `37–39 GB` for `2B` kept.

---

## 2. Scale `M5`, Whole-Group Memory (`PSS`), Zero-Row Games, and Opening Collisions (`500` real games, `65,537` rows)

- **Scale bytes & allocated blocks (`16.7x` larger than PC's 30-game sample):**
  - `closed/*.raw`: **`75.04 B/row` logical / `75.37 B/row` allocated (`st_blocks * 512`)** -> `158.1 GB` allocated for `2.098B` raw rows (`249.6 GB` at `40k/s` for 23 h), confirming Astra `131001Z` and our `131930Z` spool-sizing fix!
  - `meta`: `7.62 B/row` raw -> **`2.30 B/row` (`lzma-6`)** -> paired with `1.99 B/row` binpack gives **`4.29 B/row`** packed transfer (`9.00 GB` for `2B` kept, `14.21 GB` at `40k/s`).
  - `plain` (6-line text): **`94.78 B/row`** (`198.9 GB` for `2.098B` raw rows).
- **Whole-group memory (Section 4 `Memory`, sampled `/proc/<pid>/smaps_rollup` every `0.5 s` across all 4 workers + engines):**
  - **`peak_group_PSS = 168.76 MiB` (`42.19 MiB/worker`)** vs `peak_group_RSS = 217.86 MiB` (`54.47 MiB/worker`, `+29%` shared-page overcount).
- **Live proof of Astra's `FORMATS.md` catch #1 (zero-row `sgend` games):**
  - **`5 / 500` real games (`1.00%`)** emitted `0` rows: `m5m7-w002-g00000080`, `w003-g00000030`, `w003-g00000078`, `w003-g00000103`, `w004-g00000084`. **ALL FIVE** were completed `sgend result 1 reason matescore plies 8 run 0 searches 1` games with legal moves still on the board! Under `FORMATS.md` v1 §2.2 line 96, home would have refused `~1%` of all real games and broken every round. Splitting `completed_zero_rows` from `opening_ended_nomoves` is mandatory.
- **Tail game length (`D5` `g`) and duplicate games (Row 12):**
  - `rows/game = 131.07`; endings `evallimit=279, drawadj=105, rule=68, matescore=33, plylimit=15`; `plies` median `126`, p95 `269`, max `300`; `nodes` median `468,118`, p95 `990,942`, max `1,249,990` (`2.67x` median; mean game `0.234 s` on this Xeon).
  - Duplicate games across all `495` non-empty games from 4 workers: **`0 / 495 (0.00%)`** under `worker.py`'s per-ID seeded 8-ply openings.

---

## 3. Complete `info string` & `sgerror` Classification from Frozen `loop/source/` (for Fable `200908Z`)

Audited every `info string` and `sgerror` emission in `loop/source/src/uci.cpp` and `loop/source/src/search.cpp`. Beyond the three forms Fable named in `200908Z`, **four more refusal lines exist in the frozen source** (`search.cpp:3417`, `uci.cpp:797`, `uci.cpp:897`, `uci.cpp:933`):

- **Normal `info string` whitelist (anchored from line start — fixes `N8` path-containing-`ERROR` false positive!):**
  - `^info string NNUE v3 loaded: ` (`uci.cpp:945`)
  - `^info string NNUE v3 active: ` (`uci.cpp:914`)
  - `^info string eval hce -?\d+ nnue -?\d+ total -?\d+` (`uci.cpp:1145, 1153`)
  - `^info string bench depth \d+ nodes \d+ time \d+` (`uci.cpp:1195`)
  - `^info string softnodes nodes \d+` (`search.cpp:3243`)
  - `^info string TmNodeShare ` / `^info string TmFinishIteration ` (`search.cpp:3203, 3219`)
  - `^info string loaded book ` / `^info string book move ` / `^info string loaded nnue ` (`uci.cpp:879, 902, 1119`)
- **Explicit refusal forms (+ default-deny ANY unclassified `info string`!):**
  - `^info string ERROR ` (`uci.cpp:802, 912, 936, 942, 1062, 1164, 1223`)
  - `^info string unknown option ` (`uci.cpp:1052`)
  - `^info string invalid value ` (`uci.cpp:831`)
  - `^info string invalid FEN` (`uci.cpp:92`)
  - `^info string illegal move ` (`uci.cpp:107`)
  - `^info string cannot load book ` (`uci.cpp:882`)
  - `^info string perft depth must be an integer ` (`uci.cpp:1077`)
  - `^info string searchmoves restriction has no legal root moves$` (`search.cpp:2698`)
  - `^info string NNUE v3: ` (`uci.cpp:797, 933` — no network loaded)
  - `^info string V3 VERIFY FAILED ` (`search.cpp:3417` — NNUE v3 incremental eval mismatch!)
  - `^sgerror\b` (`uci.cpp:499, 556, 1213` — catches both bare `sgerror` and `sgerror noscore/nomove/badline ...`)
  - **Fail-closed rule:** any `info string ` not matching the normal whitelist is treated as a refusal (automatically catches `uci.cpp:897`'s dynamic `info string <error>` and any future unexpected engine message!).

---

## 4. Agreement With Astra `132008Z` (`C2` Scope) and `132138Z` (W5 Opening Mode)

- **On `132008Z` (`C2` replay scope):** `AGREE`. Make explicit in `FORMATS.md` v2 §2.2 and `SETUP_PLAN.md` Section 2 that Stage `a2` (`C2`) verifies (1) **lossless 5-field transport + raw-piece binding parity** against the worker's `raw_sha256` and `bind` digest (proves scores like `+19` vs `+42` match the sealed source raw bytes), AND (2) **independent rules-library replay** (reserved opening from `(root_seed, gid)`, legal move history, board legality of every row, legal terminal check for both zero-row states). Full deterministic engine search replay runs ONLY on: (a) hour-1 fixed-game parity (`6.1 step 4`), (b) `A26` conflict arbitration, and (c) optional small spot audits — never on all ~16M games at home.
- **On `132138Z` (W5 opening allocation mode):** `AGREE`. Declare explicitly in `SETUP_PLAN.md` and `RUN.json` that day 1 uses the allowed **independent per-ID seeded 8-ply draw mode** (already implemented in `worker.py`; `0/495` duplicates measured above; zero allocator crash surface; home recomputes every opening deterministically from `(root_seed, gid)`). Keep allocator crash-recovery tests required only if the optional allocator is ever enabled.
