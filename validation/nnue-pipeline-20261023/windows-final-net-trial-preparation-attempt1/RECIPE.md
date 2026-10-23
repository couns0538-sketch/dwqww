# Windows Zen 5 final-network trial: preparation only

**Ready tools; waiting for root’s chosen frozen include and SHA256.** No source export, object build, executable, network selection or engine run occurred during this preparation. The only compiler execution was version queries and empty-input C++20 preprocessing. `AVAILABILITY.json` and original streams retain actual commands, hashes and exit codes.

Verified now: LLVM-MinGW Clang **23.1.3**, Windows x64 target; CMake **3.31.6**; GNU Make **4.4.1**; Wine **10.0**. All 11 existing Windows24 compiler/config/linker/reader/Wine identities match the prior pinned proof, including the actual compiler shared library. Absolute paths work; these custom tools are not on the ambient PATH. C++20 and Zen5 flags were accepted and `__cplusplus=202002L`/AVX2 verified by preprocessing. This does not test a new PE or physical Ryzen.

Use the existing `validating-chess-simd` skill. Relevant recovered commands are in `validation/see-proof-reuse-windows-20261021/{commands.json,validation-driver.py,PINNED-TOOLS.json}`. The old driver is **historical reference**, not a new-net runner: it binds a different source commit and requires the unchanged-network signature 334752. Do not run or rewrite its closed evidence.

## 1. Freeze and export only after root supplies the chosen network

Set task-specific paths to fresh, nonexistent source/build/evidence directories. `BASE` is exactly `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`, not the live working tree or an older checkout. Preserve the chosen include's original path/hash and training/selection evidence. Label the output a **trial, not Elo accepted**. Source metadata remains 6.4.24 because changing version headers would violate the net-only contract; distinguish the filename by network SHA.

```bash
FORGE_WIN_ROOT=/workspace/.cloud-setup/nnue-final-windows-attempt1
FORGE_WIN_SOURCE="$FORGE_WIN_ROOT/source"
FORGE_WIN_BUILD="$FORGE_WIN_ROOT/build"
FORGE_WIN_EVIDENCE="$FORGE_WIN_ROOT/evidence"
FORGE_WIN_INC=/ABSOLUTE/FROZEN/CHOSEN.inc
FORGE_WIN_NET_SHA=ROOT_SUPPLIED_64_HEX_SHA256
FORGE_WIN_PYTHON=/workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python
FORGE_WIN_CMAKE=/workspace/.cloud-setup/venv/bin/cmake
export LLVM_MINGW_ROOT=/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1

"$FORGE_WIN_PYTHON" -B /workspace/forge-nnue-handoff-20261023/windows-final-net-trial-preparation-attempt1/export_trial.py \
  --inc "$FORGE_WIN_INC" --sha256 "$FORGE_WIN_NET_SHA" \
  --source "$FORGE_WIN_SOURCE" --manifest "$FORGE_WIN_EVIDENCE/source-freeze.json"
```

The helper was syntax-checked only, not executed to export source. It exports all 74 non-pyc source/build/test/tool files directly from the original Git blobs, including `bench/` and fixtures, verifies all bytes, then changes exactly `src/nnue_weights.inc`. Three historical tracked pyc files are omitted explicitly. It validates H128/residual=1 using the existing include parser and records that parser's hash. Every `src/`, `include/` and CMake byte is checked against base1ab except the chosen include. No worktree or Git write. An include identical to the old network is deliberately rejected as a purported new-net trial.

Preserve failure/partial directories. Never edit source to force a passing test. Do not select a network merely to obtain an executable.

## 2. Fresh strict Release build

Save both commands, their environment, stdout/stderr and actual return codes before interpreting success. Check the fresh build path does not exist first. Export `PATH` with the verified toolchain bin and `/usr/bin:/bin` if the later runner lacks standard utilities; do not choose another compiler implicitly.

```bash
"$FORGE_WIN_CMAKE" -S "$FORGE_WIN_SOURCE" -B "$FORGE_WIN_BUILD" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE="$FORGE_WIN_SOURCE/tools/windows-zen5.cmake" \
  -DCMAKE_MAKE_PROGRAM=/usr/bin/gmake \
  -DPython3_EXECUTABLE="$FORGE_WIN_PYTHON" \
  '-DCMAKE_CXX_FLAGS=-march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto' \
  '-DCMAKE_EXE_LINKER_FLAGS=-static -fno-lto' \
  -DFORGE_NATIVE=OFF -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
"$FORGE_WIN_CMAKE" --build "$FORGE_WIN_BUILD" --parallel 1
```

Use no `-march=native`, fast-math, FMA contraction or LTO. The recovered full Windows24 j1 build took 90.86 seconds; this is a historical diagnostic, not a promised duration or speed comparison. A bounded full trial build is practical with the currently present toolchain. Preserve CMakeCache, all flags/link commands, compile_commands and exact PE/core/object hashes. Rehash the source against `source-freeze.json` after every stage.

## 3. PE, code generation and functional Wine checks

Use these exact established absolute tools:

