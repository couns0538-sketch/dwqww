# Job 23 prediction

All runs use A-kF, PC20, the pinned net768, Threads 1 and Hash 16.

| Run | Workload | Assert stops | ASan or UBSan report blocks |
| --- | --- | ---: | ---: |
| R1 | All 2,000 P rows, depth 9 | 0–1 | 0 |
| R2 | Ten highest-discovery P starts, self-play at softnodes 2000 | 0–1 | 0 |

I expect zero in all four cells. The known-answer rows kept their search
results, and the direct-only control established that a discovery can
reach A1. The expanded fixture deliberately concentrates rare quiet
moves, so I allow one assertion stop in each workload. The prior clean
AU run used the same underlying kF and options.
