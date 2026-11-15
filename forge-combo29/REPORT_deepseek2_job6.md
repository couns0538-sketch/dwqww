# deepseek2, job 6 report: three search candidates played

## 1. First line

**Of the three candidates, none gains per node: c4_iirshallowtt LOSES (−13.73 ± 10.41), and both
c5_conthistsplit (−2.95 ± 10.15) and c6_lowplyhist (0.00 ± 10.50) show nothing.**

**What was cut, first, because it is the main limitation.** The budget did not stretch to six
2,000-game matches. All three first matches did finish — C, M1, M2 **and M3**, the last at 18:50,
after this report's first version had already been written and pushed; M3's result is added here and
replaces the "not finished" line that version carried. **M4, M5 and M6 (the second seeds) were NOT
started**, so no candidate has a second seed and every number below rests on one 2,000-game sample.

| match | build / option | games | Elo | 95 % | pairs [0,1,2,3,4] | crashes | illegal | status |
|---|---|---|---|---|---|---|---|---|
| **C** control 20000 vs 10000 nodes | c4, option off | 300 | **+172.78** | ±31.01 | [2, 7, 31, 71, 39] | 0 | 0 | done |
| **M1** `IirShallowTt 1` vs off | c4_iirshallowtt | **2000** | **−13.73** | ±10.41 | [77, 235, 420, 226, 42] | 0 | 0 | done |
| **M2** `ContHistSplit 1` vs off | c5_conthistsplit | **2000** | **−2.95** | ±10.15 | [53, 244, 420, 233, 50] | 0 | 0 | done |
| **M3** `LowPlyHist 1` vs off | c6_lowplyhist | **2000** | **0.00** | ±10.50 | [63, 231, 404, 247, 55] | 0 | 0 | done |
| M4/M5/M6 second seeds | — | 0 | — | — | — | — | — | **not started** |

The control at +172.78 ± 31.01 is in the range the job predicted ("near +200"), so the harness
measures what it should: a 2:1 node handicap is worth about +170 Elo here, and both real matches have
intervals of about ±10.

## 2. My one-sentence reading of each patch

- **c4_iirshallowtt** (`IirShallowTt`, `src/search.cpp`, ~10 lines): when the hash **move** comes from
  an entry at least `IirDepth` plies shallower than the current search, apply the same one-ply
  internal-iterative **reduction** that the code already applies when there is **no** hash move —
  i.e. treat a stale hash move as being about as unhelpful as none. That is exactly what the job's
  line says, and the patch does nothing else.
- **c5_conthistsplit** (`ContHistSplit`, 3 files, ~100 lines): instead of one continuation-history
  table, a move that was made **in check** and/or **capturing** indexes its own follow-up table
  (index `in_check*2 + capture − 1`, so 1.3 MB extra per thread held as `array<ContinuationHistory,3>`
  and `memset` to zero on clear), while quiet non-check moves keep the old table. Read and write both
  go through the new `continuation_for()`. That matches the job's line; the only thing I would flag is
  that the label "separate follow-up histories after quiet moves, captures and check evasions" is
  slightly misleading — quiet moves keep the *shared* table, they do not get one of their own.
- **c6_lowplyhist** (`LowPlyHist`, 2 files, ~80 lines): a per-search `[ply<4][from][to]` quiet-history
  table, reset with `memset` at the start of every search (`Worker::search`), written in
  `update_quiet_stats` (bonus for the best quiet, malus for the tried ones), and read in the move
  picker with a ply-dependent weight `*4/(ply+2)` (2.0 at the root, 1.33, 1.0, 0.8 at plies 1–3).
  That matches the job's line. **One thing to look at:** the weight is applied at `ss_->ply` when
  scoring moves *at* that node, so the history written at ply p is read at ply p in *later* nodes, and
  the root's own table is read and written only at the root node — I did not convince myself that is
  the intended semantics, but I did not change the patch either (it is not mine to change).

No patch did something different from its one-line description.

## 3. Step 0

Base: clean export of `d4f43124dde1d1e37de90e18930e374f32ea7ffa`, each candidate applied **alone**
with `patch -p1 --fuzz=0` (no fuzz, no rejects). Build flags, the same for all three:

```
cmake <tree> -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_C_COMPILER=gcc \
      -DFORGE_MARCH=native -DFORGE_EXPOSE_TUNABLES=ON -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256"
```

**`FORGE_EXPOSE_TUNABLES=ON` is necessary and is not this tree's default** — without it the switches
are accepted silently but never listed in the `uci` answer, so fastchess refuses to set them
(`Warning; ON doesn't have option IirShallowTt`) and every match would compare the option-off engine
with itself. I found this on the first probe and rebuilt all three. It is exactly the failure mode
the job warns about ("if it does not, the match program never sends it").

