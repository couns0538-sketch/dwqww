# ABBA record and native adapter contract

`python scripts/summarize_abba.py RECORD.json` reads JSON/JSONL plus hash-bound nominated files, prints JSON and exits0/PASS,1/FAIL or2/INVALID. Python3.10+ stdlib only. It never launches a process, changes affinity or measures a live host. A report PASS is internal evidence consistency, not a self-authenticating speed claim.

Record schema1:

- `baseline`, `candidate`, `network`, `baseline_options`, `candidate_options`, `native_log`, `host_evidence`, `protocol`: references with `path` (relative forward-slash syntax, based on record parent) and exact `sha256`. Nominate authorized files only. Binary references must be the exact executed files, not another rebuild.
- `host`: nonempty `os`, `cpu_model`; nonnegative integer `logical_cpu`; integer `threads:1`; boolean `quiet_confirmed:true`. These are declared observations whose proof belongs in host_evidence/native logs, not claims established by this offline helper.
- `nodes`: nonempty ordered mapping from unique position/depth labels to positive expected integer node counts. Use the same order in the protocol and samples; each run must have exactly this suite once.
- `noise_gate`: finite nonnegative `max_median_deviation_pct` and `max_range_pct`, chosen before measurement. Range is `100*(max_ratio/min_ratio-1)`, not a confidence interval.
- `calibration`: `binary_sha256` equal to baseline's hash, plus a `samples` reference. Both A/B labels must actually execute that same baseline; review original commands.
- `comparison`: `samples` reference.

The hashed `protocol` is a JSON object containing matching `nodes`, `noise_gate`, `logical_cpu`, `threads:1`, `order:"ABBA"` and integer `minimum_blocks>=10`. It also contains matching `baseline_sha256`, `candidate_sha256`, `network_sha256`, `baseline_options_sha256` and `candidate_options_sha256`. Its filesystem/crew publication history establishes preregistration; merely hashing a plan after a run does not prove it was declared beforehand.

Each samples file is JSONL. Rows are block0/run0/suite positions, block0/run1/suite positions, then run2, run3, block1 etc. `arm` must be A,B,B,A for run0..3. Every row contains the following timing fields plus `binary_sha256`, `network_sha256`, `options_sha256` and `protocol_sha256`:

```json
{"block":0,"run":0,"arm":"A","position":"startpos-d13","nodes":123,"start_ns":1000000000,"end_ns":1010000000,"wall_ns":10000000,"logical_cpu":2,"threads":1}
```

Sample identities must bind the actual executed files, effective accepted options and hashed protocol. In calibration, both A/B labels use baseline binary/options and the frozen network. In comparison, A uses baseline binary/options and B uses candidate binary/options; both use the frozen network. Merely updating a record's binary hash while retaining old samples cannot pass. The adapter must capture these identities during execution; this is consistency checking, not cryptographic authentication of a command having run.

The values above are syntax examples, **not Forge pins or measured NPS**. Actual node pins come from the current lock contract. External start/end timestamps are nonnegative integers from one monotonic clock domain across the entire experiment, including A/A then A/B. `wall_ns` must equal end-start and be positive. Intervals must not overlap. The comparison must begin after all calibration samples ended. Do not reset each process's timestamp origin in the adapter.

Every node count must equal its explicit pin. Boolean counts, wrong order, partial suites/blocks, mismatched cores/threads and hash changes fail. All blocks are retained; one missing sample prevents qualification. The helper reports each block's four NPS values and geometric B/A ratio plus median, inclusive quartiles/IQR, min/max, range and block count. It performs no outlier trimming, no Elo calculation and no claim of statistical significance.

Original native transcripts, finite timeout/error receipts, warmup metadata, accepted options, same-binary AA identity, clock frequency/units, affinity measurements and process/thermal observations remain necessary for independent review. Test the adapter with deliberate node mismatch and incomplete output before any real timing run.

Protocol and sample files are limited to 32 MiB each. Their exact parsed bytes are hashed against the pinned references, with file identity checked across the read. Initial/final hashes alone are insufficient against transient rewrite-and-restore substitution.
