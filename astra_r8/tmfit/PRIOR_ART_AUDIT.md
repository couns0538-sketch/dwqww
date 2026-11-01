# Time-management prior-art audit — UNPROVEN

Source base: `905e2325caeabea92b1017b22b434218a43145a7`, the authorized
`forge-bundle-int` parent fallback. Native bench identity must independently
establish its relationship to the FD3A5190 binary lock.

Read `src/search/timeman.hpp`, `src/search/iterative.inc`, and the `Tm*`
declarations/defaults/registry on this base. The lock composes stability,
cumulative root-node effort, score fall, and minimum-factor rules. Its soft
allocation and hard cap are left intact.

Read `9459238d:include/forge/timeman.hpp` (TimeManV2). That experiment uses
hand-set scaling plus a node budget, next-iteration prediction, in-search soft
stopping, and adaptive hard-deadline clock-read intervals. TmFitModel adds none
of those search-stop or node-check mechanisms. It learns a logistic model of
later completed-iteration move disagreement and applies its calibrated
probability mapping only to the existing iteration-boundary soft target.

Discovery commands:

```text
git log --all --oneline -- '*timeman*' '*timepack*'
git grep -n 'Tm[A-Z]' -- src include
git log --all --oneline --grep='timepack\|TimePack\|TimeManV2\|tmdiv18\|omni_tm\|TmOppClock\|TmScoreLoss'
```

A further case-insensitive `git grep` of `src`, `include`, and `tools` on the
locally available main/astra/fable/bundle refs found no implementations named
timepack 1–4, tmdiv18, omni_tm, TmOppClock, or TmScoreLoss. Their existence and
hand-set-factor character are given by the task; the absent source was not
silently treated as reviewed. Source-level comparison with those variants
was initially a review limitation. Couns subsequently confirmed these are off-repo
crew patches and directed comparison using their descriptions in IDEA_SOURCE.md;
no further source discovery is required. All use fixed hand-tuned factors.

All new inference, logging, and tests are original. The sigmoid table is
generated from the mathematical logistic formula, not another engine's tuned
constants. No GPL/AGPL source or tuned constants were copied, translated, or
paraphrased.
