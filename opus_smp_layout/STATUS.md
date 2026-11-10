# opus_smp_layout — STATUS

**Last update:** 2026-11-09 ~20:50 Vienna (HTTPS Date header; job start 18:53:44). **State: READY FOR CODE REVIEW → QA.**

## Done
- **Parent P** = `7ce10a05` (d4f4312 + trial_w6.patch md5 5786e9b8 + the six src_kit flips). Kit pc1 = pc2 = trial_w6 `4181a589` byte for byte.
- INVENTORY.md and SPEC.md (fixed before code).
- **Engine candidate `0599271`**: R1 review fixes included; everything inside `#if FORGE_SMP_LAYOUT`. `smp_layout_after_w6.patch` is +319/-0, md5 dfa3d11d…
- **OFF build** = `4181a589` (pc1 = pc2, s0c/s0d) = P = trial_w6. Macro-0 `g++ -E -P` is identical in all 8 units.
- **GATE build** = `541e8b3d4333b99044ccafa7bcda82a1b5bf42a561eaf3b043b9871ed9faea1b` (pc1 = pc2, s1c/s1d).
- **Threads 1 node identity, OFF and ON:**
  - kit pins and perft;
  - fens12k net on/off: 12,000/12,000 identical to P;
  - warm table: 1,000 FENs, 40 changes, transcripts identical to P;
  - liveness PASS.
- **Race/stress:**
  - CI TSan "0 reports" in 4 runs (the last two on the final code, incl. the real engine over UCI at T2/T4 in both modes);
  - ASan+UBSan green;
  - fixture: 0 incoherent in 4.05 G probes over 8 runs, with the positive control gating;
  - UCI stress at T1/4/8: 2 × 300 + 2 × 2,000 cycles PASS;
  - unit tests repeated, PASS.
- **Layout**: `nodes_` alone on its line (measured before and after).
- **NPS**: advisory only (an A/A copy shows ±5 %).
- **Review**: R1 fable (no BLOCKER/MAJOR; 3 MINOR fixed, NITs handled). Recheck replaced by SR1, a self-review marked NOT independent.
- **CI evidence**: runs 42673707949, 42674616047, 42677341394 (final engine) and 42682884789 (CI hardening), all green.
- **Skill**: `skills/forge-smp-lockless-qualify` (mirrored to `D:\grok-pc-data\dwqww\.claude\skills\`).
- **Final bug hunt** (20:33:00-21:00:30 Vienna, 27.5 min; it ended when the checklist was exhausted, without padding): clean (BENCH §6). It covered:
  - exes re-hashed;
  - pins in both modes on the final exe (net on and off, perft);
  - the gate rebuilt from the published patch (= 541e8b3d);
  - adversarial UCI cases;
  - a 6 s fixture run and a depth-11 T1 identity run;
  - stale documentation fixed.

## In progress
None.

## Exact next action (other owners)
1. Code Review of engine candidate `0599271` (diff `7ce10a05..0599271`, files `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`) plus tests/CI.
2. QA, optional:
   - quiet native-core timing per SCALING_PLAN.md;
   - any strength question at Threads ≥ 2 through QA's own SPRT.
   - Nothing is queued by this job.

## Resume
```
cd /d/forge_jobs_20261107/opus2/repo && git log --oneline -6        # branch opus-smp-layout-20261107
cat /d/forge_jobs_20261107/opus2/out/JOB_STATUS.md ; cat /d/forge_jobs_20261107/opus2/out/FILES.md
```

## Unproven / not claimed
- **No** scaling, NPS or Elo claim. On this PC the A/A noise (±5 %) hides everything at Threads 1-4.
- TSan "0 reports" covers only the executed paths: **no race proof**.
- Threads ≥ 2 search results are nondeterministic in both modes; only legality, liveness and the absence of TSan reports are shown there.
- The mix32 tag quality is argued by construction (bijective fold-multiply mixing), not by a statistical test.
- The native multi-thread runs use 2 physical cores (SMT), so Threads 8 is an oversubscribed smoke.
- Operational note: toggling `TtLockless` allocates the new table before releasing the old one (exception safety), so peak memory during a toggle is 2 × Hash (measured 4,106 MiB at Hash 2048). This is the same as P's own `Hash` resize.
