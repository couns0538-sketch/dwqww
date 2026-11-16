# REPORT — deepseek6, long 36 (SENSITIVITY D: the four biggest G-movers of long 27, all six pairs)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long36/ · claimed with claim.sh (exit 0); stamps per stage; PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** take the four long-27 settings with the largest |ratio − 1| on G (SingularDepth, LmrQuietDivisor, LmrQuietBase, IirDepth), run all six PAIRS at the ends that made the G tree smaller, and compare each pair's measured ratio against the product of its two single ratios — do they add up within 1 %?
**Answer:** **NO — they interact, strongly. On G only one of the six pairs is within 1 % (SD7×LQD193: 0.65 %); the other five are off by 3.4 % to 12.0 %** — every pair composes SUB-multiplicatively (the combined shrink is less than the product: two "shrink" settings together shrink less), and **on O the SD7×LQB85 pair even INVERTS: both singles shrink (0.9646 × 0.9804 = 0.9457) but the pair's tree is 1.0596 — BIGGER than S14** (+5.96 %). Predictions 2 and 3 are killed across the board; prediction 1 held (all twelve rows exist, none an identity).
**How sure:** certain of the twelve runs and the arithmetic (single ratios from my own long-27 committed rows); the interaction's mechanism is untraced.

## 2. Honesty numbers
The plain build /tmp/glmflash5_base/build/forge (sha e06310ec…); no new build.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| the four settings derived | done | PREDICTION.md (from long 27's committed G ratios) | SingularDepth, LmrQuietDivisor, LmrQuietBase, IirDepth; IirDepth flagged as the odd one (neither end shrinks G) |
| 12 runs (6 pairs x O,G) | done | runs/*.rows + table.txt, .meta each | all rc=0, none an identity |
| the product comparison | done | table.txt | five of six G pairs off by 3.4–12.0 %; O: five of six off by 3.2–12.0 %, one inversion |
| prediction own commit first | done | PREDICTION.md | 1 held; 2 and 3 killed |

## 4. The table (ratios against S14; products of the long-27 single ratios)
| pair | O measured | O product | O off | G measured | G product | G off |
|---|---|---|---|---|---|---|
| SD7 + LQD193 | 0.9470 | 0.9174 | 3.22 % | 0.8504 | 0.8449 | 0.65 % |
| SD7 + LQB85 | 1.0596 | 0.9457 | 12.04 % | 0.9607 | 0.8581 | 11.96 % |
| SD7 + IIR1 | 1.0390 | 1.0346 | 0.42 % | 0.9518 | 0.9130 | 4.24 % |
| LQD193 + LQB85 | 0.9636 | 0.9325 | 3.34 % | 0.9709 | 0.8771 | 10.69 % |
| LQD193 + IIR1 | 0.9617 | 1.0201 | 5.73 % | 0.9653 | 0.9332 | 3.44 % |
| LQB85 + IIR1 | 1.0961 | 1.0516 | 4.23 % | 1.0379 | 0.9478 | 9.51 % |

(The two pairs containing IIR1 on O compose nearly additively — 0.42 %/5.73 % — because IIR1's own O effect is an increase; the G side does not.)

## 5. Findings
1. **One-step sensitivities do not compose**: the sub-multiplicative pattern (combined shrink < product) on five of six G pairs means the four settings share mechanism overlap — they move the same subtree populations, so their savings partially cancel when combined.
2. **The SD7+LQB85 pair INVERTS on O** (both singles shrink, the pair grows +6 %): the strongest warning yet against tuning settings one at a time — the tuner's independent-step assumption fails exactly among its biggest movers.
3. **The one clean pair (SD7+LQD193 on G, 0.65 %)** pairs the two settings whose single effects act at different depths (SingularDepth at the extension/re-search boundary; LmrQuietDivisor inside the LMR term) — consistent with the overlap story, not proof of it.
4. Suspicions, not proven: the shared-mechanism reading in 1 and 3.

## 6. What I read from my colleagues
kimi5's job-4 note (its deeper/shallower arms also failed the independence test: |product − both| = 0.086 > 0.05) — my six pairs are the same phenomenon across the tuner's biggest movers; the peer's long-25 progress (live claim respected).

## 7. What I did NOT do
The three-way and four-way combinations (the item names pairs); the O/G direction flips' mechanism.

## 8. What I am NOT sure about
The shared-mechanism story (5.1/5.3).

## 9. A better way
A tuner that wants to move these four should evaluate PAIRS, not singles — this table is the evidence; a full 2^4 factorial (16 runs) would complete the picture if wanted.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long36/stamps.txt
?? forge-combo29/REPORT_deepseek6_long36.md
?? forge-combo29/tests_deepseek6_long36/runs/
?? forge-combo29/tests_deepseek6_long36/table.txt
$ ls forge-combo29/tests_deepseek6_long36/
CLAIM.txt
PREDICTION.md
runs
stamps.txt
table.txt
```
