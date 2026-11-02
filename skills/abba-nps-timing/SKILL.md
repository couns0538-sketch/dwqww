---
name: abba-nps-timing
description: Use when measuring a Forge candidate's NPS at identical search work, reviewing small speed claims, checking ABBA timing logs, or preparing a native quiet-core baseline-versus-candidate performance comparison after correctness and exact-evaluation gates.
---

# ABBA NPS Timing

Measure matched work on **one quiet logical CPU, Threads=1**, sequentially. Use `grok-pc-safe-run` on that PC. Do not start timing before required exact-evaluation and lock gates pass. Linux or Wine results do not certify native Windows Ryzen speed.

1. Freeze both source/net/binary identities and options, position/depth suite, expected node counts, hash size, warmup/lifecycle, selected core, affinity, compiler/ISA, OS/CPU and power conditions. Same-depth node differences invalidate an exact-work comparison. No competing benchmarks, compilers, self-play or training on the assigned resources; do not stop or alter other people's jobs to create quietness.
2. Predeclare a protocol including **at least10 complete ABBA blocks**, position order and A/A median/range tolerances before observing outcomes. Record real affinity/T1 verification and an observed quietness check. Missing or unreadable host evidence is UNVERIFIED; wait for an authorized quiet slot rather than infer quietness.
3. Warm up consistently, then collect at least10 **same-binary A/A ABBA** blocks with A and B labels both running the baseline. If its preregistered noise gate fails, preserve the logs and stop the comparison. Do not loosen limits after seeing results or explain away host noise with a favorable ratio.
4. Run at least10 candidate comparison blocks in A-B-B-A order. Each letter is one complete position suite using the same documented process/cache lifecycle. Bind every sample to the actual arm binary/net/options/protocol hashes and record external monotonic start/end timestamps, wall time, nodes, CPU and threads for every position. Parse the actual engine output through a tested adapter; no invented UCI benchmark syntax. Check exit codes, expected nodes and completed runs immediately. Keep failed/incomplete blocks; do not silently discard them.
5. Summarize each block by four suite NPS values `sum(nodes)/sum(wall_seconds)`; calculate `sqrt(B1*B2/(A1*A2))`. Report median block ratio, percentage change, quartiles/IQR and full min/max plus every block ratio. Ratios above1 favor candidate. These dispersion measures are not confidence intervals. Avoid averaging ratios from unmatched positions or cherry-picking the best run.

PowerShell, using the frozen record in [record-format.md](record-format.md):

```powershell
python "$SkillDir\scripts\summarize_abba.py" "$RunDir\abba-record.json"
if ($LASTEXITCODE -ne 0) { throw 'Timing evidence is incomplete, inconsistent or failed calibration.' }
```

The helper is read-only and computes statistics from recorded data; native execution, quietness and affiliation with the real binaries still require original log/adapter review. State platform and uncertainty. Report a verified sub-threshold gain honestly; apply the current crew's adoption threshold rather than invent one. NPS, fixed-node cost or a short screen does not prove equal-time Elo. Retain all raw runs, protocol hash, host observations and the exact next action.

## R10 reviewed native adapter

The branch's astra_r10/job1/timing/ contains the reviewed native Windows adapter,
fixed 10-block A/A then 10-block ABBA protocol, external-wall geometric block
statistics, immutable protocol/input binding and native topology checks. Use its
PROTOCOL.md and actual frozen protocol.json; the template is intentionally not
executable. Root RESULTS.md records focused reviews and native/fixture scope.
Calibration defaults for this R10 task are abs median<=0.5%, IQR<=1 percentage
point, every eligible block within +/-2%. Do not generalize or relax these after
observing results. Original read-only summary helper remains available unchanged.
