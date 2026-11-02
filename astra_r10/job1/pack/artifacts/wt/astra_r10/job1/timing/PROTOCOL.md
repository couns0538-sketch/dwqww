# R10 ABBA protocol - UNPROVEN

This is the protocol specification, not an executed timing result. Before execution,
fill a NEW copy of protocol.template.json with actual build/input/prerequisite hashes,
review it, and commit/push it. The template deliberately cannot run as supplied.
No engine timing before all seven native prerequisite rows PASS for the actual
production candidate: identical pc1/pc2 builds, exact OFF/ON pins, perft, T1 smoke,
ASan+UBSan, raw-bit pinned-fens12k parity and detected one-weight negative control.
T4 status remains explicitly disclosed in the overall proof packet.

## Fixed experiment

- A is the FD3A5190 lock. During calibration both A and B labels execute that same
  binary with identical default OFF options. During comparison B is the exact new
  kit binary with NNUEWideOutput=true. Both arms use Threads=1, Hash=16, OwnBook=false.
- One engine at a time, Idle, logical CPU2. Controller uses sibling CPU3, also Idle.
  Actual affinity and priority are checked before and after each measured run.
  UCI advertises Threads default1; the adapter sends Threads1 and awaits readyok.
  OS thread count is reported separately; it is not relabeled as search workers.
- Each arm starts a fresh process, completes one d20 warmup and then one measured
  d20 bench. Both must return 12,389,307 nodes. Hash/cache lifecycle is identical.
  External perf_counter_ns brackets the measured send/wait; reported engine NPS is
  preserved but is never used in the ratio. Startup and warmup are untimed.
- Before each whole block, sample CPUs2/3 for three seconds; both must be <20%.
  For every measured arm require process CPU/wall>=0.95 and sibling utilization<30%.
  Windows system CPU includes interrupts/DPC, counted once. Missing telemetry fails.
- Collect exactly ten eligible A-B-B-A calibration blocks. Median gain must lie
  within +/-0.5%, inclusive IQR<=1 percentage point, and every eligible block within
  +/-2%. Calibration failure ends the experiment before candidate comparison.
- After calibration passes, collect exactly ten eligible candidate A-B-B-A blocks.
  Both phases are capped at 80 attempts; the entire experiment has a 60-minute
  deadline after preflight. Normal child shutdown/owned-child cleanup may finish
  after the deadline; no new timed work starts then.
- Eligibility uses only fixed telemetry. Contaminated whole blocks are retained
  and replaced. A wrong node count, malformed output, hash drift or failed arm
  stops the experiment; incomplete rows/blocks remain evidence.

## Statistics and evidence

Per-arm rate is nodes/external wall seconds. One block ratio is
sqrt((B1/A1)*(B2/A2)); gain is 100*(ratio-1). Quartiles use the inclusive method.
Report median, Q1/Q3, IQR and min/max for eligible and all complete attempted blocks.
The selected median >=1% meets the advisory threshold; a valid smaller result is
BELOW_THRESHOLD. Failed control/incomplete runs are inconclusive, never zero gain.
None of these statistics is a confidence interval or evidence of Elo improvement.

Every arm binds executable/network/protocol hashes, UCI settings, monotonic interval,
exit code and original transcript. Binary hashes are rechecked after engine exit.
Waits, all runs, all blocks and final summary are retained. Full input/prerequisite
hashes are rechecked on normal experiment completion, including calibration failure.

The JSON prerequisite statuses are a trusted review declaration bound to original
native evidence hashes. They do not parse or replace inspection of that evidence.
The source/compiler/network associations and actual SMT topology require the wider
Job1 proof and host record; fixture tests do not establish native correctness.
The host record is hash-bound and must record CPU2/3 as siblings of one physical
core in processor group0. Protocol identity is computed from consumed bytes and
immediately compared with the file; the file is checked again at completion.
The compiler role points to a byte-identical D: copy of the actual native build's
g++.exe (08c11faa...). That copy is used for identity only and is never executed;
the original build records remain the authority for the compiler invocation.

## Tests and launcher

Arithmetic and negative-control tests are in test_timing.py; they launch no engine.
They retain their fixture files under a new --out directory. The valid-binding case
tests hash-checking mechanics using synthetic receipt content, not native proof.
Tests were authored without execution while pc1-a builds; root schedules them.

Run the actual adapter only through the reviewed grok-pc-safe-run launcher with the
full user protected-roots list and a NEW output directory. Its arguments are:

    D:\a10\python\python.exe -B D:\a10\wt\astra_r10\job1\timing\run_timing.py --threads 1 --protocol <frozen-absolute-json> --out <new-absolute-directory>

Read paths must include every frozen input and prerequisite. No random seed is used.
Implementation derives from project-owned R9 timing/UCI adapters, with ordered-block
geometric statistics and stricter R10 calibration. No external engine code copied.
