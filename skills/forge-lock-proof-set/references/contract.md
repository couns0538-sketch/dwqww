# Lock-proof native adapter contract

Python 3.10+, standard library. The runner executes explicit argv without a shell, serially, in new stage directories; no discovery of arbitrary current engine commands. It is not an OS sandbox. Adapters are reviewed executable code and must respect all user restrictions. A subprocess timeout terminates only the runner's owned direct adapter, stops later work and reports failure; cleanup of descendants is not certified. Use adapters which manage their own finite native workloads, never production trainers/gates. No engine, Windows or PGO run is supplied by the fixture tests.

Top-level contract JSON:

| Field | Required value |
|---|---|
| `schema` | Integer 1 |
| `evidence_scope` | `native` only for actual reviewed native adapters, or `fixture` for helper tests |
| `baseline_commit`, `candidate_commit` | Full 40-hex source revisions |
| `network_sha256` | Actual 64-hex network hash; use lowercase throughout |
| `max_worker_threads` | Integer >=4 when executing T4; positive integer when T4 is explicitly skipped. Records actual authorization, never overrides the grok-pc launcher. |
| `identity_mode` | Optional `behavior-changing` (default) or `exact`. Unknown values fail before execution. |
| `expected_off_nodes` | Nonempty depth-string to integer-node map from current lock pins |
| `off_options`, `on_options` | Different UCI name/value objects; must match the emitted receipts |
| `inputs` | Pinned file objects `{role,path,sha256}`; required roles compiler, recipe, source, network, baseline_binary. Exactly one baseline_binary. Include every adapter, interpreter and other execution dependency. Paths may be absolute or relative to this contract. |
| `stages` | Exactly build_a, build_b, off_pins, on_active, perft, smoke_t1, smoke_t4, asan_ubsan. Executed stages contain `argv` string array and positive integer `timeout_seconds`. Only smoke_t4 may instead contain exactly `{"skip_reason":"nonempty reason"}`. |

Each stage argv[0] must be an absolute executable path among the pinned inputs. Interpreter scripts must also appear among inputs; review this dependency inventory since the runner cannot discover all imports/dynamic libraries. `{stage}`, `{out}`, `{result}` tokens expand to the new stage directory, overall output and that stage's result.json. At least one argv value must include `{result}`. Native adapters get stdin closed; they cannot prompt. Each adapter's actual exit code must be zero, plus a valid receipt. Its stdout/stderr/argv/exit and every regular stage file are hashed into the proof. Inputs and earlier candidate binary hashes are rechecked around execution; final evidence hashes are rechecked.

The runner copies the contract bytes it actually parsed into output/CONTRACT.json. A successful native report has the nine required check rows, resolved `identity_mode`, baseline/candidate source revisions, `contract_sha256`, `baseline_binary_sha256`, `candidate_binary_sha256`, `net_sha256`, and `tested_options={off:...,on:...}`. Each row references original evidence by path relative to REPORT.json's directory and SHA-256. Gate packaging must bind these hashes/options to the actual shipped artifacts; no same-name substitutions.

An explicit T4 skip creates only an `outcome.json` stating UNVERIFIED, the reason and `executed:false`; no adapter is launched and no native evidence is invented. Input and previous-binary identity checks still run. The runner then continues to ASan+UBSan. If all executed checks pass, overall status is UNVERIFIED, never PASS. A failure in any other stage retains fail-fast behavior, and a failure of the input checks at the skipped stage is still FAIL. Skip fields on another stage, blank reasons and a skip combined with argv/timeout fields are refused.

## Every adapter result.json

Object with `schema:1`, `status:"PASS"`, `source_commit` equal to candidate commit, `network_sha256` equal to the contract, `metrics` object and a nonempty `logs` list of `{path,sha256}`. Logs use relative forward-slash paths within that stage, no symlinks or path escape. Preserve the raw native outputs; do not replace them with a fabricated summary. The runner checks hashes/declared semantics, not whether the adapter told the truth.

Stage-specific metrics:

| Stage | Metrics |
|---|---|
| build_a/build_b | `binary` relative path; nonempty `profile_files` references; `compile_commands` list of recorded native compiler argv arrays: every command must keep effective LTO and `-ffp-contract=off -fno-fast-math`; an earlier command must generate profiles, and the final command must be the profile-use link with `-o` followed by the exact emitted binary path (relative to stage or absolute). Conflicting `-fno-lto`, ineffective `-flto=0`, FMA and unsafe-math overrides reject; final `-c/-S/-E` compile-only witnesses reject. Profiles must exist and hash-match. Record the actual generate/train/use phases, profile corpus and seeds in logs. Profile-use commands must contain GCC `-Werror=missing-profile -Werror=coverage-mismatch` or plain `-Werror`; explicit downgrades/suppressions of these diagnostics are rejected. Original logs/stdout/stderr are additionally scanned for missing/outdated-profile diagnostics. The runner does not infer complete compiler-profile consumption from filenames. |
| off_pins | `binary_a_sha256`, `binary_b_sha256`; `nodes_a`, `nodes_b` maps equal explicit pins; `options` equal off_options. |
| on_active | `binary_sha256` for build_a; `nodes` map with the exact same depths; positive integer `active_count`; `options` equal on_options. In default `behavior-changing` mode at least one node count must differ; in explicit `exact` mode the entire vector must equal expected_off_nodes. Additional build_b ON evidence is an adapter responsibility when required by the task. |
| perft | build_a `binary_sha256`; `startpos5:4865609`, `kiwipete5:193690690`. Canonical Kiwipete FEN below. |
| smoke_t1/smoke_t4 | build_a `binary_sha256`; `threads` 1 or4 exactly; positive integer `searches`; `completed:true`; integer `illegal_moves`, `crashes`, `time_forfeits` all0. Record actual UCI requests/results and legal-move oracle/test-suite checks. |
| asan_ubsan | `instrumented_binary` relative path; `compile_commands` showing combined `-fsanitize=address,undefined`; `sanitizers:["address","undefined"]`; `runtime_started:true`; positive integer `executed_tests`; integer `failures:0`. Retain full native test output and instrumentation/toolchain details. Original logs/stdout/stderr are also scanned for common ASan/LSan/UBSan error markers; this supplementary scan is not a complete sanitizer parser. |

Kiwipete: `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`.

Byte identity checks the two distinct, non-hardlinked final files. It does not prove that adapter authors did not copy a binary; independently review the native build logs and dependencies. GCC flag witnesses do not prove zero FMA instructions; where the project requires FMA=0, include a reviewed actual disassembly/count check in the adapter and retain its logs. Failed or absent required checks cannot become PASS merely through a known-failure label.

Exit0 means all declared native/fixture stage checks passed; exit1 means a completed proof has FAIL/UNVERIFIED rows; exit2 means the contract/output setup was blocked. `fixture` remains fixture even with exit0. Missing metrics, source/network mismatches, changed inputs, bad hashes, nonzero exits, timeout and output reuse block qualification. REPORT.json is not a signed attestation and does not prove playing strength.

Known kit v2.3 compatibility: its `-Wmissing-profile` commands plus fatal post-log validation do not currently satisfy this runner's `-Werror` compiler-witness requirement. No relaxation is included in the identity/skip change. A separate reviewed recipe-specific extension is required before submitting those actual witnesses; never add flags to a receipt that the compiler did not receive.
