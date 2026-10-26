# Successor v2 source ready; actual execution pending, 2026-10-26

Probe SHA256:
`e43b6ec82a611e9fd03a1b44b70487189b7df1ed32cfe5734de9e139b055d7bb`

Controller SHA256:
`72c906970a2d96db54e9c0dae70450c5af0ebd28f98c82ecaf658e202eeaed62`

The actual f022 failure and source63d521 remain unchanged. The v2 probe changes
only the f023 BUILD tag and recording its received loader environment. The
new controller sets child-only LD_LIBRARY_PATH before exec to the exact private
Torch library directory. Tiny independent children demonstrated ordinary bare
libgomp RED and exact-path GREEN; this is not a Torch-import pass.

Twelve bounded tests pass: seven shared gzip/hash/seal/evidence tests and five
controller tests. The controller verifies the frozen probe and small loader
dependency hashes, requires a new output folder and active BUILD, rechecks the
phase immediately after preflight, then monitors every0.1 seconds. Signaling
tolerates a child exiting between poll and signal; both TERM/KILL paths wait
and preserve the controller receipt. The pre-fix controller is retained.
The confirming RED uses only a harmless Python pass child in a disposable
fixture, never the private archive/probe; current GREEN launches no candidate.

The planned concrete invocation, **only after root's explicit fresh grant**, is:

```sh
taskset -c 1 nice -n19 python3 -B forge_sol_S09_torchram_controller_v2_20261026.py \
  --authorized-build-window f023-BUILD \
  --out /workspace/forge-pack24-20261026/S09_TORCHRAM_20261026/runtime_f023_v2_once_20261026 \
  --job-dir /workspace/forge-pack24-20261026/S26/forge_sol_S26_NATIVE_f023_once_20261026/00_4c5936ebcfd3 \
  --watchdog-seconds 150
```

The job path is derived from the supplied f023 net hash, not evidence that the
job has spawned. Root must confirm actual current phase/path. The controller
requires job/002_build.stdout, rejects completed build in commands.json, and
cuts off on bench/processes.json or watchdog expiry. Only its own child group
is signaled. The exact private Python child inherits CPU1/nice19, BLAS/MKL/OMP1
and empty CUDA visibility. The parent environment and private package remain
unchanged; no disk CPU-library restore is attempted.

If successful, the same process will retain reversible parity exports and
before/after CPU state checkpoint, with the existing explicitly limited smoke
scope. No training-gain, full50k/real013014, native1M, Std or null-regression
claim follows. If it fails, preserve that actual error and stop; no automatic
retry or source mutation is implemented.

Independent final read-only review found no remaining blocker in the v2 race
fixes. No actual v2 archive read, load, import or training has occurred as of
this preparation checkpoint.
