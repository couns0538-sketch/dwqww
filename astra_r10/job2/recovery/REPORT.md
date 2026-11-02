# CR input recovery — UNPROVEN

Required CR inputs remain **UNVERIFIED / missing**. No patch was recovered or
invented. These bounded lookups supplement the earlier planning failures.

| Required input | GitHub repository lookup | Original local object lookup |
|---|---|---|
| P4 crfix `1e7b5d20` | HTTP 422: No commit found | Not a valid object name |
| Delta commit `cc826b0a` | HTTP 422: No commit found | Not a valid object name |
| P7 crfix `129d440e` | HTTP 422: No commit found | Not a valid object name |

The exact `crfix/delta/p4_v2nets_delta_crfix.patch` lookup at `cc826b0a` returned
HTTP 404: no commit found for that ref. Repository branch search `crfix` and
commit searches `crfix` / `p4_v2nets` returned no results. A single global short-SHA
search found unrelated prefix collisions in other repositories; they were rejected
without fetching their files. They are not Forge CR evidence.

Read-only local refs confirm P4 `df79fb6e33e0ec45e4bdf40cbbdfadb3b6fc27a6`,
P7 `cd9cb992fd6a6b05766d1117c1de441a430586a9`, and status
`43af044a14a375b653f3d0bc633d9f476325ca81`. No `crfix`/`code-review` refs were found
in the inspected original repository. Shell inspection ran at own Idle priority,
affinity mask 4; it performed no fetch, branch mutation or filesystem write there.

Exact lookup definitions, errors and sanitized result metadata are retained in
`cr_lookup.json`. No Opus folder, forbidden drive, live queue or training source
was accessed. No engine, benchmark or training process ran.

Stop this repeated lookup item. Resume application only after obtaining the actual
CR full commit identities or original patch exports from their publisher. Any
independent follow-up can be labeled separately, but cannot claim these CR fixes
were applied or fill their prerequisite as PASS.
