# REPORT R8: self-play data generation speedup — DONE (numbers below; switching is the owner's decision)

Branch `opus-r8-datagen` (base `86c91628` = the Forge 6.2.0 release source; only its Board code is used, for the chess
rules of the driver). Everything new is in `r8/` (README = how to build, run and switch on). PC clock times
(2026-10-29). Machine exclusive: no (gate conc 8, the live NNUE trainer, Grok Bot). Live self-play workers were not
touched; every test ran beside them in `F:\opus_scratch\r8\`, BelowNormal, pinned to CPUs 0-11 (tests on 8-9),
<= 3 threads.

## Summary
| | live pipeline (baseline) | `forge_selfplay_fast` (after) |
|---|---|---|
| what | `forge_selfplay.py` (Python, python-chess, SQLite) + Forge 6.2.0 `forge.exe` | native C++ driver + the **same** `forge.exe` |
| positions/h, 1 worker, CPUs 8-9, Idle (A/B/A/B) | **783,695** (17.6 min) and 788,393 (9.2 min): **785.7k** over 26.8 min | **1,045,080** (25 min) and 1,035,851 (10 min): **1,041.6k** over 35 min, **+32.6%** |
| CPU used (process tree) | 1.015 CPUs | 0.965 CPUs |
| positions per CPU-hour | 772k | 1,083k (**+40%**) |
| memory (tree) | 97.7 MB working set, 68.8 MB private | 80.9 MB working set, 72.5 MB private |
| search duty (go -> bestmove / wall) | 85.8% | 99.4% |
| data | text | identical text lines + direct `.pos` (FPOS v1) |
| quality | | **byte-identical games on fixed openings** (v1, v3, final v4); same score/result/ply spread on random ones (4 runs) |

## 1. Baseline (measured before any change)
- Live run on 2026-10-29: **stalled since 17:04:36** (see "Incident"); its rate before that, from file times:
  shard 037 -> 038 = 10,000,000 lines in 7.37 h = **1.36M positions/h for 2 workers** (0.68M/h per worker; 32.6M per
  day). The Oct-18 log shows 1.07M/h for 2 workers at 89% search duty. (The job text says ~53M/day; the measured
  shard rate is lower.)
- Beside-run of the same pipeline (unchanged script and engine, copy of `forge.exe` sha256 `00e4178c...`, 1 worker on
  CPUs 8-9, Idle, own output folder and dedup DB, `r8/logs/baseline/`): 2,500 games, 229,809 positions in 0.293 h =
  **783,695 positions/h**, search duty 85.8%, dedup removed 2.2% (fresh DB), ~1.0 CPU, < 100 MB. Second segment:
  see section 5.
- PC during the tests: system CPU median 66-67% (gate 8.0 CPUs, trainer 1.1-1.3, mine ~1.0), short spikes to
  75-86% from other processes; free RAM >= 10.98 GB.

## 2. What other engines do (ideas only, licences checked; `r8/IDEA_SOURCE.md`)
Stockfish's tools-branch `generate_training_data` (GPL-3.0) and Stormphrax's datagen (GPL-3.0-or-later): in-engine
self-play, per-thread searcher with a small hash reset per game, filtering of in-check / noisy-best-move positions at
generation time, one write batch per finished game, an in-process duplicate table, win adjudication and optional
draw adjudication / opening verification, NUMA binding per worker. Berserk (GPL-3.0): no datagen in the public
tree; Obsidian (GPL-3.0): trains on Lc0 data. No code was copied.

## 3. What changed and why it is the same data
- **The engine is not changed.** The live engine's source is not in the repo: the cursor-branch 6.2.0 release
  (`86c91628`) builds an engine whose `bench 13` is 1,234,322 nodes (its documented signature) while the live
  `forge.exe` gives 885,561, and its fixed-node searches differ (`r8/tools/compare_engines.py`). An in-engine
  generator on any source tree would therefore change the data. The driver keeps the live binary and removes what
  is around it.
- **Native driver** `r8/forge_selfplay_fast.cpp`: one engine process per worker, the live UCI sequence (Threads 1,
  Hash 16, `ucinewgame` per game, `position startpos moves ...`, `go nodes 5000`), the live rules (8 random plies,
  the eligibility filter, the last-score-line bound rule, 2000 cp x 4 plies win adjudication, threefold / 50-move /
  insufficient material / 300 plies), python-chess's FEN, the same "FEN | cp | result" lines, de-duplication on the
  first four FEN fields in memory, one write per finished game (1 MiB buffer, no fsync per game), optional direct
  FPOS `.pos` (`--pos`) + `.pos.info`, never overwrites a file.
- **Proof of identical data**: on 60 fixed openings the live script's own `play_game()` (imported unchanged) and the
  driver produce the same 5,499 records, byte for byte (sha256 `5d1e6783...`, `r8/logs/equivalence/`), for v1 and
  for the final v3. The `.pos` equals the text record by record (435,554 of 435,554; the live 015 pair checked the
  same way: 200,000 of 200,000).
- **Quality on random openings** (`r8/tools/quality_check.py`, 229,809 vs 435,554 records): cp std 537.1 vs 534.5,
  median |cp| 168 vs 167, |cp| <= 50 / 200 / 600 / 1500: 22.1/54.1/82.3/97.2% vs 22.3/54.3/82.4/97.2%, full-move
  quartiles 20/38/58 vs 20/37/58, score sign agrees with the result 63.6% vs 63.5%, White win / draw / loss 43.3 /
  32.0 / 24.7% vs 42.2 / 31.6 / 26.3% (game-level sampling noise of ~2.5k vs ~4.8k games); duplicates inside each set
  0 after de-duplication (2.2% / 2.3% removed); 1,300 positions shared between the two sets.

## 4. Options looked at (the job's list)
| idea | result |
|---|---|
| fixed nodes instead of fixed depth | the live pipeline already searches 5000 nodes per move; kept |
| smaller hash per worker | Hash 8: 1.19M vs 1.20M records/h on the fixed openings (no gain) and different data; Hash 4: see section 5; not adopted |
| batched writes | done: one batch per finished game, 1 MiB buffer, no SQLite insert + fsync per game (the live DB is 7.56 GB) |
| filter during generation | done in-process; waste on 60 games: 7,608 searches, 5,499 records; not recorded: best move capture/promotion 17.5%, in check 9.3%, mate 0.9% |
| skip wasted positions early | `--check-nodes N` (OFF): in-check positions are never recorded, so they can be searched with fewer nodes; changes the game path after them (not the labels); see section 5 |
| threads / NUMA | one CCD (no NUMA); the driver pins each worker to its own slice (2 workers on 12-15 -> 12-13 and 14-15); SMT test: section 5 |
| faster .pos writer | done: `--pos` writes FPOS v1 directly (no text -> .pos step) |
| adjudication rules | kept identical; draw adjudication (Stormphrax/Stockfish style) would end drawn games earlier, which removes positions without making the others cheaper: no positions/h gain, a change of the data mix; not adopted |
| OwnBook | the live script leaves the engine's default `OwnBook=true`: a book hit returns a move without a score and the script dies ("Engine returned no score", `nnue/logs/selfplay.err.log`, Oct 18). The driver sets `OwnBook=false` (those rare games are searched instead) |

## 5. Further measurements (chains, `r8/logs/chain/`)
- **Order and repeat**: baseline 17:24-17:42, after 17:49-18:14, baseline 18:15-18:25, after 18:25-18:35, same CPUs
  (8-9), priority (Idle) and engine; each segment ends by itself. Segment rates 783,695 / 1,045,080 / 788,393 /
  1,035,851 positions/h: the gain repeats (+33.4% and +31.4% against the neighbouring baseline segments).
- **Final driver v4** (`forge_selfplay_fast_v4.exe`, sha256 `1768770e...`, = the committed source): byte-identical to the
  live `play_game()` reference on the 60 fixed openings again; its bounded de-duplication (default, 512 MB table)
  keeps exactly the same lines as the exact set on those games (5,395 lines, 104 duplicates).
- **Waste** over 244,552 searches of the 10-minute run: 72.3% recorded; not recorded: capture/promotion best move
  17.6%, in check 9.0%, mate 1.1%, |cp| > 3000 21 positions, bound scores 0.
- **`--check-nodes`** (in-check positions with fewer nodes): 2500 -> +2.8%, 1000 -> +3.0% records/h on the fixed
  openings, but the games diverge after the first such position; not worth a data change: OFF.
- **Hash**: 8 MB +0% (1.193M vs 1.198M records/h), 4 MB +3% (1.235M), both with different games: not adopted.
- **SMT (2 engines per core)**: not measured; the PC was at 62% before the test and two busy engines would have taken
  it past the job's 70% CPU limit (the chain checks and skipped it).
- **Global duplicates**: 8.50% of the 25-minute run's positions (37,032 of 435,554) are already in the live 7.56 GB
  hash DB (`dedup_against_db.py --count-only`, opened read only and immutable, 45.7 s). The live pipeline removes
  these at write time; the driver's run-local de-duplication does not, so use the post-filter (or count 8.5% fewer
  new positions) when comparing with the live production rate.
- **Quality, four runs** (229,809 / 435,554 / 120,863 / 172,752 records): cp std 537.1 / 534.5 / 536.7 / 531.1, median
  |cp| 168 / 167 / 168 / 165, |cp| <= 200 54.1 / 54.3 / 54.0 / 54.8%, full-move quartiles 20/38/58 (20/37/58 for the
  first driver run), score sign agrees with the result 63.6 / 63.5 / 63.4 / 63.9%, draws 32.0 / 31.6 / 31.5 / 31.3%;
  each set 0 duplicates inside, 0.2-0.65% shared between sets. The baseline-to-baseline spread is as large as the
  baseline-to-driver spread.

## Incident (owner item)
The live self-play (`forge_selfplay.py`, 2 workers at Idle priority pinned to CPUs 12-15) stopped writing at
17:04:36 and its processes sat at 0 CPU (still at 17:13). That began while an unpinned R7 test of mine (a conc-3
mini-gate, BelowNormal) ran; the cause is not proven. The pipeline's output queue is bounded (4), so a blocked main
process stalls the workers. Nothing was killed or restarted; restarting is the owner's decision.

## How to switch on (owner)
See `r8/README.md`. In short:
1. Take `F:\opus_scratch\r8\driver\forge_selfplay_fast_v4.exe` (sha256 `1768770ebff208edca0968bb12a10ea5101d382b32699c19fcf48ab8f7be2861`)
   or build it from this branch (`r8/tools/build_driver.py`).
2. Run it instead of the `forge_selfplay.py` line of `selfplay_guard.py`, with the same engine and CPUs, into a new
   folder: `forge_selfplay_fast_v4.exe --engine C:\Users\Administrator\grok-pc\nnue\forge.exe --out
   D:\grok-pc-data\selfplay_out_fast --workers 2 --cpus 12-15 --nodes 5000 --hash 16 --pos`. It writes the same text
   lines plus ready `.pos` + `.pos.info` files (the text -> .pos step can be skipped).
3. Optional: `r8/tools/dedup_against_db.py <live forge_seen_hashes.sqlite3> <kept.txt> <driver.txt>` before
   training, to keep the global de-duplication (about 8.5% of new positions are old ones).
Expected with the live layout (2 workers, CPUs 12-15): about +33% positions per hour at the same CPU footprint
(projected from the 1-worker A/B; 2 workers on 12-15 were not run, they belong to the live pipeline's CPUs).

## Not done / owner items
- The 2-engines-per-core and 4-workers-on-12-15 layouts (more total throughput, more CPU) were not measured
  (70% limit). The live engine's source was not found, so no engine-level change was possible.
- The live self-play is stalled since 17:04:36 (above); the live script's OwnBook=true can crash it again.

## Time
R8 started 17:20 (after R7 was pushed); commits 17:46-18:4x on `opus-r8-datagen`; measurements 17:24-18:37.
