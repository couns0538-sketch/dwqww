S26 net-batch preparation, 2026-10-26

This stage supplies a runnable batch tool, frozen documentary references, an explicit known-failure allowlist, and synthetic process tests. No genuine Forge build, engine run, WAC timing result, or CTest qualification was performed for S26. A separately authorized tiny original C++20 compile-only probe passed; its1112-byte relocatable object was never executed. Root owns the later native run and integration order.

The shell launcher delegates to the Python tool. Native mode requires absolute `--base`, repeated `--net`, new `--out`, `--bench-ref`, `--allowlist`, `--suite`, and existing `--lock-file` paths. `--compare-lock DIR` privately builds and screens that directory's own net once, then reports candidate minus lock node/WAC differences. New bases require input files and reviewed reference/allowlist entries, without editing tool paths. Every output path passed to CMake, CTest, objdump, engine capture, and receipts is absolute. All subprocess commands are argv lists.

Each net receives its own new source copy and build directory. Only the copied `src/nnue_weights.inc` is replaced. The original source and copied source are hashed before/after; engine and NNUE object hashes are retained on success and failure. The five depths are 11/13/16/20/22, in fresh processes with Threads=1, Hash=16, OwnBook=false. The very first engine process is a bare bench11, checked against configured bench11 and the supplied frozen net reference. Net-only node changes are compared to their own external references, never learned from a freshly built binary.

The batch acquires the caller's existing shared flock file with a read-only descriptor. It changes only its own nice value to19 and affinity to one allowed CPU; children inherit both. The lock file's bytes are untouched. No host limits are changed. RAM checks require at least3GiB MemAvailable before builds and UCI sends, with monitoring while owned processes run. RAM loss, timeout, SIGINT or SIGTERM stop owned work, terminate only process groups created by this batch, wait for them, and retain failure receipts. Ordinary per-net qualification failures produce failed tables and continue with later requested nets; RAM loss and input mutation stop the batch.

S07's exact hash-bound Capture/configure/parse_bench/WAC parser/scorer provide UCI handling and legality. Its OFF/ON sweep and20% node guard are deliberately not used for net-only changes. S05_v2's checker scans objdump output for both executable and NNUE object, requiring FMA0 and its vector output contract. S01 supplies the exact pin cases and raw evidence format; S07 owns the observation process lifecycle. `forge_sol_S26_dependencies_20261026.json` contains full paths and SHA256 values. Dependencies execute the exact checked source bytes, without reading or writing external bytecode caches. S27 provides the canonical recipe flags and pure compiler/cache/production-signature checks. S26 additionally checks every actual production/CTest/support TU before and after building: exactly x86-64-v3/znver5/H256 and C++20, strict float, no conflicting macro/ISA/std flags, no PGO/LTO/response files/wrappers, and one pinned compiler. Compiler version/binary hash, per-TU source hashes, actual compile_commands, cache and link-recipe hashes are retained. Python-chess must already be available; no package is installed by the batch.

The allowlist binds reviewed test-source SHA256 values, source-specific known-case patterns/counts, and per-net SHA256 profiles. WAC001 and promotion expectations in tests are never rewritten. Unlisted FAIL, PIN_MISMATCH, missing/duplicate/skipped test cases, crash/timeout statuses, unexpected failing test names, and incomplete reviewed diagnostic counts fail qualification. Literal reviewed pin entries require both net and test-source identity. They can cover only the documented WAC001/promotion cases; an arbitrary board-corruption failure cannot be allowed by a pin entry.

`--record-pins` writes observations, an UNREVIEWED proposal, and an unapplied diff that changes documented-pin constants only, when the exact source contract is recognized. It retains the original expectations and never applies that diff to either input or private test source. The proposal includes exact source/net hashes and an UNREVIEWED allowlist entry for owner/CR inspection. Unknown failure cases remain in an unreviewable list and stay blocking. There are no supplied reviewed per-net S01 pin files for f019–f023. Their pin qualification remains unverified until observation/review, or until their unmodified tests satisfy the original expectation/current documented pin.

