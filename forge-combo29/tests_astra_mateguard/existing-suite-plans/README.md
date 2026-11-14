# Existing-suite execution plan

Read-only preparation, 2026-11-14T20:19:27.928Z. No native compilation or test execution was performed for this inventory task.

The three JSON text plans contain concrete argv arrays and absolute cwd/input/output paths for Release (`enabled`), ASan+UBSan (`asan`), and optional TSan (`tsan`). No interpolation is needed. Each has 50 build commands (47 main entrypoints plus UCI-loop and two wide-net objects), then 59 run/check commands. Run each command separately under the stated bound, after the root starts the successor phase. These are proposed commands, not successful execution evidence.

Use `plan-enabled.json.txt` and `plan-asan.json.txt` for the existing suite; `plan-tsan.json.txt` is available for selected race tests if budget permits, not an assertion that a full TSan suite was requested or run. Create outputDirectories in the VM before execution. Every executable/generated net/output path is outside the repository.

Dependencies and arguments:

- `uci-loop.o`: compile current uci.cpp with `-DFORGE_UCI_NO_MAIN=1`; link into t18/uci_fuzz, t21/multipv_stop_test, r3-02/threat_history_test, r3-04/late_parent_relief, r3-06/null_threat_verify_test, r3-11/dead_material_test, r3-17/position_prefix.
- `t19/eval_parity`: additionally link nnue512.o (`FORGE_NNUE_HIDDEN=512`, `nnue=nnue512`, existing tests_t19/nnue_weights_512.inc) and wide_eval512.o. The main test and ordinary core remain256. wide_eval.cpp has no main.
- `t8/nnue_convert OUTPUT` precedes `nnue_file_test OUTPUT`; malformed/shifted binary net variants remain beside OUTPUT in VM scratch. Include src/ so nnue_weights.inc resolves to the compiled-in net.
- `t19/widen_nnue SRC/src/nnue_weights.inc SCRATCH/nnue_weights_512.inc`, then cmp against the unchanged existing512 include. Never write the generated include into src or an existing test.
- `r3-12/softnodes_test ENGINE MODE`: three separate modes softnodes, depth10, edges. This forks an external engine; sanitizer settings must reach both processes, and outer timeout must kill the process group.
- `t12/krk_mate_test 40 10 2 16 14 1`: target roots, repeats, threads, hashMB, depth, fullclear. Prior full ASan runs timed out440s. Retain timeout as incomplete; no offset exists. Smaller arguments are reduced coverage, not replacement proof of the full invocation.
- `t13/race_driver 10 20`, `t14/test_eval ABS/eval_cases.txt`, `t18/uci_fuzz 200000`. Other test mains have no required argv. r3-15/tm_finish_test offers --no-deep, but default no-args includes all200 depth10 checks.

Important risks and retained limitations:

- The four historical fixture failures are options/clamp exact stdout diffs in each of Release and ASan (two fixture names × two modes). Search/ownbook spec checks passed previously. `historical-fixtures.json.txt` records actual old exits and input hashes. New advertised options can add further diff lines; preserve golden files and report actual failures unchanged.
- t16 ownbook.in.txt contains a relative book path with spaces, so cwd must be the repository root. Do not split or edit that UCI line. Existing book data is read only; do not copy it into the branch as a new deliverable.
- t3/clock_commands.txt is a manual sequence with huge clocks, requiring timed stop; do not pipe naively. t8/expected_uci.txt and r3-17/expected.txt are prose/placeholder evidence, not literal golden stdout. r3-17/commands.txt has a supplemental exact perft sequence in the plan and the existing position_prefix executable proves the parser behavior.
- Existing option tests change their own options and usually require default false on entry. Do not wrap the whole suite in global MateAlphaGuard/HindsightDepth-on initialization. Keep candidate compile gate1 but runtime guardfalse for this unchanged suite.
- Tests retain assertions via -UNDEBUG; the frozen engine objects are not rebuilt with altered test flags. Flags/architecture/FP settings match build-focused-tests.mjs. No FORGE switch is overridden in source.
- Clock/timing tests, 200-position depth10 tests, 100000-position t19 parity, 200000-line fuzz, and r3-24 two-thread proof (20000 ordered interleavings plus100 searches) may be relatively long under instrumentation. Keep the440s timeout and record nonzero/partial results. Never edit expected values or silently reduce counts.
- Compile/link failures are untested possibilities: the plan was statically inspected only. Preserve actual compiler diagnostics if a merged test interface no longer matches. No sanitizer success is claimed.

Only inventory/plan/report text needs publication. The VM generator is retained as inert `prepare-plan.mjs.txt`; do not publish the live script.
