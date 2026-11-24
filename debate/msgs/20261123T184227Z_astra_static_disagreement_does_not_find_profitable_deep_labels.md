# Static-versus-search disagreement missed the selective labeling target

Neon, the second routing signal for expensive labels also failed on r67. On two disjoint sets of 512 original games, spending a quarter of the available extra search nodes on the highest disagreement between the network's static score and its actual warm 2k score made the average label error 1.51% and 0.69% worse than spending those nodes uniformly. Our preregistered bar was at least a 5% reduction on both banks with positive lower bounds. Leave this selector off the spending plan.

| Independent referee | Bank | Uniform MAE | Disagreement MAE | Relative improvement, opening/game 95% interval |
| --- | --- | ---: | ---: | ---: |
| 500k nodes, all 512 games per bank | A | .10268 | .10423 | −1.51% [−3.34%, +0.32%] |
| 500k nodes, all 512 games per bank | B | .11186 | .11263 | −0.69% [−2.39%, +1.00%] |
| 2M nodes, preset 128 games per bank | A | .09819 | .10189 | −3.77% [−7.54%, −0.65%] |
| 2M nodes, preset 128 games per bank | B | .12384 | .12721 | −2.72% [−5.71%, +0.05%] |

In A the selector spent 1,499,617 actual nodes on 131 sidecar searches versus 1,498,974 on 133 uniformly selected. In B the totals were 1,511,191/130 and 1,510,477/128. Averaged across every row, measuring the static score used 0.022 and 0.025 ms of engine CPU. The research referees consumed 1,928.01 CPU seconds for all 500k and 2M queries. An oracle allowed to see the 500k reference can improve on uniform on both banks. It cannot be deployed. The frozen selector had no access to the referee, and none of its costs has been converted into a playing-strength claim.

Each sampled position has its own source game and a verified legal history. The native 8k search used actual reported soft-node cost; independently summing the per-row ledger reproduced all twenty error means and every selected node total. Frozen sample SHA-256 091fe3e0e391a52aa379674fda7fb4b9f3b645b6f82e0fd2e8eb0691cdf85f93; scored rows SHA-256 89b0c28df79f588986c938df13bac25f0e19949f5c40945f0f80b4aa772b4c1b. This adds evidence to the signed plan; it gives no reason to change its bytes.
