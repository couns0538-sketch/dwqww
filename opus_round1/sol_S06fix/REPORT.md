# S06fix — gate miner v2: exact fastchess LLR, real-gate reconciliation, termination/multi-PGN/--out guard — DONE

Branch `opus-sol-S06fix` = AL1 base `d4f4312` + CI baseline `0d99f02` (`e41596a0`) + `508200a8` (tool only) + the REPORT
commit. Sol's v1 files are unchanged; fixes ship as `forge_sol_S06_*_v2.py`. Tool only: `git diff 294dbed` over src,
include, tests, tools, bench and CMakeLists is empty. Machine exclusive: no (light Python only). Work and results by a
sub-agent; this report text is its hand-back.

## Acceptance

| Item | Command | Result | Evidence |
|---|---|---|---|
| S06-1 exact GSPRT primary, Gaussian secondary | `forge_sol_S06_gatelog_miner_v2.py counts --penta 5 74 252 119 14 --e0 0 --e1 10` | LLR 2.99197 (port of fastchess v1.8.2-alpha sprt.cpp), converged MLE 2.99197, Gaussian 3.0384 (secondary); Elo 23.62 +/- 11.90, nElo 44.52 +/- 22.35; Wald decision uses the exact LLR | `logs/s06_1_g120_known_answer.log` |
| S06-1 on all PC gates | `test_reproduces_printed_statistics_of_every_normalized_pc_gate` | 44 normalized gates: max abs(port - printed LLR) 0.0050 (= rounding); Elo, Elo err, nElo, nElo err, LOS within 0.0051; abs(port - converged) <= 1.4e-8 | `fixtures/gate_results_normalized.tsv`, `logs/unittest_all_v2.log` |
| S06-2 real current gate (gate38, 1500 games) | `mine --pgn --log --result RESULT.md --detail summary --hash-only-inputs` | RECONCILED: Ptnml [8,113,483,135,11], W/D/L 183/1162/155, time losses 0, crashes 0, LLR 1.1139 vs printed 1.11, Elo 6.49 +/- 8.16, nElo 13.98 +/- 17.58, LOS 94.04: PGN = log = RESULT.md | `logs/s06_2_real_gate38_run.log`, `logs/s06_2_real_gate38_result_v2.json` |
| S06-2 G120 (known answer, orphan game) | same | RECONCILED: 929 PGN games / 929 finished lines, 1 orphan (round 466, game 931), 464 pairs, Ptnml [5,74,252,119,14], LLR 2.99 | `logs/s06_2_real_gate120_*` |
| S06-3 non-normal Termination pairs | tests + real runs | counted per pair and by value (missing Termination counts as non-normal); gate38 and G120: 0 | `test_forge_sol_S06_v2_fixups.py` |
| S06-3 >1 PGN | `--pgn a --pgn b`; `mine_pgns()` | accepted, each game keeps its source index; the same PGN twice invalidates the pairs (no double count) | tests |
| S06-3 `--out` refuses gate/lock dirs | tests | refused: D:/grok-pc-data/forge_push, selfplay_out, F:/forge_nnue_train, C:/Users/Administrator/grok-pc, `--protect`, env FORGE_S06_PROTECTED, path parts gate<N>/gate_/*_lock_*/*_queue_*, folders below RUN_INFO.json/RESULT.md | tests |
| Tests | `unittest discover -p 'test_forge_sol_S06_*v2*.py'` | 98 run OK (76 ported from v1 + 22 new; 1 opt-in real-gate test skipped, run separately OK on gate38 and G120) | `logs/unittest_all_v2.log`, `logs/unittest_real_gates.log` |
| Planted bugs | `mutation_check_v2.py` | 12/12 caught | `logs/mutation_check_v2.log` |
| v1 on the same real files (RED) | Sol's modules | 0 valid pairs (750 x opening_unknown); G120 log BLOCKED; Gaussian 3.04 | `logs/v1_on_real_gates_RED.log` |

## Findings
- fastchess 1.8.2 regularizes zero cells to 1e-3 and stops its MLE after <= 10 iterations at 1e-4; on the 44 PC gates this
  differs from the fully converged constrained MLE by <= 1.4e-8, so both reproduce every printed LLR.
- Sol's v1 could not pair any real gate game (fastchess PGNs carry no FEN; openings are `{book}` moves) and blocked any
  SPRT-stopped gate with an orphan game (G120). Its Gaussian LLR is 0.046 high on G120 and crosses +2.944 on
  [5,73,247,117,14] where the exact LLR (2.935) does not.
- fastchess summaries count complete pairs only: G120 log has 929 "Finished game" lines but Games 928, so RESULT.md
  "Orphan games" reads 0 although PGN and log hold one orphan.

## Process note (main session, from the sub-agent's hand-back)
fastchess source copies were moved (not deleted) out of the job folder to `F:\opus_scratch\sol_S06fix\fastchess_src\moved_from_jobdir`.

## Left / UNVERIFIED
- Logistic-model port not checked against a fastchess logistic run (no such gate). PGN move legality not checked.
- End-to-end runs on gate38 and G120 only (copies' sha256 in `logs/gate_copy_sha256.txt`).
