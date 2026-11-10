# opus_smp_layout — STATUS

**Last update:** 2026-11-09 ~23:00 Vienna (HTTPS Date header; job start 18:53:44). **State: READY FOR CODE REVIEW → QA**, engine candidate **`a675c04`** (supersedes `0599271`).

## Done
- **Parent P** = `7ce10a05` (d4f4312 + trial_w6.patch md5 5786e9b8 + the six src_kit flips). Kit pc1 = pc2 = trial_w6 `4181a589` byte for byte.
- INVENTORY.md and SPEC.md (fixed before code; §3 updated for enc2-enc4).
- **Engine candidate `a675c04f4d2ea648dc32f3633c3e70cb2189bd08`**: everything inside `#if FORGE_SMP_LAYOUT`. `smp_layout_after_w6.patch` is +357/-0, md5 83928636…
- **OFF build** = `4181a589` (pc1 = pc2, f0c/f0d) = P = trial_w6. Macro-0 `g++ -E -P` is identical in all 8 units.
- **GATE build** = `a4b57032294d9d9efe2742408bb0a56da970cd1146f15c360a1fe99aada2c54b` (pc1 = pc2, f1c/f1d). It is also reproduced from the published patch (`diff -r` identical tree).
- **Threads 1 node identity, OFF and ON** (BENCH §10):
  - kit identity, pins net on/off + perft;
  - fens12k net on/off 12,000/12,000 = P;
  - warm 1,000 FENs = P;
  - Hash-1 replacement = P;
  - deeper warm (200k nodes) = P;
  - liveness PASS on this PC and in CI.
- **Race/stress** (BENCH §10):
  - CI run 42697936926 on `a675c04`: TSan "0 reports" (fixture 0 incoherent in 136 M probes, control 501,641; real engine over UCI at T2/T4 in both modes); ASan+UBSan green;
  - native tests PASS;
  - UCI stress at T1/4/8, both modes: PASS.
- **TT micro-benchmark** (BENCH §8):
  - lockless vs legacy at Threads 1: 0.50 → 0.71-0.74 (hot pool), 0.85-0.93 (random);
  - at Threads 2/4: 2.1-2.3 × P's striped locks (hot pool), 1.25-1.69 × (random).
- **Tag census** (BENCH §9): exact; 0 collisions for every single bit, every small field difference and every depth/bound/pv/rule50-only difference.
- **Review**:
  - R1 (fable): 3 MINOR fixed;
  - SR1 (self, NOT independent);
  - **R2**: a fable bug hunter ran beside the work over `0599271`, `527a696` and `a675c04`. No BLOCKER/MAJOR/MINOR; NIT-1..7 fixed (REVIEW_LOG.md).
- **CI evidence**:
  - `0599271`-era runs 42673707949, 42674616047, 42677341394, 42682884789;
  - enc2 run 42692617722;
  - **`a675c04` run 42697936926**, all green.
- **Skill**: `skills/forge-smp-lockless-qualify` (updated; mirrored to `D:\grok-pc-data\dwqww\.claude\skills\`).

## In progress
None. The advisory NPS of the new gate is in BENCH §10. The apparent 4-5 % OFF-mode gap at Threads 1 was a per-file effect: the byte copy of the gate exe ran as fast as the old gate, and the hot machine code is instruction-identical.

## Exact next action (other owners)
1. Code Review of engine candidate `a675c04` (diff `7ce10a05..a675c04`, files `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`) plus tests/CI.
2. QA, optional:
   - quiet native-core timing per SCALING_PLAN.md (gate `a4b57032`);
   - any strength question at Threads ≥ 2 through QA's own SPRT.
   - Nothing is queued by this job.

## Resume
```
cd /d/forge_jobs_20261107/opus2/repo && git log --oneline -6        # branch opus-smp-layout-20261107
cat /d/forge_jobs_20261107/opus2/out/JOB_STATUS.md ; cat /d/forge_jobs_20261107/opus2/out/FILES.md
```

## Unproven / not claimed
- **No** scaling, NPS or Elo claim. On this PC the A/A noise (±5 %) hides everything at Threads 1-4. The micro-benchmark measures the TT path alone.
- TSan "0 reports" covers only the executed paths: **no race proof**.
- Threads ≥ 2 search results are nondeterministic in both modes; only legality, liveness and the absence of TSan reports are shown there.
- The tag's collision rule is exact (SPEC 3.3). For unrelated data words the residual is about 2^-31 per torn pair **on average**, not a bound for every pair.
- The native multi-thread runs use 2 physical cores (SMT), so Threads 8 is an oversubscribed smoke.
- Operational note: toggling `TtLockless` allocates the new table before releasing the old one (exception safety), so peak memory during a toggle is 2 × Hash (measured 4,106 MiB at Hash 2048 on `0599271`). This is the same as P's own `Hash` resize.
- Deviations (`logs/enc4/DEVIATIONS.md`):
  - one unpinned `g++ -fsyntax-only` (seconds);
  - one 12k identity run aborted by my own log read and re-run; the invalid partial result is not cited;
  - one new 10 KB file on C: (`C:\Users\Administrator\AppData\Local\Temp\o2_files.txt`, from Git Bash `/tmp`). It was left in place, because deleting is not allowed.
