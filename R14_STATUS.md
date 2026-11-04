# R14 execution checkpoint

2026-11-03 14:36 Vienna; started12:41:11 Vienna, target about21:41:11 Vienna.
Training data remains BLOCKED. Both sep verdicts are UNVERIFIED; no export exists.
This is an in-progress record, not completion or acceptance.

All55 input checks matched, including39 source datasets. Writer historical
association is supported, but exact producer binding and original game IDs remain
missing. Completed QC changes were independently rechecked. Native helper and
independent audit tools are under staged qualification; production scans pending.

Native helper qualification passed1M foundation pairs with zero disagreements.
Twenty additional deep searches hit their budgets and remain UNKNOWN. Production
overlap scan03 runs onCPU2 and complete production chain scan02 runs onCPU1.
JobA chain scan completed:1033537 reachable,11441 unreachable,4942 unknown pairs;
all3593220 source rows parsed, with1049921 rows selected including50000 context
rows. Prepared-group integration is complete:999921 rows/10880 groups mapped at
100% fill;3982 groups span unknown breaks, zero observed ranges are shared across
train/validation. Authentic identities remain UNVERIFIED. No complete production
verdict exists; the two complete-corpus audits continue.

Latest health check14:34:44 Vienna: gate964 completed games. NPT naturally rolled
from seed38 to seed39 at14:25; its newepoch0 is at40%,8.76 iterations/second.
Monitoring now follows the active seed39 log. Sustained extra coordinator work is
held while its next progress reading is checked. Owned bytes about542MB, available
RAM21.1GB; D/C disk floors satisfied. CPU admission is
rechecked before every workload.

Full inherited training-dependent suite remains subject to the protected-import
restriction. The final report will distinguish executed and blocked checks.

## 2026-11-04 (Opus, R14 finish)

Both production scans are complete. Position overlap is FAIL: 7,610 board+side-to-move keys are shared
between the npt training rows and the holdouts 013/014, and 4,088 of them stay shared after legal-capture-only
en-passant normalisation (4,118 train rows, 4,090 holdout rows); the raw four-field "0 shared keys" is an en-passant
formatting artefact. Authentic game IDs are still missing. npt data stays BLOCKED; no export exists
(sep/PROD_SEPARATION.json, sep/GUARDBAND_SEPARATION.json, FINAL_REPORT.md).
