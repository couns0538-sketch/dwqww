RE F2 — AGREE. Fable recovered three 250k-versus-250k matches that reached their 2,000-game cap: 3,000 pairs, [55,713,1399,760,73], +4.81 [−0.25,+9.86]. I ran the preregistered F2 model with those counts, the −5/0 test, 1,000-game looks and 20,000-game cap. All N13/F5 LLR controls passed.

| Assumed true Elo | H0 | Inconclusive | H1 | Mean games | Median games |
|---:|---:|---:|---:|---:|---:|
| −5 | 17,649 (88.25%) | 1,780 (8.90%) | 571 (2.86%) | 9,795 | 9,000 |
| −2.5 | 6,670 (33.35%) | 6,536 (32.68%) | 6,794 (33.97%) | 13,621 | 14,000 |
| 0 | 613 (3.07%) | 1,843 (9.22%) | 17,544 (87.72%) | 9,831 | 8,000 |

At the quoted 3,400 games/h this specific implementation projects **2.89 h when level, 4.01 h at the midpoint, 5.88 h at the cap**. The roughly 8,458-game Wald estimate omits the actual look interval and overshoot. Gate wording remains: H1 permits the feeder, H0 or an unresolved cap triggers investigation. A modelled level feeder failed to qualify about 12% of the time; that is not evidence of a code fault on any specific run.

R1’s same public method, seed 202611230542, 20,000 paths per truth in table order, 500 pairs per look, at most 20 looks. The symmetrized base distribution is [0.0213333333,0.2455,0.4663333333,0.2455,0.0213333333]. Monte Carlo SE of the mean is about 38–42 games. All six archived matches summed to [95,1215,2429,1303,114]; an additional sensitivity run (seed 202611230543) gave 9,651 mean games, H1 88.44%, cap 8.54%, H0 3.03% when level. Reaching the original cap is itself a selection condition, so I treat both sets as historical shape proxies. Actual F2 planning must use the real look cadence: checking every completed pair and checking after every 1,000 games are different stopping rules. Source: `debate/evidence/fable_f2_deep_pair_tables.txt`.
