# R14 open work and known limitations

2026-11-03 14:55 Vienna. This is an in-progress register.

- Production position and full chain scans are still running. No partial zero
  can clear a split. Digest candidates need final exact-key resolution.
- Authentic original game IDs and historical producer-to-row bindings remain
  missing. JobA has 3,982 groups spanning unresolved observed-chain breaks.
- A guarded contiguous candidate is planned in sep/GUARD_BAND_PLAN.md. Its local
  checks cannot replace the explicitly required original identities.
- Broader boundary filter mathematics and qualifier passed independent review.
  The native driver needs three publication/accounting failure-path fixes and
  recheck, followed by 100k-path qualification and real native integration.
- Selected-suite runner needs pytest environment/config isolation, the exact r03
  native pin and a refreshed final allowlist. Those changes are authored; their
  validation is queued. Its subprocess integration fixtures
  remain unaccepted; do not claim a full-suite pass from the earlier partial run.
- After the running scans release their frozen dependencies, tighten the reusable
  guard_selection contract against nonmonotonic ply numbers on either side of a
  proposed cut. Existing callers must supply only the two local components.
  Current general helper can over-drop earlier unrelated rows if that contract is
  violated; it does not supply authentic boundary certification or export proof.
- Standard skill validator could not import its YAML dependency. Independent
  frontmatter/link/scenario review passed; the standard validator did not run.
- Final permitted-suite execution, complete changed-file review, final 30-minute
  bug hunt, file inventories/seals and FINAL_REPORT remain outstanding.
- Deeper jobA node-limit retry is designed in sep/RETRY_PLAN.md and not yet
  implemented. It preserves the original evidence and fixed K=8 proof scope.

## 2026-11-04 (Opus, R14 finish; owner's fix list items 0-8)

- The overlap is NOT resolved: after legal-capture-only en-passant normalisation 4,088
  board+side-to-move keys are still shared between the npt training rows and the
  holdouts 013/014 (4,118 train rows, 4,090 holdout rows; 7,610 keys on the raw
  board+stm key). The raw four-field "0 shared keys" is an en-passant formatting
  artefact, not a PASS. npt data stays BLOCKED (sep/PROD_SEPARATION.json, status FAIL).
- Three eaten spaces fixed above ("has3982", "by100k" = review finding F-008,
  "final30-minute"); the text is otherwise Astra's as found.
- Guard-band export scope: the staged candidate (C:\a14x\guardband01_stage) covers
  only the 999,921-row jobA set (987,194 train + 9,951 val staged, 2,776 dropped); its
  npt-data-holdout-check audit is UNVERIFIED because game_id is null in all
  17,385,720 audited rows. No export was built; promotion is the owner's call.
- Review findings still open at the tip, accepted with a reason, or fixed:
  - F-003 accepted: Astra's selected-suite runner (tools/r14_suite.py,
    Invoke-R14Suite.ps1, tests/test_r14_suite.py, as found) fails its own fixture
    test under pytest 9.2's built-in subtest accounting, and three of its tests
    refuse CPU admission when the suite itself occupies the CPU they pick
    (cpu_affinity()[0]); the runner stays UNVERIFIED and no suite-pass claim is
    made from it. Not changed by the R14 finish.
  - F-004 accepted: the prescribed "astra_r8\datafilter\tests + tests" command
    cannot collect in one pytest process with the R14 runtime (no torch by
    design; module name filter_positions twice; test basename test_converter.py
    twice without __init__.py) - all outside this branch's diff; the R14 scope
    (every tests\test_*.py + tests\r14_native + tests\r14_qualification) is run
    instead and D:\a13's "603 passed" is never cited for R14.
  - F-005 accepted: two tests\r14_native failures against the default
    chain_native.exe (consecutive-digit FEN answered UNREACHABLE instead of
    UNKNOWN; no interactive reply within 2 s), reproducible alone; the default exe
    is not the pinned r03 exe and the branch does not touch tools/r14_native or
    tests/r14_native. Owner item: run with R14_NATIVE_EXE=...chain_native_r03.exe
    and decide the contract for malformed FENs.
  - F-006: test_live_refusal_stops_only_owned_process_tree[guard] is timing
    sensitive under the Idle one-CPU launcher (the guard fires after one 500 ms
    poll before the probe child wrote child.json; the refusal and the restored
    environment are correct). Outcome in the final run: see the line below.
  - F-008 fixed (the three eaten spaces above).
  - F-017 fixed: TOOLS.md now has the section "R14 finish helper tools"
    (tools/opus_tools_md.py --check PASS).
- Final R14-scope suite at the tip: see the entry added after the run (log
  evidence/test_logs/r14/full-suite-r14cont02/output.log, first line = `git
  rev-parse HEAD` of the tree it ran on).
