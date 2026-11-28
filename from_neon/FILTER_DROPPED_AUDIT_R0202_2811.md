# Forge Live Filter Audit — Part 2: What `filterqc.py` DROPS on Unfiltered `r0202`
- **Generated:** 2026-11-28 15:51:45 PC (`81.27s` on `runs/forge/r0202/data/raw_selfplay.binpack`)
- **Exact replay cross-check vs `r0202/data/qc.json`:** raw records `16,005,733` (qc.json `16,005,733`), kept `15,156,682` (qc.json `15,156,682`), dropped `849,051` (`5.305%`).
- **Downstream trainer (`--skip-noisy`):** among the `15,156,682` kept rows, `2,817,726` (`18.59%`) have a capture or promotion best move (plus in-check rows skipped by `skip_check`).

## 1. Dropped Rows by `filterqc.py` Rule (Unfiltered `r0202`)
| Rule | Dropped | % of Raw | `qc.json` | Mean |score| | % Draw | Mean Ply | Mean Pieces | Verdict: Rightly Dropped or Should Keep? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `score_limit` | 0 | 0.000% | 0 | 0.0 | 0.0% | 0.0 | 0.00 | Inactive (0 rows): self-play `eval_limit = 2000` already truncates games at 2000 cp. |
| `ply` | 0 | 0.000% | 0 | 0.0 | 0.0% | 0.0 | 0.00 | Inactive (0 rows): `min_ply = 0, max_ply = 400` drops nothing (random moves `0..7` aren't emitted by self-play). |
| `duplicate` | 526,611 | 3.290% | 526,611 | 238.5 | 69.3% | 154.5 | 9.41 | Mostly opening/transposition repeats; keeps first occurrence (note: Python `hash()` is randomized & collision-prone vs canonical FEN, and drops second game's distinct result/score). |
| `score_result_conflict` | 465 | 0.003% | 465 | 842.4 | 0.0% | 55.5 | 22.34 | Rightly dropped (and TOO LOOSE at `>= 600` & `result != 0`: only 465 rows dropped, missing 64,679 drawn-game `|score| >= 400` conflicts!). |
| `rule50` | 206,406 | 1.290% | 206,406 | 161.2 | 83.8% | 220.6 | 7.25 | MIXED: mostly drawn shuffling (`r50 > 80`), BUT drops real decisive/non-zero endgame positions where 50-move damping matters. |
| `few_pieces` | 115,569 | 0.722% | 115,569 | 702.3 | 12.3% | 177.0 | 3.00 | **FAULT (F-06 — SHOULD KEEP!):** Drops ALL 2- and 3-piece endings (`min_pieces=4`), including `KQvK`, `KRvK`, `KPvK`, `KBvK`, `KNvK`, `KvK` — while `SyzygyPath` is NOT set in search! |
| `already_none` | 0 | 0.000% | 0 | 0.0 | 0.0% | 0.0 | 0.00 | Inactive (0 rows). |

## 2. Deep Dive: `few_pieces` (`min_pieces = 4`) — What We Drop and SHOULD Keep
- **Total dropped:** `115,569` (`0.722%` of raw `r0202`).
- **Result split:** Loss `44.6%`, Draw `12.3%`, Win `43.0%`.
- **Top dropped 2- and 3-piece material signatures (`L / D / W`):**
  - `KRvK`: `55,940` (`L=28,365, D=250, W=27,325`)
  - `KvKR`: `36,450` (`L=18,472, D=144, W=17,834`)
  - `KPvK`: `13,236` (`L=2,782, D=7,680, W=2,774`)
  - `KvKP`: `9,499` (`L=1,673, D=6,167, W=1,659`)
  - `KQvK`: `244` (`L=156, D=16, W=72`)
  - `KvKQ`: `200` (`L=130, D=10, W=60`)
- **Concrete dropped `few_pieces` examples:**
  - `KRvK` | `fen 8/R7/8/1k4K1/8/8/8/8 w - - 0 80` | `move a7d7` | `score 722` | `ply 158` | `res 1`
  - `KvKP` | `fen 8/8/8/8/5k2/6p1/6K1/8 w - - 0 87` | `move g2g1` | `score 0` | `ply 172` | `res 0`
  - `KPvK` | `fen 8/8/8/8/K1P1k3/8/8/8 b - - 0 99` | `move e4e5` | `score -842` | `ply 197` | `res -1`
  - `KQvK` | `fen 1K6/8/8/8/8/8/8/6kQ b - - 0 75` | `move g1h1` | `score 0` | `ply 149` | `res 0`
  - `KvKR` | `fen 8/8/2k4r/8/5K2/8/8/8 w - - 0 75` | `move f4e4` | `score -707` | `ply 148` | `res -1`
  - `KvKQ` | `fen 8/8/7k/8/3K4/8/8/2q5 b - - 0 74` | `move h6g5` | `score 1990` | `ply 147` | `res 1`

## 3. Deep Dive: `rule50` (`max_halfmove_clock = 80`)
- **Total dropped:** `206,406` (`1.290%` of raw). Mean `r50=89.1`, mean pieces `7.25`.
- **Decisive games dropped by `rule50`:** `33,537` (`16.25%`); `|score| >= 200`: `51,874` (`25.13%`).
- **Examples of decisive `rule50 > 80` rows dropped:**
  - `r50=81`, `pieces=7` | `fen 8/3r4/4B2p/8/8/p1k5/6K1/b7 b - - 81 122` | `move d7e7` | `score 1575` | `res 1`
  - `r50=82`, `pieces=7` | `fen 8/4r3/4B2p/8/8/p1k5/6K1/b7 w - - 82 123` | `move e6d5` | `score -1616` | `res -1`
  - `r50=83`, `pieces=7` | `fen 8/4r3/7p/3B4/8/p1k5/6K1/b7 b - - 83 123` | `move e7e2` | `score 1557` | `res 1`
  - `r50=84`, `pieces=7` | `fen 8/8/7p/3B4/8/p1k5/4r1K1/b7 w - - 84 124` | `move g2h3` | `score -1552` | `res -1`

## 4. Deep Dive: `duplicate` (`dedup = true` via per-round `hash(' '.join(parts[:4]))`)
- **Total dropped:** `526,611` (`3.290%` of raw). Ply bins: `{"80+": 469107, "32-79": 55044, "16-31": 2111, "8-15": 349}`.
- **Duplicate vs first-seen disagreement:** mean `|score_dup - score_first| = 20.6 cp`, sign flips (>50 cp opposite sign) `2`, game result disagrees `5,547` (`1.05%`).
- **Observation:** Keeping first-seen only (rather than deduplicating with label averaging or cross-round dedup) is cheap and removes exact opening/repetition clones, though `526k` within-round dupes are tiny compared to the `101.32` correlated plies/game kept by having `0%` random-skip.

## 5. Deep Dive: `score_result_conflict` (`conflict_score = 600`)
- **Total dropped:** `465` (`0.0029%` of raw) — histogram `{"600..799": 232, ">=800": 208, ">=1200": 25}`.
- **Concrete examples:**
  - `fen rnb1kbnr/2pp1ppp/pp2p3/6q1/P5Q1/4P3/1PPPKPPP/RNB2BNR w kq - 1 5` | `move g4g5` | `score 680` | `ply 8` | `res -1`
  - `fen rnb1kbnr/2pp1ppp/pp2p3/6Q1/P7/4P3/1PPPKPPP/RNB2BNR b kq - 0 5` | `move d7d6` | `score -916` | `ply 9` | `res 1`
  - `fen rnb1kbnr/2p2ppp/pp1pp3/6Q1/P7/4P3/1PPPKPPP/RNB2BNR w kq - 0 6` | `move g5h5` | `score 946` | `ply 10` | `res -1`
  - `fen rnb1kbnr/2p2ppp/pp1pp3/7Q/P7/4P3/1PPPKPPP/RNB2BNR b kq - 1 6` | `move b8c6` | `score -1051` | `ply 11` | `res 1`
