# Match M9 (wide pilot net against candidate 3, 10 s + 0.1 s): declared before the first game (2026-11-12 10:05 PC clock)

Not the crew gate, not a lock claim, and **no candidate**: the 1024-unit net is a pilot net (plan
`h512/train/plans/h1024_pilot.json`), selected by nothing, and this match does not make it a candidate.
Question: with the data that exists today, does doubling the hidden layer pay at equal playing time? The wide net
scores 0.013800 on the selection set against 0.013882 for candidate 3, and the engine searches 0.8579x as many
nodes per second with it.

| Item | Value |
|---|---|
| Executable, both sides | `_work\builds\h512_v3_c3_b3c746944937\forge_fair_h512_v3_c3.exe`, md5 `0836190d2a2653dbbfad3904d187b446` (the rebuild that prints `id author Couns`; first games played by this file) |
| Side `cand` | net `_work\runs\arms\h1024_pilot\net_seen10000023552.fnn3`, md5 `516d450489d5fcc750f35563e41689ee` (1024 units, 10.0B presentations, random start) |
| Side `c3` | net `_work\nets\h512_cand_W2_seen10000023552.fnn3`, md5 `aab64b3342d7c1c33e82845f5d2d1fa4` (candidate 3, 512 units) |
| Budget | **2,000 games = 1,000 opening pairs**, fixed, no early stop |
| Openings | `UHO_Lichess_4852_v1.epd`, random order, seed 2026111202, each opening with both colours |
| Clock | 10 s + 0.1 s per move for both sides, time margin 1000 ms |
| Engines | Threads 1, Hash 16 MB, OwnBook false, `NNUEArch` true |
| Concurrency | 12 games at once; GPU idle; nothing else of this job runs |
| Adjudication | none |
| Runner | `fair_eval/tools/run_match.sh` with `MATCH_BASE`, `MATCH_BASE_OPTS`, `MATCH_BASE_NAME=c3`, via `h512/results/phase3/launch_m9.sh` |
| Analysis | `h512/tools/match_elo.py`, opening pairs as units, 95 % interval; time losses and crashes by side |

Caveats fixed now: the executable's profile was trained with the 512-unit net (the code path is the same for both
widths; the measured speed ratio above was taken on this executable). One clock only. With 1,000 pairs the 95 %
interval will be about 8 Elo either side, so a difference smaller than that will not be resolved.

Expectation written down before the match, from the loss difference and the speed ratio: between about -15 and +5
Elo for the wide net. Estimated duration: about 85 minutes.

Known when this was written: everything in `h512/STATUS.md` up to commit `793b8013`.
