# REPORT — deepseek6, long 14 (recipe R on kimi5's tunable_AspReopenMargin, its job 3.2)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long14/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run (fe51c7f36).

## 1. Three lines
**Asked:** reproduce kimi5's AspReopenMargin tunable: pins, identity at the default, its tested margin settings compared with its numbers, and a sanitizer pass with a planted fault.
**Answer:** R1–R3 met (sha 0e950197…; pins exact; `AspReopenMargin` spin default 13 min 0 max 400 in the uci list; the tunable build under S14 equals my long-1 rows on O 200/200 and G 353/353). R4 has ONE finding and ONE surprise: **(a) my remake of the wiring control does NOT reproduce kimi5's three sums** — with AspCappedReopen true on its wire8.fens at depth 12 I get 270,415 / 249,794 / 320,651 for margins 0/13/100 against its reported 279,937 / 407,550 / 469,476 (depths 14 and 16 do not match either; the wiring run's depth and option context are not in its committed artifacts — reported as a finding, not reconciled by guessing); **(b) on the full sets the margin is INERT under S14 at depth 12**: margins 0 and 100 give EXACTLY the S14 sums on O (9,500,069) and G (18,466,239) — the aspiration reopen never fires in the tuner's actual configuration, so my direction prediction is KILLED by exact equality. R5: the planted fault IS reported (ASan, exit 1); the clean sanitizer build over O under S14 d12: **0 sanitizer lines over 200 positions**.
**How sure:** certain of every number I produced (all committed with .meta); the R4a mismatch is stated as unresolved, with the candidate causes named and the raw rows committed for whoever holds the missing context.

## 2. Honesty numbers (tunable build /tmp/l14_tun/build/forge)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| R1 sha + apply + four builds | done | build logs; sha in R1.txt | 0e9501973142fe93… matches; tun, wire (counters+asp, one hunk at offset 29, zero fuzz), san, plant |
| R2 pins + uci | done | honesty_*.txt, uci.txt | four exact; the option listed with default 13 |
| R3 identity under S14 | done | compares.txt | O 200/200, G 353/353 |
| R4a wiring remake | done | runs/r4a_*.rows, compares.txt, wire depths 14/16 in wire_depths.txt | DOES NOT match kimi5's three sums — finding 4.1 |
| R4b margins on O and G | done | runs/r4b_*.rows, compares.txt | inert under S14 d12 (exact equality) — finding 4.2; prediction killed |
| R5 planted fault | done | plant_evidence.txt | ASan heap-buffer-overflow, READ of size 4, exit 1 |
| R5 clean sanitizer | done | san/O_s14_d12.rows | 0 lines / 200 positions |
| prediction own commit first | done | PREDICTION.md (fe51c7f36) | items 1, 4 held; item 2 killed (the mismatch); item 3 killed (inert) |

## 4. Findings
1. **The wiring-control sums do not reproduce.** Same 8 positions (wire8.fens from kimi5's branch), same two patches (counters then asp, zero fuzz), AspCappedReopen true, depth 12: mine 270,415 / 249,794 / 320,651 vs its reported 279,937 / 407,550 / 469,476. Depths 14 (861,837 / 1,251,023 / 1,012,533) and 16 (2,271,809 / 2,334,819 / 1,900,216) do not match either, and the margin ORDER is not monotone at any tested depth. Its report commits no wiring run log, so the missing context (depth, option base, or a build state older than the committed patches) cannot be recovered from the branch. This is the first R4 reproduction failure in my long 9–14 series.
2. **AspReopenMargin is inert where the tuner would move it**: under S14 at depth 12, margins 0 and 100 give node-for-node the S14 rows on O and G — the capped-reopen branch of the aspiration loop never executes on these 553 positions at this depth. (Consistent with the mechanism: AspirationDelta 18 windows hold at these depths.) The option is WIRED (the wiring control proves it acts when the loop fails) but DEAD in the S14/d12 configuration — the same "dead at this configuration" sense my long-9-to-13 series has now met three times.
3. Suspicions, not proven: the R4a mismatch's cause (depth unstated / build state older than the committed patches / an option context not in the report text).

## 5. What I read from my colleagues
kimi5's REPORT_kimi5_job3.md (its Part 3.2 postscript naming the cont4 weight as the measured suspect; its honest note that the wiring control exists because of deepseek5's job-4 lesson); the peer's progress (long 10 done on its side). Nothing contradicts this report.

## 6. What I did NOT do
The eight-switch counter study of kimi5's job 3 Part 2 (that is counters.patch.txt's job — recipe R here is for the TUNABLE patch; my long 2–5, job 1 and job 3 reports already cover the counter patch's descendants per the recipe's own skip rule).

## 7. What I am NOT sure about
The R4a mismatch's cause (named above). I did not guess a depth that fits.

## 8. A better way
kimi5's wiring control should have committed its input log and rows file (its own job-4 lesson, which its job-3 postscript cites) — the 8-position sums without raw output cannot be audited; that gap is what leaves my R4a open.

## 9. times: see stamps.txt
## 10. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long14/stamps.txt
?? forge-combo29/REPORT_deepseek6_long14.md
?? forge-combo29/tests_deepseek6_long14/compares.txt
?? forge-combo29/tests_deepseek6_long14/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_long14/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_long14/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_long14/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_long14/long14_runs.sh
?? forge-combo29/tests_deepseek6_long14/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long14/runs/
?? forge-combo29/tests_deepseek6_long14/san/
?? forge-combo29/tests_deepseek6_long14/wire_depths.txt
$ ls forge-combo29/tests_deepseek6_long14/
CLAIM.txt
compares.txt
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
long14_runs.sh
plant_evidence.txt
PREDICTION.md
runs
san
stamps.txt
wire_depths.txt
```
