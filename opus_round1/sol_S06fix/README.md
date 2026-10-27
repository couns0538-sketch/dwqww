# S06fix — offline gate miner v2 (exact fastchess LLR, real-gate reconciliation, termination/multi-PGN/--out guard)

Tool only (Python 3.10+, standard library; no engine, no package). Branch `opus-sol-S06fix` = AL1 base
`d4f4312` + CI baseline `0d99f02` + this folder; no engine/test/CMake change.

Sol's delivered v1 files (`forge_sol_S06_*_20261026.py`, 17aa0cae) are unchanged; the fixes ship as v2 copies:

| v2 file | Change |
|---|---|
| `forge_sol_S06_statistics_v2.py` | S06-1: primary LLR = line-by-line port of fastchess v1.8.2-alpha `sprt.cpp` (`getLLR` pentanomial, `getLLR_normalized`, `getLLR_logistic`, `itp`; zero counts -> 1e-3, uniform start, <= 10 MLE iterations, ITP root finder). Reference: fully converged constrained MLE (`converged_llr`, port of `sol_S44` numpy `exact_llr`). Gaussian LLR kept as the secondary cross-check. fastchess display figures: Elo +/- (half Elo span of the 95% score interval), nElo +/-, LOS. Wald diagnostic uses the exact LLR. |
| `forge_sol_S06_pgn_v2.py` | S06-2: opening key from `{book}` moves when the PGN has no FEN (fastchess gate PGNs); orphan games (partner never played) excluded from the pentanomial like fastchess, reported, not blocking. S06-3: `non_normal_termination_pairs` (+ by value, missing Termination counts as non-normal); `mine_pgns()` for several PGN texts (parsed one by one, global game index + source index). |
| `forge_sol_S06_logs_v2.py` | S06-2: finished games paired by fastchess game id (2k-1, 2k); the summary may count all finished games or complete pairs only (fastchess pentanomial summaries exclude orphans, e.g. G120 929 lines vs Games 928); summary Ptnml rebuilt from the finished-game pairs; time-loss/crash/illegal event counts. |
| `forge_sol_S06_gatelog_miner_v2.py` | CLI: `--pgn` repeatable; `mine --result RESULT.md` reconciles PGN, log and RESULT.md (games, W/D/L, Ptnml, time losses, crashes, LLR, Elo +/-, nElo +/-, LOS); `--out` refuses PC gate/lock/queue data; `--hash-only-inputs`; `--detail summary`. |

## Run

```sh
python -B -m unittest discover -s . -p 'test_forge_sol_S06_*v2*.py' -v          # 98 tests (76 ported from v1 + 22 new)
python -B forge_sol_S06_gatelog_miner_v2.py counts --penta 5 74 252 119 14 --out NEW_DIR   # G120: LLR 2.99, Elo 23.62 +/- 11.90
python -B forge_sol_S06_gatelog_miner_v2.py mine --gate-id gate38_packa_w55_vs_h256e12 \
   --candidate cand_packa_w55 --baseline base_h256_e12 --pgn COPY/gate38.pgn --log COPY/gate38.log \
   --result COPY/RESULT.md --detail summary --hash-only-inputs --out NEW_DIR           # status RECONCILED
python -B mutation_check_v2.py --out NEW_SCRATCH_DIR                                   # 12/12 planted bugs caught
```

Copy gate files to scratch first (`D:\grok-pc-data\forge_push` is read-only); `--out` must be a NEW directory
outside protected roots (`D:/grok-pc-data/forge_push`, `D:/grok-pc-data/selfplay_out`, `F:/forge_nnue_train`,
`C:/Users/Administrator/grok-pc`, `--protect DIR`, env `FORGE_S06_PROTECTED`), with no path component that looks
like a gate/lock/queue directory (`gate<N>...`, `gate_...`, `*_lock_*`, `*_queue_*`) and not below a folder holding
`RUN_INFO.json` / `RESULT.md`. Opt-in real-gate unit test: set `FORGE_S06_REAL_GATE` (folder with one gate's
.pgn/.log/RESULT.md copies), `FORGE_S06_REAL_CANDIDATE`, `FORGE_S06_REAL_BASELINE`.

Exit 0 means a report without a blocking issue, never acceptance; `acceptance_authorized` stays false.

## Files

- v2 modules and tests (above); `test_forge_sol_S06_v2_fixups.py` = the S06-1/2/3 tests.
- `fixtures/gate_results_normalized.tsv` — read-only extract of 44 PC gate RESULT.md files (Ptnml, bounds,
  printed LLR/Elo/nElo/LOS, RESULT.md sha256) plus the `sol_S44` numpy reference LLR.
- `mutation_check_v2.py` — planted-bug check (12 mutants).
- `logs/` — test runs, real-gate runs (gate38 current, G120 known answer) and their result JSONs, v1 RED baseline,
  mutation check, copies' sha256.
