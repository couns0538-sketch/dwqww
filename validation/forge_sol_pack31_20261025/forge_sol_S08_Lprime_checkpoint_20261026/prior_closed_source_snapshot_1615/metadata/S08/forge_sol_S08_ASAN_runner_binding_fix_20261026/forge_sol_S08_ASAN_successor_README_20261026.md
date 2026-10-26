# S08 sanitizer qualification runner repair, 2026-10-26

Original `e019d64b…` is preserved unchanged. Four regression controls invoke its actual main with downstream CTest mocked PASS and no child process: a changed test ELF, helper ELF, source file or build recipe is accepted. Each control therefore fails its required reject assertion. The unchanged positive control passes; six successor-only controls are explicitly skipped. These are preflight regression probes, not native CTest evidence.

Successor `forge_sol_S08_ASAN_full_qualification_v2_20261026.py` passes all eleven controls. It binds the complete frozen source map, all twelve target ELFs, compiler, actual sanitizer compile/link recipe, original first-ASAN bare-bench receipt, allowlist and CTest binary. It uses the unchanged verified `85acc…` subreaper controller for both discovery and full CTest, including deadline/disk/stop closure and adopted descendant reaping. No extra cleanup implementation is introduced.

Full native acceptance requires every one of the fifteen configured tests, matching JUnit inventory, zero failed cases, strict stderr, enabled ASan/UBSan and leak detection, then unchanged full bindings. It does not claim a sanitizer pass before that run. Native execution remains root-owned; this agent ran no engine. The raw reused build-controller receipt field `engine_executions=0` is a legacy build-only value and is explicitly excluded from native-count interpretation.

The main command must use taskset CPU4, nice19, a full closed stage-all build receipt, a new output directory and a stop-file path. On this host the actual runtime needs approved escalation because LeakSanitizer cannot inspect its own process inside the sandbox; disabling leak detection is not used.
