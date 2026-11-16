# REPORT — deepseek6, long 19 (the two bundle builds for glmflash5's file 28)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long19/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run.

## 1. Three lines
**Asked:** build the two bundles glmflash5's file 28 needs and produce their rows: (a) ChecksLmr + LmrFine for S14, V, T1, V+T1; (b) ChecksLmr + the three job-5 Sound patches for S14, P, V+P.
**Answer:** bundle (a) required a BY-HAND composition (the two patches collide in the LMR block — each rewrites the other's context; both orders fail a dry run; the composed tree = LmrFine's block with ChecksLmr's two option reads in its INTEGER branch, committed as bundle_a_compose.patch.txt). **Its known answers are all EXACT: S14 9,500,069 / 18,466,239; V on O 8,565,026; T1 10,170,054 / 19,269,858. V+T1 = 9,331,413 (O) / 15,801,647 (G) — both inside my prediction ranges.** Bundle (b) applied in the order ChecksLmr, SoundArms, SoundRegret, SoundSteps (the job-5 order fails SoundRegret's dry run after Steps — disclosed); S14 exact on both sets; **P is nearly inert at depth 12 (O 9,476,627 = −0.25 %, G 18,535,879 = +0.38 % — my d10-ratio extrapolation KILLED); V+P = 8,650,468 (O, +1.0 % OVER V alone — direction flipped vs P alone, prediction killed) and 14,378,693 (G, inside my range)**. Both bundles' pins exact.
**How sure:** certain of every sum; the composition's semantic gap (V's LmrGiveCheck=0 acts only when LmrFine=0, because the fine branch keeps its own LmrGiveCheckF) is stated in the patch header and matters for how file 28's matches must set their options.

## 2. Honesty numbers
Bundle A /tmp/l19a/build/forge: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609. Bundle B /tmp/l19b/build/forge: the same four exact (honesty_*.txt; the second set overwrote the first — both ran, both exact; noted).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| shas verified | done | R1.txt | clmr d33b27ca…, lf f7bf3f43…, Arms 57524c71…, Steps 07713c3b…, Regret 10208495… — all as the recipes state |
| dry runs on top of the previous | done | order log in stamps/notes | bundle (a): BOTH orders fail (LMR-block collision) → hand composition; bundle (b): Arms,Steps,Regret FAILS; Arms,Regret,Steps works |
| bundle A composed + built | done | bundle_a_compose.patch.txt (2,891 lines, diff -u vs clean) | built; LmrFine and both ChecksLmr options verified present |
| bundle B built | done | build log | four patches in the working order |
| bundle A rows (8) | done | runs/a_*.rows, sums.txt | S14/V/T1 all EXACT; V+T1 inside predictions |
| bundle B rows (6) | done | runs/b_*.rows, sums.txt | S14 exact; P nearly inert (prediction killed); V+P: O killed, G held |
| prediction own commit first | done | PREDICTION.md | 1 held, 2 held (both), 3: S14 held, P/V+P killed on O and P killed on G, 4 held |
| R5 sanitizer | not applicable | — | long 19 is a bundle-builds item; the recipe's R5 belongs to recipe-R items; noted here |

## 4. The sums (depth 12)
| config | O | G |
|---|---|---|
| (a) S14 | 9,500,069 ✓ | 18,466,239 ✓ |
| (a) V | 8,565,026 ✓ | 14,633,520 |
| (a) T1 | 10,170,054 ✓ | 19,269,858 ✓ |
| (a) V+T1 | 9,331,413 | 15,801,647 |
| (b) S14 | 9,500,069 ✓ | 18,466,239 ✓ |
| (b) P | 9,476,627 | 18,535,879 |
| (b) V+P | 8,650,468 | 14,378,693 |

## 5. Findings
1. **ChecksLmr and LmrFine are text-incompatible** — both rewrite the LMR block's gives_check/in_check lines. The composed bundle exists (bundle_a_compose.patch.txt) and its four known answers are exact, so the composition is behaviorally sound at the defaults; but the SEMANTICS of V+T1 under it are asymmetric: V's LmrGiveCheck=0/LmrInCheck=0 reach only LmrFine's integer branch (dead when LmrFine=1); the fine branch keeps LmrGiveCheckF/LmrInCheckF at 1024. **File 28's V+T1 match therefore tests a mixed semantic unless it also sets LmrGiveCheckF=0/LmrInCheckF=0** — that decision is glmflash5's (or Opus's) to make; both variants are one option line apart.
2. **P (SoundPvArm 1 + SoundStepMask 1) is nearly inert at depth 12** on both sets (−0.25 % / +0.38 %) — my long-8-addendum d10 ratio (0.967) does not carry to depth 12; the d10 effect was depth-specific.
3. **P's direction flips under V on O** (+1.0 % over V alone after being −0.25 % under S14) — the Sound arms interact with the extension-changed tree; not additive.
4. The working patch order for bundle B is Arms → Regret → Steps (Regret's uci hunks expect Arms's lines; Steps inserts before Regret's anchor).
5. Suspicions, not proven: the mechanism sentences in 1 and 3.

## 6. What I read from my colleagues
glmflash5's job-21 report (B10's recipe and sha — re-verified); kimi5's job-5 patches (shas verified). Nothing contradicts this report.

## 7. What I did NOT do
The sanitizer pass (not part of this item's spec); the bundle rows were produced by the release builds only.

## 8. What I am NOT sure about
Whether file 28's V+T1 wants LmrGiveCheckF=0/LmrInCheckF=0 with it — flagged in finding 1 for the match owner.

## 9. A better way
kimi5's job-5 patches and ChecksLmr/LmrFine should ship a stated compose order (or composed bundles) — three of my five dry-run failures came from unstated order constraints.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long19/stamps.txt
?? forge-combo29/REPORT_deepseek6_long19.md
?? forge-combo29/tests_deepseek6_long19/bundle_a_compose.patch.txt
?? forge-combo29/tests_deepseek6_long19/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long19/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long19/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long19/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long19/runs/
?? forge-combo29/tests_deepseek6_long19/sums.txt
$ ls forge-combo29/tests_deepseek6_long19/
bundle_a_compose.patch.txt
CLAIM.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
PREDICTION.md
runs
stamps.txt
sums.txt
```
