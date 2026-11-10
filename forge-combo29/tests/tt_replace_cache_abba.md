# TT cache coordinated ABBA diagnostic

Command: `python3 forge-combo29/tests/tt_replace_cache_abba.py`.
Frozen source candidate 2da9593; binary provenance/build commands in
`tt_replace_cache_receipt.json`. A is the exact immutable-lock binary, B enables
only FORGE_SPD_TT_REPLACE_CACHE. Full pre/post binary hashes, all input/output,
wall times and node counts are retained in `tt_replace_cache_abba.json`.

Parent coordinated a quiet window: other known workers held CPU-intensive
work. Both engine processes inherited affinity to allowed CPU0. Each mode had
one untimed warmup for each binary, followed by three ABBA cycles (12 measured
fresh processes per mode). UCI explicitly set Threads1, Hash16, OwnBookfalse,
UseNNUE true/false. Measured wall time includes process startup, bench16 and
exit; it is not isolated TT latency. Every measured node count matched the
immutable signature: NNUE on3024920, off2448617. Hashes matched after timing.

Observed mean wall seconds and candidate/baseline ratio:

- NNUE on: A1.929805, B1.905387, B/A0.987347.
  Three cycle ratios:0.965727,0.982397,1.014227.
- NNUE off: A1.315601, B1.350983, B/A1.026894.
  Three cycle ratios:1.036684,1.017073,1.026843.

Results are mixed: the on-mode cycles cross parity; every off-mode cycle took
longer for B. This small cloud diagnostic does not establish a general gain,
and does not justify promotion. Source/assembly evidence shows cached score
arithmetic but additional saved registers after the first occupied slot. That
is a plausible cost, not a measured causal attribution. CPU isolation from
unrelated host work, clock stability, hardware counters and native target
representativeness were not established. No speed/Elo acceptance claim is made.
