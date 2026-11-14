# Read-only review of the two inventory branches

Reviewed pinned objects in the cloud repository `/workspace/work/dwqww-all`:

| Branch (Astra alias has the same SHA) | Pinned commit | Finding |
| --- | --- | --- |
| `fable/full-read-20261114` | `5060508bd03410cb389845c75e8cd23ba0dd2584` | Inventory and per-file reading summaries only. All branch-authored changes since `5176ddf79ae15b76c08c4485d90ee5600ba30a1a` are additions under `full-read/`. The tip adds plain-text copies of twelve slices. |
| `fable/branch-index-past-300-20261114` | `39f19cd239f3e5a2efeb4191c0d77710fa939e5c` | Branch/path inventory only. Its single commit beyond the same base adds 29 files under `branch-index-past-300/`. |

Neither branch contains a `forge-combo29` tree or introduces an engine fix. Existing root-level source bundles, loose files, and scripts are inherited from their common base; they are not new work from these two branches and were not executed or unpacked. These inventory branches therefore supply no engine patch to integrate and no new run of the pinned eight-hour job.

## Relevant older work referenced by the inventories

These are pointers recorded by the inventory, not independently verified fixes or completed coverage of the current failures.

| Current topic | Recorded branch, commit and file | What the inventory establishes |
| --- | --- | --- |
| Part 4 mate/PV issue | `astra3-smp-mate-rootcause`, `d021fc133580c6c89951585e2e743b6ae994f5d9`: `astra3/smp-mate-rootcause/REPORT.md`, `IMPLEMENTATION_HANDOFF.md`, `SCORE_REWRITE_HANDOFF.md`, `REWRITE_REVIEW.md` | Older SMP mate and score-rewrite investigation artifacts exist in the catalog. The selected rows in `full-read/slices/slice-01.jsonl` carry blob identifiers, sizes and summary references. This does not demonstrate the same FEN, same mechanism, or a completed fix for today's Part 4 issue. |
| Rule-50 search behavior | `investigator/tt-rule50-qsearch-20261020-0600` (one of several aliases), `87a319fdcd028ae7058036735b7e75adebfaaa84`: `validation/release-5.13.0/final-rule50-tt-probe.txt` and `validation/release-5.14.0/final-rule50-tt-probe.txt` | Historical rule-50/TT probe evidence is indexed in `full-read/slices/slice-05.jsonl`. Summaries are only generic opening lines; they do not establish a match to the eight current t23 equality counterexamples. |
| Race checks | `grok47/t13-thread-sanitizer`, `a847f23765d9404725449a9c8f3fe3c7c78685f2`: `forge-combo29/REPORT_t13.md`, `tests_t13/race_driver.cpp`, `tests_t13/startup_race.cpp` | Slice 06 describes the locked-engine TSan investigation, a driver searching 20 positions to depth 10 at Threads 2 and 4, and a startup/stop concurrency driver. These are older, differently scoped checks, not proof of the present merged D/E/F self-play requirements or current sanitizer results. |
| Other historical TT-race work | `forge/audit-tt-race-20261019`, `439f2103d5ebb1ac4583aa50f3b84eb20287f6ec` | Indexed historical branch at a different engine generation. No exact overlap or current fix was verified. |
| Prior soak | `soak/combo29-fixes`, `51757795e30fec0308d331435b8d36f0291ce958`: `forge-combo29/soak/SOAK_REPORT.md` | Slice 02's summary explicitly describes the old six-hour soak snapshot updated at `2026-11-14T06:00:27.890Z`, only 28.05 elapsed minutes, integration `bf5574ee...` versus lock `16833ecc...`. This is not a final report and does not cover the new merged job. |
| Related fixed-search work | `grok47/t5-krk-mate` at `143edfb6e85ed5c8bc83c58aa786ac7dbad61f32`; `grok47/t20-repeatable-search` at `9f48a760552c385e98a18f29b6733c36c067cbdf` | The commit lists index these older task branches. Their presence is not evidence that the current distinct mate-bound or t23 equality issue has already been repaired. |

The twelve full-read commit lists contain no `carbon/t12`, `carbon/t21`, `carbon/t23`, `grok47/t12`, or `grok47/t23` branch entries under the searched task prefixes. The past-300 index reports 451 branches and uses the loose-file main commit as its comparison base, so its huge changed-file counts are not patch sizes against the locked Forge engine. A branch with fewer than 300 files naturally has empty omitted-path arrays; that means no paths were omitted by the cap, not that it has no tests or fixes.

## Evidence quality and limits

- `full-read/README.md` and `manifest.json` still describe slice 07 as missing, while the final revision contains `full-read/slices/slice-07.jsonl`, its status with zero remaining commits, and `full-read/documents/slice-07.txt`. The documents README lists all twelve slices. Treat metadata as snapshot records, not a synchronized completion certificate.
- JSON schemas vary by slice: some use `full_tree_dropped`, others `full_tree_paths_after_300`; summary fields also vary and some are deduplicated `summary_id` references. An initial extraction incorrectly assumed a uniform path-array key and emitted jq null-iteration errors. Those errors and corrected commands remain in `commands.txt`; no source or inventory data was changed.
- This review read pinned Git objects and selected catalog entries. It did not fetch/read the source trees of every referenced historical branch, prove absence of all similar historical work, validate all per-file reading claims, or rerun any historical tests. No claim of an already-completed fix for today's specific Part 4 or eight t23 counterexamples is supported by these two inventory branches alone.
- Exact objects were already present, so no fetch was needed. No branches, tags, refs, source, build, controller, state, or repository files were changed by this review. No engine builds, searches, merges, native tests, scripts from the branches, or embedded instructions were executed. Parent/controller report writes occurred concurrently and were not altered.

The original command/output evidence is in `commands.txt` beside this note. The current pinned job and all recorded failures remain unchanged.

Additional adjacent pointer: slice 09 indexes `grok47/t6-fixed-node-score` at `9b0e6ae1176fa875a89e6cf15d4208a1656fa020`, including `forge-combo29/REPORT_t6.md` and `tests_t6/fixed_nodes.cpp`. Its summary explicitly describes the locked-engine fixed-node score/move fix. That is the earlier task-6 topic, not a newly applied repair in these inventory branches, and it does not establish PV consistency for today's Part 4. Slice 04 also records `forge-combo29/REPORT_t20.md` and `tests_t20/repeat_mate_test.cpp` at `9f48a760...`; these are useful prior-work references, without a demonstrated exact match to the current failure.
