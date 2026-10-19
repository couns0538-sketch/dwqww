# Independent hosted NNUE performance audit

Run **39334266771, attempt 1**, results commit `b3bf48525540e64db12b592c913b160298bad6d1`: the audit passes, and the experiment correctly reports **failed primary calibration; performance inconclusive**. No A/B or kernel timing phase ran. No NPS, speedup or Elo gain is established. No retry or gate bypass was performed.

All 12 retained calibration processes used the same archived 6.4.9 baseline executable, exited normally with wait status 0, had empty stderr and exact twelve-bench input, and completed 12 depth-11 bench records with 419798 nodes each: **144 complete benches**. Recorded CPU equals wait4 user plus system time. The launcher verifies singleton CPU 0 affinity. A second independent raw review confirms command, status, report and commands.jsonl agreement.

Both CPU and wall controls fail the preregistered gate: pairs 3 and 6 exceed 1.03, and both medians exceed 1.01. Independent ratios match the archived report exactly.

| Pair | CPU A/B | Wall A/B |
| --- | ---: | ---: |
| 1 | 0.977974697033 | 0.977240285970 |
| 2 | 1.014298593497 | 1.013542364934 |
| 3 | 1.032938600280 | 1.033737565559 |
| 4 | 1.009675197273 | 1.007905775728 |
| 5 | 0.978025677298 | 0.979577753975 |
| 6 | 1.047224906804 | 1.048432497494 |

CPU median: **1.011986895384661**. Wall median: **1.010724070330779**.

Actual source tars are byte-identical to fresh read-only Git exports of 6.4.9 `4edda780c68a742f20565d4e6a54a0c99a2c88a6` and 6.4.10 `36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`; their source manifests cover 66 and 68 files. Both 13-translation-unit builds use GCC 14 with strict generic x86-64-v3 flags and no LTO. Both full CTest suites pass 9/9. All 35 recorded build/check commands exit 0. The same candidate-commit drivers link to each retained core. Actual retained disassembly contains out-of-line update calls and no core LTO sections. Both NNUE streams are byte-identical across cores and match prior gold SHA-256 values: 4,097,860 and 21,192,328 bytes. Network source bytes match.

All 43 frozen files are retained, including both source tars, core archives, engine/helper binaries and driver sources. Build and workflow-final manifests exactly match actual bytes. The runtime final check covers 44 inputs with no changed, missing or new inputs. Detailed checks and actual artifact hashes are in independent-audit.json.

The builder-stage `timing_started=false` field is a placeholder; raw performance records demonstrate that calibration executed. Candidate correctness/preflight execution is distinct from A/B timing. All original evidence remains intact. This audit executed no engines, builds, benchmarks or retries.
