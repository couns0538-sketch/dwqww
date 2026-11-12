# Wider-net pilot: 1024 hidden units against 512, same data, same recipe (2026-11-12)

Plan `h512/train/plans/h1024_pilot.json` (written before the run), launcher `h512/train/run_h1024.sh`. Random start,
271,830,023 training rows, 10.0B presentations (about 37 passes), 147 minutes on the GPU. Selection set only;
no candidate, no test set, no match. Loss = mean squared error against the alpha 0.4 target, integer net.

| Presentations | 1024 units, unseen rows | 512 units, unseen rows | Difference | 1024 units, own training rows | 512 units, own training rows |
|---|---|---|---|---|---|
| 1.0B | 0.014000 | 0.014126 | -0.000126 | 0.012945 | 0.013495 |
| 2.0B | 0.013941 | 0.014055 | -0.000115 | 0.012817 | 0.013399 |
| 4.0B | 0.013868 | 0.013968 | -0.000100 | 0.012702 | 0.013283 |
| 7.4B | 0.013827 | 0.013916 | -0.000089 | 0.012628 | 0.013215 |
| 10.0B | 0.013800 | 0.013882 | -0.000082 | 0.012615 | 0.013190 |

- Gap between unseen rows and own training rows at 10.0B: 0.001185 with 1024 units, 0.000692 with 512 units.
  The wider net fits the rows it has seen much better and transfers less of that: it is limited by the amount of
  data. More positions should help it more than they help the 512-unit net; that is untested.
- The gain on unseen rows shrinks as training goes on (0.000126 at 1.0B, 0.000082 at 10.0B).
- Engine speed with the final 1024-unit net: **0.8579x** the nodes per second of candidate 3's 512-unit net (95 % CI
  0.8552 to 0.8606; 3.03M against 3.53M nodes per second), same executable, 16 pairs of `bench 20` on one pinned core,
  Normal priority, quiet machine (`../abba_h1024_speed/`). The executable's profile was trained with the 512-unit
  net, so this is descriptive. A first rough reading earlier in the morning with an early checkpoint gave 0.82x.
- Run-to-run noise of this trainer is about 0.00002 in the first 45M presentations (see STATUS.md); the
  differences in the table are four to six times that.
- Final net `_work/runs/arms/h1024_pilot/net_seen10000023552.fnn3`, checksum `28fbc246638a6d81`; hashes in `files.md5`.
- Raw data: `metrics.jsonl`, `log.txt` (8 thermal holds of 5 s, 40 s in total; hot spot at most 61 C, memory 87 C).
