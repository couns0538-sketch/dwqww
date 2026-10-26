# Forge S16 completion report — 2026-10-26

The existing v2 filter is now qualified through the complete 200k SQLite, writer and audit pipeline. This closes the previously deferred full-output test; it does not approve production data or change the engine. GitHub publication and ordered integration remain the lead agent's next delivery step.

The unchanged prepared v2 source SHA256 is `5dd0c009566bc5a8c8e06300a8541c5d130d458ca75266a432d1477d1d156332`. It imports the original Job D parser/writer SHA256 `6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3`; the old 21-test source is unchanged at `d817182610a63a76380aea4297464873f3098cfd103c1393f5349fa855329478`. These dependencies retain their original filenames and are not new implementations.

## Checks

| Check | Result |
|---|---|
| Fresh complete test suite, including the original 21 tests | PASS, 41/41 |
| Production refusal without authoritative game IDs; interleaved-text controls | PASS in suite |
| Caller-selected SQLite work dir, low-disk refusal, conflict counter, whole-shard MD5 controls | PASS in suite |
| Linux runner and paths containing spaces | PASS in suite, fixture inputs only |
| Full OFF pipeline on four synthetic 50k shards | PASS: 200000 retained, 0 dropped |
| Full t300 pipeline, first run | PASS: 157666 retained, 42334 dropped |
| Full t300 pipeline, independent repeat invocation | PASS: 157666 retained, 42334 dropped |
| Every t300 output, summary, removal ledger and MD5 manifest | PASS: byte-identical, without normalization |
| Output position overlap with supplied synthetic h000; output duplicate positions | PASS: 0 / 0 |
| Output POS/HCE fields equal selected original rows | PASS, independent direct-format scanner |
| Input/source SHA256 before vs after | PASS: unchanged |
| Read-only output modes and empty owned scratch after success | PASS |
| Real 013/014 position or authentic-game overlap | UNVERIFIED: absent inputs/authority |
| PowerShell/Windows and its RAM check | UNVERIFIED: runtime unavailable |
| Exact Python3.10 execution | UNVERIFIED: actual interpreter is Python3.12.14 |
| Production-scale scratch requirements | UNVERIFIED on owner data; estimate is not a guarantee |
| Training gain, speed gain or Elo gain | UNVERIFIED; no such experiment run |

The 200k input contains the four supplied synthetic training shards; the separate 50k h000 file is used only as the supplied diagnostic holdout. Original 013/014 and game IDs are not invented. All generated summaries retain `production_eligible=false`, `sealed_for_training=false` and `game_overlap_verified=false`.

| Shard | Input | Kept at t300 | Draw/large-score drops | Loss/positive-score drops | Win/negative-score drops |
|---|---:|---:|---:|---:|---:|
| t00000 | 50000 | 39533 | 5288 | 2676 | 2503 |
| t01000 | 50000 | 39447 | 5174 | 2714 | 2665 |
| t02000 | 50000 | 39342 | 5378 | 2665 | 2615 |
| t03000 | 50000 | 39344 | 5282 | 2701 | 2673 |
| Total | 200000 | 157666 | 21122 | 10756 | 10456 |

No synthetic input position overlaps h000, no output position is duplicated, and no conflicting-label duplicate occurs in this particular sample. Planted cases exercise the missing conditions in the tests. Every OFF POS/HCE file is byte-identical to its provided input file, proving the full reader/writer control rather than just a count.

The MD5 manifest itself has identical MD5 `c169a23777c05d9fc8106e5ff6edd637` in both t300 runs. Individual POS MD5s are t00000=`5d9e2434592e39b3ea0a7b74dc33c87b`, t01000=`b50dc79bb56b5d09b75eb0a9dcbbc6ee`, t02000=`b13fb69dbe51f711b1acd686fb9970aa`, t03000=`80a98bd51479c1678fd7dff1f69697c4`. The complete actual per-file MD5/SHA256/size/mode index accompanies the evidence.

## Execution and evidence

All three full filter runs used the unchanged CLI with `--diagnostic-mode`, seed20261025, the four original training POS files, h000.pos, matching HCE, and fresh output/work paths. t300 adds `--disagreement-threshold 300`. Exact argv, original stdout/stderr, exit status, PID and owned-process observations are in the receipts. Each child alone was pinned to CPU4 at nice19, with a 1GiB address-space limit, sampled aggregate RSS ceiling1GiB and 600-second cutoff. The caller was not pinned or signalled. No timeout, retry or residual owned group occurred. Maximum observed group RSS was 38,985,728 bytes during the suite and about20.4MB during filtering; sampling is not an exact instantaneous peak. Durations are recorded solely as completion evidence, not speed comparisons.

The filter's preflight reserved 92,600,000 bytes for scratch and 76,498,576 bytes for new outputs on this sample, on one filesystem. Those conservative estimates were enforced before writing. No source/input deletion or overwrite, engine/compiler/GPU execution, trainer modification or PC execution occurred.

`forge_sol_S16_full_pipeline_result_20261026.json` SHA256 is `3d08da4ad7b45a7033f0797a9f32c5012fca506b8477fec45767cbffdb7ce1dd`; the complete output index SHA256 is `b349bb66e88b051233ee5e7eea2186da09d70b47429d29c5e59993741758df03`. The original generated outputs remain in `/tmp/forge_sol_S16_full_pipeline_20261026/sealed_{off,t300_first,t300_repeat}`; their manifests and original logs are staged separately for publication. These local data paths are not a claim of durable remote publication.

A separate direct-format scanner, importing neither filter nor legacy parser, reconciled all 200000 source rows against 157666 exact retained records and 42334 ledger entries. It verified 50000 unique h000 positions, all 10 manifest entries and all 11 read-only outputs. It found no concrete defect. Its report is preserved with the evidence.

Earlier RED failures, the original 916-line diagnostic result, the earlier read-only count proof and the old prepared receipt are retained as history. The previous statement that full200k output validation was deferred is superseded by this report, not silently erased. The 916-line HCE placeholder and inferred game groups still do not become authoritative data.

Next: publish this source/tests/runners/report and original evidence in its ordered place. The owner can then run the one-command production configuration with real013/014, every sealed shard and authoritative game IDs. Only that run can establish the requested real position/game overlap counts. Subsequent threshold ablation must wait for that real overlap report; the synthetic pipeline results make no training-gain claim.
