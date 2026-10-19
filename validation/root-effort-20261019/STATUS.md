# Stable root effort: actual parent bug reproduced, candidate pending tests

6.4.8 isolated on forge/root-effort-20261019, preserving6.4.7 source2c0c7ef and
all earlier code. Accepted integration remains9108d012. The hosted39325939081
job tests only6.4.7 versus6.4.4; no result transfers to this time-management fix.

Actual frozen6.4.7 instrumented search, with four fixed-depth FENs and exact
untouched-driver PV/score/node parity, reconstructs every cumulative ordinal bucket.
Middlegame depth7 selectedc3d5 bucket contains1355nodes from4differentmoves;
c3d5 itself used601 of3355nodes. Offline source effort-factor arithmetic differs
1.146125 vs1.370864;7of8 depth6/7 samples differ after clamps. These are actual
counters and arithmetic, not evidence of a changed timed stop or Elo.

Candidate preserves cumulative child deltas/aspiration retries/local-node denominator,
constants/pruning/order/NNUE. Initialize canonical legal root Move identities once,
then account and select by full Move equality. Fixed256keys add1KB/Worker; lookup
is root-only, and release writes are bounds-guarded. Superseded vector/v1patches
and all original tests/logs remain in the preparation archive.

Next: fresh complete Release and ASan/UBSan builds, all8 suites, exact untimed
parent cold/warm parity, actual candidate traced totals compared with independent
per-Move child-event sums at every completed iteration, Windows functional/signature
checks. Time-managed stopping intentionally may change; strength/performance and
actual deadline safety remain separately required before promotion.
