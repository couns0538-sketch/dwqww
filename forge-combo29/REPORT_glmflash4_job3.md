# glmflash4, job 3 report (2026-11-15)

## 1. Answer in one line

ContHistDeep=2 does NOT gain strength per node: seed 8101 gave -1.39 ±
10.51, seed 8102 gave +1.22 ± 10.13, and the two pooled (4000 games, 2000
pairs) give -0.09 with a 95 % pair interval of [-7.39, +7.21] — no
detectable gain at 20000 nodes. ContHistDeep=1 (seed 8103) gave +4.52 ±
10.65 [-6.13, +15.18], consistent with the other helper's single +4.9 ±
10.3 but not conclusive on its own. Nothing was cut and nothing was left
unreached: the control and all three matches ran their full game counts
(exit 0, 0 abandoned).

## 2. Step 0, expected against printed

Fresh engine process per line; raw outputs in `tests_glmflash4_job3/step0/`.

| line | expected | printed | file |
|---|---|---|---|
| bench 11, no option | 312866 | 312866 | step0/bench11.txt |
| bench 13, no option | 862329 | 862329 | step0/bench13.txt |
| go perft 5 (after `position startpos`) | 4865609 | 4865609 | step0/perft5.txt |
| `uci` lists the option | must list ContHistDeep | `option name ContHistDeep type spin default 0 min 0 max 2` | step0/uci_reply.txt |
| ContHistDeep=1 then bench 13 | a number different from 862329 | 989877 | step0/bench13_deep1.txt |
| ContHistDeep=2 then bench 13 | different again | 729826 | step0/bench13_deep2.txt |

All step-0 lines pass; the build went on.

## 3. The matches

Match form exactly as the job gives it (one exe both sides, `proto=uci
nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false` under
`-each`, no adjudication, `-concurrency 4` — this VM has 4 cores; control C
carries `nodes=` per engine instead). fastchess alpha 1.8.3
(20261107-d7b47e8), built from source; openings
`UHO_Lichess_4852_v1.epd` from the official zip.

| match | cand options | seed | games | W-L-D (cand) | pair counts (Ptnml) | fastchess Elo ± err | my Elo [95 % pair interval] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|
| C | none; cand nodes=20000 vs base nodes=10000 | 8100 | 300 | 191-24-85 | [1, 2, 31, 61, 55] | +218.19 ± 33.26 | +218.19 [+186.60, +253.35] | 0 |
| M1 | ContHistDeep=2 | 8101 | 2000 | 570-578-852 | [71, 219, 405, 257, 48] | -1.39 ± 10.51 | -1.39 [-11.90, +9.12] | 0 |
| M2 | ContHistDeep=2 | 8102 | 2000 | 567-560-873 | [55, 222, 436, 235, 52] | +1.22 ± 10.13 | +1.22 [-8.92, +11.35] | 0 |
| M3 | ContHistDeep=1 | 8103 | 2000 | 598-572-830 | [66, 219, 397, 259, 59] | +4.52 ± 10.65 | +4.52 [-6.13, +15.18] | 0 |

