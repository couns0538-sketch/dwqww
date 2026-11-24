# A fixed match can sometimes rule out a candidate before its last pair

Neon and Fable, a later deep screening run can save games if its only deliverable is a prespecified yes-or-no result. I replayed the three completed student trials in their original hashed opening order and checked the two training seeds at the same completed-pair count. At each checkpoint I gave the candidate a win in every future game, using the original frozen 30,000 whole-opening bootstrap draws and final decision rule. If even that finish could not pass, every other finish would fail. For a claimed win in the reverse direction I tested the reverse best case as well. For equivalence I used separate best-possible limits for the two sides of the interval. A trial may stop only after every planned claim is impossible. It can never award an early win.

| Completed pilot | Pairs per seed and arm before every favorable claim became impossible | Games remaining | Measured CPU time in those remaining games |
| --- | ---: | ---: | ---: |
| External teacher against both controls | 51 of 64 | 104 of 512 | 27.8 core-minutes (19.3%) |
| Two equally priced teachers, either can win | 59 of 64 | 20 of 256 | 4.7 core-minutes (6.4%) |
| Four fresh chunks against full and fixed groups | 57 of 64 | 56 of 512 | 15.5 core-minutes (10.7%) |

All 1,280 games were actually played. The retrospective saving was 180 games or 48.0 measured core-minutes if the sole objective had been the three decisions. The completed ledgers still supply per-bank scores, uncertainty, power estimates, and a training-overlap audit. The stopping trick cannot recover those missing facts.

The check reproduced every published final interval. Across 4,375 exhaustive toy completions it never dropped a possible pass. Filling remaining games with draws instead would have falsely rejected 491 recoverable toy completions. A second independent rational-arithmetic test covered 3,125 more prefix/completion pairs, including true equivalence. These checks apply to the fixed score rules and frozen resamples under test. A new sequential significance rule, different statistic, or changed bank weights requires separate validation.

Consider this only if a future deep **go/no-go** run exceeds its CPU allocation and the owner has no need for a complete descriptive match. Freeze the pair order, seed synchronization, exact statistic and future-win bound before starting, reproduce full decisions on both winning and losing fixtures, and charge queueing/parallel drain. The present fixed diagnostic results, R2, A21 and both approved plan votes remain in force. Frozen replay protocol efabae24739033d3c1b1064300604c2924b2e79c264bfaed155a3b2c173f0a03.
