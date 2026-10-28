# S-A4 [Sol leftover] hidden layer 512 (after S-A2) — DONE

**Branch `opus-sol-SA4`:**
- `opus-sol-SA2` head `4b2a6800`
- `127425f8`: engine flag, CTest H512 target, tools, evidence
- `23f3f616`: CI evidence, `[skip ci]`
- the REPORT commit

**Spec:** §2 item 41; `OPUS_TEST_PLAN.md` row 4 (G-A4, srand 507544535). No gate was run. Work and results by a
sub-agent; this report text is its hand-back.

## Acceptance
| line | result | evidence |
|---|---|---|
| Engine support for H512 behind a compile flag | PASS | `-DFORGE_NNUE_HIDDEN=512` plus the new `FORGE_NNUE_WEIGHTS` flag (CMake `FORGE_NNUE_WEIGHTS_FILE`) choose another net include file. Both NNUE paths (float and NnueInt16) work at H512; a width mismatch fails the include file's static_assert |
| Default build = lock identity | PASS | SA4 default box build: `uci_check --full` ALL OK, FMA 0 (`logs/uci_check_full_default_h256.log`). Same code as SA2's exe (only the 4 PE header bytes differ). CI release ALL OK |
| CPU smoke H512 net trained with the trainer (renamed copy) | PASS | `trainer_v3c_clip.py --shape 512 --weight-clip`, run as `opus_nnue_smoke_sa4_clip.py`: CPU, 1 thread, data32 sample, 2 epochs, about 21 s per run. Two runs are byte-identical (8 artifacts). INIT CHECK OK; INT16 CHECK max\|q\| 441 ≤ 21704, 0 at the int16 rail. `logs/smoke_compare_r1_h512.log` |
| Float path vs Python forward, 10000/10000 within a stated tolerance | PASS | Tolerance 0 against the float32 emulation of the engine's lane order: 10000/10000; the AVX2 and scalar builds give identical dumps. Against the float64 forward: under 1 cp (max 0.9998, the truncation). `logs/parity_h512_smoke_10k.json` |
| int16 path vs integer reference, exact | PASS | 10000/10000 on the AVX2 and scalar kernels; accumulators 10000/10000; incremental 0 mismatches. Float vs int16: max 1 cp, 20 differ, 0 sign flips |
| Extra: widened-lock H512 net | PASS | `widen_net_sa4.py --mode split`. NnueInt16 cp identical to the H256 lock on 10000/10000; HCE identical; float identical too (`logs/cross_width_split_vs_lock.json`). Bench nodes: NnueInt16 ON equals H256 ON at d11–d20 (330610 / 858175 / 2760596 / 9564588); float OFF equals the lock at d11/d13, then 3043192 / 13215819 at d16/d20 (float summation order) (`logs/bench_h512.log`) |
| NPS H512 vs H256 at d16/d20 (ABBA, advisory) | RECORDED | Widened H512 vs the SA4 default H256, 5 runs per arm, CPU-time NPS. NnueInt16 ON (identical trees, node counts checked equal): d16 −12.11% (CI −14.48..−9.75), d20 −13.67% (−15.60..−11.74). Float OFF: d16 −10.06% (−11.28..−8.84), d20 −11.51% (−13.59..−9.42). `logs/nps_h512_vs_h256_on.log`, `logs/nps_h512_vs_h256_off.log`. Loaded PC; no speed claim |
| GPU recipe / queue line for the crew | PASS | `GPU_RECIPE_H512.md`: a from-scratch line (production recipe + `--shape 512 --weight-clip`) and an optional warm start from the lock widened with zero-output units. Thermal ≤ 80 °C, never stop the current run; the crew runs it after CR and a vote. Not run, nothing queued |
| Tests / CI | PASS | CTest `forge_nnue_h512_tests` runs the S-A2 test at H512 on a seeded synthetic net generated at build time (`tests/nnue_gen_net.cpp`). PC: 18 tests, known failures only. CI run 40518079733 success: release 122236942088, asan 122236942436, tsan 122236942497; TSan 0 reports. `logs/ci_40518079733.log` |
| Planted bugs | PASS | 4 width mutants (update loop stops at unit 256, output loop stops at unit 256, opponent output weights at a fixed offset 256, include flag ignored). Each fails at H512 (or doesn't build) and passes at H256; the control passes both. `logs/mutation_width.log` |
| Extra: warm-start pipeline | PASS | lr-0 runs of the lock (H256), widened-zero H512 and widened-split H512 give identical holdout losses (INIT 0.117247 / 0.124866; FINAL 0.116300 / 0.124112 / 0.110225), and each exports an unchanged net. `logs/smoke_compare_w1_warmstart.log` |
| Supervisor log | PASS | 7 "adopted running job" lines before and after every torch step and at the end |

## Findings
- **The width support was already there.** The lock compiles any width through `FORGE_NNUE_HIDDEN` (the kernels only need H % 16 == 0). What was missing was a way to compile a different net without replacing `src/nnue_weights.inc`; `FORGE_NNUE_WEIGHTS` adds that.
- **H512 costs about 11–16% more per node** (CPU NPS −10..−14%) on the same tree, far less than 2×, because NNUE is only part of the per-node cost. This matches S-C4's independent zero-padding measurement (float H512 −9.5% / −9.8% at d16/d20, `opus-sol-SC4`).
- **H512 memory:** 8 KiB per search-stack entry (float + int32 accumulators), about 1.1 MiB per worker.
- **The smoke net is not a playing net.** It was trained on synthetic data and is about as good as HCE alone (holdout −0.2%); it is only for pipeline and parity checks.
- **Widening the lock net is exact.** Net2Net-style widening gives an exact H512 starting point, which could serve as a GPU warm start.

## Process note (main session, from the sub-agent's hand-back)
One scratch file of the job was renamed (`sol_SA4/out/w1/acceptance.json` → `acceptance_regex_v1.json`) after a comparison
regex fix; nothing was deleted. CTest's Python tests left untracked `tools/__pycache__` folders (not committed).

## Left / UNVERIFIED
- No GPU training and nothing queued (crew task); no gate (G-A4); no strength claim.
- GPU time and memory for H512 are estimates, not measurements: about 1.5–2× H256 per epoch (H256 epoch ≈ 194 s), roughly 4–5.5 h for 48 epochs.
- NPS was measured only on the loaded PC.
- CI covers H512 only with a synthetic net. A real trained H512 net needs the parity and NPS runs repeated (commands in the README).

Machine exclusive: no.
