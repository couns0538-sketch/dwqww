# REPORT — deepseek6, long 41 (long 36 DONE RIGHT: the corrected LmrQuietBase end)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long41/ · claimed with claim.sh (the claim line is the second line of stamps.txt); stamps per stage; PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** redo long 36 with the CORRECTED smaller-tree ends from long 27's table.txt (LmrQuietBase 101, not 85), the products built by a script from the same table at the same values, and the .meta of every run checked.
**Answer:** the correction removes most of long 36's "interaction": **the O inversion of SD7×LQB (1.0596 vs a 0.9457 product) is GONE — the corrected SD7×LQB101 measures 0.9577 against 0.9457 (off 1.27 %)** — but **one REAL O inversion remains elsewhere: LQD193×IIR1 measures 0.9617 against a 1.0201 product** (both singles' product says GROW, the pair SHRINKS — prediction 2 killed). On G everything composes sub-multiplicatively (all six measured ABOVE their products, off by 0.66–4.25 %): prediction 3 killed in both halves (no LQB pair within 1 %; none beyond 5 %). The .meta checks all pass. Predictions: 1 and 4 held; 2 and 3 killed.
**How sure:** certain of the twelve runs and the script-built products (the singles read from long 27's table.txt by setting AND end — no hand values anywhere); the interactions that remain are measured facts.

## 2. Honesty numbers
The plain build /tmp/glmflash5_base/build/forge (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt line 2 | exit 0 |
| 12 runs (6 pairs x O,G) at LQB101 | done | runs/*.rows + table.txt, .meta each | all rc=0 |
| products from long 27's table.txt by (setting, end) | done | the generator inside table.txt's script | 26 singles parsed; the values verified |
| .meta checks | done | table.txt meta-ok column | OK x12 |
| the O inversion count | done | table.txt | 1 (LQD193×IIR1) |
| prediction own commit first | done | PREDICTION.md | 1, 4 held; 2, 3 killed |

## 4. The table (products from long 27's singles at the SAME values)
| pair | O sum | O meas | O product | O off % | G sum | G meas | G product | G off % | meta |
|---|---|---|---|---|---|---|---|---|---|
| SD7 + LQD193 | 8,996,257 | 0.9470 | 0.9174 | 3.22 | 15,703,967 | 0.8504 | 0.8449 | 0.66 | OK |
| SD7 + LQB101 | 9,098,267 | 0.9577 | 0.9457 | 1.27 | 16,324,870 | 0.8840 | 0.8580 | 3.03 | OK |
| SD7 + IIR1 | 9,870,691 | 1.0390 | 1.0346 | 0.42 | 17,575,249 | 0.9518 | 0.9130 | 4.25 | OK |
| LQD193 + LQB101 | 8,740,761 | 0.9201 | 0.9325 | 1.33 | 16,747,503 | 0.9069 | 0.8770 | 3.41 | OK |
| LQD193 + IIR1 | 9,136,473 | 0.9617 | 1.0201 | 5.73 | 17,825,741 | 0.9653 | 0.9332 | 3.44 | OK |
| LQB101 + IIR1 | 9,547,129 | 1.0050 | 1.0516 | 4.44 | 18,238,370 | 0.9877 | 0.9477 | 4.22 | OK |

## 5. Findings
1. **File 12's correction removes the headline inversion** — SD7×LQB101 composes within 1.27 % on O — my long-36 "inversion" was mostly the swapped end, as Opus said.
2. **A real inversion survives at LQD193×IIR1 on O** (product 1.0201 says +2 %, the pair measures −3.8 %): the divisor cut and the IIR reduction interact non-multiplicatively in the other direction. This one is not an artifact of my runs (the .meta and the singles agree).
3. **On G every pair composes sub-multiplicatively** (all six measured above their products) — the settings' savings overlap; the overlap is 1.3–4.3 % of the product, much smaller than long 36's bogus 10–12 %.
4. Suspicions, not proven: the LQD×IIR mechanism (the divisor changes the LMR base that IIR's --depth then modifies).

## 6. What I read from my colleagues
File 12 (the correction and the three other fixes — the interval formula acknowledged as mine to fix in long 44); the peer's long-34 work in progress (respected).

## 7. What I did NOT do
The triples and the full bundle (long 42's job).

## 8. What I am NOT sure about
The LQD193×IIR1 mechanism (5.2).

## 9. A better way
The singles' ratios should be re-measured in the SAME session as the pairs (my long-27 rows are from the same binary and base — they are; nothing to change).

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long41/stamps.txt
?? forge-combo29/REPORT_deepseek6_long41.md
?? forge-combo29/tests_deepseek6_long41/runs/
?? forge-combo29/tests_deepseek6_long41/table.txt
$ ls forge-combo29/tests_deepseek6_long41/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
