# REPORT — deepseek6, long 22 (ThreadSanitizer, 2 and 4 threads, first 50 of O)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long22/ · CLAIM.txt before the first command; PREDICTION.md before the first counted run (e923d2889).

## 1. Three lines
**Asked:** run the plain base (S14), B_FINE at T2, and FailHighBlend 7 under ThreadSanitizer at Threads 2 and 4 over the first 50 of O at depth 12, with one planted data race that must be reported.
**Answer:** **the planted race IS reported** (2 data-race reports, TSan exit 66, on the scratch copy with one unlocked global incremented from every worker thread — the reports were initially hidden by a pre-set `TSAN_OPTIONS=log_path=...` in my shell environment, left over from an earlier session's run; with the variable cleared the reports appear on stderr — disclosed in 4.1). **The three real builds at both thread counts: ZERO TSan reports in all six runs** (300 positions × 2 thread settings, every position exit 0, every position produced a bestmove).
**How sure:** certain that the tool was live for the clean runs (the plant fired under the same runner with the same env handling); the clean zeros are real.

## 2. Honesty numbers
Not applicable to TSan builds (instrumentation changes timing; the tree identities of these three sources are established in long 1, long 5c/job 4 and the peer's job 3).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| four TSan builds | done | build logs | plain, fine (LmrFine), fhb (FailHighBlend), race (the plant) — all with -fsanitize=thread |
| plant fires | done | /tmp/l22race2.txt copy: plant_evidence.txt | 2 data-race reports, exit 66 |
| six clean runs | done | runs/*.rows.tsan (per-position tsan-lines count + exit), runs/*.rows (bestmoves) | 0 reports x 300 position-runs; 0 NONE/REFUSED rows |
| prediction own commit first | done | PREDICTION.md (e923d2889) | all four items held |

## 4. Findings
1. **The environment carried a stale TSAN_OPTIONS** (`log_path=/tmp/glmflash/j4tsan halt_on_error=0 second_deadlock_stack=1`) from an earlier session's shell state: TSan wrote its reports to files under that prefix and the terminal saw nothing, while the exit code still said 66. My runs use `env -u TSAN_OPTIONS`; the plant's reports were then visible. Anyone re-running TSan on this VM should clear that variable first — it silently diverts reports.
2. **The engine's threading is TSan-clean** on all three sources at 2 and 4 threads over 50 positions each: no data race, no deadlock report (the atomics-based TT and the counters hold).
3. Suspicions, not proven: none.

## 5. What I read from my colleagues
Nothing new this item (the 4-hour colleague clock is due ~20:30; the last full read was 16:29 plus the job-file relays since).

## 6. What I did NOT do
G-set TSan runs (the item names the first 50 of O only); deeper runs (depth 12 as named).

## 7. What I am NOT sure about
Nothing material.

## 8. A better way
The per-position process restart is wasteful under TSan (the tool benefits from long-lived processes); a game-loop runner would cover more nodes per report cycle — not needed at this size.

## 9. times: see stamps.txt
## 10. model name my runtime gives: glm-5p3-flash

## 11. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long22/stamps.txt
?? forge-combo29/REPORT_deepseek6_long22.md
?? forge-combo29/tests_deepseek6_long22/plant_evidence.txt
?? forge-combo29/tests_deepseek6_long22/runs/
$ ls forge-combo29/tests_deepseek6_long22/
CLAIM.txt
long22_runs.sh
plant2.txt
plant_err.txt
plant_evidence.txt
plant_out.txt
PREDICTION.md
runs
stamps.txt
tsanrun.py
```
