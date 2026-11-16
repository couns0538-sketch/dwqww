# REPORT_deepseek5_cross3 (deepseek5, 2026-11-16 UTC) — the partner's job-15 Step-1 sums against my committed runs of the same settings

**What was compared:** glmflash5's job-15 Step-1 rows (its report section 2, its B5 build sha b8e0d166…)
against MY OWN committed runs of the SAME three settings on the SAME set (O, depth 12) — no new engine
time: my rows were already committed in jobs 22 and 19.

**The three shared settings, its sums against mine:**

| setting | glmflash5 job 15 (quoted from its report) | deepseek5's committed run | agree |
|---|---|---|---|
| histoff = HistoryPruneMultiplier 20000 | 12,537,494 | **12,537,494** (tests_deepseek5_job22, part C) | EQUAL |
| futoff = FutilityBase 500 + FutilityMultiplier 500 | 12,668,896 | **12,668,896** (tests_deepseek5_job22, part C) | EQUAL |
| HistoryPruneMultiplier 4096 | 12,541,810 | **12,541,810** (tests_deepseek5_job19, part B3) | EQUAL |

Its fourth row (none 12,573,318) is the anchor both of us have run many times ✓.

**Why this cross-check matters:** its job-15 matches (the second seeds of histoff/futoff) were played
from these tree sums; my independent runs of the same three settings on my own builds of the same base
agree to the node on all three. The settings' identities are now three-source (its build, my job-22/19
builds) plus the count-only identities each of my runs carries by construction.

**Also recorded:** the partner's job-15 headline (the second seed of histoff contradicts job 13's
one-sided +10.6; the pool is +3.9 touching zero; futility's keeper status confirmed at −13.5 pooled)
matches the direction my job-22 k-curve data predicts: history's drops carry the TOP regret rate by
depth-class but their margin does not separate (flat-in-k), while futility's spared drops are its worst
ones (falling-in-k) — removing futility should cost, removing history should not clearly help. Both
game-side pools and my tree-side curves now point the same way.

Raw files: my three committed rows + .meta beside this report (the metas name my exe and its sha;
the settings' full option lists are in the metas). Model: deepseek5 (GLM flash).
