# S43 S26 add-on: absolute paths, --base, bench-ref file — DONE (PC-native net-batch v5; native runs on B and on the new AL1 base)

`SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 25. Branch `opus-sol-S43` = `d4f4312` + `0d99f02` cherry-picked (`e44d3123`) + `c28bf027`.
Tool-only job (no engine source change), `[skip ci]`, no CI run. Worktree `F:\opus_scratch\worktrees\opus_sol_s43_wt`; a stray
non-worktree directory `F:\opus_scratch\worktrees\opus_sol_s43` holds one early copy of the tool and is left in place.
Scratch `F:\opus_scratch\sol_S43`. Machine exclusive: no. Work and results by a sub-agent; this report text is its hand-back.

**Spec (Sol, verbatim):** make the S26 net-pack batch script take `--base <dir>` and a bench-ref file, and use ABSOLUTE output
paths everywhere (a relative path once aborted ctest with exit 2). Pass: on B with the lock net it reproduces exe 55fa7e81
bench d11-d22 exactly; a test runs it from a different cwd and passes; applying it to a new base needs no path edits.

## Acceptance
| item | result | evidence |
|---|---|---|
| starting point | Sol's S26 v4 already takes `--base`, a `--bench-ref` FILE and absolute paths. But it is Linux-only (flock, nice, affinity, setsid, GCC 14 box recipe) and its native qualification was outstanding. v5 (`forge_sol_S43_netbatch_v5_20261027.py`) is a new PC-native file. Sol's files are unchanged; his refs and allowlist JSON are read as-is (sha256 match his SHA256SUMS). | `README.md`, `sol_S26/` |
| on B with the lock net, exe 55fa7e81's bench d11-d22 exactly | PASS. Run A: base B (PC buffix h256e12 tree, staged read-only, 32 source files identical) with net 74c4009d gives bench 308972 / 745494 / 2460422 / 11901452 / 31111774, which equals Sol's S26 "lock" reference (the bench of CR box exe 55fa7e81). Perft 4865609 / 193690690; FMA 0; base unchanged. The exe sha differs from 55fa7e81 (Linux box vs PC MinGW), but equals the PC's own buffix build of the same tree except 5 PE-header bytes. | `logs/step4_*`, `logs/step4b_*`, `results/runA_baseB_locknet/` |
| a test runs it from a different cwd and passes | PASS. Unit test 1: relative paths from one cwd give the same results as absolute paths from another, and every recorded path is absolute. Unit test 7: the CTest path from a foreign cwd; the fake ctest exits 2 on any relative path, reproducing the historical failure. Native run B was launched from `F:\opus_scratch\sol_S43\cwd_elsewhere\deeper` with relative paths only. | `logs/step3_tests_final.log`, `logs/step5_*` |
| applying it to a new base needs no path edits | PASS. Run B uses the AL1 lock tree (verified 75/75 against the lock archive's sha256 list) with the AL1 net. The tool file is the same (sha256 `4664886b…` in both runs); only two new DATA files were added: AL1 bench refs and the AL1 allowlist (WAC 001 score 623; h256_e12 gives 661). Bench == AL1 pins 312866 / 862329 / 3024920 / 12389307 / 34048354; perft OK; FMA 0. CTest 13/14: only `forge_tests` failed, with exactly the 4 known lines (allowlist PASS). The junit path is absolute and exists. | `results/runB_AL1_newbase_relative_othercwd/` |
| absolute paths everywhere | Every output, log, private tree, build product and junit path is absolute. Every subprocess gets an explicit absolute cwd. CTest uses `--test-dir <abs>` and `--output-junit <abs>`. | tests 1, 7 |
| tests / planted bugs | 7/7 (synthetic toolchain). Unmutated control + 9/9 mutants caught; the first run was 8/9, because the max_total check masked max_count, so a new test case was added. | `logs/step3*` |

## Findings
- In the first v5 draft, `a.ctest` (the flag) was overwritten by the ctest executable, so CMake always ran. Test 1 caught it.
- Windows pitfall: `shutil.ignore_patterns` is case-insensitive there, so a `cmake*` pattern silently drops `CMakeLists.txt` from
  the private copy, which would break CTest. v5 uses exact, case-sensitive names, asserts that `CMakeLists.txt` survives, and
  test 7 guards it.
- Sol's allowlist is net-specific (WAC 001 score 661 for h256_e12, 623 for AL1). A new net needs its own allowlist data file,
  not a code change.
- The PC recipe build takes about 14 s and the bench at d11-d22 about 37 s; run B's CMake build (30 steps, `-j 1`) took 34 s
  and CTest 5 s.
- The tool's only kill path is its own engine child on timeout or error; it never triggered.

## Left / UNVERIFIED
- CTest on B with Sol's unchanged allowlist was not run natively; only run B's CTest was. The B tree has the lock `tests.cpp`
  (93c56def), which is in Sol's allowlist binding.
- S26's WAC 1000 ms screen is not part of v5. A timed screen was out of the S43 scope, and the machine was not exclusive.
- No per-net ASan/UBSan (CI) run.
- On Linux, use Sol's v4 or pass `--gpp/--objdump/--cmake/--ctest-exe` explicitly (untested).

## Files
- Tool and data: `forge_sol_S43_netbatch_v5_20261027.py`, `forge_sol_S43_bench_refs_AL1_20261027.json`,
  `forge_sol_S43_allowlist_AL1_20261027.json`, `sol_S26/` (Sol's refs and allowlist, unchanged).
- Tests: `test_forge_sol_S43_netbatch_v5_20261027.py` (7), `fake_toolchain_s43.py`, `mutation_check_s43.py`.
- Evidence: `logs/`, `results/runA_baseB_locknet/`, `results/runB_AL1_newbase_relative_othercwd/` (exes and objdump text stay in
  scratch; sha256 recorded). Docs: `README.md`, `IDEA_SOURCE.md`. Index: `FILES.txt`; checksums: `SHA256SUMS`.
