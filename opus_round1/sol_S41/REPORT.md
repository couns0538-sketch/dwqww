# S41 [Sol leftover] Eval-scale check for a new lock net + `NetScale` (UCI, default OFF) — DONE

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 23. The spec is Sol's inventory (`F:\opus_scratch\sol_inventory_17aa0cae.json`,
`jobs[]` S41). Sol never started it: there are no S41 files on `17aa0cae`. Work and results by a sub-agent; this report
text is its hand-back.

Branch `opus-sol-S41` = `d4f4312` (AL1 lock tree + baseline evidence + CI recipe) + `0d99f02` cherry-picked
(`e101e315`) + these commits:
- `5a197863`: the engine change (NetScale + ctest);
- `d27ac364`: the job folder (`[skip ci]`);
- `c5aa9e32`: the Linux CI evidence (`[skip ci]`);
- the REPORT commit.

Machine exclusive: **no**. The PC ran a fastchess gate, self-play and NNUE training throughout. All steps ran at
nice 19 / Idle, one compiler or engine process at a time, with free RAM ≥ 6 GB checked before each heavy step.
**No Elo or speed claim.**

## Result
Five nets were compared on 10,000 fixed positions (WAC300 + 9,700 self-play positions from the holdout file 013).
- **Scale vs h256_e12** (robust symmetric slope; every 95% CI excludes 1): s198 (AL1) +1.17%, e48f006 +1.32%,
  e48f029 +2.43%, e48f034 +0.88%.
- **Mapping values:** NetScale **99** for s198, e48f006 and e48f034; **98** for e48f029.
- **Against the lock s198:** e48f006 and e48f034 are on the same scale (100); e48f029 is +1.3% (99).
- **Cause:** the drift is all in the residual network. Its mean |net| grows from 84.6 cp to 86.6-90.8 cp; the
  HCE is the same code.

The new UCI option `NetScale` (default 100 = OFF) maps a net back to h256_e12's scale.
- OFF: bench-identical to AL1, and to the e48f006 base when built there.
- ON at the proposal for the lock (99): every bench depth within ±14.6%.
- Details: `EVALSCALE_20261027.md`.

## Acceptance (Sol's pass line + default A)
| line | result | evidence |
|---|---|---|
| 10k fixed positions (WAC300 + self-play sample) | **PASS** | 300 WAC + 9,700 at fixed byte offsets of the closed holdout file `forge_selfplay_013.txt` (read-only seeks); `data/positions_10k_20261027.txt.gz` (text sha256 `e144236a…`), `logs/step1_sample.log` |
| eval spread of e48f006 (and f029, s198) vs h256_e12: \|eval\| quantiles + robust slope | **PASS** | `tools/evalscale_20261027.py`; quantiles q10-q99, slopes (sym + bootstrap CI, LAD both ways, Theil-Sen, Huber, OLS, q-ratios), also vs s198 and for e48f034; `EVALSCALE_20261027.md`, `logs/evalscale_stats_20261027.json` |
| same net on both sides gives slope exactly 1.000 | **PASS** | h256_e12 vs h256_e12 and s198 vs s198: every estimator, ratio and CI bound 1.0000; unit test asserts `== 1.0` (15/15 tests) |
| one OFF-default `NetScale` option | **PASS** | `NetScale` spin 50..150, default 100 (`include/forge/net_scale.hpp`, `Worker::static_evaluate`, `src/uci.cpp`); proposal 99 for the lock |
| deliverables: tool, EVALSCALE, patch, IDEA_SOURCE | **PASS** | `tools/evalscale_20261027.py`, `EVALSCALE_20261027.md`, `forge_sol_S41_netscale_20261027.patch` (passes `git apply --check` and `patch -p1 -F0` on a clean `d4f4312`), `IDEA_SOURCE.md` |
| patch OFF: bench = lock refs at 5 depths | **PASS** | `uci_check.py --full` ALL OK (`logs/step5_identity_al1_off.log`) |
| patch OFF on the e48f006 base = 328459/945640/3024381/9162399/20421972 | **PASS** | unpatched base reproduces the refs; patched OFF equal, perft OK (`logs/step7_benches.log`) |
| ON bench at 5 depths, no blowup over 20% | **PASS (lock) / NOTE** | AL1 @99: max 14.6%. Listed too: AL1 @90 (d22 −43.7%), e48f006 @99 (d20 +43.9%), sweep 95-105. 100-position totals at depth 12: 1.0057 / 1.0061 / 0.9980, so no blowup (`logs/step8_sweep.log`) |
| Std: FMA 0, warnings 0, CTest | **PASS** | FMA 0, 0 warnings; CTest 14/15, only the 4 known `forge_tests` lines; `forge_net_scale_tests` 155/155 (`logs/step9*`) |
| Std: ASan+UBSan, TSan | **PASS** | opus-ci 40507678991 on `5a197863`: release, asan, tsan all success; Linux identity ALL OK; TSan 0 reports (`logs/step13_ci_40507678991.log`) |
| UCI option list = lock + one line; clamping, invalid value, restore | **PASS** | `logs/step7_uci_options_diff.txt`, `logs/step11_uci_behaviour.log` |
| planted bugs | **PASS** | engine 5/5 (`logs/step10_engine_mutants.log`); tool 8/8 (`logs/step6_tool_mutants.log`) |
| determinism | **PASS** | second dumps and second analysis byte-identical (`logs/step12_repro.log`) |
| no Elo claim | **PASS** | no gate run |

## Findings
- The scale drift since h256_e12 is small (+0.9% to +2.4%). The bulk (q10-q75) matches within ±6 cp; the tail
  carries the difference.
- The lock s198 is +1.2%, so `NetScale=99` maps it back. `NetScalePct=90` (idea board) would over-correct by 8-9%.
- A residual-only rescale would need 90-96%. `NetScale` scales the total static eval, so margins see exactly the
  mapped value.
- The per-depth 20% rule is a chaos check: any 1-5% rescale moves single bench depths by up to ±50%, while total
  tree size is unchanged (≤ 0.6%).

## Process note (main session, from the sub-agent's hand-back)
Two small helper files went to `F:\opus_scratch\tools_s41_45_49` instead of a job folder; they are left in place.
Read-only inputs (manifest, results, the self-play holdout file) were read through copies or short seeks only.

## Left / UNVERIFIED
- UNVERIFIED: any strength effect of `NetScale` (no gate run).
- Not measured: the NPS cost of the added branch; bench NPS on the loaded PC is advisory only.
- A gate, if wanted: `NetScale=99` vs AL1, one option, a new srand from TEST_PLAN (crew/QA decision).
- For a future lock net: rerun `dump` + `analyze` with that net (README). S-A6's SPSA plan uses this tool as its step 0.
