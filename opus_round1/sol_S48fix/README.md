# sol_S48fix — S48 gate guard v2 (fix-ups S48-1..4). ADVICE ONLY

Fixes Sol's S48 delivery (`releases/forge_sol_pack31_20261025/S48/` on 17aa0cae, read only; his files are not
edited — the fixes ship as new `_v2_20261027` files). Nothing here changes a gate, rule, lock or ranking.

| file | what |
|---|---|
| `forge_sol_S48_gate_guard_v2_20261027.py` | the fixed guard: `comparability()`, `selection_bias()`, `simulate_gate_bias()`, `write_grid()`, `from_gate_files()`, `normalize_tc()`, `normalize_hash_mb()` |
| `forge_sol_S48_exact_sprt_v2_20261027.py` | fastchess 1.8.2 exact GSPRT + stopping-rule simulator, functions copied verbatim from the Opus S44 tool (numpy only) |
| `test_forge_sol_S48_gate_guard_v2_20261027.py` | 38 tests (synthetic + six real PC gate files in `tests_fixtures/`) |
| `forge_sol_S48_mutants_v2_20261027.py` | planted bugs: re-introduces each fixed defect, the tests must fail |
| `forge_sol_S48_real_run_v2_20261027.py` | real-file run: G100r, G104, G104c, G119, G120, G120c |
| `forge_sol_S33_sprt_planner_20261026.py`, `forge_sol_S06_statistics_20261026.py` | Sol's files, byte copies (sha256 008819d5…, 4598c583…), only for `model='approx'` (needs scipy) |
| `logs/` | test, mutant, real-run (`s48_real_run_v2.{json,md}`) and determinism logs |

## Run (PC: venv python, numpy; no scipy needed)

```sh
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 S48_SCRATCH=F:/opus_scratch/sol_S48fix/tmp TMP=$S48_SCRATCH TEMP=$S48_SCRATCH
nice -n 19 $PY -I -B test_forge_sol_S48_gate_guard_v2_20261027.py -v
nice -n 19 $PY -I -B forge_sol_S48_mutants_v2_20261027.py F:/opus_scratch/sol_S48fix/<NEW dir>
nice -n 19 $PY -I -B forge_sol_S48_real_run_v2_20261027.py --gates F:/opus_scratch/sol_S44/inputs/gates --out logs \
    --grid-dir F:/opus_scratch/sol_S48fix/<NEW grid dir outside git>
```

`S48_SCRATCH` must be outside any git work tree (the S48-4 tests write there). `--gates` holds read-only copies of
`D:\grok-pc-data\forge_push\gate*\{RESULT.md,RUN_INFO.json}`.

## API changes vs v1

- `simulate_gate_bias(gate, ...)`: `gate` must contain `e0`, `e1`, `cap_games`, `selection` (H1/H0/cap/H0-early)
  and `early_stop` (None or `{games, elo_max, llr_max}`); missing or invalid -> `ValueError` (v1 defaulted
  0/10/1500/'H1'). `model='exact'` (default, fastchess exact GSPRT, honours the queue's early stop) or
  `model='approx'` (Sol's S33 planner; results labelled `approx model`). `grid_out=` writes the samples via `write_grid`.
- `comparability(left, right, mode='rank'|'replicate')`: required fields are now concurrency, tc, book_sha256,
  base_exe_sha256 (v1 `opponent_exe_sha256` accepted as alias), core_mask, sprt (elo0/elo1/alpha/beta/model) and
  cap_games; optional (blocking if present on one side or different): threads, hash_mb, engine_options,
  base_net_md5. Per-side identity (cand_exe_sha256, cand_net_md5, openings_seed) is always reported; `replicate`
  requires the same candidate and a different openings seed.
- `selection_bias(..., outcome=...)`: `outcome` is keyword-required (no 'H1' default); `H0-early` allowed.
- `normalize_hash_mb('64MB') == 64`; `normalize_tc('tc=10.0+0.10') == '10+0.1'`.
- `write_grid(path, rows)`: refuses paths inside a git work tree; deterministic gzip; returns the manifest
  (bytes, sha256, location). Grids go to a GitHub release asset or stay in scratch (S48-4).
- `from_gate_files(RESULT.md, RUN_INFO.json)`: gate metadata for both functions; concurrency from RUN_INFO, else
  from the RESULT.md settings line (old RUN_INFO files have null); quoted figures are the fastchess-printed ones.

## Limits

The bias rows are model sensitivity points (gate profile + 0.5 per cell, exponentially tilted to an assumed
true Elo); the MC interval is simulation error only, not a corrected confidence interval. No Elo claim.
