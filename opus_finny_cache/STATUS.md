# opus_finny_cache — STATUS

**Last update:** 2026-11-09 ~19:50 Vienna (HTTPS Date header; job start 18:53:44).

## Done
- Parent P = `7ce10a05`, and its kit build = trial_w6 `4181a589` byte for byte (pc1 = pc2).
- D3 gate measured: 0 in-tree refreshes; refresh = searches × workers; refresh share ≈ 0.01-0.02 % of accumulator work (BENCH.md).
- Ownership check: the v3 cache already exists (FB1); HalfKA r10fix1 has none (INVENTORY.md).
- SPEC with the reserved names, the design for king-dependent networks and the full event table.
- **Verdict: NOT APPLICABLE on trial_w6. No engine code, no builds, no option.**

## In progress
- An independent review of this pack (REVIEW_LOG.md).

## Exact next action
After the review, update REVIEW_LOG.md, regenerate MD5SUMS/SHA256SUMS, push (`[skip ci]`: documentation only).

## Resume
```
cd /d/forge_jobs_20261107/opus2/wt_cache && git log --oneline -3   # branch opus-finny-cache-20261107
cat /d/forge_jobs_20261107/opus2/out/JOB_STATUS.md
```

## Unproven / not claimed
- No cache identity or speed claim of any kind (no cache exists).
- The SPEC §3 design for king-dependent networks is prepared only: not implemented, not tested.
- The int8 pack's open item (Threads > 1 untested) belongs to its owner and is not closed here.
