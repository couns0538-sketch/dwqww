# Fable/Opus checks of the Forge engine (GitHub Actions, free on this public repository)

Written 2026-11-15 by the Opus session; every line read by Fable before it was pushed. The repository owner allowed
this one branch that day ("yes" to: one new branch with a test recipe and test scripts that GitHub runs for free).

## What runs

The workflow `.github/workflows/fable-opus-checks.yml` builds the engine of one commit (input `engine_commit`,
default `6b98f2170a32...`, the king-bucket net path) with GCC on an `ubuntu-24.04` runner and runs four suites in
parallel jobs. Nothing of the engine source is run except the engine built from it; it is never changed.

| Suite | Build | What it checks | A planted fault or known answer that must show |
|---|---|---|---|
| `perft` | release | move generator: six positions with published perft counts; 1,000+ seeded random positions, `go perft 3` (total and per first move) against python-chess, depth 4 on the first 100 | the 12 published counts; a self-test (one count altered must be reported) |
| `mates` | release | 200 mate-in-one positions (seed 20261117), `go depth 4` must mate | every position is checked to have a mate first |
| `badinput` | AddressSanitizer + UBSan (-O1) | 150+ bad or odd inputs (unknown commands, broken FENs, illegal moves, bad option values, missing net files, odd go limits, overlapping commands); readyok within 10 s after each | `controls/san_control.cpp`: heap, stack, use-after-free, signed overflow, shift must all be reported, else the job fails |
| `tsan` | ThreadSanitizer (-O2) | stop / quit / ponderhit / option changes while search threads run, clock and node limits, MultiPV, 8 threads; with a random king-bucket net and with the built-in net | `controls/san_control.cpp race` must be reported, else the job fails |

No Elo and no speed figure comes from a runner (shared, unknown machines).

## Where the results go

Each suite writes text files (summary.txt first). A second job, which runs no engine code and has the only
write token, checks them (plain UTF-8 text, safe names, size limits, no links) and commits them to the branch
`ci-results/fable-opus` under `runs/<run id>-<attempt>/`. Fable and Opus read that branch with `git show`.

## Rules

- Triggers: by hand (`workflow_dispatch`) or a push to `ci/fable-opus-checks`. No pull-request trigger, no schedule.
- Permissions: read-only for the test jobs; `contents: write` only for the publishing job; no secrets.
- Actions: only GitHub's own `checkout`, `upload-artifact`, `download-artifact`, pinned to full commit ids
  (v7.0.1, v7.0.2, v8.0.2 at the time of writing), `persist-credentials: false`.
- Python packages from PyPI, pinned: chess 1.11.2 (python-chess; that is its PyPI name since version 1.0), numpy 1.26.4.

## Files

- `run_suite.sh` one suite: environment record, build, positive control, the suite script, log capping
- `build.sh` release / asan / tsan builds (CMake from the engine's own CMakeLists.txt); `cxx_opt_launcher.sh` lowers
  its -O3 for the sanitizer builds and records the flags each compiler call really got
- `uci.py` the UCI driver; `positions.py` seeded random positions (the method of the 2026-11-15 helper trials)
- `perft_suite.py`, `mates.py`, `bad_input.py`, `tsan_campaign.py`, `tsan_group.py` the suites
- `controls.py` + `controls/san_control.cpp` the positive controls (after Fable's forge/tools/san_control.cpp)
- `forge_v3_random.py` writes a random king-bucket (FORGENN3) net (a copy of the lab's pipeline/forge_v3.py)
- `cap_logs.py` cuts any result file over 1 MB to its first 300 lines plus size, sha256 and report counts
