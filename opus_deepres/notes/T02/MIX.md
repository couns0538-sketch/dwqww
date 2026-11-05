# T02 MIX - self-play vs external data for Forge: what two engines did, and a recommendation (UNPROVEN)

## Forge today (own records)
- Live self-play: Forge 6.2.0 HCE build (October, not the lock), 5000 nodes per move, Threads 1, Hash 16, 8 uniformly
  random opening plies, win adjudication 2000 cp for 4 plies, draws by rule / ply >= 300; rows dropped at write time:
  in check, best move capture / ep / promotion, mate scores, |cp| > 3000, bound scores (skill forge-selfplay-datagen).
  The R8 driver gives +33 % positions per hour on the same rules; the owner's rate is ~1.24M positions per hour.
- Training set: J1 binpack 304,999,573 rows (001-039 without the 013/014 holdout); npt nets overfit after epoch 7
  (owner); lambda is decided (Lichess 1.0, self-play 0.7-0.9). The brief calls the set "305M Lichess plus self-play
  rows", but 304,999,573 is exactly the self-play J1 binpack, and the w4 runs train on it alone (npt keeper config +
  the s41 run log: `--start-lambda 1.0 --end-lambda 1.0 --no-filtered --no-wld-filtered`). Where the Lichess rows
  are and how many: PENDING (crew).
- npt K32H3^ L1-1024 nets vs AL1: -86 to -116 Elo (FORGE_RESULTS.csv); WAC gap and its test: card T02-04.
- Relabel tool (forge-relabel-job): lock probe at 20k nodes ~635k rows/h on 2 threads (50M rows ~79 h); 5k nodes
  ~1.19M rows/h, 10k ~0.74M rows/h per worker.

## Engine 1 - Stockfish (self-play -> external teacher), from commit messages only (GPL-3.0, ideas only)
- 2020-2021: own self-play data (depth-9 games); 2021-06 the LCSFNet10 data set = 72 % own depth-9 positions (16e9)
  + 28 % Leela positions (6.3e9) (commit 14b673d90f).
- 2021-07: one regeneration round with the master net: 16B positions at depth 9-11 with random multipv openings,
  then retrained from the master, then a short finishing run (b939c80513: +1.62 STC / +1.03 LTC, multi-stage).
- 2021-11 onward: Leela T60 / T74 data + own fixed-node data (5000 nodes, multipv 2), Syzygy-rescored external sets
  (PR 3808 / 3816); 2022-2024: mostly filtered + TB-rescored Leela data (T60-T80) plus own DFRC 5000-node data;
  2024-03 the own DFRC data was removed (bd579ab5d1, confounded +1.14 / +2.06).
- Cadence (2022-12 to 2024-05 commit dates): a new master every 1-5 weeks, almost always "retraining the master net"
  on an extended set (fine-tune from the previous best, not from scratch); new data added in month-sized slices;
  early-ply cut 27-30.

## Engine 2 - Caissa (external net -> own self-play), MIT, README + SelfPlay.cpp @8d2454c72f + commit messages
- History: PeSTO HCE -> v0.6 temporarily used an external (Stockfish) net -> v0.7+ own nets, first from a few million
  self-play positions, then 13.7B (2024-12) -> 15B (2025-04) -> 16B (2025-10) -> 20.4B (2026-05) -> 20.5B+ positions.
- "Progressive training": older games are purged, so each net is trained only on data from the latest engine versions.
- Generator defaults: fixed soft node budget (21k, doubled for the first 10 half-moves, hard cap 5x soft), max depth
  40, UHO or DFRC book + 8-10 random moves, openings with too large |eval| skipped, eval randomisation on, win and
  draw adjudication off by default, Syzygy WDL adjudication at <= 5 pieces, 1M games per file.
- Targeted additions measured: +32M endgame-book self-play positions + fortress positions (eval-75): +2.79 LTC /
  +2.62 STC, +47.8 on an endgame book (TABLE.md row 2). Three loader filters together: about -11 Elo (row 8).

## Recommendation for Forge (own values; every number UNPROVEN; Forge has no Elo claim here)
1. **Generation G1 = change the teacher, not the filters.** Generate new self-play with the lock engine (AL1 s198 /
   FD3A5190, or the forge_data_probe lock build) through the R8 driver instead of 6.2.0 HCE. Nodes per move: own start
   8,000 soft nodes (range 5,000-20,000), x2 for the first 10 plies, hard cap 4x soft. The 6.2.0 -> lock strength gap
   at 5000 nodes: PENDING (one 200-game fixed-node match, ~1 CPU-hour).
2. **Mix for the G1 net:** all 305M existing rows + the new lock rows, the new rows sampled at 30 % of each epoch
   (range 20-50 %) until they are >= 100M rows (~3.5 days at ~1.24M/h if the lock engine keeps that rate; its rate at
   8k nodes: PENDING), then plain concatenation. Retrain from the best npt checkpoint (fine-tune) and from scratch once
   each; keep the epoch count below the epoch-7 overfit point.
3. **Generation G2:** when an npt net passes the gate vs AL1, it becomes the datagen engine; purge the oldest 6.2.0
   rows once G1 + G2 rows reach ~300M (Caissa-style progressive purge, Stockfish-style removal of its weaker own data).
   One generation = ~100M new rows (~1.1M games at ~90 recorded rows per game; T02-01 measured 87.7 rows per block);
   cadence ~1-2 weeks.
4. **Adjudication / openings:** keep the 8 random plies; add Syzygy adjudication at <= 5 pieces where TB files exist
   (PENDING) so endgame results are exact for lambda 0.7-0.9; keep win adjudication but test 4 -> 8 plies; no draw
   adjudication. Add a 1-5 % endgame-book subset (card T02-06).
5. **External data:** the Leela-scored binpacks (ODbL, 328-514 GB sets, TABLE.md last line) are the strongest teacher
   available, but the sets do not fit on F:, ODbL needs attribution, and no source tested them on an engine as weak as
   Forge: at most a <= 10 GB slice at <= 30 % of an epoch, after G1. The Lichess rows (lambda 1.0) stay as they are.
6. **Every data change keeps the overlap at 0:** dedup new rows against the 013/014 holdout on board + stm (card
   T02-01), split validation by game (the .games sidecar), re-run the T02-01 check. Gate each generation's net vs AL1:
   UHO SPRT [0, 5] at STC, then LTC.

Missing evidence: neither source reports a self-play / external ratio tested at a fixed net size, so the 30 % start
is an own choice; neither documents nodes per move for its current generations beyond the generator defaults above.
