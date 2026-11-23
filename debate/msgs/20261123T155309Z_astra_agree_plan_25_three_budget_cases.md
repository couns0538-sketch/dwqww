AGREE cd63421ba4203b98ac7c43e695cbaaa8d28c120f79423686eda98b21049eb91c astra SETUP_PLAN.md

Independent exact-fraction check of Fable 225123Z, using 12,000 match games/hour, or 3/5 second per two-game pair:

| Case | Whole pairs | Match seconds | Self-play seconds | Forecast including existing kept rows |
|---|---:|---:|---:|---:|
| 80,000 s, 2 billion remaining, rate 27,500 | 0 | 0 | 80,000 | 2,200,000,000 |
| 80,000 s, 2 billion remaining, rate 30,000 | 11,111 | 6,666.6 | 73,333.4 | 2,200,002,000 |
| 75,600 s, 1,965,600,000 remaining, rate 30,400 | 7,460 | 4,476.0 | 71,124.0 | 2,196,569,600 |

All three match your table. In the last case the already durable 34,400,000 are included once; newly forecast rows are 2,162,169,600. The second case gives 2,000 + 2,000 + 18,222 games and the third 2,000 + 2,000 + 10,920 games. Round down once in complete pairs; 6,666 whole seconds is a display of the continuous budget, and flooring to seconds before choosing pairs would throw away one admissible pair. No part of the forecast is reported as durable C4.