| build | option off: 11 / 13 / 16 / perft 5 | option on: 11 / 13 / 16 | branch's recorded ON |
|---|---|---|---|
| c4_iirshallowtt | 312866 / 862329 / 3024920 / 4865609 | **309855 / 724372 / 2173900** | 309855 / 724372 / 2173900 |
| c5_conthistsplit | 312866 / 862329 / 3024920 / 4865609 | **323985 / 753650 / 3128498** | 323985 / 753650 / 3128498 |
| c6_lowplyhist | 312866 / 862329 / 3024920 / 4865609 | **320362 / 897394 / 2563336** | 320362 / 897394 / 2563336 |

All nine ON numbers match exactly; all three OFF sets are the known numbers. Evidence:
`tests_deepseek2_job6/step0_and_probes.txt`.

## 4. Before every match: the probes and the seed check

- The three options appear in the `uci` answer as
  `option name IirShallowTt type spin default 0 min 0 max 1` (and the same shape for the other two),
  and after the `FORGE_EXPOSE_TUNABLES` rebuild the fastchess warning is gone, so the candidate side
  received the `setoption`.
- **Two seeds give different openings**, which is what job 5's M2 failed to do:
  `probeB` (seed 7831) opened `r1bqk1nr/4ppbp/p1np2p1/...` and `probeC` (seed 7821) opened
  `rn1qk2r/pp3pp1/2p1bn1p/...` — different FENs, from `order=random` with `-srand`.

**A control that was wrong first, and why I re-ran it.** My first C run had `nodes=20000` on **both**
sides (my script hardcoded it), so it compared identical engines and read −8.11 ± 26.41. That number
looked like a broken harness, and it was: I fixed the script to pass the node counts per engine and
re-ran C, which then gave **+172.78 ± 31.01**. The −8.11 row is discarded and is not in any table
above; the first C *is* a useful accidental control, though: it shows what "no difference" looks
like on 300 games (±26), which is much wider than the ±10 of a 2,000-game match.

## 5. The matches

`nodes=20000` per engine, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO
(`UHO_Lichess_4852_v1.epd`), each opening twice with colours reversed, `order=random` with
`-srand <seed>`, no adjudication, the patched exe on both sides with the option on one side only,
`-concurrency 4` on 4 cores. fastchess alpha 1.8.3.

| match | seed | games | Elo | 95 % | pairs [0,1,2,3,4] | Points | LOS |
|---|---|---|---|---|---|---|---|
| C (20000 vs 10000) | 7820 | 300 | **+172.78** | ±31.01 | [2, 7, 31, 71, 39] | 73.00 % | — |
| M1 `IirShallowTt` | 7821 | 2000 | **−13.73** | ±10.41 | [77, 235, 420, 226, 42] | 48.02 % | 0.48 % |
| M2 `ContHistSplit` | 7822 | 2000 | **−2.95** | ±10.15 | [53, 244, 420, 233, 50] | 49.58 % | 28.43 % |
| M3 `LowPlyHist` | 7823 | 2000 | **0.00** | ±10.50 | [63, 231, 404, 247, 55] | 50.00 % | 50.00 % |

**M3's 0.00 needs the job's own check, because the job says a 0.00 row means the option did not
arrive.** It is not that: the pairs are [63, 231, 404, 247, 55] (spread across all five columns, not
[0,0,N,0,0]), the match log has no `doesn't have option` warning, the engine lists
`option name LowPlyHist type spin default 0 min 0 max 1` in its `uci` answer, and the 2,000 games are
2,000 *distinct* move sequences. The win/loss counts came out 568/568, which is a coincidence at that
precision; the spread pair distribution is what says the option was live. Crashes 0, illegal moves 0, time forfeits 0 (nodes-only games cannot lose on time).

**Reading the two finished candidates.** M1's pair distribution is not centred on the middle: 77
pairs at 0/2 and only 42 at 2/2, i.e. the candidate loses more double-losses than it wins
double-wins, and its LOS of 0.48 % says the same. That is a **real loss** at 2,000 games, not noise.
M2's distribution is closer to symmetric ([53, 244, 420, 233, 50]) and its interval straddles zero
comfortably: **nothing demonstrated**, in either direction. M3 is the same picture, even flatter
([63, 231, 404, 247, 55]): **nothing demonstrated**.

## 6. Files of the repository I opened

