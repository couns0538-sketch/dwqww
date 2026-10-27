# IDEA_SOURCE — C5 output buckets by piece count (UCI NNUEOutputBuckets + NNUEFile)

Ideas only. No code was copied from any engine or trainer; the engine output-row selection, the v2 output field,
the trainer heads, the export, the selection and fail-loud rules, the parity checks and the tests are written from
scratch for Forge on top of C4's v2 format. Every constant (default map, maximum 16 heads, field layout) is our own
choice.

| idea | public source (concept) | what we took | what is ours |
|---|---|---|---|
| Output buckets: several output heads (rows of the last layer) selected by the amount of material on the board | bullet trainer, output buckets (`MaterialCount` output buckets in the examples and docs): https://github.com/jw1912/bullet , docs https://github.com/jw1912/bullet/blob/main/docs/0-contents.md ; Chess Programming Wiki, NNUE: https://www.chessprogramming.org/NNUE | the concept: the head is chosen by the piece count of the evaluated position | 33-entry map `output_bucket_map[popcount(occupied)]` (kings included) stored in the v2 header, so any map is possible; default map n = pieces - 2 non-king pieces -> min(N - 1, n * N / 32) (8 heads: (pieces - 2) / 4); 1-16 heads; head-major `w2[OB][2H]`, `b2[OB]` |
| Layer stacks / PSQT buckets selected by piece count | Stockfish NNUE architecture as described in `official-stockfish/nnue-pytorch` docs/nnue.md (layer stacks and PSQT buckets chosen by piece count): https://github.com/official-stockfish/nnue-pytorch/blob/master/docs/nnue.md | the concept of choosing a sub-network by piece count | only the output layer is bucketed (Forge's net has no hidden layers after the accumulator); same SCReLU and float arithmetic as the compiled-in net |
| Forge's own earlier research | 5_nnue/research_buckets8_step1/ (Sol's buckets8 design, 8 duplicated output heads; listed as "research only" in 7_history/TRIED_REJECTED_UNPROVEN.md) | the observation that duplicated heads must reproduce the single-head net exactly (lock replicas) | runtime selection (no compile-time head count; the lock net stays compiled in, unchanged), our own default map (the earlier research used clamp((pieces - 1) >> 2, 0, 7)), trainer `--output-buckets/--output-map` with export into v2, combined king + output buckets |
| Fail loudly on an unusable net / output bucket request (C4 review fix, merged) | QA code review of opus-C4 (2026-10-27) | the requirements | the rule extended to NNUEOutputBuckets (`options::nnue_v2_problem`): a count that does not match the net, both counts 0 with a file, a count without a file -> ERROR and exit status 2 at isready / go / bench; hint naming the settings that select the loaded net |

Exactness argument (own, as C4): weights de-quantised as int16/4096; the head only selects which `w2`/`b2` row
enters the same 16-lane float sum, so a net whose heads are identical copies evaluates bit-for-bit like the
single-head net (checked with lock replicas: identical evaluations and node counts at every bench depth).
