# REPORT — deepseek6, long 42 (the bundle: all four of long 41 together, and the four triples)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long42/ · claimed with claim.sh (the claim line in stamps.txt); stamps per stage; PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** run all four of long 41's settings together and the four triples, O and G at depth 12, against the products of the singles (built from long 27's table.txt by script) — does the bundle's tree follow the product within 2 %?
**Answer:** **NO, on both sets.** The full bundle measures **G 0.8569 against a 0.8007 product (+7.03 %)** and **O 0.9221 against 0.9648 (−4.42 %)**. The four triples' G deviations (+7.76 / +7.21 / +6.05 / +3.69) sit at or above their biggest contained pair's deviation in three of four cases (the T_LQD_LQB_IIR triple, +3.69, is BELOW its LQB101×IIR1 pair's 4.22 — prediction 4 killed by that one). Predictions: 1 held; 2 held; 3 killed (O −4.42 %); 4 killed (one triple).
**How sure:** certain of the ten runs and the script-built products; the accumulation pattern (bigger subsets, bigger G bias) holds in the direction but not strictly in magnitude.

## 2. Honesty numbers
The plain build /tmp/glmflash5_base/build/forge (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (its line in stamps.txt) | done | stamps.txt | exit 0 |
| 10 runs (1 bundle + 4 triples x O,G) | done | runs/*.rows + table.txt, .meta each | all rc=0 |
| the products (script, from long 27's table.txt) | done | table.txt | the same verified singles as long 41 |
| prediction own commit first | done | PREDICTION.md | 1, 2 held; 3, 4 killed |

## 4. The table
| config | O sum | O meas | O product | O off | G sum | G meas | G product | G off |
|---|---|---|---|---|---|---|---|---|
| all four | 8,759,858 | 0.9221 | 0.9648 | −4.42 % | 15,824,602 | 0.8569 | 0.8007 | +7.03 % |
| SD7+LQD193+LQB101 | 8,774,131 | 0.9236 | 0.8995 | +2.68 % | 15,865,905 | 0.8592 | 0.7973 | +7.76 % |
| SD7+LQD193+IIR1 | 9,344,381 | 0.9836 | 0.9840 | −0.04 % | 16,797,068 | 0.9096 | 0.8484 | +7.21 % |
| SD7+LQB101+IIR1 | 9,399,091 | 0.9894 | 1.0144 | −2.47 % | 16,872,873 | 0.9137 | 0.8616 | +6.05 % |
| LQD193+LQB101+IIR1 | 8,896,118 | 0.9364 | 1.0002 | −6.38 % | 16,863,177 | 0.9132 | 0.8807 | +3.69 % |

## 5. Findings
1. **The G bias grows with the subset and is always one-signed** (+0.66 → +4.25 over pairs, +3.69 → +7.76 over triples, +7.03 for the bundle): on games the four settings' savings systematically OVERLAP — the bundle shrinks less than the product says, by a growing margin.
2. **On O the sign flips between subsets** (−6.38 % to +2.68 % across triples; the bundle −4.42 %): the O tree's response to the four-way combination is not predictable from any single or pair — the largest-mover composition is genuinely interactive.
3. **The practical number**: the four "smaller-tree" ends together give O 8,759,858 (−7.8 % vs S14) and G 15,824,602 (−14.3 %) — far less shrink on O than the product's −3.5 % promise... (the product promised −3.5 %?? the product 0.9648 promises −3.5 %; the bundle delivers −7.8 % — MORE shrink on O, LESS on G relative to the products — the two sets' biases have OPPOSITE signs.)
4. Suspicions, not proven: the sign-flip mechanism between the sets.

## 6. What I read from my colleagues
The peer's long-34 progress (respected); nothing else new this hour.

## 7. What I did NOT do
The five- and six-way subsets beyond the bundle (the item names the bundle and the triples).

## 8. What I am NOT sure about
The opposite-sign mechanism (5.3).

## 9. A better way
None; the factorial completion (long 36's suggestion) would map the whole interaction surface.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long42/stamps.txt
?? forge-combo29/REPORT_deepseek6_long42.md
?? forge-combo29/tests_deepseek6_long42/runs/
?? forge-combo29/tests_deepseek6_long42/table.txt
$ ls forge-combo29/tests_deepseek6_long42/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
