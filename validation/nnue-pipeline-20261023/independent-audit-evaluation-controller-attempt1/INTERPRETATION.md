# Once-only independent audit of the publicly frozen network

The fixed candidate was publicly frozen as zero-initialized full-data epoch3 before any independent-audit model losses. Selection used only the original4,149-position set; this separate8,881-position audit was never used for training or candidate selection. Both the new shipped-only baseline and the one fixed-candidate comparison actually exited0; the controller tool45840 exited0. All original source, network, freeze/public-proof and data hashes remained unchanged.

| Evaluator | Pure teacher probability MSE |
| --- | ---: |
| HCE | 0.006741170688 |
| Shipped HCE + residual | 0.005970920200 |
| Frozen candidate HCE + residual | 0.005991080029 |

Candidate versus HCE: 11.127% lower loss,95% whole-game interval[5.858%,16.472%]. Candidate versus shipped: improvement -0.338% (negative means worse),95% interval[-5.783%,4.286%]. The candidate point is slightly worse than shipped and the interval includes zero: no teacher-loss improvement over the accepted network is demonstrated.

The2,000 paired whole-game bootstrap draws use seed20261023 and ratio(sum loss/sum rows). There are109 represented game clusters,111 assigned validation IDs and1,321 UNUSED train rows. Residual-term-only scores in the original report are diagnostic; the engine uses HCE plus residual. The original generic report cautions against selection on the same holdout; the attached freeze/publication protocol establishes that this audit was separate from selection.

These are teacher-loss results. They do not establish Elo or complete native-runtime qualification. No reselection, retraining, tuning, alternate candidate or audit retry occurred. Root owns separate native qualification, publication and any future equal-time strength test.
