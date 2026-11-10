# opus_smp_layout — STATUS

**Last update:** 2026-11-09 ~23:45 Vienna (HTTPS Date header; job start 18:53:44). **State: READY FOR CODE REVIEW → QA**, engine candidate **`89cddf7`** ("enc5"; supersedes `a675c04` and `0599271`).

## Done
- **Parent P** = `7ce10a05` (d4f4312 + trial_w6.patch md5 5786e9b8 + the six src_kit flips). Kit pc1 = pc2 = trial_w6 `4181a589` byte for byte.
- INVENTORY.md and SPEC.md (fixed before code; §3 updated for enc2-enc5).
- **Engine candidate `89cddf7e3727ed0f461537af785dc344386fac50`**: everything inside `#if FORGE_SMP_LAYOUT`. `smp_layout_after_w6.patch` is +366/-0, md5 f07082fd…
- **OFF build** = `4181a589` (pc1 = pc2, h0c/h0d) = P = trial_w6. Macro-0 `g++ -E -P` is identical in all 8 units.
- **GATE build** = `2940fb0514dd2ef058d6512bf66659074f162293f7d31ccac23779c2e65762e5` (h1c = h1d = g1c). It is also reproduced from the published patch (`diff -r` identical tree).
- **Threads 1 node identity, OFF and ON** (BENCH §11):
  - kit identity, pins net on/off + perft;
  - fens12k net on/off 12,000/12,000 = P;
  - warm 1,000 FENs = P;
  - Hash-1 replacement = P;
  - deeper warm (200k nodes) = P;
  - liveness PASS on this PC and in CI.
- **Race/stress** (BENCH §11):
  - CI run 42708220996 on `89cddf7`: TSan "0 reports" (fixture 0 incoherent in 182.7 M probes, control 678,627; real engine over UCI at T2/T4 in both modes); ASan+UBSan green; no new compiler warning;
  - UCI stress at T1/4/8, both modes: PASS.
- **TT micro-benchmark** (BENCH §8):
  - lockless vs legacy at Threads 1: 0.50 → 0.71-0.74 (hot pool), 0.85-0.93 (random);
  - at Threads 2/4: 2.1-2.3 × P's striped locks (hot pool), 1.25-1.69 × (random).
- **Codegen** (BENCH §11): in the kit exe, the lockless probe/store are speed-optimised and in normal `.text` (enc5). In enc4 they were size-optimised in the cold tail.
- **Tag census** (BENCH §9): exact; 0 collisions for every single bit, every small field difference and every depth/bound/pv/rule50-only difference.
- **Review**:
  - R1 (fable): 3 MINOR fixed;
  - SR1 (self, NOT independent);
  - **R2**: a fable bug hunter ran beside the work over five commits. **No engine defect at any severity**; tooling/doc: 1 MINOR + 9 NIT, all fixed (REVIEW_LOG.md).
- **CI evidence**:
  - `0599271`-era runs 42673707949, 42674616047, 42677341394, 42682884789;
  - enc2 42692617722;
  - enc4 42697936926, 42706554114;
  - **enc5 42708220996**, all green.
- **Skill**: `skills/forge-smp-lockless-qualify` (updated; mirrored to `D:\grok-pc-data\dwqww\.claude\skills\`).

## In progress
None.

## Exact next action (other owners)
1. Code Review of engine candidate `89cddf7` (diff `7ce10a05..89cddf7`, files `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`) plus tests/CI.
2. QA, optional:
   - quiet native-core timing per SCALING_PLAN.md (gate `2940fb05`; fresh byte copies per round);
   - any strength question at Threads ≥ 2 through QA's own SPRT.
   - Nothing is queued by this job.
- Observed only, by directory listing: QA's folder `D:\forge_qa\smp_c29_20261109` holds a combo29 port of enc2/enc4 (`smp_layout_enc2_527a6965_after_combo29.patch`, `src_e4gate`, `forge_e4gate_pgoT2_DIAG.exe`). The enc4 → enc5 step for such a port is the one macro on two definitions (GATE_ENTRY.md).

## Resume
```
cd /d/forge_jobs_20261107/opus2/repo && git log --oneline -6        # branch opus-smp-layout-20261107
cat /d/forge_jobs_20261107/opus2/out/JOB_STATUS.md ; cat /d/forge_jobs_20261107/opus2/out/FILES.md
```

## Unproven / not claimed
- **No** scaling, NPS or Elo claim. On this PC the A/A noise (±5 %) and per-file effects (6 %) hide everything at Threads 1-4. The micro-benchmark measures the TT path alone.
- TSan "0 reports" covers only the executed paths: **no race proof**.
- Threads ≥ 2 search results are nondeterministic in both modes; only legality, liveness and the absence of TSan reports are shown there.
- The tag's collision rule is exact (SPEC 3.3). For unrelated data words the residual is about 2^-31 per torn pair **on average**, not a bound for every pair.
- The native multi-thread runs use 2 physical cores (SMT), so Threads 8 is an oversubscribed smoke.
- Operational note: toggling `TtLockless` allocates the new table before releasing the old one (exception safety), so peak memory during a toggle is 2 × Hash (measured 4,106 MiB at Hash 2048 on `0599271`). This is the same as P's own `Hash` resize.
- Deviations (`logs/enc4/DEVIATIONS.md`):
  - one unpinned `g++ -fsyntax-only` (seconds);
  - one 12k identity run aborted by my own log read and re-run; the invalid partial result is not cited;
  - one new 10 KB file on C: (`C:\Users\Administrator\AppData\Local\Temp\o2_files.txt`, from Git Bash `/tmp`). It was left in place, because deleting is not allowed.
