# Astra QA Final2 launcher checkpoint — 2026-10-30

Branch `astra-bullet-export-20261030`; starting revision `f86ef82538980ae22d018136534035c59090e3d6`.

| Item | Pushed commit | Scope |
|---|---|---|
| 3 | `c4f15df` | Production script basenames relative/absolute and case-insensitive; any guard tag and unreadable command lines refuse; readable plain Python allowed. |
| 4 | `76a1992` | WDDM labels with spaces, Graphics indices, per-physical-engine aggregation, five snapshots; malformed/missing telemetry refuses without retry. |
| 6b | `e0a95bb`, `995496a` | Split comma-separated exact gate executable basenames; reject drive-relative paths. |
| 6c | `bab7e0e` | Explicit scratch-drive parameter through run/target/TEMP and disk checks, updated current recipes. |

Each implementation commit has a failing-before/passing-after portable regression and original logs under `validation/astra-bullet-export/qa_final2_item*/`. Tests for Windows behavior are supplied in `tests/bullet/test_hip_launcher.ps1`; they were not executed here. No grok-pc commands, GPU workloads, queue changes, STOP/PAUSE files, force pushes or source-data deletions occurred.

Final integrated command:

```bash
FORGE_LOCK_ORACLE=/tmp/astra-al1-native/current_final/lock_oracle \
 /tmp/astra-a1-torch-cpu-env/bin/python -m unittest discover -s tests/bullet -v
```

**51/51 PASS**, including 11 portable launcher policy checks, exported-network oracle and file-integrity regressions. Original log and source/runtime hashes: `validation/astra-bullet-export/qa_final2_integrated/`.

**UNVERIFIED:** native PowerShell 5.1 and HIP runtime. This source qualification is not a claim that a GPU smoke was run, nor a playing-strength claim. A future HIP smoke must use a confirmed GPU-free slot, pinned Python and Rust 1.87+, explicit scratch drive and CPU affinity, with the production/telemetry guards passing.

The complete cross-branch fix map, converter tests, real-holdout and capacity limitations, and continuation instructions are in the [converter report](https://github.com/couns0538-sketch/dwqww/blob/ae223de/docs/ASTRA_QA_FINAL2_20261030.md). Its checkpoint is `ae223de`; all converter items are implemented, with actual Windows/private-PC qualification pending. The proposed same-name validator skill update is on that branch and is not installed.

IDEA_SOURCE: user QA Final2 review, Windows WDDM/process interfaces and existing original launcher; no other engine code.
