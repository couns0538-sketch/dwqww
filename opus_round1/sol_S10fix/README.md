# S10fix — QA fix-ups S10-1..6 for Sol's S10 (search ideas batch)

Branch `opus-sol-S10fix`, folder `opus_round1/sol_S10fix/`. Tool/evidence job: no engine source change on the branch.
The one engine re-run (S10-3) built Sol's base B + the ImprovingRazorGuard patch in scratch. Sol's files (commit
`17aa0cae`) were only read.

## Files
| file | what |
|---|---|
| `S10_screen_rule_v2.md` | S10-1/4/5/6: the screen rule for later search ideas (order, FAIL = skip B, deadlines, machine exclusive, hygiene). |
| `opus_s10_screen_verdict.py`, `s10_screen_verdicts.json` | S10-1: the rule as code, applied to Sol's four ideas (all FAIL, B skipped). |
| `opus_s10_wac_flips.py`, `s10_wac_flips.md`, `s10_why_rejected_v2.md` | S10-2: WAC positions flipped vs OFF per idea (from Sol's logs) and one line per rejected idea. |
| `opus_s10_rebuild_baseB.py` | S10-3: rebuilds Sol's base B (73/78 files byte-exact from git objects, every engine source among them) and applies the patch (LF kept). |
| `opus_s10_bench_rerun.py` | S10-3/S10-6: one bench run with a long deadline; logs wall/CPU time, system CPU %, RAM, busiest processes; machine exclusive recorded. |
| `opus_s10_hygiene_check.py`, `s10_superseded_vs_final.diff` | S10-4/S10-5: `_before_` copies, duplicate files and every `.tar.gz` size; one diff log of Sol's superseded files vs their finals. |
| `test_opus_s10fix.py`, `opus_s10_mutants.py` | 12 unit tests; 5 planted bugs, the tests must fail on each. |
| `IDEA_SOURCE.md`, `FILES.txt` (the one index), `SHA256SUMS`, `logs/step*.tar.gz` (one per step) | |

## How to run (PC rules: Idle priority, one thread, scratch only)
```
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
nice -n 19 $PY -I -B opus_s10_rebuild_baseB.py --repo <dwqww clone> --out <new dir> --patch <improving_razor.patch> \
   --feature improving_razor --apply-include CMakeLists.txt --apply-include include/forge/search.hpp \
   --apply-include src/search.cpp --apply-include src/uci.cpp --json <out.json>
nice -n 19 bash <tools>/build_pc.sh <src dir> <out.exe> -DFORGE_S10_IMPROVING_RAZOR=1
nice -n 19 $PY -I -B opus_s10_bench_rerun.py --exe <exe> --out <new dir> --depth 22 --option ImprovingRazorGuard=false \
   --deadline 3600 --expect-nodes 31111774
nice -n 19 $PY -I -B opus_s10_wac_flips.py --off <S07 wac300 dir> --on NAME=<idea wac_ON dir> ... --epd <wac300.epd> --out-json o.json --out-md o.md
nice -n 19 $PY -I -B opus_s10_screen_verdict.py --sol-consolidated <consolidated_results_v2.json> --out v.json
nice -n 19 $PY -I -B opus_s10_hygiene_check.py --git <clone> --tree 17aa0cae --prefix releases/forge_sol_pack31_20261025/S10
nice -n 19 $PY -I -B test_opus_s10fix.py ; nice -n 19 $PY -I -B opus_s10_mutants.py --work <new dir>
```
Inputs: Sol's sealed S10 evidence archives and the S07 native evidence archive, read with `git show 17aa0cae:<path>`
and extracted in `F:\opus_scratch\sol_S10fix\sol_evidence`.