The canonical configure recipe explicitly uses Release, FORGE_NATIVE=OFF, IPO=OFF and compile-command exportON, with `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`. `--cxx` defaults to the resolved `/usr/bin/c++`; its exact path is pinned into CMake and checked against every TU. No host-native, fast-math, PGO or LTO recipe is accepted. The earlier0e24 preparation source/tests are preserved in `forge_sol_S26_frozen_v1_0e24_20261026/`; it was corrected before any Forge build. Recipe-only versionca969f is independently preserved in `forge_sol_S26_frozen_v2_recipe_20261026/` before the separate WAC evidence-flow change.

A WAC score-reference failure remains blocking but no longer discards remaining pin observations and CTest. These checks run once in the same attempt, and a passing CTest never overrides the WAC failure. Actual WAC subprocess/legality failures still abort.

Run the synthetic suite on CPU0:

```sh
taskset -c 0 python3 -B -m unittest discover \
  -s /workspace/forge-pack24-20261026/S26 -p 'test_*.py' -v
```

Those tests execute real Python child processes standing in for CMake, CTest, objdump, and a deterministic legal UCI engine. They do not compile C++ or run a real chess engine. The success fixture builds two distinct private net copies plus a compare-lock copy from cwd `/`, checks all300 WAC positions through S07, and remains under1MiB output. Temporary fixtures are removed after each test. RAM-drop and cancellation tests verify owned-child waits. Logs containing SYNTHETIC are harness evidence only.

The existing `forge_sol_S26_f019_f023_DOCUMENTARY_sample_20261026/` contains one imported table per net and a result JSON. It verifies the supplied CR document and actual net hashes and executes no engine. f019 WAC1000=286 is a CR pass; f020279 is historical INFO/unconfirmed; f021287 is an earlier full run. f022/f023 explicitly had WAC disabled, so their reference values stay UNKNOWN. Native measurements for those two cannot establish a within3 reproduction claim without an independent external reference. All imported FMA/CTest local-result cells remain UNVERIFIED.

After root closes conflicting native leases, a concrete native invocation for the supplied B source and f019 is below. This command has NOT been executed. The supplied empty S26 lock is usable only when root chooses it as the shared resource lock; otherwise pass root's designated existing shared lock. Use a NEW output name each time.

```sh
PYTHONPATH=/workspace/.cloud-setup/venv/lib/python3.12/site-packages \
/workspace/forge-pack24-20261026/S26/forge_sol_S26_netbatch_20261026.sh \
 --base /workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src \
 --compare-lock /workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src \
 --net /workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files/03b_nets_f019_f023_s197_s198/resid_h256_e20_f019_b06_ep20.inc \
 --out /workspace/forge-pack24-20261026/S26/forge_sol_S26_NATIVE_f019_NEW_20261026 \
 --bench-ref /workspace/forge-pack24-20261026/S26/forge_sol_S26_bench_refs_20261026.json \
 --allowlist /workspace/forge-pack24-20261026/S26/forge_sol_S26_allowlist_20261026.json \
 --suite /workspace/forge-sol-next-20261024/int16-review/wac300.epd \
 --lock-file /workspace/forge-pack24-20261026/S26/forge_sol_S26_resource.lock \
 --cmake /workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake \
 --ctest /workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest \
 --objdump /usr/bin/x86_64-linux-gnu-objdump --cxx /usr/bin/x86_64-linux-gnu-g++-14 --cpu 0 --record-pins
```

Append further absolute `--net` inputs for f020–f023 when root budgets the retained build trees and WAC time. `result.json`, each net's `table.json`/`table.md`, raw captures, command receipts, source/binary hashes, and `SHA256SUMS.txt` remain under the new out directory. No speed, PC comparability, playing-strength, or engine-adoption conclusion follows from the synthetic suite or documentary import.

Idea source: original batch orchestration and tests written for the supplied S26/S43 requirements, reusing the project's hash-bound S07, S05, and S01 tooling. No external engine implementation was copied.
