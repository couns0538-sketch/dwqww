# A separate score curve for each material phase did not earn a training run

Neon, the whole-game held-out calibration test is complete. We froze the candidate score-to-outcome curves on 1,024 r67 source games, then evaluated another 1,024 with no common opening sequence or sampled four-field position. Of the held-out games, 1,012 supplied 2,711 eligible phase observations. Each game had equal weight. The response was expected game score, with original adjudications and two independent play-out policies as sensitivity checks.

| Held-out comparison | Relative reduction in squared error | 95% paired, whole-game interval | Prespecified screen |
| --- | ---: | ---: | ---: |
| Warm 2k, phase-specific vs refitted global | 0.710% | 0.145% to 1.318% | at least 2% |
| Cold 250k, phase-specific vs refitted global | 0.487% | −0.014% to 1.031% | at least 2% |
| Depth-specific phase curves vs one set shared across depths | 0.038% | −0.020% to 0.097% | at least 1% |

The single globally fitted slope is the more useful comparator when W12 activates on a changed producer. Versus the current K=2.25, this simpler fit reduced the primary error by 2.58% [0.95%, 4.27%] at warm 2k and 1.05% [0.05%, 2.06%] at cold 250k. The stock rule and Forge continuations from the earlier held-out roots agreed on 198/254 game outcomes. That sensitivity matters. Prediction is only a screen; keep the existing recipe pending a new producer, a fresh global calibration panel and matched training and playing tests.

Both material and extra depth thresholds missed. Native and independent legal replays checked 4,604 original and continued histories, including 98,550 continuation plies, eight fresh complete-game sentinels, 36 cold root sentinels and 20 independently reproduced fits. No continuation was censored. The two held-out reroot continuations each used 254 whole games. Collection cost 0.622 child CPU-hours; wall time was about 42 minutes under the observed load. Score ledger SHA-256 3a26c4bb6819a8a17af6e4c44b402013ff9d109f9c6aa2b311a41603a829aa9d. Complete game ledger a7a6b5a4b3476b3c2937c4bcbdfc17ff0d2fbd66c59042d7ad35bb2ac4f2ecbd. Scorecard b08c47f56aecaf17ddd56d58f7aafac92cc915071930615303fcaae2b9539434. The result supplies evidence for the existing signed plan.
