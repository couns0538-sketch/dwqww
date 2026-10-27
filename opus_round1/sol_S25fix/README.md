# sol_S25fix — S25 output-contract checker v2 (fix-ups S25-1, S25-2 L4-L7)

Sol's S25 delivery (17aa0cae, `releases/forge_sol_pack31_20261025/S25*/`) is read only and unchanged; the fixes ship
as new files. Tests/tooling only: no engine source change on this branch, no Elo or speed claim.

| file | what |
|---|---|
| `forge_sol_S25_outcontract_v2_20261027.py` | the v2 checker (standard library only) |
| `forge_sol_S25_options_v2_20261027.json` | approved normal-release UCI options (Sol's 10, re-observed on the AL1 lock exe); no pins inside any more |
| `forge_sol_S25_outcontract_v3_20261027.patch` | registration patch for AL1: CMake option `FORGE_OUTPUT_CONTRACT` (default OFF) + the two files above under `tests/` |
| `test_forge_sol_S25_outcontract_v2_20261027.py`, `tests_fixtures/fake_engine.py` | 17 tests incl. Sol's 12 parser cases (ported) |
| `forge_sol_S25_mutants_v2_20261027.py` | 6 planted bugs |
| `logs/` | tests, mutants, real runs on the PC (lock exe, expose build, Sol v1 contrast), CMake ON/OFF + ctest |

## Use

```sh
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe        # any Python >= 3.10
$PY -I -B forge_sol_S25_outcontract_v2_20261027.py path/to/forge.exe            # AL1 pins, d11, temp dir removed
$PY -I -B forge_sol_S25_outcontract_v2_20261027.py forge.exe --depths all --out NEW_DIR   # 5 depths, results kept
$PY -I -B forge_sol_S25_outcontract_v2_20261027.py forge.exe --ref Lprime        # another tree's pins (or --ref pins.json)
$PY -I -B forge_sol_S25_outcontract_v2_20261027.py forge_expose.exe --allow-expose
```

Output: `OUTPUT_CONTRACT_<PASS|FAIL> bench=<PASS|PIN_MISMATCH|FAIL> uci=<PASS|FAIL> ...`; exit 0 PASS, 1 FAIL, 2 bad call.

- **S25-1 pins per tree.** `--ref` = `AL1` (default: 312866/862329/3024920/12389307/34048354), `Lprime`/`B` (Sol's dev
  base 308972/…) or a JSON file `{"11": nodes, ...}`. The first engine process is still the bare `bench 11`; `--depths`
  adds depths, one process each. Only a node difference gives `bench=PIN_MISMATCH`; format problems (tail bytes,
  prefix, missing terminator, exit code, stderr) stay `FAIL`. The UCI option check always runs (v1 skipped it after a
  failed d11 gate, so on AL1 it never checked UCI at all).
- **S25-2 L4 timeout.** `--timeout` (default 300 s) per engine process; on expiry the checker kills only its own child
  and records `bench_timeout` / `uci_timeout`.
- **L5 temp directory.** Without `--out`, captures go to a NEW `mkdtemp` under the system temp dir (`TMP`/`TEMP`) or
  `--work-root`, never the build tree; after the run that directory — and only it, identified by a marker file with a
  random token — is removed, unless `--keep`. `--out NEW` is never removed. The v3 CMake registration passes no output
  path, so ctest leaves nothing in the build tree.
- **L6 expose builds.** A build with `FORGE_EXPOSE_TUNABLES` (CMake option, or `-DFORGE_EXPOSE_TUNABLES=1`) advertises the
  search tuning constants as extra `spin` options (51 on AL1). Without `--allow-expose` that is a contract FAIL
  (`unexpected_option`), by design: a normal release must not advertise them. `--allow-expose` accepts extra `spin`
  options only, still requires the 10 approved options exactly, and lists the accepted names. The v3 CMake registration
  adds `--allow-expose` automatically when `FORGE_EXPOSE_TUNABLES=ON`.
- **L7 Windows runner notes.** Works with `forge.exe` and CRLF output (the summary regex and the UCI line split accept
  `\r\n`). `os.access(X_OK)` is true for any existing file on Windows, so point it at the real `.exe`. Use the venv
  Python with `-I -B`; set `TMP`/`TEMP` to a scratch folder (default temp dir location). For ctest on the PC use the
  MSYS2 ucrt64 g++ with `-DCMAKE_EXE_LINKER_FLAGS=-static` (no DLL lookup for the test exe) and the VS BuildTools
  CMake/Ninja (as in `cmake_build.sh`); build only `--target forge` when you only need this test. Run at Idle priority
  (`nice -n 19` in Git Bash). The contract needs no `nice`/affinity changes inside the tool.

## CMake (after applying the v3 patch to an AL1 tree)

```sh
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DFORGE_OUTPUT_CONTRACT=ON [-DFORGE_OUTPUT_CONTRACT_REF=AL1]
cmake --build build --target forge -j 1 && (cd build && ctest -R forge_sol_S25 --output-on-failure)
```
