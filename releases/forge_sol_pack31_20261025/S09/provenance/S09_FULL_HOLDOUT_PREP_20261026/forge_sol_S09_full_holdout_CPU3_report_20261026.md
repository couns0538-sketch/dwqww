# S09 full actual-f006 synthetic holdout — closed 2026-10-26

PASS for bounded CPU execution and full-sample evaluation. This is not a
training-gain, native bit-parity or playing-strength result. Real holdouts013/014
were not supplied. The actual f006 network remains untouched.

| Check | Result |
|---|---|
| Normal process exit | PASS rc0,52.3205947340 seconds, no forced stop |
| All supplied h000 records | PASS50000,98batches,512maximum,336tail,0dropped |
| Onehead vs replicatedeight Torch logits | PASS maxabs3.814697265625e-06 <=1e-5 |
| Changed-bias positive control | PASS512/512 first-batch logits changed |
| Original input hashes | PASS7/7 unchanged before/after and re-read after closure |
| Owned group cleanup | PASS no remaining members |
| Loader | PASS rawmemfd SHA0aae29741806982c5778f7863e53711edc5c4afb829595d7296f729ac176cfe3, seals15 |
| Math runtime | Torch2.4.1+cpu, NumPy1.26.4, CPU3nice19, math threads1 |
| Conservative summed parent/child peakRSS |264425472bytes, below4GiB |
| Onehead MSE |0.12416724592633246 |
| Replicatedeight MSE |0.12416724590392758 |
| HCE-only MSE |0.04558598686496771 |
| Training, exports, GPU operations |0,0,0 |

The sample is a supplied synthetic stand-in. Its HCE loss is lower than the
actual f006 model's loss here; this does not establish that the accepted network
regresses on authentic held-out data. No accepted net, source, GPU queue or gate
was changed. Differences between one/eight Torch losses are floating-point
rounding, within the declared forward tolerance; no gain is claimed.

Head counts0..7: [3,574,7295,20447,16654,4587,423,17]. The evaluator uses the
unchanged v3b reader and targets, k2.25/blend0.6. Every model parameter comes from
actual f006 include SHA0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661.
The existing S09 converter/unchanged step1 parser reads the include; inverse
export layout is tested. No binary/FEN/include parser was reimplemented.

Preregister: d40048171c71ef2c1a86aea4a4ead1c116d7552585aca2b9df3f3868653fcefa.
Executed script:8468de76d9719a03178561ba7be1d4d27cd6107714c3417824ffeddaab52eceb.
Result:63487797d80f96de9cbb0cfad7a8de3487f58d0877ecd6bb662b0f1e25fc4fda.
Independent closed-result audit:cedf724cc027a77d3d9bb40e9f81eb9e9badbdf1c8f95ff6b8eaa1ac95dbeb6f.
Source preparation four tests PASS. Original CPU1 preparation is preserved;
CPU3 successor changes only affinity check/error/record, with a separate proof.
The older overall150s full training/export probe remains FAIL. This distinct
work evaluates actual f006 over the full sample, without training or exports.

Main returned at50.3377571240 seconds, leaving187.662242876 seconds before the
first forced-signal threshold. The process exited normally; both Python atexit
markers were observed. No shutdown-hang conclusion was made.

Exact executed command:

```sh
taskset -c 3 nice -n 19 python -B /workspace/forge-pack24-20261026/S09_FULL_HOLDOUT_PREP_20261026/forge_sol_S09_full_holdout_CPU3_20261026.py --execute --root-authorized-window root-S09-actual-full50k-holdout-CPU3-nice19-180work240hard-20261026 --out /tmp/forge_sol_S09_native_20261026/full50k_actual_f006_holdout_CPU3_once_20261026
```

Original logs/events/proc states/faulthandler and child/controller JSON are in
that new output directory. No original input/package file was created, edited
or removed. Ordinary private Torch CPU library remains absent; the temporary
sealed loader is process-local. Future execution needs a NEW output folder.
Authentic holdout generalization, new trained8-head quality, defaultDML runtime,
Windows testing, native1M and native10k parity are outside this result.