`opus_r15/cands/c4_iirshallowtt/c4_iirshallowtt.patch`,
`opus_r15/cands/c5_conthistsplit/c5_conthistsplit.patch`,
`opus_r15/cands/c6_lowplyhist/c6_lowplyhist.patch` (all on branch `opus-r15-20261103`, whose tip is
`2de61ac8c`, not the `d4f43124` the base export came from); from the base tree:
`src/search.cpp` (55–110 the tune table, 560–600 the worker's tables and `clear`, 726–760
`update_continuation`, 1000–1140 the search move loop), `include/forge/search.hpp` (310–360 the
worker's members), `src/uci.cpp` (165–210 the `uci` answer and `setoption` chain) — `uci.cpp` was
read to explain the `FORGE_EXPOSE_TUNABLES` behaviour, not modified.

## 7. Stamps

| point | UTC |
|---|---|
| job 6 start | 2026-11-15T17:49:11Z |
| branch and patches fetched, three trees patched | 17:49 |
| three builds, Step 0 OFF/ON verified | 17:49–17:50 |
| first probe: fastchess refused the option (not advertised) | 17:50 |
| rebuild with `FORGE_EXPOSE_TUNABLES=ON`, options verified | 17:50–17:51 |
| first C launched; **wrong** (`nodes=20000` on both sides) | 17:51 |
| wrong C finished −8.11 (discarded) | 17:56 |
| C re-run correctly: +172.78 ± 31.01 | 17:58–18:00 |
| M1, M2, M3 chain launched | 18:00 |
| M1 finished: −13.73 ± 10.41 | 18:17 |
| M2 finished: −2.95 ± 10.15 | 18:35 |
| first version of the report written (M3 still running) | 18:45 |
| M3 finished: 0.00 ± 10.50, 2000 games | 18:50 |
| this version of the report | 18:55 |

Budget: 90 minutes from 17:49:11, i.e. 19:19, with the stop at 19:09; the report is written at about
56 minutes.

## 8. What I did not do

- **No second seed for any candidate** (M4, M5, M6 not started). So c4's loss rests on one
  2,000-game match, and c5's and c6's "nothing" each on one. A second seed would have been the right
  check for all three, and the job asked for it.
- The first version of this report (commit before this one) said c6 was unmeasured; it finished
  later and is reported now. Nothing else changed.
- No SPRT; fixed blocks as specified.
- I did not investigate *why* c4 loses — the patch is a plausible idea (a stale hash move is a weak
  ordering hint) and the measurement says it costs about 14 Elo. A breakdown by depth (how often the
  condition fires) would say whether it fires too often, and I did not instrument it.
- The 2000-game matches ran at `-concurrency 4` on 4 cores, so the wall times are not clean
  measurements (not used for anything).
- No engine source committed, no pull request; the patches are read from the branch, not copied into
  my folder (only their text evidence notes are).

## 9. What I am not sure about

- **c6's 0.00 ± 10.50 is "no demonstrated effect", not "proven neutral".** It benches the largest
  deviation of the three (320362 / 897394 / 2563336) and touches the most common code path, so a real
  small effect either way would be inside this interval. One seed cannot separate "0" from "±5".
- **c4's −13.73 ± 10.41** could be an opening-set effect: the UHO set is fixed to the first 2,000
  lines and `order=random` only shuffles which of them come first, so the *set* is the same for every
  match. A loss on one sample from a fixed set is still a loss, but the second seed would have said
  whether it is stable.
- Whether the `*4/(ply+2)` weighting in c6 is what its author intended, given that the table is
  indexed by the ply of the node that *reads* it (see §2).
- M2's −2.95 is inside its own interval, but its LOS of 28 % is not a flat 50 %; I would not call it
  "neutral" as strongly as "no demonstrated effect".

## 10. A better way

1. **A control should be run before the long matches, not in the chain with them.** My wrong C cost
   about 5 minutes and, worse, would have gone into the report as "the harness is broken" if I had
   not spotted the +200 expectation in the job text. One 40-game probe at 20000-vs-10000 nodes takes
   seconds and would show the harness works before 40 minutes of real matches start.
2. **Check the engine's `uci` answer before every match job, not after the first probe.** The
   `FORGE_EXPOSE_TUNABLES` trap cost a rebuild of three trees; one `printf 'uci\n'` comparison of the
   option list against the job's option names would have caught it at Step 0, where the job already
   asks for "the `uci` answer must list the option".
3. **Three 2,000-game matches do not fit an 80-minute budget on four cores** with everything else in
   the job (builds, probes, Step 0). Either the job should give one match per candidate plus a second
   seed for the one that is closest, or the budget should be ~3 hours. I would rather run 1,000 games
   for each of three candidates *and* their second seeds than 2,000 for one and none for another.

## 11. Model

deepseek2. As I know it: DeepSeek V4.1 Flash, build 1017, running as a Cursor cloud agent.
