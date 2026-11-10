# opus_finny_cache — REVIEW_LOG

Policy: AGENTS.md (`git show 3e900941:AGENTS.md`, md5 94169aefef79ccb69c21f8f2c86298f0) asks for one focused reviewer subagent per milestone. If none is available, the policy calls for a structured self-review that is not called independent.

| round | Vienna | reviewer | scope | result |
|---|---|---|---|---|
| SR1 | 20:25-20:35 | main session (Opus 5.5), **NOT independent**. The `fable` reviewer of this job became unreachable (`fable`/`opus-max` agent types disappeared from the session; the user's CLAUDE.md allows only those types, so no substitute was spawned) | branch at `4858ed5` + this round's corrections | 1 wording fix (below); verdict unchanged |

## SR1 checks
| check | evidence | result |
|---|---|---|
| the network really is king-independent | P `include/forge/nnue.hpp` `feature_index(perspective, piece, square)`: `(relative_color*6 + type)*64 + relative_square`, `relative_square = square` (White) or `square ^ 56` (Black). No king square, no bucket, no mirror | OK |
| every refresh site is accounted for | `git grep 'nnue::refresh(' 7ce10a05 -- src include`: exactly two sites, search.cpp:791 (`static_evaluate` fallback) and search.cpp:1613 (root of `Worker::search`). `Evaluator::evaluate_uncached` (eval.cpp:482) calls no NNUE refresh | OK |
| the fallback is unreachable inside a search | the root accumulator is refreshed at search start, and the walk-back stops at the first valid ancestor (at the latest the root) | OK, and confirmed by measurement: in-tree count 0 |
| the measurement measures trial_w6 | the scratch copy = P export + `rc_make.ps1` anchored edits only (`refresh_count_scratch_after_w6.patch`, 25 added lines, counters only); bench 16 = 3,024,920 = the pin, so the search was unchanged | OK |
| the exactness statement | SPEC §2 said "every partial sum is exact" without proof | **FIXED**: now states the bound \|sum\| < 2^12 and that it is not verified here (the verdict does not depend on it) |
| names reserved but unused | `git grep -E 'FORGE_NNUE_FINNY\|NnueFinnyCache'` on the branch: only in docs | OK |
| ownership claims | HalfKA (7f79c349) has `refresh` + `apply` and no cache; v3 (fable-nnue-arch) has `refresh_from_pieces` keyed (perspective, bucket, flip) | OK |
