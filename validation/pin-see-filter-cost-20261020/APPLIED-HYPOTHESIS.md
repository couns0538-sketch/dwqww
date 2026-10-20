# Applied 6.4.16 mask candidate

Parent is isolated6.4.15 source8d303e4, fully tested and preserved through
checkpoint886ca51. Apply exactly the independently reviewed and archived
mask-board.cpp prototype, with version labels only. Production tests, search,
evaluation, NNUE arithmetic/network and all thresholds stay unchanged.

Hypothesis: computing forbidden recapture origins once per exchange avoids
repeated own-king attack queries while retaining the corrected pin-aware SEE.
Eight actual bench11 positions preserve every score/move/PV/node count and
the total385792nodes. The316-case API output is byte-identical to15, including
two unchanged inherited promotion-recapture limitations. A diagnostic shadow
also matches3614complete masks against the original helper.

On those eight searches, full own-king queries371702->0 and occupied slider
queries742109->0, replaced by474626empty-board lookups and49015between-path
classifications. Each non-slider test371702->237313. This is operation-count
evidence, not a calibrated speed/NPS/Elo result. Full clean native sanitizer
profiles and Windows gates are still required for this production candidate.

Retain the frozen unlaunched15strength package and its unused openings. No
strength outcome exists to influence selection of16. A separate fresh16vs14
protocol will measure the combined pin-correctness/filter implementation;
it cannot isolate each component's Elo contribution. Prior14bench timeout
and hosted baseline forfeit remain unexplained. No integration acceptance.