Pooled over the two ContHistDeep=2 seeds (my script, both games files
concatenated with M2's rounds renumbered +1000): 4000 games, 2000 pairs,
0 unpaired, W-L-D 1137-1138-1725, score 0.4999, Elo -0.09, pair se 0.0054,
95 % pair interval [-7.39, +7.21]; pair counts 0.0:126 0.25:441 0.5:841
0.75:492 1.0:100.

Per-match evidence files: `tests_glmflash4_job3/matches/<name>_games_and_tail.txt`
(argv, stamps, one line per game, last 40 lines of fastchess output, warning
and crash counts, my pair statistics).

First two opening FENs per match (rounds 1 and 2 of each match, showing
different seeds drew different openings):

| match | opening 1 (round 1) | opening 2 (round 2) |
|---|---|---|
| C | r2qkb1r/pb1N1ppp/1pp1pn2/3p4/3P4/1Q2P3/PPP2PPP/RNB1KB1R b KQkq - 0 8 | rn1qkb1r/pp1n1ppp/2p1p3/3p4/3P4/6P1/PPP1PPBP/RNBQ1RK1 w kq - 0 8 |
| M1 | r1bqk2r/ppp2ppp/2n5/1B1pP3/3pn3/P4N2/1PPb1PPP/R1BQK2R w KQkq - 0 9 | rn1q1rk1/ppp2ppp/3bbn2/8/4P3/3B3P/PPP2PP1/RNBQK1NR w KQ - 1 7 |
| M2 | rn1qkbnr/pp3ppp/2p1p3/3pPb2/3P1NP1/8/PPP2P1P/R1BQKBNR b KQkq - 0 7 | rn2kbnr/ppp1p1pp/5p2/5q2/4pP2/7P/PPPP3P/RNBQKB1R w KQkq - 1 7 |
| M3 | rn2kb1r/p1pq1ppp/4pn2/1p6/2QP2b1/5NP1/PP1NPP1P/R1B1KB1R w KQkq - 0 8 | rnbqk2r/pp4pp/2p1pn2/3pBp2/1b1P4/2N2P2/PPPQP1PP/2KR1BNR b kq - 3 7 |

## 4. The probes

Before every match: the same command with `-rounds 1` and
`-log file=<probe>.log level=trace engine=true`. Quoted lines (two games per
probe → the line twice; probe logs are on this machine at
`/tmp/matches/probe_<name>/probe.log` and the quoted lines are committed in
`tests_glmflash4_job3/probes/`):

- probe C (no option to deliver): `Warning;` count 0; no ContHistDeep line exists, as expected.
- probe M1: `cand <--- setoption name ContHistDeep value 2` (twice) — option arrived.
- probe M2: `cand <--- setoption name ContHistDeep value 2` (twice) — option arrived.
- probe M3: `cand <--- setoption name ContHistDeep value 1` (twice) — option arrived.

## 5. What the patch changes, in my own words

(Read from `conthist_deep.patch.txt` and checked against the patched files.)

- At value 1: quiet-move scoring additionally READS the continuation-history
  table of the move four plies back, at half weight, wherever quiet moves are
  scored or their history read: `src/search.cpp:795` and `src/search.cpp:798`
  (the move picker's scoring functor), `src/search.cpp:1335` and
  `src/search.cpp:1349` (`Worker::quiet_history`). The four-ply table was
  already being written (distances 1, 2 and 4 were always updated); value 1
  only turns on the reading, which the option `ContHist4PlyRead` had gated
  before and `ContHistDeep >= 1` now turns on as well.
- At value 2: additionally WRITE a six-plies-back continuation-history entry
  at half bonus and READ it at half weight in the same places:
  write at `src/search.cpp:1389-1393` (`Worker::update_continuation`), read
  at `src/search.cpp:798` and `src/search.cpp:1353`. The declaration and the
  `setoption` handling live in `src/uci.cpp:222` and `src/uci.cpp:404-408`;
  the variable at `include/forge/search.hpp:296` and `src/search.cpp:94`.
  Value 0 changes nothing (all new paths are gated on `>= 1` / `>= 2`).

## 6. Files of the repository I opened

- `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_glmflash4_3.md` (this job file; files 1-2 were read earlier in the session).
- `for-fable-and-opus/deepseek2-work`: `forge-combo29/tests_deepseek2_job5/conthist_deep.patch.txt` (read in full; copied into `tests_glmflash4_job3/`).
- Commit `6b98f2170a3210e71beed04bbd2553972c253ed7`: exported `forge-combo29/` with `git archive` to /tmp; after the matches I opened, in the PATCHED tree, `src/search.cpp` (the `ContHistDeep` sites, lines 94, 795-798, 1335-1353, 1389-1393), `src/uci.cpp` (lines 222, 404-408) and `include/forge/search.hpp` (line 296), plus the patch itself; nothing else of the tree was opened.

## 7. Start and end of each step (`date -u`, UTC)

- 18:50:41 job file 3 fetched and read; session restarted by the owner's message
- ~18:50:45 engine commit verified present locally (it is this session's base commit 6b98f217); patch fetched from `for-fable-and-opus/deepseek2-work`
- ~18:50:55 `forge-combo29/` exported with `git archive` to `/tmp/engine_job3/forge-combo29` (outside the git work tree); patch applied `patch -p1 -F0`, clean, no rejects (`engine_job3_patch_output.txt`)
- 18:51:11 Release build finished (binary mtime), command: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && cmake --build build --target forge -j4`
- ~18:51:20 step 0, six lines, all pass
- 18:51:27-18:51:34 four 2-game probes (log timestamps inside the probe logs)
- 18:51:4x-18:53:09 control C, 300 games: +218.19 ± 33.26
- 18:53:12-19:06:59 M1, 2000 games, exit 0
- 19:08:09-19:26:35 M2, 2000 games, exit 0
- 19:26:38-19:43:47 M3, 2000 games, exit 0
- 19:44-19:5x pooled statistics, report, commit, push

## 8. What I did not do

- I did not test ContHistDeep=2 against ContHistDeep=1 directly, nor any
  value above 2 (the option caps at 2), nor combined with other options.
- I did not re-run M3 with a second seed; its +4.52 rests on one sample.
- I did not investigate WHY value 2 searches fewer bench nodes than value 1
  (729826 vs 989877); both differ from the off-value 862329 as required.
- No PR was opened; nothing outside my own branch was pushed or changed.

## 9. What I am not sure about

- Every configuration is one seed except value 2 (two seeds, both flat).
  The pooled value-2 interval [-7.39, +7.21] is the strongest statement I
  can make; a gain smaller than ~7 Elo at this node count would hide in it.
- fastchess's Elo error and my pair interval are different estimators; they
  agree in width in all four runs. I report both and claim neither.
- M3's +4.52 vs the other helper's +4.9 ± 10.3: the numbers are consistent,
  but I do not know the other helper's seed/protocol in detail, so I treat
  the agreement as informal, not a measurement-level reproduction.

## 10. A better way

- fastchess's `-pgnout` APPENDS to an existing file by default
  (`app/src/types/pgn.hpp:17`, `append_file = true`; enforced in
  `app/src/matchmaking/tournament/base/tournament.cpp:45-55`). I reused the
  earlier session's match directory for M1 and only noticed because the PGN
  held 3500 games for a 2000-game match. Two cheap rules prevent this:
  (a) never reuse a match directory across runs, or (b) pass
  `append=false` on `-pgnout` (with no resume state it truncates). I
  re-ran nothing: M1's own 2000 games were recovered exactly from the PGN's
  second block (boundary = the 1501st `[Event` line), and its fastchess
  results table (fresh stdout, `Games: 2000`) agrees with the recovered
  W-L-D. M2/M3 ran in fresh directories and their PGNs contain exactly
  2000 events each.
- A count check worth adding to any match wrapper: after the match, the
  PGN's `[Event` count must equal the games total fastchess reports. It
  would have caught my M1 contamination automatically.

## 11. Model name and version

I am glmflash4. The model behind this agent is GLM, trained by Z.ai; the
runtime presents it as GLM 5.3 Flash. I cannot verify a precise version
string from inside the run.
