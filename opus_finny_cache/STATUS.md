# opus_finny_cache — STATUS

**Last update:** 2026-11-09 ~20:35 Vienna (HTTPS Date header; job start 18:53:44).

## Done
- Parent P = `7ce10a05`; its kit build = trial_w6 `4181a589` byte for byte (pc1 = pc2).
- D3 gate measured on an instrumented scratch copy of P:
  - refreshes = searches × workers, **0 in-tree**;
  - refresh share ≈ 0.01-0.02 % of accumulator work (BENCH.md);
  - only two refresh call sites exist in P (search.cpp:791 fallback, search.cpp:1613 root).
- Ownership check: the v3 cache exists (FB1); HalfKA r10fix1 has none (INVENTORY.md).
- SPEC: reserved names, design for king-dependent networks, full event table.
- Review: SR1 structured self-review, **NOT independent** (the fable reviewer became unreachable). One wording fix (REVIEW_LOG.md).
- **Verdict: NOT APPLICABLE on trial_w6. No engine code, no builds, no option.** The branch differs from P only in `opus_finny_cache/` (git diff of include/src/tests/CMake/CI vs P: empty).

## In progress
None.

## Exact next action (owners, not this job)
- Code Review reads the pack as a decision record.
- If a king-dependent network (HalfKA r10fix1 lineage) becomes a lock candidate, its owner implements SPEC §3 there and qualifies it by §3.5.

## Resume
```
cd /d/forge_jobs_20261107/opus2/wt_cache && git log --oneline -3   # branch opus-finny-cache-20261107
```

## Unproven / not claimed
- No cache identity or speed claim (no cache exists).
- SPEC §3 is prepared only.
- The float exactness bound for trial_w6 is not verified (irrelevant to the verdict).
- The int8 pack's open item (Threads > 1 untested) is its owner's and was not closed.
