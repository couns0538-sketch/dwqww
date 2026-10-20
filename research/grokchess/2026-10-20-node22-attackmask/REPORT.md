# GrokChess v1.7.50 guarded-slider-attack candidate, Node22, 2026-10-20

**Disposition: correctness PASS on tested fixtures; speed INCONCLUSIVE; strength NOT TESTED. Do not merge the candidate as an accepted performance improvement.**

Baseline: recovered GrokChess v1.7.50 compiled JS, Node 22.16.0 on Linux AMD EPYC, CPU2 affinity. The baseline and candidate compiled-JS sources and raw logs are preserved in the conversation artifact forge-grokchess-hourly-20261020-0405-checkpoint.zip (SHA-256 a0eed623aff29f4b7b7400b13956d21e0fbbd80bb0c8da9a71c17ab853f384ca). This report/diff alone are NOT a full source distribution.

Hypothesis: Board.isAttacked can skip bishop/rook magic lookups when attacking side has no bishop-or-queen or rook-or-queen. One small patch; no search, NNUE, or pruning changes. Code diff is in attackmask.diff beside this report.

## Fresh verification

- Original and candidate: official movegen **36/36 each**, full perft **25/25 each**.
- Randomized differential: **259200 identical attack queries** across **2025 legal random-walk positions**.
- Official d9 benchmark: six per-position nodes and best moves identical, total **219323**.
- Official d10 benchmark: six per-position nodes and best moves identical, total **286029**.
- Explicit UCI comparison at d10: six final scores (types and values), depths, PVs, node counts, and best moves identical.
- Twenty timed official d10 launches independently verified nodes and best moves.

## Exploratory speed

Ten counterbalanced A/B and B/A pairs (fresh processes) showed candidate median **+0.779%** and geometric mean **+2.578%** speed, but the first pair gave a +38.7% cold-start/noise outlier. Four baseline/baseline controls showed median absolute drift **5.46%** and maximum **10.18%**. The apparent benefit is smaller than noise. **No reliable speed improvement or Elo gain is claimed.**

## Next

Repeat on a quiet Windows/Node20 system with A/A controls; if strong timing evidence emerges, port to authoritative TypeScript and regenerate JS. Current checkpoint contains compiled JS only and must not be released as authoritative TS source. Continue Sol's isolated Forge SMP-TT race investigation without merging speculative engine changes.

Github state at run start: Forge 6.4 head d2d8dfe4fe9df20697f993bf44dea0f65e57ba39 added UCI timeout-diagnostic-only regression patches, reportedly 11/11 synthetic tests and 8/8 mock trials but NO new native match or Elo verdict. Hosted NNUE SPRT is in progress, PR #6 remains broad (34 commits and 1067 files).

No engine production code was modified on this research branch.