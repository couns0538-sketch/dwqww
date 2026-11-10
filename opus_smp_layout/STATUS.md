# opus_smp_layout — STATUS

**Last update:** 2026-11-09 ~19:20 Vienna (from the HTTPS Date header). Job start 18:53:44 Vienna.

## Done
- Parent P = `7ce10a05` (d4f4312 + trial_w6.patch md5 5786e9b8 + src_kit flips). Kit build pc1 = pc2 = **4181a589… = trial_w6 byte for byte**. Pins and node identity ALL OK (`logs/parent/`).
- INVENTORY.md (reconciliation) and SPEC.md (names and protocol fixed before code).

## In progress
- Layout probe (SPEC §4), then the lockless TT tests and code (SPEC §3, §5).

## Exact next action
Write `tests/tt_lockless_tests.cpp` (test first), the CMake option and the code under `#if FORGE_SMP_LAYOUT`.

## Resume
```
cd /d/forge_jobs_20261107/opus2/repo && git checkout opus-smp-layout-20261107 && git log --oneline -5
cat /d/forge_jobs_20261107/opus2/out/JOB_STATUS.md
```

## Unproven / not claimed (so far)
Everything about the lockless TT and the layout fix: no code yet.
