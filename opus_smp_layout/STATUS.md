# opus_smp_layout — STATUS

**Last update:** 2026-11-09 ~19:55 Vienna (HTTPS Date header; job start 18:53:44).

## Done
- Parent P = `7ce10a05`; kit pc1 = pc2 = trial_w6 `4181a589` byte for byte. INVENTORY.md. SPEC.md fixed before code.
- Code `893b78d`: all inside `#if FORGE_SMP_LAYOUT`.
  - `smp_layout_after_w6.patch` is +326/-0 (P's lines untouched) and applies to a fresh P export.
  - The macro-0 `g++ -E -P` is identical to P.
- **OFF build = 4181a589 (pc1 = pc2) = P byte for byte. GATE build = 6c07563b (pc1 = pc2).** Gate with `TtLockless=true`: pins, perft and kit identity ALL OK.
- Native tests:
  - tt_lockless: 0 incoherent hits in 453,850,112 probes; the positive control gave 1,673,288 incoherent hits.
  - smp_lifecycle: PASS, with T1 identity three ways.
  - tt_coherence: PASS.
- **CI green**, TSan "0 reports":
  - 42673707949 (`893b78d`);
  - 42674616047 (`4a8f12b`): tests plus the real TSan engine over UCI at T2/T4 with TtLockless off and on.
- Layout of P measured: `nodes_` shares a cache line with `local_nodes_` and other owner fields.

## In progress
- L3 full fens12k, net on and off (P and gate OFF running; gate ON next).
- Reviewer R1 (fable) on the frozen `893b78d`.

## Exact next action
1. Compare the L3 bodies, P vs gate OFF.
2. Run gate ON L3 net on and off, warm identity (P / gate OFF / gate ON), liveness_check, uci_lifecycle_stress (gate OFF and ON, Threads 1/4/8), the gate layout probe, repeated native CTests, then the advisory NPS (alone).
3. Then fill BENCH §2/§4/§5/§6, handle the R1 findings, and refresh the manifests.

## Resume
```
cd /d/forge_jobs_20261107/opus2/repo && git log --oneline -4
cat /d/forge_jobs_20261107/opus2/out/JOB_STATUS.md ; ls /d/forge_jobs_20261107/opus2/out/id
```

## Unproven / not claimed
- No scaling or Elo claim. Threads ≥ 2 is nondeterministic; native multi-thread runs use 2 physical cores only.
- "Race proof" is never claimed: TSan shows no report on the executed paths only.
- L3, warm and stress results are pending until they are filled in BENCH.md.
