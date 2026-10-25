# Forge Sol Windows qualification contract, 2026-10-25

The delivered runner is `forge_sol_int16_winqual_script_20261025.ps1`. It has not run on native Windows or a verified Zen5 CPU here. Native results and a 3% gain remain **UNVERIFIED**.

Run from a dedicated PowerShell 7 x64 process after placing the supplied frozen source trees and `forge_sol_int16_build_manifest_20261025.json` beside the script:

```powershell
pwsh -NoProfile -File .\forge_sol_int16_winqual_script_20261025.ps1
```

The defaults require `C:\msys64\ucrt64\bin\g++.exe` and `objdump.exe`. `-GppExe` and `-ObjdumpExe` can select another installation, but the invoked compiler must still report MSYS2 GCC **15.2.0**, target `x86_64-w64-mingw32`. The script rejects Linux, Wine, non-x64 hosts, CPUs other than AuthenticAMD family 26 (0x1A), and multi-processor-group systems where mask 0xF would not identify global CPUs 0-3 unambiguously. It records the full CPU name and identifier. Family identification is not a proof of an exact retail CPU model or bare-metal execution.

The runner verifies every source-file SHA256 before and after compilation, rejects extra/missing files and reparse points, and requires the original H256 e12 network SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. It records the complete input manifest, tool hashes, exact invocations, compiler output, and executable hashes in **one** newly created `forge_sol_int16_winqual_results_20261025.txt`. It refuses to overwrite any previous report or executable. Run a new supplied folder for a new attempt; preserve a failed attempt.

The exact recovered build flags, in order, are:

```text
-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread
```

There are no extra AVX512/alignment defines. Both engines use `src/{bitboard,board,book,eval,eval_params,nnue,search,uci}.cpp`. The actual-core parity helper replaces `src/uci.cpp` with `tools/nnue_int16_parity.cpp` from the int16 tree. Outputs are `forge_sol_buffer_only_20261025.exe`, `forge_sol_int16_20261025.exe`, and `forge_sol_int16_parity_20261025.exe`. GNU objdump rejects dynamic GCC/libstdc++/winpthread imports. Static Windows executables still import Windows system DLLs.

The manifest schema is:

```json
{
  "protocol": "forge_sol_int16_winqual_20261025",
  "compiler": {"version":"15.2.0","target":"x86_64-w64-mingw32","distribution":"MSYS2"},
  "flags": ["-std=c++20","-O3","-DNDEBUG","-DFORGE_NNUE_HIDDEN=256","-ffp-contract=off","-fno-fast-math","-march=znver5","-static","-pthread"],
  "source_trees": {
    "buffer": {"directory":"forge_sol_buffer_source_20261025","network_sha256":"<64 hex>","files":[{"path":"relative/path","sha256":"<64 hex>"}]},
    "int16": {"directory":"forge_sol_int16_source_20261025","network_sha256":"<64 hex>","files":[{"path":"relative/path","sha256":"<64 hex>"}]}
  }
}
```

`files` enumerates every file in its tree. A tree hash is SHA256 of UTF-8, BOM-free, ordinal-path-sorted lines `lowercase_sha256` + two spaces + forward-slash relative path + LF. Tree directories must be distinct and inside the runner folder. The int16 tree includes the parity driver. Network and source manifests establish provenance; a compiler version string and matching hashes are not an independent compiler/toolchain reproduction.

## Qualification sequence

1. Both builds first pass OFF bench depths 11/13/16/20/22 with **308972 / 745494 / 2460422 / 11901452 / 31111774** nodes. A mismatch stops later work. Bench 11 is each executable's first engine test.
2. The combo build advertises OFF-default `NnueInt16`, acknowledges activation without fallback, and measures ON nodes at all five depths. These native measurements are frozen before timing. Linux ON counts **335382 / 850773 / 3130100 / 10757244 / 27884195** are printed as unverified cross-platform references; matching them is not a native gate or an identity claim. Every later ON bench20 must match its frozen native count.
3. Buffer OFF, combo OFF, and combo ON each pass start-position perft5 **4865609** and standard Kiwipete perft5 **193690690**. The buffer build is never represented as ON.
4. Full `objdump -d -t -C --no-show-raw-insn` streams are parsed. Every emitted symbol containing `forge::nnue::`, including internal functions and compiler clones, has a recorded instruction/FMA count. Every defined NNUE function in the COFF symbol table must also have parsed instructions in the disassembly. At least one such symbol and recognized PE-x64 format are required. Any FMA variant in any such function fails. FMA in external static runtime functions is attributed by function and counted separately. Unknown-scope FMA, an undecoded NNUE instruction, or malformed parser input fails. This covers emitted named functions with no LTO, rather than all semantically inlined NNUE operations in other functions. The bounded report includes a disassembly prefix and complete NNUE/FMA inventory; it does not retain the entire external-runtime disassembly.
5. The existing actual-core `tools/nnue_int16_parity.cpp` runs with arguments `10000 20261025`, without a FEN output-file argument. Full JSON includes corpus hash, mean/max/p99 cp error, sign/zero crossings, all state mismatch counters, and special-move coverage. Exactly 10,000 unique four-field FENs, zero state/lane/oracle/parent/in-place mismatches, mean error at most 2 cp, maximum at most 30 cp, and the driver's special-move thresholds are required. This is numerical-tolerance parity, not float/int16 bit exactness. The FNV corpus hash is a corpus identifier, not a cryptographic digest of a retained FEN file.
6. At least eight ABAB blocks run fresh processes at bench20: A=buffer OFF, B=combo ON. One block is A1/B1/A2/B2; its supplementary block ratio is `sqrt((B1/A1)*(B2/A2))`. The primary result is the median of **all 16 adjacent B/A ratios** from eight blocks. The native NPS screen passes only when this primary median is **at least 1.03**, all checks finish, and final cleanup is clean. This statistic and threshold are printed before the first child runs. The report retains all NPS samples, all adjacent ratios, every supplementary block ratio, and both medians. No outliers are removed. Eight blocks mean 32 fresh timed engine processes, eight block observations and 16 adjacent A/B pairs. The 3% screen is a descriptive NPS threshold, with no A/A noise gate, confidence interval, or strength/Elo acceptance. A failed/incomplete final status resets the NPS screen to UNVERIFIED, even if partial ratios exceed 1.03. ON and OFF search different nodes because quantization changes evaluation.

