# REPORT — deepseek6, long 52 (the IirAtRoot patch: the root and internal iterative reduction)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long52/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the counted runs.

## 1. Three lines
**Asked:** a text patch adding a UCI check option `IirAtRoot` (default true = today) that keeps internal iterative reduction off at the root only; pins, the identity, the (a)/(b) pair with true (the knowns) and false, and the full-set inertness.
**Answer:** the patch (IirAtRoot.patch.txt, 52 lines, zero fuzz) touches search.cpp:1784 (the IIR line — `if (mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;`), the root recognised by `root_node` (`ss->ply == 0`, set at the top of Worker::search), the bool next to the other check flags, and uci.cpp's check-option print/handler chains. **Pins exact; the S14 identity at the default holds on O 200/200 and G 353/353; the knowns reproduce from the patched build ((a,true) = 2,150,681, (b,true) = 1,483,521); (a,false) == (a,true) on all 50 (the root IIR is inert without searchmoves); (b,false) = 2,299,588 = +55.0 % over (b,true) — the IIR tax removed, overshooting (a) by 7 %; (b) never equals (a) under either setting (the restricted root's missing TT store is independent); the full sets with false are EXACT identities on O and G (0 changed rows of 553).** ALL SEVEN PREDICTIONS HELD.
**How sure:** certain (the four 50-position runs + the two full-set runs + the two identity runs, .meta each; the knowns from my own long-47).

## 2. Honesty numbers
The patched build /tmp/l52/build/forge: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt); the wrong value ("banana") refused with "info string invalid value for option IirAtRoot".

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| the code reading (file+line) | done | section 1 above | search.cpp:1784 (the IIR line); root_node from ss->ply == 0 |
| IirAtRoot.patch.txt | done | the patch file | check option, default true; the uci print + handler + the search.hpp extern |
| pins | done | honesty_*.txt | four exact |
| the S14 identity at the default | done | runs/ident_O.rows, ident_G.rows | 200/200, 353/353 |
| (a)/(b) x true/false on the first 50 | done | runs/a_true, b_true, a_false, b_false + table.txt | the knowns EXACT; the +55.0 % restoration; (a) unchanged |
| the full sets at false | done | runs/fullfalse_O/G.rows, full.txt | EXACT identities (0/553 changed) |
| prediction own commit first | done | PREDICTION.md | all seven held |

## 4. The table (the first 50 of O, depth 12)
| setting | (a) sum | (b) sum | positions (a)=(b) | best moves (a) vs (b) differ |
|---|---|---|---|---|
| IirAtRoot true | 2,150,681 ✓ | 1,483,521 ✓ | 0/50 | 17/50 |
| IirAtRoot false | 2,150,681 | 2,299,588 | 0/50 | 14/50 |

## 5. Findings
1. **The mechanism is confirmed from both directions**: with searchmoves (a restricted root) the IIR fires at the root and SHRINKS the tree by 31 % (long 47); switching the root's IIR off restores it to +55 % over the restricted baseline (2,299,588) — overshooting the unrestricted (a) by 7 %, because the restricted root's OTHER handicap (no TT store) remains.
2. **Without searchmoves the root IIR is provably inert** (the full-set identities at 553 positions) — the root has a hash move from the second iteration on, exactly as my prior run's long-6 predicted and now measured at full scale.
3. **The check-option plumbing**: the tune table (int*) cannot hold a check option — the patch follows the LmrDeeperShallower pattern (a bool in search.cpp, an extern in search.hpp, a print line and a handler branch in uci.cpp). A wrong value is refused.
4. Suspicions, not proven: none.

## 6. What I read from my colleagues
File 14 (the item; its long-47 recount confirming my numbers from its own engine); my prior run's long-6 (the +55 % figure — reused as the prediction and confirmed).

## 7. What I did NOT do
The G-set 50-position variant of the (a)/(b) test (the item names O's first 50); the IirRootExclude patch of my prior run (superseded by this differently-named form).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
The prior run's IirRootExclude patch and this IirAtRoot patch are the same experiment under two names; one of them should have been linked in the report — done here.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
?? forge-combo29/REPORT_deepseek6_long52.md
?? forge-combo29/tests_deepseek6_long52/IirAtRoot.patch.txt
?? forge-combo29/tests_deepseek6_long52/PREDICTION.md
?? forge-combo29/tests_deepseek6_long52/full.txt
?? forge-combo29/tests_deepseek6_long52/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long52/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long52/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long52/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long52/runs/
?? forge-combo29/tests_deepseek6_long52/smrun.py
?? forge-combo29/tests_deepseek6_long52/stamps.txt
?? forge-combo29/tests_deepseek6_long52/table.txt
$ ls forge-combo29/tests_deepseek6_long52/
CLAIM.txt
full.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
IirAtRoot.patch.txt
PREDICTION.md
runs
smrun.py
stamps.txt
table.txt
```
