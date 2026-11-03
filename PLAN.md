# R14: authentic game separation and conditional export

Start: 2026-11-03 12:41:11 Vienna. Target: nine hours, ending about 21:41:11 Vienna.
Base: 11d382085f29310980d4822cd6b8d382d9910185. Branch: astra-r14-20261103.

## Objective

Prove authentic production and jobA game separation, or record precisely why it
fails or remains unknown. Export only after exact authenticated game identities,
separation and the independent holdout audit pass. The user explicitly selected
exact identities: conservative blocks cannot qualify export on their own.

## Jobs, budget and evidence

| Elapsed | Job | Required evidence |
|---|---|---|
| 0:00-0:30 | Checkout/runtime, pins, resource baseline, policy | receipts, TOOLS.md |
| 0:30-5:30 | Writer provenance, segmenter, production/jobA proof | sep/PROD_SEPARATION.json, sep/R14B_SEPARATION.json |
| 5:30-8:00 | R13 fixes, conditional export, future-ID proposal | red/green logs, audit, manifest or blockers |
| 8:00-8:30 | Complete change review and regression | findings/dispositions, test logs, report draft |
| 8:30-9:00 | Dedicated bug hunt, fixes and regression | adversarial findings, rechecks; seal immediately afterward |

Early completion or blockage reallocates time to other jobs and deeper proof.
Safety stops override the duration. Record progress in evidence/R14_PROGRESS.md.

14:13 Vienna scheduling refinement: the full production chain scan receives a
five-hour maximum deadline so a slower complete-corpus pass can finish. The
measured jobA pass took508.25 seconds for1049921 selected/context rows. Expected
production work remains within the original main-job budget; the longer cap is
contingency using time already saved on completed QC fixes. Resource checks and
hourly workload monitoring continue throughout. The final30-minute bug hunt is
still reserved at21:11 Vienna; no new expensive run may consume that reservation.

The coordinator may execute a bounded, single-process correctness audit in its
reserved slot while the independent reviewer is idle, provided admission allows
it and the two background pipelines plus coordinator remain at most four CPU
worker threads. This does not admit another native pipeline or subprocess test
suite. Test suites that create descendants wait for a background slot to clear.

## Mandatory boundaries

- All new files, Git metadata, runtime, temporary files and caches below D:/a14;
  total owned storage below 5,000,000,000 bytes. Never copy source datasets.
- D:/a13 and frozen datasets are read-only. Never modify training, self-play,
  gates, queues, other worktrees, locks or networks. No STOP/PAUSE files.
- Stop on any input MD5 mismatch, D: below 50 GiB or C: below 30 GiB. Check before
  bounded allocations and during jobs. Never delete datasets or evidence.
- Default one computation worker; at most two single-thread computation workers
  and four total activity slots including supervision/reviewer. Idle priority;
  GPU visibility disabled in child environments. No training or strength claims.
- Reserve 8 GiB free RAM, cap computation at 2 GiB; use chunked RAM-only indexes.
- Before substantial work and hourly verify normal gate/training progress using
  authorized read-only telemetry. Sustained >10% throughput reduction throttles
  owned work. Missing reliable telemetry blocks expensive scans. CPU activity
  alone is insufficient. Never import the protected training runtime.
- Scripts default to PowerShell 5.1; copied launcher explicitly requires 7. No
  nested shells. Times use Vienna wall labels; elapsed timing is monotonic.
- Every commit: git -c user.name=Astra -c user.email=astra@forge.local commit.
  Push only astra-r14-20261103 about every ten minutes and verify remote identity.
  No force, history rewrite, skip-CI markers or vendor names in patched files.
- Restore the historical policy section verbatim after checking source MD5
  94169aefef79ccb69c21f8f2c86298f0. Follow milestone reviews automatically.

## Proof requirements

Authenticate historical writer version/configuration against frozen shards.
Cite full source paths, MD5 and lines for whole-game buffering, serialization,
filters, seen-hash omissions, rotation and restart. Present source alone is not
historical provenance. Do not read the live seen-hash database or locks.

Implement an original native helper with independent python-chess oracle. K=8;
absolute ply=2*(fullmove-1)+(side==black). Continuation needs positive exact ply
distance, equal White result, legal path and exact full FEN/clock consistency.
Return REACHABLE/UNREACHABLE/UNKNOWN and a legal witness. Default node cap 100,000;
critical-boundary retry cap 1,000,000. Exhaustion or gap>K is unknown, never a
proven boundary. Possible legal continuation does not authenticate identity.
Cross-check at least 1M resolved stratified random pairs with zero disagreements;
report attempted/resolved/exhausted cases by depth and special-move coverage.

Scan all of 013/014 and first/last 50,000 rows of both 012 and 015. Keep compact
range evidence and unresolved boundaries; explain harmless 013|014 continuation.
Verify all 39 source MD5s before use via Get-FileHash and supplied pins/sidecars.
Compare complete holdouts against other 37 files on four-field and board+side
keys using RAM-only 64-bit indexes. Resolve hash matches by exact keys. Every
overlap count includes rows, valid/missing keys, parse failures and fill rate.

Join every jobA row to exact source location, examining omitted intervening rows.
Compare inferred groups to authenticated chains, list each mismatch and cross-
split link. If needed form contiguous candidate blocks near the existing 1%
validation allocation at certified boundaries, drop entire ambiguous crossing
components and K-ply guards, listing all dropped row IDs/reasons. Exact identities
still required: conservative fallback without them remains UNVERIFIED.

Verdict JSONs bind input and candidate hashes, counts, coverage, witnesses,
unknowns and every reason. Demonstrated violations FAIL; missing evidence is
UNVERIFIED; PASS requires all mandatory proofs. Never manufacture authentic IDs.

## Fixes, export and tests

Retain red/green tests for explicit fixture-only nonproduction source paths;
child-only launcher environment and owned runtime; and six-/four-field/board+side
duplicate reporting. DuplicateIndex currently lives in p5_qc.py: move shared
RAM-only implementation to qc_core.py and preserve caller imports.

Only after strict separation PASS create export payloads. Preserve existing full-
FEN text and label conventions; exclude abs(score)>=30000 with immutable row-ID
list and exclude old440k. Preserve source provenance/authenticated IDs. Audit
both splits against complete holdouts independently, including all six fields.
Manifest: counts, WDL, score histograms, MD5/SHA256 for every payload. Seal manifest
externally, avoiding self-reference. No native-binpack claim without reader proof.
Without PASS create no export payload, only precise missing-evidence records.

Write text-only future-writer proposal: stable IDs, result, cross-file line ranges,
producer identity and crash-consistent .games sidecars. Do not modify self-play.

Negative tests: straddling game, shuffled rows, mismatched result, gap>K, distinct
games that connect, search exhaustion, missing keys, hash collisions, lost rights/
EP, input mutation and resource breach. Freeze each meaningful candidate for one
read-only reviewer before expensive validation. Assess all findings, fix confirmed
issues and retain rejected/unresolved findings. Recheck substantive changes.

Run complete permitted suite. Inherited datafilter conftest imports protected
training code: if independent execution cannot satisfy it, report blocked totals
and exact failures; never call a subset a full pass or stub missing proof.

FINAL_REPORT.md records Vienna times, verdicts/counts, test logs with MD5, unfinished
work and explicit training clearance. Inventory every delivery file by absolute
path/full MD5; externally seal report/inventory. Commit logs under evidence/test_logs
and verify remote HEAD. Preserve runtime/local artifacts with their own inventory.
