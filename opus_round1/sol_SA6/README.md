# S-A6 SPSA re-tune plan (plan only)

- `forge_sol_SA6_spsa_plan_20261027.md`: the plan (trigger, step 0 eval-scale check, parameter groups, SPSA settings
  and budget, harness changes, validation, risks).
- `forge_sol_SA6_spsa_plan_20261027.json`: the same plan in machine-readable form.
- `inputs/forge_sol_S15_parameter_catalog_20261027.json`: S15's catalog of the 51 tunables (sha256 `85601714…`,
  equal to S15's SHA256SUMS).
- `opus_sa6_plan_check.py`: checks the plan against the catalog. Every parameter must be assigned exactly once, with
  valid ranges and c_end. It prints the schedule constants and the QA-slot budget.
- `test_opus_sa6.py` (6 tests) and `mutation_check_sa6.py` (6 planted bugs).

```
python -I -B opus_sa6_plan_check.py --plan forge_sol_SA6_spsa_plan_20261027.json [--out <new dir>]
python -I -B test_opus_sa6.py -v
python -I -B mutation_check_sa6.py --work <new dir>
```
