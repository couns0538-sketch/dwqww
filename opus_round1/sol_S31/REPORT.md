# S31 [Sol leftover] Checkpoint-averaging tool — DONE (no strength claim)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 15. Branch `opus-sol-S31` = `d4f4312` + `0d99f02` cherry-picked + this
job. Tool job, no engine change (`[skip ci]`). Inputs are read-only copies under `F:\opus_scratch\sol_S31\inputs`.

## Acceptance (Sol's pass line + resume rework)
| line | result | evidence |
|---|---|---|
| averaging one file reproduces its md5 | **PASS**. e12 ep12 `.inc` -> 6d22f612 = input; f006 ep48 `.inc` -> 0fae54a4 = input; f006 ep48 `.bin` -> 0fae54a4 = the trainer's own ep48 `.inc`; f006 ep48 `.pt` -> 0fae54a4 | `logs/step1_avg.log`, `logs/step5_pt_inputs.log` |
| the averaged net passes parity 10000/10000 | **PASS (4 of 5 exact; 1 boundary case)**. Engine `forge::nnue` (lock `nnue.cpp` + the archive's `nnue_check.cpp`, one build per net) vs the tool's forward on 10,000 FENs: e12 avg2, e12 avg3, f006 avg2 and f006 avg3 are 10000/10000 exact. f006 avg4 is 9999/10000 exact plus 1 position differing by 1 cp (FEN `4B2Q/4n3/1q2k1p1/pP6/P6P/1K6/8/8 b - - 0 61`): the float64 forward gives 34.999995523, truncated to 34, and the engine's float32 sum gives 35. The step-4 run failed it as written; the re-run counts such integer-boundary 1 cp cases apart (only when within 1e-3 of an integer) and passes | `logs/step4_parity.log`, `logs/step4b_parity_boundary.log` |
| every arm on the same holdout md5 | **PASS**. Data32 h000 (50,000 rows, synthetic labels: pipeline check) and the production holdout subset `holdout_013_014_s16` (1,024,286 rows of 013+014, pos md5 9ebe2f9c, hce md5 c8723ec2); every score JSON records both md5s | `logs/step2_holdouts.log`, `logs/step3_score.log` |
| deterministic | **PASS**. Integer quantization of float64 means; re-averaging gives identical md5s; the subset tool is deterministic (test) | tests |
| table: last vs avg-2 vs avg-3 on the same holdout | **DONE**, see below | `logs/step3_score.log` |
| PC-ready runner for the f006 last-4 epochs | **DONE and run for real**. The f006 files exist on the PC (`F:\forge_nnue_train\runs\resid_h256_e48_f006_...`), so the run is not UNVERIFIED: read-only copies, sha256 checked. `run_s31_pc.sh` does any run's last k `.pt` checkpoints end to end | `logs/step5_pt_inputs.log`, `logs/step7_pc_runner_f006.log` |
| resume rework: accept any 2+ `.pt` files from one run | **PASS**. `avg --pts`: the `.pt` path equals the `.bin` path byte for byte on f006 avg2/avg3/avg4 (31603226 / e61c4a18 / 035842c1); mixed-run checkpoints are refused (test) | `logs/step5_pt_inputs.log`, `logs/step6_tests.log` |
| tests | **PASS 7/7** (venv Python 3.10, numpy, torch cpu) | `logs/step6_tests.log` |
| no strength claim | none made | — |

## Results: production holdout subset (1,024,286 rows), MSE (lower is better)
| net | md5 | b0.6 | b0.8 | teacher (b1.0) |
|---|---|---:|---:|---:|
| f006 ep45 | 4c8e6fb4 | 0.0143400 | 0.0067164 | 0.0045045 |
| f006 ep46 | d946fd63 | 0.0143417 | 0.0067332 | 0.0045364 |
| f006 ep47 | 6eaa57f4 | 0.0143427 | 0.0067478 | 0.0045647 |
| **f006 ep48 (last)** | 0fae54a4 | **0.0143462** | 0.0067644 | 0.0045944 |
| f006 avg-2 (47-48) | 31603226 | 0.0143440 | 0.0067558 | 0.0045793 |
| f006 avg-3 (46-48) | e61c4a18 | 0.0143428 | 0.0067477 | 0.0045643 |
| f006 avg-4 (45-48) | 035842c1 | 0.0143416 | 0.0067394 | 0.0045490 |
| e12 ep02 | 3bd78c28 | 0.0151370 | 0.0068409 | 0.0039566 |
| e12 ep11 | 0f0c51f0 | 0.0145289 | 0.0068434 | 0.0045695 |
| **e12 ep12 (last)** | 6d22f612 | **0.0145361** | 0.0069020 | 0.0046797 |
| e12 avg-2 (11-12) | 0795a5ab | 0.0145310 | 0.0068719 | 0.0046245 |
| e12 avg-3 (02, 11, 12) | f62d544e | 0.0146319 | 0.0066871 | 0.0041541 |
| HCE alone | — | 0.0170588 | 0.0083605 | 0.0050739 |

**Reading:**
- On f006, averaging the last 2/3/4 epochs beats the last epoch by 2.2/3.4/4.6e-6 b0.6. All of these are below
  the pooled seed spread of 7.1e-6 (S30), so none is a measurable gain.
- The single epoch-45 net (0.0143400) is as good as avg-4. The run's last epochs drift slightly upward on this
  holdout, so "average the tail" and "pick an earlier epoch" are the same small effect.
- On e12, avg-2 sits between ep11 and ep12. The spec's three e12 files are ep02, ep11 and ep12, so avg-3 includes
  the early ep02. That hurts b0.6 by 1e-4 but helps the teacher/b0.8 targets, the usual blend trade-off of an
  under-trained net.
- The subset reproduces the full-holdout f006 final line (teacher 0.004593, b0.6 0.014341, b0.8 0.006761) within
  2-5e-6.

Data32 h000 (synthetic labels, pipeline check only): the HCE baseline (teacher 0.0218623) equals S18's figure; the
real nets score worse on those synthetic labels, as expected (`logs/step3_score.log`).

## Left / UNVERIFIED
- No strength claim. An averaged net would need a gate; the holdout effect here is within seed noise.
- `eval_inc.py` (the spec's parity reference) imports the trainer and uses DirectML, so it cannot run on this PC
  under the rules. Parity therefore compares the engine's own `forge::nnue` against this tool's forward, which S21
  validated against the engine (916/916, 0 cp).
- Machine exclusive: no.

## Files
`forge_sol_S31_avg_ckpt.py`, `test_forge_sol_S31_avg_ckpt.py`, `run_s31_pc.sh`, `README.md`, `IDEA_SOURCE.md`,
`REPORT.md`, `logs/` (steps 1-7), `FILES.txt`, `SHA256SUMS`. The averaged `.inc` arms (about 1.1 MB each) stay in
`F:\opus_scratch\sol_S31\arms`, `arms_pt` and `F:\opus_scratch\s31_runner_f006`; their md5s are in the logs.
