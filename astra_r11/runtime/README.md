# R11 CPU test-runtime continuation — UNPROVEN

Official CPython 3.12.10, pip and all 31 original R10 NumPy2.5.4 dependency wheels are downloaded, hash verified and retained under `D:/a11/runtime`. Only the small Python/pip bootstrap archives were unpacked in PowerShell; the interpreter and Python checks have not run. The external GPL chess1.11.2 source archive is downloaded for test-tool use only. Nothing is installed in Forge or the live trainer.

`prepare_runtime.ps1` reproduces the official bounded downloads and small bootstrap extraction. `prepare_suite.ps1` records the one-time copying of 32 R10 source/fixture files, including 15 byte-identical test files, from the checked-in R10 source binding. The unused historical F: handoff tool is excluded. The copied runner was subsequently adapted here and is the version to execute; do not rerun the copy script over this committed directory. The 73 original assertions are unchanged. The only datafilter implementation change is the owned artifact root, a10 to a11.

The R11 runner combines the staged lane guard with R10 tip's NumPy2.5.4, explicit pytest log and recorded optional-alias behavior. It preserves runtime/source/DLL/toolchain before-and-after binding and forbids training loops/optimizer updates. Its deadline emits a traceback without killing; pytest stops cooperatively at the next test. A single stuck native call cannot be forcibly bounded under the no-kill policy, so expiry is not a passing completion receipt.

The parent Python audit hook refuses F:, a10, `.nnue` and queue/control opens and restricts writes to a11. It is not inherited by subprocesses. A separately pinned `sitecustomize.py` installs forbidden-open/outside-root-write checks in normal Python children through explicit PYTHONPATH. Those child commands were inspected to use neither `-I` nor `-S`, which would bypass this startup hook. Windows trailing-dot/space, stream and device-prefix aliases are refused before normalization; existing ancestors are checked root first before descendants. This behavior needs native tests and is not an OS sandbox. Existing child test commands use synthetic owned files and inherit D-only caches, disabled bytecode, hidden GPU devices, Idle priority and admitted affinity. The native compiler and external imports remain reviewed dependencies, not sandboxed code. No .nnue file has been opened during this preparation.

The direct archive assembler imports only Python's standard library. It verifies archive hashes, bootstrap extracted identities, wheel names, sizes and symlinks, preserves licenses and writes a complete `RUNTIME_FILES.json`. It does not import Torch, NPT or run package setup/build scripts. It is unrun and still needs exact-candidate review and safe-lane admission.

Prepare captures every runtime source/fixture/helper file, copied-source manifests and immutable runtime input manifests; fixtures mode also captures the complete gameprov tree. PowerShell verifies every extracted Python executable/DLL/stdlib/development file and pip bootstrap file against the two literal-pinned official archives, including an exact file census, before any Python start. This complete bootstrap snapshot is captured at Prepare and verified again at Run and after exit. Run also rechecks the complete task candidate before startup and after exit. The wrapper validates job/manifest/binding/admission paths before reads or writes; its JSON writer independently enforces the owned root and root-first reparse checks. It clears inherited PYTHON variables and pytest option/plugin injection, supplies exact PYTHONPATH plus disabled user-site/bytecode, clears GPU visibility, and restores the caller's environment afterward.

The first next-job check is `fixtures`: stdlib-only unittest discovery pinned to exactly 26 gameprov plus four direct runtime-guard tests (30 total), with preserved D-only temporary artifacts and JSON/log results. It needs no package installation or external NPT/toolchain access. It does not test automatic child-hook startup; that remains separate native qualification. After review and a clear CPU2/3 lane, execute these one at a time from PowerShell:

```powershell
& 'D:\a11\wt\astra_r11\runtime\launch_runtime.ps1' -Mode fixtures -Tag fixtures01 -Action Prepare
# Review the exact prepared candidate before Run; no package install needed.
& 'D:\a11\wt\astra_r11\runtime\launch_runtime.ps1' -Mode fixtures -Tag fixtures01 -Action Run
& 'D:\a11\wt\astra_r11\runtime\launch_runtime.ps1' -Mode assemble -Tag assemble01 -Action Prepare
# Review the exact prepared command/runner/helper hashes before Run.
& 'D:\a11\wt\astra_r11\runtime\launch_runtime.ps1' -Mode assemble -Tag assemble01 -Action Run
& 'D:\a11\wt\astra_r11\runtime\launch_runtime.ps1' -Mode preflight -Tag preflight01 -Action Prepare
# Review the exact prepared preflight binding, then run it.
& 'D:\a11\wt\astra_r11\runtime\launch_runtime.ps1' -Mode preflight -Tag preflight01 -Action Run
& 'D:\a11\wt\astra_r11\runtime\launch_runtime.ps1' -Mode suite -Tag suite01 -Action Prepare
# Review the exact prepared suite binding, then run it.
& 'D:\a11\wt\astra_r11\runtime\launch_runtime.ps1' -Mode suite -Tag suite01 -Action Run
```

Never bypass a refusal. Admission scans process affinity/command metadata without changing other processes and rejects unrelated pinned masks12/15 and timing jobs; it also requires CPU2/3 load below50% and8GiB free RAM. Normal all-CPU processes remain normal load. Launch receipts and refused admissions stay under `D:/a11/runtime-runs`. All writes remain beneath a11; C30GiB and D50GiB plus reservation floors apply. The helper retains narrow read-only NPT/toolchain exceptions without allowing dataset/queue or toolchain writes.

Checks executed: 17 small PowerShell path/storage/alias/root-first assertions, the synthetic lane-conflict predicate, and five guarded-writer refusal checks passed; no native child was started. Complete candidate capture and deliberate in-memory hash drift refusal were also checked without launching a child. PowerShell independently verified the exact census and bytes of all 1,791 extracted bootstrap files (44,598,362 bytes) against the two pinned official archives during `reviewbootstrap01` Prepare. PowerShell source parses, original test-file hashes and staged CR identities are checked separately. Python syntax, synthetic fixtures, archive assembly, native preflight and all73 tests remain UNRUN while the shared lane is occupied. No PASS claim for the data or runtime is implied by these setup checks. All `review*` preparation receipts are static-check artifacts, not approved launch requests; subsequent reviewed edits invalidate their candidate captures. `fixtures01` is reserved for the first reviewed admission attempt.
