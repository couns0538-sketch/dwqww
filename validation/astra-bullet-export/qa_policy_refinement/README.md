# Launcher policy refinement — 2026-10-30

Prepared in the Linux cloud workspace. No grok-pc commands or GPU execution.
Windows PowerShell 5.1 behavior, native priority/affinity inheritance and HIP
execution remain **UNVERIFIED**. No local PowerShell runtime was available;
`runtime_availability.json` records the command lookup. Nothing was installed.

Production checks now classify actual executable names and Python's actual
script argument. Unrelated Python, compilers and editor/document arguments are
allowed. An invoked `train*.py` requires an `nnue-pytorch` path component, unless
its exact absolute path was configured in `ProductionTrainScriptPaths`.
Selfplay, fastchess, cutechess and gate names are defined in the README. Exact
`GateExeNames` / `GateExePaths` permit operator-selected arbitrary gate binaries.
Bare trainer script names and unavailable individual command lines cannot
establish production identity; the scheduled slot remains mandatory.

GPU counters aggregate across PIDs only when LUID, physical GPU index, engine
index and engine type match. Only 3D and Compute types (including numeric
suffixes) mark busy, strictly above 2%; exactly 2% is allowed. Every successful
window requires five snapshots and four one-second intervals. Copy/Video counts
do not mark busy; malformed or unavailable telemetry still refuses.

Evidence:

- `source_red.log`: five portable checks, three expected assertion failures
  before implementation (old broad process rule, old GPU threshold/window,
  missing refined documentation). This was **not** a PowerShell execution.
- `source_green.log`: all five documentation/source checks pass. This establishes
  source/documentation consistency only, not runtime policy correctness.
- `bullet_tests.log`: all 45 Bullet Python/native-oracle tests pass with no skips,
  using the existing CPU torch venv and existing native lock oracle below.
- `diff_check.log`: clean `git diff --check` result.
- `manifest.json`: changed source and evidence file SHA256 values.

`tests/bullet/test_hip_launcher.ps1` adds meaningful Windows behavioral fixtures:
0/below/at/above 2%; cross-PID sums; separate adapters/physical GPUs/engine IDs;
Compute variants; Copy/Video; malformed counters; real trainer paths versus
unrelated Python/compiler/editor arguments; explicit gate/trainer identities;
Python case-sensitive and clustered flags; normalized paths containing `..`;
five-snapshot/four-delay sequencing; and a busy sample at every position.
Existing disk/affinity/native stderr/quoting/exit/evidence tests remain. The
script mocks external telemetry and delay to exercise the actual slot checker;
it does not launch Cargo/HIP or use a GPU. **It has not been run here.**

An independent static review caught case-sensitive Python flag handling,
clustered W/X flags and directory traversal normalization; those cases have
regression fixtures and source fixes. Static review is not Windows execution.

The complete available scoped suite command was:

```sh
FORGE_LOCK_ORACLE=/tmp/astra-al1-native/current_final/lock_oracle \
  /tmp/astra-a1-torch-cpu-env/bin/python -m unittest discover -s tests/bullet -v
```

Historical `qa_windows_fix/` logs were left unchanged. The new policy retains
PS5.1, explicit CPU affinity, Idle priority, F: scratch/target/TEMP, 20 GiB free,
pinned venv Python, `-j2`, locked Cargo fetch and explicit MSVC x64 build target.
