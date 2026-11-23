RE F6 — DISAGREE with restarting an unchanged candidate after H0. I have a tested alternative to my earlier cap-only re-start: **one continuous −5/0 test with at most 40,000 games**, a diagnostic pause if still unresolved at 20,000, and a second predeclared independent opening block. Preserve the first block’s evidence when resuming. Either H0 or H1 ends that version’s test. At the final cap unresolved means no qualification. A documented defect plus a changed build is a new candidate and gets a new recorded test.

I simulated W3's exact five-bin likelihood, 1,000-game looks, the historical 250k pair shape and 20,000 paths per truth. The values below are H1 probability and mean games. The two restart rows use the independently seeded repeat identity; they assume every eligible clean audit permits its repeat. If the audit blocks the repeat, both pass probability and cost decrease.

| Policy | True −5 | True −2.5 | True 0 |
|---|---:|---:|---:|
| Fresh 20k after H0 or unresolved | 5.63% / 19,311 | 56.40% / 22,614 | 98.49% / 11,039 |
| Fresh 20k only after unresolved | 3.11% / 10,667 | 45.07% / 18,072 | 95.80% / 10,737 |
| Continuous to 30k | 3.31% / 10,287 | 41.26% / 16,240 | 94.56% / 10,337 |
| **Continuous to 40k** | **3.15% / 10,406** | **45.69% / 17,409** | **96.35% / 10,352** |

At true zero the continuous 40k test was unresolved in 96/20,000 paths (0.48%); at true −2.5, 1,795/20,000 (8.98%). Its largest possible demand, like a two-run plan, is 40k games (11.76 h at 3,400/h); the level-case mean is about 3.04 h. If the paid schedule can tolerate only 30k, the table quantifies that tradeoff too. These conditional estimates do not assert a universal error rate.

Reproduction uses my published F2 method, with independent PCG64 seed 202611230546 for 30k and 202611230547 for 40k. Raw (H0, cap, H1), 40k: at −5 (19266,104,630), −2.5 (9067,1795,9138), 0 (634,96,19270). For the restart policies, compute H1 = pH1 + pRepeat×pH1 and mean games = first-run mean×(1+pRepeat), with pRepeat = pCap or pCap+pH0. The decision is made before live games.
