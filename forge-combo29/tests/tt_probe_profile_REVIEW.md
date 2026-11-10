# TT replacement-score profiling follow-up

**Source-only investigation; no production patch, speed result or acceptance.**

## Finding

GCC 14 does remove the redundant entry 0-versus-itself comparison and initially
computes the first two candidate scores only once. It does **not** retain the
selected best score across the following comparisons. The pristine production
binary reloads the chosen entry's depth/generation and recalculates its score
when occupied entries 2 and 3 are evaluated.

This is real residual work, but a narrow part of the probe workload. A guarded
best-score-reuse experiment is justified for further inspection; these results
do not justify promotion or treating all TT probe self-time as recoverable.

## Production-code evidence

The disassembly is from the byte-verified, **uninstrumented** immutable lock:
SHA-256 `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
It is not the counter-instrumented binary and not the earlier `-pg` binary.
Both public-lock and owned probe bodies are preserved in
`tt_probe_profile_disassembly.txt`. The measured bench uses owned
`probe_body<false>` at `0x305d0`:

- `0x30644..0x30662`: compute entry 0 score.
- `0x30674..0x3068e`: compute entry 1 score.
- `0x30696..0x30699`: compare and select a best pointer in rax.
- `0x306ab` and `0x306c2`: reload selected-best generation and depth from rax;
  `0x306d2..0x306e0` rebuild its depth/age score before comparing entry 2.
- `0x30718` and `0x30735`: reload selected-best generation and depth from rbx;
  `0x30728..0x30741` rebuild its score before comparing entry 3.

The first-pair caching is therefore partial. A source-level rewrite must still
be inspected after compilation: additional conditional moves/register pressure
or effects on common empty-slot paths could offset the removed work.

## Measured path distribution

Built-in bench, Threads 1, its existing 16 MB hash, eight positions and a cleared
TT for each position. Counts are aggregate per process, not timing estimates.

| NNUE | Depth | Probe calls | Hits | Empty-slot misses | Full replacements |
|---|---:|---:|---:|---:|---:|
| on |16|3,021,035|1,082,705 (35.839%)|1,932,156 (63.957%)|6,174 (0.204%)|
| on |18|6,058,697|2,166,978 (35.766%)|3,774,493 (62.299%)|117,226 (1.935%)|
| off |16|2,446,113|745,943 (30.495%)|1,689,638 (69.074%)|10,532 (0.431%)|
| off |18|6,121,437|2,301,306 (37.594%)|3,670,655 (59.964%)|149,476 (2.442%)|

The redundant best-score recomputation also occurs on some misses that later
find an empty fourth slot. Thus full-replacement counts alone understate it.
Counting the occupied third plus occupied fourth slot yields:

| NNUE | Depth | Occupied third slot | Redundant best-score evaluations | Per probe |
|---|---:|---:|---:|---:|
| on |16|32,309|38,483|0.0127|
| on |18|330,276|447,502|0.0739|
| off |16|42,260|52,792|0.0216|
| off |18|387,729|537,205|0.0878|

At depth 18, the third occupied slot is reached by only 5.451%/6.334% of all
probes (NNUE on/off). About 94% of probes do not reach even the first redundant
recomputation. These are dynamic operation counts derived from the observed
pristine instructions and counted control-flow paths, not measured cycle cost.
The earlier 5.7–8.3% TT self-sample attribution includes all probe paths.

## Node and source integrity

Instrumentation preserved exact node signatures against the immutable binary:

- NNUE on: depth 16 **3,024,920**; depth 18 **6,066,072**.
- NNUE off: depth 16 **2,448,617**; depth 18 **6,134,776**.

Depth18 total probe counts also match the independent earlier gprof entry
counts exactly (6,058,697 and 6,121,437).

The recipe uses `git archive 16833ecc03b425586f91f4c8834dea8807bf4c22 --
forge-combo29/src forge-combo29/include`, verifies all 20 pristine source/include
blobs, then modifies only the isolated snapshot's search.cpp to add thread-local
path counters. No Windows trees, bundled executables or archives are fetched.
Production files are untouched. Original/instrumented source hashes, compiler
command, executable hashes, all slot-level counts and raw outputs are recorded
in `tt_probe_profile_results.json`.

All counter invariants passed: calls=hits+misses;
misses=empty-slot returns+full replacements; occupied fourth slot=full
replacements; earlier empty-slot exits account for each occupied-scan count.
No shared-lock probe was executed by this T1 bench. It does not measure SMP.

## Narrow experiment proposal, not implementation

Retain the complete hit loop and generation-refresh behavior. After a miss,
return immediately if slot 0 is empty. Otherwise initialize its depth/age score
once, scan slots 1–3, keep each existing empty-slot return, and update both the
best pointer and cached score only on strict `<`. This preserves first-slot tie
selection and the opaque replacement destination. Entry contents are stable
inside the current striped lock or exclusive lease.

Use a new default-zero switch and preserve the exact original branches in both
NOTLS implementations. Before considering promotion: inspect candidate assembly,
verify immutable-lock byte identity with the switch off, exercise TT ties,
empty-slot ordering, age wrap, hit-generation refresh and stale handles, then
run pins/equivalence. Measure cost on a controlled native workload separately;
these source/counter findings are not a speed result.

## Reproduce

```sh
python3 forge-combo29/tests/tt_probe_profile_run.py \
  --output /workspace/shared/forge-build/tt-probe-profile-reproduction \
  --baseline /workspace/shared/forge-build/baseline
```

The baseline hash is checked before and after. Builds use GCC 14, O3, strict FP,
x86-64-v4 and the lock's speed switches, without `-pg`. Counting alters generated
code and timing; only path counts and unchanged search work are interpreted.
All four runs are bounded, deterministic T1 workloads, not a broad position
sample or proof of benefit at other TT sizes/depths/native compilers.
