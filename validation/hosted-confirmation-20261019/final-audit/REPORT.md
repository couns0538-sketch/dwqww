The original 6.4.7 versus 6.4.4 confirmation is a valid completed **inconclusive** capped run. It establishes no accepted playing-strength gain.

This audit independently checked the official original artifact, rather than relying on its summary. All 2,794 offline checks passed. The audit ran no archived executable or helper, launched no games, changed no original evidence, and performed no Git mutation or network operation.

| Original strength result | Independently verified value |
| --- | --- |
| Candidate / baseline | 6.4.7 `2c0c7efa49023d8e3f49de3f5596f333a3f01202` / 6.4.4 `816423b1ddac23a00244449deef59dba736055a9` |
| Complete games / color-swapped pairs | 320 / 160 |
| Candidate W / D / L | 114 / 101 / 105 |
| Pentanomial, scores 0, 0.5, 1, 1.5, 2 per pair | [1, 30, 96, 25, 8] |
| Candidate score | 164.5/320 = 51.40625% |
| Final native / independent logistic LLR | 0.46 / 0.4574291989231206 |
| Preregistered H0 / H1; alpha / beta | 0 / +10 Elo; 0.05 / 0.05 |
| LLR boundaries | −2.9444389791664403 / +2.9444389791664403 |
| Outcome | No native acceptance; natural 160-pair cap; inconclusive |
| Descriptive Elo estimate | +9.7742 |
| Approximate paired 95% interval | [−10.4749, +30.0899] Elo |

The interval uses independent pair scores X in {0, .25, .5, .75, 1}: mean .5140625, empirical population variance .035349121093750005, standard error sqrt(variance/160) = .014863781713814878. Transform mean ±1.959963984540054 standard errors through 400 log10(p/(1−p)). This reproduces the native display +9.77 ±20.28; the half-width is 20.28240738862744. It is a descriptive large-sample interval at the observed cap, not a sequential confidence sequence. Its positive estimate cannot replace the SPRT decision.

All 160 cumulative complete-pair likelihoods remained within the boundaries (range −0.38384919485586433 to +1.2325623475017327); all 80 native printed checkpoints agreed with the independent constrained multinomial MLE within the native two-decimal rounding tolerance. No previous pilot games were pooled.

Python-chess legally replayed all 42,454 strength-game plies from each exact frozen starting position. Every game belongs to its sequential, unique, color-swapped pair, with the exact frozen opening prefix and advertised time control. All 320 terminations are normal, and the replayed final results match: 219 checkmates, 23 insufficient-material draws, 62 threefold draws and 16 fifty-move draws. All 42,454 recorded remaining-clock values are nonnegative; their minimum is 0.043 seconds.

The complete 160,201,505-byte strength communication log was scanned (1,003,060 lines). All 42,454 search positions and best moves match the PGN move histories. Both players have exactly 320 fresh UCI sessions, new-game commands, normal status-zero process exits and quits. Every session receives Threads1, Hash32, Move Overhead10 and OwnBookfalse; Ponderfalse and empty Book File are advertised runtime defaults. There are no extra option settings or fault records. The retained command/state confirms equal 2+0.02 clocks, serial concurrency1, seed20261020, restart enabled, and disabled resign/draw/tablebase/maxmoves adjudication. No recovery/resume is enabled.

The separate baseline/baseline readiness match contains eight normal games/four deterministic color-swapped pairs, W3 D2 L3, pentanomial [0,0,4,0,0]. Its 998 plies and complete raw exchanges also match and replay legally. It used 10,000 nodes with unlimited clock; its smoke-only maxmoves200 did not decide a game. Two fresh-process warmups and all six measured bench11 runs retain the expected 419798-node signature. The three paired wall ratios and CPU ratios pass the frozen calibration bounds. This is operational calibration, not a precise speed or zero-Elo result.

All 164 new opening positions are disjoint from the retained 6,477-position prior exclusion set and from the entire separately frozen 504-position hosted-pilot registry, including its unused tail. Each comes from the claimed source corpus row with its original EP target already `-`. The selected runtime orders exactly match the frozen seeded permutation.

The official ZIP SHA-256 is `1dc3d43767bc95251acdf2ec363e4e79b8a00e15d16b1fbd3202ec644b9a5600`. All 85 original ZIP members match the restored files in size and SHA-256, with an exact file set. All 14 initial/final/restored input hashes agree, including the protocol, workflow, runners, openings and binaries. The archived package/support files match trusted frozen repository commit `f1b44cc71554e8ea1ec61b3ca6adc90da65646b6`.

| Actual retained artifact | SHA-256 |
| --- | --- |
| Baseline forge | `09d901683f123d97aa2a71460d1cd8b26afbb48229c8af675939e23fdd33a3cc` |
| Baseline core archive | `ecdf7ccf89efaf657301357bdeecacfa5b9e480cde09c8eaa0ac7231c7896cd2` |
| Candidate forge | `8944476e9e705847433442dc09d758bb0198911e081d233323cb3259987cbc96` |
| Candidate core archive | `296d953f4c634d1adff42639f139ce456e583969e7df0f6b4d0d47c0cc43169b` |
| Fastchess | `f98ac4102d79598ab29d1f5abdff37e2ae729cdb8e85ab29692e405011fbb0de` |

All 24 baseline and 26 candidate exported-source hashes match their claimed frozen Git objects, including embedded NNUE weights. Actual archived forge/core bytes match the separate build provenance and retained artifact manifest. Compile records use GCC14/GNU C++20, O3, x86-64-v3, generic tuning, no fast-math and disabled FP contraction. Retained Release logs contain 7/7 baseline and 8/8 candidate passing tests. The original job log records GCC14.2 and checkout/runtime version of pinned Fastchess `60d7a7a26c6b0582a15c112fb29a1829bef2adb3`; the ELF artifact embeds that pin. This checks the retained hosted build record; the audit did not rebuild or execute those binaries.

The match finished normally at 22:44:48 UTC on 2026-10-19. Original results publication then failed for a separate reason: original job log line584 says `hosted-results/confirmation/sprt/fastchess.log is 152.78 MB; this exceeds GitHub's file size limit of 100.00 MB`; line587 rejects `results/hosted-confirmation-39332822379-1`. The official artifact retained the complete log. The recovered diagnosis file's `unknown` cause is superseded by this direct original-log evidence; originals remain untouched.

Scope is conditional on this native hosted Linux AMD EPYC7763, one-CPU-affinity, short-control, synthetic-opening protocol. It provides no native Windows/Ryzen result, no Stockfish comparison, and no strength inference for 6.4.8 or later candidates, including 6.5.1/6.5.2. The accepted baseline does not change.

Evidence files in this directory are `audit-results.json`, per-game `aa-legal-replay.json` and `sprt-legal-replay.json`, complete-pair `sequential-likelihood.json`, and the authored `audit_original.py`. Run the helper with the installed venv Python and `-B`; `--supplement` rechecks documented compiler/PGN formatting assumptions and adds the separate prior-registry/native-source crosschecks. Initial auditor assumptions expected literal `-std=c++20` and PGN `inf`; actual retained forms are `-std=gnu++20` and standard unlimited-clock `-`. These were corrected and only affected checks repeated. The correction record is retained in the JSON.

Raw originals are referenced in the verified recovery archive; this directory does not duplicate the large logs or binaries.
