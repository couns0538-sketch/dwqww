# Astra QA Final2 — 2026-10-30 checkpoint

Converter branch: `astra-fen-convert-20261030`; starting revision `beb1074d60f5c1becf59cadfca02f83b2ebd0ee8`.
Launcher branch: `astra-bullet-export-20261030`; starting revision `f86ef82538980ae22d018136534035c59090e3d6`.
Every implementation commit below was pushed immediately after its tests. No engine/search change or new Elo claim. No grok-pc commands were run. No queue, STOP/PAUSE, branch deletion or force-push operation was performed. Source data and historical evidence remain preserved.

| Item | Commit | Result and evidence |
|---|---|---|
| 1 writable fsync | `e4a0854` | `r+b` descriptor; Windows-semantics regression fails before and passes after. `qa_final2/1_fsync/` |
| 2 audit ctime | `e5759a2` | ctime omitted only outside POSIX; dev/inode/size/mtime remain checked. Three regressions pass. `qa_final2/2_ctime/` |
| 3 production guard | `c4f15df` (launcher) | Relative/absolute case-insensitive script matching, guard-tag and unreadable command refusal, readable plain Python allowed. `qa_final2_item3_process/` |
| 4 GPU guard | `76a1992` (launcher) | Spaced labels, Graphics indices, totals by physical engine across PIDs, five samples, immediate malformed/missing refusal. `qa_final2_item4_gpu/` |
| 5 runbook | `c663bef` | Retained index path/size per attempt, fresh per-shard free-space inequality, no operational prune step; five document regressions pass. `qa_final2_runbook/` |
| 6a standalone GPL gate | `dd61ff3` | Explicit acknowledgement and shared repository/symlink boundary before writes/execution; four regressions pass. Runbook command corrected in item 5. `qa_final2/6a_roundtrip/` |
| 6b comma gate names | `e0a95bb`, `995496a` (launcher) | Comma split, whitespace trim, exact basenames; review follow-up rejects drive-relative `R:forge.exe`. `qa_final2_item6b_gate_names/`, `qa_final2_item6b_gate_path/` |
| 6c scratch drive | `bab7e0e` (launcher) | Explicit `-ScratchDrive`; target/TEMP/run path and disk checks use it. `qa_final2_item6c_scratch_drive/` |
| 7A Idle native stderr | `c5e194f` | Process APIs capture stdout/stderr without PS5.1 NativeCommandError. Bounded pipe drains continue after a disk sink failure, preserve child exit, then report capture failure. Four portable checks; Windows regression supplied. `qa_final2/7a_idle/` |
| 7B reserve | `2e8b75f` | Converter and audit defaults 32768 MiB; three regressions. `qa_final2/7b_reserve/` |
| 7C probe allowance | `01b5be5` | 128 bytes/row estimate; 32 GiB reserve and live guards remain; regression plus 23 disk cases. `qa_final2/7c_probe/` |
| 7D batches | `63d3cf8` | Explicit full-37 inventory and observed capacity; retained indexes accumulate, one-volume shortfall blocks, separate provisioned volumes support batches. Twelve tests. `qa_final2_shardplan/` |
| Existing skill update | `14b1683` | Proposed `skills/validate-chess-engine/`, same name, seven relative links verified and bounded review preserved. **NOT INSTALLED**; provider read-only. |

Converter evidence prefixes above are under `validation/astra-converter-20261030/`; launcher evidence is under `validation/astra-bullet-export/` on the launcher branch. The final integrated logs and source hashes are preserved alongside this report.

## Executed validation

- Converter/data2: **139 tests, PASS**, with the explicitly selected external GPL adapter. Command: `FORGE_BINPACK_ADAPTER=/tmp/astra-binpack-work/forge_binpack_adapter python3 -W error::ResourceWarning -m unittest discover -s tests/data2 -v`. Log: `qa_final2/integrated/data2_final.log`.
- Existing data tools plus Idle static checks: **134 tests run, one native-suite discovery skip**, successful suite. Command: `python3 -m unittest discover -s tests/data -v`. Log: `qa_final2/integrated/data_final.log`.
- Native probe was run separately: **9/9 PASS**. Command: `python3 tests/data/test_probe.py --probe /tmp/astra-a1-native-build/budget-status/forge_data_probe --evidence validation/astra-converter-20261030/qa_final2/integrated/native_probe`. Raw stdin/stdout/stderr/exit records and binary hash are retained there.
- Bullet/exporter: **51/51 PASS**, including 11 portable launcher checks. Command: `FORGE_LOCK_ORACLE=/tmp/astra-al1-native/current_final/lock_oracle /tmp/astra-a1-torch-cpu-env/bin/python -m unittest discover -s tests/bullet -v`. Original log: launcher branch `validation/astra-bullet-export/qa_final2_integrated/bullet.log`.
- Tests reproduce Windows rules with mocks/static checks on Linux where needed. These do **not** qualify the Windows runtime. Ordinary fixture cleanup operates only on test-owned temporary data, never corpus or project evidence.
- Source/test diff whitespace checks pass; one original unittest RED stderr line has trailing whitespace and was deliberately preserved as raw evidence.

## Remaining qualification and next action

**UNVERIFIED:** native Windows 3.12 fsync/stat behavior; PowerShell 5.1 launch and telemetry behavior; actual HIP smoke; actual 37-shard PC inventory/capacity; real complete 013/014 holdout clearance. No Windows or GPU runtime was available here. The two named QA reports were not located in the checked repository state; fixes use the detailed user-provided review text.

The scripts and tests are ready for independent Windows review. In a separate approved spare-CPU slot, the crew can run the supplied `tests/data/test_idle_launcher.ps1` with an explicit Python, CPU list and new evidence directory; the launcher branch's `tests/bullet/test_hip_launcher.ps1` exercises helper behavior without HIP/Cargo. HIP training still requires a separate confirmed GPU-free slot. Do not use converted data for training until the complete private holdout audit passes with trusted hashes/counts.

For storage, supply the real per-shard inventory and a fresh output-volume measurement to `tools/data2/plan_shard_batches.py` before each shard. A batch boundary gives no deletion/reclamation credit. This session does not certify that all 37 shards fit the PC.

The source changes are complete; none of the requested fix items was left unimplemented. Actual platform/data qualification remains explicitly pending. Resume from these branches, preserving all evidence; do not rerun completed Linux investigations without a new question.

IDEA_SOURCE: QA/Code Review Final2 user specifications, existing Forge tools and validator skill, Windows/.NET/Python API contracts; original implementation, no other engine code.
