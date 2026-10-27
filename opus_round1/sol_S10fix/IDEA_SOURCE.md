# IDEA_SOURCE — S10fix (QA fix-ups S10-1..6)

- Task source: QA's `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3, items S10-1..S10-6 (2026-10-27 08:50 CET).
- No new engine idea. The four search ideas (QuietCheckLmpSurvival, ImprovingRazorGuard, SingularSiblingLmr,
  CaptureHistoryLmp) and their patches are Sol's (S10, `17aa0cae`); their IDEA_SOURCE lines are in his patches.
- Data: only Sol's own logs (sealed S10 evidence archives, S07 native WAC300 OFF run, consolidated results v2,
  patch-check freezes) and one new local re-run of base B OFF d22 (S10-3).
- Base B sources: rebuilt from this repository's git objects (AL1 tree `294dbed3` = Sol's L except the net,
  h256_e12 net from `f4911f27`, base-B `search.cpp`/`CMakeLists.txt`/`bad_capture_tests.cpp` blobs from Sol's
  checkpoints on `17aa0cae`), matched file by file to Sol's sha256 freeze.
- Tools are own code (Python 3.10 + python-chess for move classification); no outside code.
