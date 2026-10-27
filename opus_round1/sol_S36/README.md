# S36 same-diff merge verifier

`forge_sol_S36_samediff_verify_20261027.py` (Python 3 stdlib, read-only, deterministic):
```
python -I -B forge_sol_S36_samediff_verify_20261027.py --a L=<merge diff of tree 1> --b B=<merge diff of tree 2> \
    [--approved patch1 patch2 ...] [--approved-new DEST=SOURCE ...] [--allow PREFIX ...] [--protect PREFIX ...] [--json out]
```
- **Parsing.** Unified diffs, `git diff` or `diff -ruN` (timestamps, `/dev/null` new/deleted files,
  "\ No newline at end of file").
- **Per-file normalisation**, ignoring offsets and context:
  - `net`: added minus removed count per line text. Sequential patches compose additively, so the approved net is
    the sum over the approved patches;
  - `blocks`: the multiset of (removed lines, added lines) change blocks.
- **Verdict.** SAME_CHANGE_SET when every file has A's net == B's net == the approved net, and no protected path
  changed (default `src/ include/ bench/ CMakeLists.txt` = the forge sources). Otherwise DIFFERENT, with every
  reason and the differing lines. Files outside `--allow` (default `tests/ tools/ docs/ README.md IDEA_SOURCE.md
  CHANGELOG.md`) are flagged.
- **Notes.** Equal nets with different blocks (the same lines placed differently, e.g. doc hunks before an extra
  section of one tree) are reported as NOTE, not as a failure.
- **Exit codes:** 0 same, 1 different, 2 usage/parse error.

`run_s36_evidence.sh <inputs> <scratch>` reruns the real-record evidence: 8 runs, including planted one-line changes
and a determinism re-run. `test_forge_sol_S36.py` has 7 tests.