```bash
FORGE_WIN_WINE=/workspace/.cloud-setup/wine/usr/lib/wine/wine64
export WINEPREFIX=/workspace/.cloud-setup/wine-prefix-ready
export WINEDEBUG=-all
export XDG_CACHE_HOME=/workspace/.cloud-setup/font-cache
"$LLVM_MINGW_ROOT/bin/llvm-readobj" --file-headers --coff-imports "$FORGE_WIN_BUILD/forge.exe"
"$LLVM_MINGW_ROOT/bin/llvm-objdump" -d --no-show-raw-insn "$FORGE_WIN_BUILD/forge.exe"
```

Retain complete raw PE/import/disassembly streams. Require AMD64 PE, resolved standard Windows imports, expected vector NNUE instructions and no emitted `vfmadd/vfmsub/vfnmadd/vfnmsub` arithmetic; preserve a machine-readable code-generation check. This supplements inference parity rather than proving it. The old `tools/check_nnue_simd.py` invokes `objdump` by PATH; use the verified reader/disassembler explicitly or a declared evidence-only launcher, not a silently different tool.

Run all nine existing C++ test executables under Wine, serially, each with its own original output/error/return-code receipt:

`forge_tests.exe`, `forge_correction_history_tests.exe`, `forge_runtime_psqt_tests.exe`, `forge_pawn_span_tests.exe`, `forge_nearest_pawn_tests.exe`, `forge_pv_metadata_tests.exe`, `forge_tt_tests.exe`, `forge_rule50_tests.exe`, `forge_legal_witness_tests.exe`.

Command form is `"$FORGE_WIN_WINE" "$FORGE_WIN_BUILD/TEST.exe"`. Legal witness additionally requires the two exact source fixture paths translated to Wine's Z: drive, e.g. `Z:\workspace\...\source\tests\legal_witness_fixtures.tsv` and `Z:\workspace\...\source\tools\openings\forge-10000.epd`. The core test includes established perft expectations 197281/97862/43238/9467/62379/89890 at its frozen depths. Keep every test assertion.

Create an evidence-only `/bin/bash` launcher outside source that exports the Wine environment above and ends with `exec ABSOLUTE_WINE ABSOLUTE_TRIAL_FORGE_EXE "$@"`. Then run the five original Python tests with the explicit host Python:

```bash
"$FORGE_WIN_PYTHON" -B "$FORGE_WIN_SOURCE/tools/match/test_match_tools.py"
"$FORGE_WIN_PYTHON" -B "$FORGE_WIN_SOURCE/tools/match/tests/test_windows_validate.py"
"$FORGE_WIN_PYTHON" -B "$FORGE_WIN_SOURCE/tools/uci_regression.py" ABSOLUTE_WINE_LAUNCHER --log ABSOLUTE_NEW_UCI_LOG
"$FORGE_WIN_PYTHON" -B "$FORGE_WIN_SOURCE/tools/ponder_regression.py" ABSOLUTE_WINE_LAUNCHER
"$FORGE_WIN_PYTHON" -B ABSOLUTE_EVIDENCE_OWNBOOK_WINE_ADAPTER ABSOLUTE_WINE_LAUNCHER ABSOLUTE_NEW_OWNBOOK_JSON
```

For OwnBook, reproduce only the existing path adapter from the historical validation driver: copy the pristine script to evidence, set its ROOT to the new source, translate the two sent book filenames and two expected messages from Linux paths to Wine Z: paths. Retain the original bytes, exact unified diff and all five transition assertions. Do not alter the exported production script. This is the only required test-path adaptation. Do not launch ordinary cross-build CTest blindly: its Python UCI tools otherwise try to execute a PE directly on Linux.

All 14 original configured checks must earn their own new result; a historical count/pass is not evidence. No timed Wine matches. If practical, additionally cross-link the current hash-pinned NNUE probe against this new Windows core outside source and run the 2048-position parity script through a Wine launcher with **explicit chosen `--weights`**, preserving a separate candidate-specific result. Existing old-network or Linux-only parity cannot qualify this exact Windows network binary.

## 4. First genuine new-net bench, then repeatability

After functional checks, start a fresh process and feed the same existing bench input bytes `bench 11\nquit\n`. The code creates a 16-MiB exclusive, single-thread bench searcher. Retain original stdin/stdout/stderr and return code. Require exactly one valid positive `info string bench depth 11 nodes ...` signature; **its node count is unknown before execution**. Freeze this first actual node count with the exact engine/net/source hashes and raw stdout hash. Then run the same immutable binary once more in another fresh process and compare the node count against that freeze. Preserve both captures even on failure.

Do not require old Windows 334752, Linux 292545, or any other old-net signature. Changed weights can legitimately change the search tree. Do not overwrite the first signature after a different result, infer NPS from Wine, or call the repeat a speed/strength result.

## 5. Trial artifact and remaining limits

Package the exact tested `forge.exe` as `forge-6.4.24-nnue-NETSHA12-trial-zen5.exe`, its SHA256, the exact chosen include/hash, license, all source hashes, build flags and original evidence. Describe it as a **Windows x64 Zen5 NNUE trial, not Elo accepted**. Source and accepted development branch remain unchanged. A Wine pass is not native Windows/Ryzen validation; the user or independent crew must run the delivered bytes on the real Ryzen7 9850X3D and complete the established external strength acceptance protocol. Do not claim Stockfish superiority from training loss, inference parity or bench nodes.

Current stop point: no chosen final include has been supplied to this subtask. Wait for root's explicit immutable path/SHA before exporting or building.
