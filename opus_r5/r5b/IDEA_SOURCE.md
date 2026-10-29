# R5B idea sources

R5B builds and measures existing node-exact switches; the ideas below are where each piece comes from.

| idea | source |
|---|---|
| N2 = one build with `-DFORGE_NNUE_O2=1 -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_SPEEDSTACK=1` | job spec R5B (Engine QA for Couns, 2026-10-29), plan N2; the switches come from opus-O2 (`opus_round1/O2`), S14 zero-fill / buffix (`fable-review-buffix`) and S29 (`opus_round1/sol_S29`), merged in `forge-bundle-int` b7c1772 (BUNDLES.md) |
| Paired ABBA NPS A/B with fresh processes, node match per pair, A/A control | the CI method in `opus_r3/R3-2Q/ci_quietnps.sh` and `opus_round1/sol_S29/nps_ab.py` (crew tools); standard paired-difference benchmarking (e.g. Fishtest's `speedtest`/`bench` comparisons in the Stockfish project, https://github.com/official-stockfish/fishtest) — my own Windows implementation |