## Resource contract and unavoidable limits

An inline C# Win32 helper creates a shared JobObject containing the dedicated PowerShell host and all newly launched descendants. It reads back and verifies the exact resource-limit flags, including the absence of kill flags. It applies CPU mask **0xF**, **Idle** priority and a **3 GiB aggregate private committed-memory limit**. The 1 GiB margin is below the requested 4 GiB budget; Windows does not offer an equivalent hard aggregate working-set/RSS JobObject cap. File-backed/shared pages and OS overhead are not identical to private commit, so a literal physical-RAM guarantee is unavailable. Initial PowerShell startup and inline-helper compilation precede job assignment. The runner logs the job's peak committed memory.

Every direct child starts suspended, inherits/is assigned to the job, verifies the job/mask/priority, and is resumed before any stdin command. Compiler descendants inherit the same job restrictions at creation. A control failure stops without fallback. A child already created suspended may remain suspended if controls cannot be verified; its PID is reported, with no termination attempt.

No process termination API, global process-name operation, or kill-on-job-close flag is used. Memory-cap allocation denial can still cause a tool's own OOM handling or exit; this differs from the script terminating a process and cannot guarantee every application survives allocation failure.

No new work is admitted after 43 minutes. Each direct child has a timeout of at most 300 seconds and the remaining work budget. Failure requests UCI `stop`, `quit`, then EOF; non-UCI helpers receive EOF. Cleanup waits at most two minutes and never beyond the original 45-minute target. All descendant PIDs are enumerated from the job; no new child is admitted while an earlier descendant remains. Failed children retain a bounded final stdout/stderr tail after cleanup, including late diagnostics. Cleanup-query errors still produce an UNVERIFIED final status. Any survivor yields `UNVERIFIED_UNCOOPERATIVE_CHILD_REMAINS`, never a successful speed result. Closing handles does not terminate surviving processes. Initial host/runtime setup, blocked OS operations, scheduler stalls, filesystem calls, and an uncooperative process make an unconditional hard 45-minute completion/cleanup guarantee incompatible with “kill nothing.” This gap is explicit rather than hidden behind a false guarantee.

All script-controlled writes and child working directories stay inside the supplied folder; TEMP/TMP/TMPDIR and DOTNET_BUNDLE_EXTRACT_BASE_DIR point there, and PSModuleAnalysisCachePath selects an in-folder dated cache file; HOME is never reassigned. Initial PowerShell startup may precede these process-local environment settings. A JobObject is a resource control, not a filesystem security sandbox: the supplied compiler/engine binaries remain trusted. The runner does not inspect, change, or terminate unrelated processes.

## Verification and negative test plan

Software verification completed with private PowerShell 7.5.2 on Linux: four PowerShell scripts parsed, the Job1 inline C# and PGO C# sidecar compiled without Win32 calls, **44 fixture assertions passed**, valid/escaped/mutated/extra/missing source-tree cases behaved correctly, Linux rejected with native validity false, and a repeated attempt preserved the report byte-for-byte. A static older-PE parser fixture reconciled all seven NNUE definitions with seven disassembly headers. Zero engines or performance jobs were started. The first PowerShell data-directory startup failure and the first test-harness Marshal.SizeOf overload failure were preserved, corrected, and followed by passing attempts. Evidence is in `forge_sol_software_tests_20261025/forge_sol_software_verification_20261025.json` and its named attempt logs. These checks provide no native Windows/Zen5 result.

The supplied software fixture command is `pwsh -NoProfile -File ./forge_sol_int16_winqual_negative_tests_20261025.ps1`. It loads function definitions and compiles the extracted C# without running the main block or invoking Win32. It starts no engine/compiler process and makes no speed claim.

Software checks that can run on Linux are syntax parsing; compilation of the extracted C# helper without invoking Win32; full-script Linux rejection in a fresh temporary copy; report-overwrite rejection; AST/parser fixture tests for strict bench/UCI/disassembly handling; and static absence of termination APIs. None is native execution evidence.

Before trusting a native result, exercise controlled Windows fixtures in new folders: wrong CPU/compiler/version/flags/source hashes; missing/stripped NNUE symbols; FMA inside a NNUE symbol versus external runtime only; bad/missing/multiple bench lines; OFF node mismatch; missing ON activation and explicit float fallback; wrong perft counts; bad parity counts/errors/state/coverage; mutation of a frozen executable; early child failure; excessive stdout; a descendant retaining stdout; and a child ignoring stop/quit/EOF. Each must fail closed, preserve the sole report, and leave unrelated processes untouched. Test report and executable no-overwrite behavior separately. Use a cooperative memory-allocation fixture to observe job cap denial, not an uncontrolled OOM workload. Native CPU/Idle/memory/descendant behavior and the real 45-minute workload remain unverified until performed on the user's Windows machine.
