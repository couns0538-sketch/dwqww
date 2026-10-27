# sol_S33fix — S33-1: every advice table labelled "approx model", only fastchess figures quoted

Sol's S33 delivery (17aa0cae, `releases/forge_sol_pack31_20261025/S33/`) is read only and unchanged; v2 files are
new. Advice only: no gate, rule or lock changes; no Elo claim.

| file | what |
|---|---|
| `forge_sol_S33_advice_{net,search,speed}_v2_20261027.md` | Sol's three ADVICE pages with every table and every model number labelled `approx model`; gate figures only as fastchess printed them |
| `forge_sol_S33_sprt_plan_table_v2_20261027.{md,csv}` | Sol's 630-cell table re-rendered from his CSV: data rows byte-identical, labels in title, caption and headers; CSV gains `model_label` |
| `forge_sol_S33_labels_v2_20261027.py` | `render` (table above) and `check` (label rule + fastchess-figure rule) |
| `forge_sol_S33_exact_sprt_v2_20261027.py` | exact fastchess 1.8.2 GSPRT (S44 functions, verbatim) + `oc_cell()` |
| `forge_sol_S33_approx_vs_exact_v2_20261027.py` | cross-check of the advice cells: approx model vs exact-LLR stopping rule (`logs/approx_vs_exact_v2.json`) |
| `test_forge_sol_S33_labels_v2_20261027.py`, `forge_sol_S33_mutants_v2_20261027.py` | 11 tests, 4 planted bugs |
| `tests_fixtures/gates/*/RESULT.md` | PC gate RESULT.md copies (source of the fastchess-printed strings) |
| `tests_fixtures/sol_original/` | byte copies of Sol's advice_net page and plan table (md + csv) |

## Rules enforced by `check`

1. Every markdown table carries `approx model` in its header row or in the caption line(s) directly above it, unless
   the caption says `fastchess-printed` (a table of real gate figures).
2. Every `LLR x` and `Elo x +/- y` quoted after a gate name (G95, G100r, G104, G104c, G119, G120, G120c) equals the
   string fastchess printed in that gate's RESULT.md (e.g. G119 `LLR 1.72`, never the Gaussian `1.727094`).

```sh
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
$PY -I -B forge_sol_S33_labels_v2_20261027.py check --gates tests_fixtures/gates forge_sol_S33_advice_*_v2_20261027.md forge_sol_S33_sprt_plan_table_v2_20261027.md
$PY -I -B forge_sol_S33_labels_v2_20261027.py render --csv tests_fixtures/sol_original/forge_sol_S33_sprt_plan_table_20261026.csv --md NEW.md --csv-out NEW.csv
S33_SCRATCH=F:/opus_scratch/sol_S33fix/tmp $PY -I -B test_forge_sol_S33_labels_v2_20261027.py -v
$PY -I -B forge_sol_S33_mutants_v2_20261027.py F:/opus_scratch/sol_S33fix/<NEW dir>
OPENBLAS_NUM_THREADS=1 $PY -I -B forge_sol_S33_approx_vs_exact_v2_20261027.py --csv tests_fixtures/sol_original/forge_sol_S33_sprt_plan_table_20261026.csv --out logs
```

The planner itself (and its scipy-based analytic path) is unchanged; its JSON output already says
`exact_fastchess: false`. Future tables should be rendered with `render` so the labels cannot be lost.
