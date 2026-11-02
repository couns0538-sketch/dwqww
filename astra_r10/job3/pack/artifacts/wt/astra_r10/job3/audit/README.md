# Native selfplay audit adapter — UNPROVEN

The draft extends the existing `npt-data-holdout-check` skill through
`scripts/audit_selfplay.py`; the original `audit_exports.py` remains unchanged.
It imports the existing independent six-field FEN parser, fingerprint and
descriptor/path identity checks. It does not import the converter under audit.

The native manifest pins all six frozen input files, the completed freeze receipt
and original trusted complete holdout metadata. Original raw source001 rows
1..466506 and source002 rows1..533494 provide the full-FEN authority. Both the
million-row normalized cohort and the 999,953 retained rows independently join
that authority using the exact original source string and physical source row.
Complete raw013 and014 are streamed directly. The retained SQLite index holds
source provenance, cohort/retained identities, conservative board+STM position
keys and any authentic game IDs. No normalized full-holdout copies are written.

Game IDs are accepted only from pinned row-aligned original sidecars and their
exact source-provenance joins. The actual input manifest has none, so a completed
zero-overlap/FEN-mismatch audit must still be UNVERIFIED. Expected train+holdout
missing-ID count, if all historical row counts match, is17,388,528. Actual counts
are not claimed until the full audit completes.

## Quick fixture evidence

Command executed through the full-protected-roots launcher:

```powershell
powershell -NoProfile -File D:\a10\wt\astra_r10\job3\audit\run-fixtures.ps1 -RunId attempt01
```

All14 tests passed in9.118 seconds. Launcher receipt
`launch-fixtures-attempt01/result.json` records exit0, Idle, CPU2 affinity4,
one worker, no capture errors and no disk-floor breach. The original stdout,
stderr, manifests, fixture inputs, reports and SQLite files are retained.
`fixtures-attempt01/fixture_summary.json` SHA256:
`58834d9108e80a5a02d4279ad11b7d420dba8507adae5933e14d094412e2940c`.

| Fixture | Required observation |
|---|---|
| Complete synthetic control | PASS, explicitly synthetic scope |
| Same game, different position | FAIL; game overlap1, position overlap0 |
| Stripped training castling | FAIL; retained state mismatch1 |
| Stripped cohort EP | FAIL; cohort state mismatch1 |
| Missing IDs | UNVERIFIED; train+holdout unknown count4 |
| Input modified after scan | FAIL; independent final rehash detects change |
| Duplicate provenance | FAIL |
| Unmapped provenance | FAIL |
| Malformed FEN | FAIL |
| Wrong trusted holdout row count | FAIL |
| Wrong trusted holdout hash | Refused before index creation |
| Misaligned ID sidecar | FAIL |
| Position overlap | FAIL; position overlap1, game overlap0 |
| Existing output | Refused; original evidence retained |

All deliberate failures were detected. These tests do not clear native datasets.

Focused review found one archive-only race: the audit parsed a hash-checked
manifest, then separately reread it for the archived copy. A transient change
could leave incorrect archived bytes even if the final rehash saw the original.
The new regression first failed on that implementation:
`fixtures-manifestred01` ran 15 tests with exactly one expected failure. The fix
archives the exact raw bytes used by the initial hash-checked parser.
`fixtures-attempt02` then passed all 15 tests in 8.961 seconds; its launcher
receipt records exit 0, Idle CPU2, one worker, no capture errors and no floor
breach. Both original runs and their fixture artifacts are retained. A focused
independent recheck of this fix has been requested before the native run.

## Stable candidate for review

| File | SHA256 |
|---|---|
| audit_selfplay.py | 506d71d0c38635a0896cdfa1a67f05138a1140927e06fa017763118a45027c61 |
| audit_exports.py (unchanged) | 1f3326a26dc6f0ee2d5dc75d080c188aa5de26e8f01d5aefd41ef4aa43523bbc |
| test_audit_selfplay.py | e870ef3dd7e0f8ea0184272efcc5eb0df34bf83cba1f8ce13966fad73503de13 |
| native_manifest.json | 484c45dd36cd2c44a1847ff30e8975ab91432973f5331e001a27bd0756f35e4b |

Independent review remains pending. No actual native audit has been launched by
this adapter's implementer. After review findings are closed, the root agent can
start the actual audit with a fresh output ID:

```powershell
powershell -NoProfile -File D:\a10\wt\astra_r10\job3\audit\run-native.ps1 -RunId actual01
```

Exit2 is expected for completed UNVERIFIED missing-ID evidence; distinguish it
from an incomplete blocked run using the output report's complete/status fields
and the launcher receipt. Exit1 represents a demonstrated audit failure. Preserve
every original record, including failures. A fresh ID is required for a rerun.

The adapter reserves2 GB under the15 GB D:/a10 cap, checks C>=30 GiB/D>=50 GiB,
and checks output growth every4096 rows. Other-workspace usage is rescanned at
most once per60 seconds. The independent raw syntax parser verifies six fields
and basic score/result shape; it does not establish chess legality or decode NPT
binary training records. No training readiness or strength claim is made.
