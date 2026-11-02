# Independent R11 runtime review — changes requested

Reviewer: `trace_design`. Review date: 2026-11-02. Static inspection only; no Python interpreter, fixture suite, native child, assembler, preflight or original 73-test suite was executed. This is not runtime qualification or a data-pack PASS.

## Reviewed frozen identities

| File | SHA256 |
| --- | --- |
| `astra_r11/runtime/launch_runtime.ps1` | `876b17b429026bd7195a15f027b4952301134623c032f296a2a357cdc6311460` |
| `astra_r11/runtime/run_fixtures.py` | `8dce04ac83593f045e2c30125d31a347779aa275bb2b1a45164b190aaa685367` |
| `astra_r11/runtime/regression/path_guard.py` | `df3f0e79a61e5333758b3408a15fa88f387c0aba898958f8108ce84a9b3b8363` |
| `skills/grok-pc-safe-run/scripts/Invoke-GrokPcSafeRun.ps1` | `d941c74be12b1076387ca2eb479177e29ef989ff07969c05686a6478f0b52b05` |
| `astra_r11/runtime/regression/run_regression.py` | `9524660107e556dc0ca2482cd730ab6202742d7c18b6320d9591354f52a25eb9` |
| `astra_r11/runtime/assemble_runtime.py` | `a74392e4a27690ead97d249f86e0ae282010c0fa762ce48ae7c1ff3eb8b51d1f` |
| `astra_r11/runtime/STATIC_CHECKS.json` | `8e8d0969bee3846c72edae5a6eeee947e31691b046051f663a5f7f5a6e21e701` |

The first four identities were rehashed at review completion and remained equal to the author's freeze. Findings below refer to this initial candidate, not subsequent corrections.

## Findings accepted by root

1. **P1 — validate preparation and refusal-output paths before access.** `launch_runtime.ps1:55` opens arbitrary `New-Json` paths without policy validation. The initial manifest existence check and `CreateDirectory` at lines 61–64, manifest/binding writes at lines 83–84, and admission receipt at line 93 occur without first validating `runtime-runs` and its descendants. An existing `D:/a11/runtime-runs` junction could redirect these accesses outside the owned workspace before the native helper's path checks. Apply owned-root/root-first ancestor checks before every such read or write, including inside `New-Json`.

2. **P1 — bind the bootstrap payload before the first interpreter launch.** `Candidate-Snapshot` at `launch_runtime.ps1:25–44` captures runtime sources and `BOOTSTRAP.json`; line 82 binds `python.exe`. The bootstrap receipt records the executable digest but no complete extracted DLL/stdlib file census. Fixture mode runs before assembly and never verifies that payload. The first complete archive-versus-extracted check is `assemble_runtime.py:124`, after Python and its standard-library imports have already started. A changed `python312.dll` or `Lib/*.py` can therefore execute during fixtures without changing the prepared candidate binding. Verify the bootstrap tree against pinned archives in PowerShell before any native startup, and retain/recheck the resulting complete file identities.

3. **P2 — reconcile the linked launcher contract.** `skills/grok-pc-safe-run/references/launcher-contract.md` still specifies `D:/a10` for `working_directory` and `write_paths`, and repeats the historical root in a later policy paragraph. The R11 skill and implementation require `D:/a11`. Correct the branch-local instructions so the required linked contract does not direct a forbidden replay.

4. **Small discovery-completeness correction.** `run_fixtures.py:52` accepts at least 20 gameprovenance tests although the frozen suite contains 26. Pin the expected 26 plus four runtime-guard tests to expose missing collection. Root assigned this with the other corrections.

## Confirmed behavior and limits

- Source/helper/manifest candidate capture and before/after rechecks are present. The wrapper clears inherited Python and pytest injection variables and restores its caller's environment.
- Parent/child Python path guards perform lexical checks before root-to-leaf reparse inspection. These hooks are not native-process sandboxes; automatic child startup remains untested.
- All 15 copied original test files, including `conftest.py`, were independently hashed against their R10 source paths and receipt hashes; every comparison matched. The regression result requires exactly 73 collected and passing calls, with no skipped or failed report.
- Admission reads process/load metadata and refuses conflicts without controlling other processes. No native admission success is claimed.
- `NEXT_JOB.md` correctly separates unresolved historical provenance from separately authorized future-corpus work. The appended `SEALED_BLOCKED_EVIDENCE` handoff contract correctly limits checksum success to evidence bytes and prohibits a qualified-data or training-unblocked claim.
- Python syntax, synthetic fixtures, bootstrap assembly, native preflight, child-hook startup and original 73 tests remain **UNRUN**. Output-shard resume remains incomplete. A corrected frozen candidate requires a separate recheck; these findings are not closed by this document.
