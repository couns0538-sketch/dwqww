# REPORT_job10_2 — seat 11, area 10 job 2: recount a helper's report from its raw files

## 1. What was asked
Recount the newest report of the helper deepseek6 (branch `for-fable-and-opus/deepseek6-work`,
`forge-combo29/REPORT_deepseek6_longK.md`, raw files in `forge-combo29/tests_deepseek6_longK/`)
from its raw files: which of its numbers equal its report and which do not.

## 2. What I actually found before recounting: the named file does not exist
`REPORT_deepseek6_longK.md` and `tests_deepseek6_longK/` are **both missing** from that branch.
`git cat-file -e` on each exact path fails, and no path on the branch contains the token `longK`.
The branch instead carries `long1 … long58` (plus `4a/4b/5a/5b/5c/8b`). So "the newest report"
is a judgement call; I took **long58**, the highest number, and checked first that the other
area-10 seat had not already taken it — seat 10 worked on `long56` (its FINDINGS 10-F1..F5), so
long58 is clear.

## 3. The answer
Every number in `REPORT_deepseek6_long58.md` reproduces from its raw rows **except one**: the
step table says "best moves changed: **6–33** of 100 per run"; the raw rows give **2** and **4**
for the two ends of `FutilityDepth`, so the true range is **2–33**. Its own committed
`table_out.txt` already shows `4/100` and `2/100` for those rows, so the discrepancy is between
the report's *prose table* and its own data — not between two computations.

What matches exactly: base run twice = 12,377,717 and row-for-row identical; 32 settings × 2
ends = 64 runs; every run 100 rows; the top-10 ranking by |ratio−1| identical; the |ratio−1|
range 0.0100 … 0.1914; SingularMargin −c 1.1914 / +c 0.8220; all 32 settings alive at the
report's own 0.1 % threshold.

## 4. How sure
High. I wrote my own reader from the report's stated rule and never opened `table58.py`; every
count is reproducible by hand with `paste`/`awk` (commands below), and the BASE1-vs-BASE2
comparison (0 differences) is the control that the counting method can see a difference.

## Honesty numbers
My build: 312866 / 862329 / 3024920 / 4865609 (unchanged). This job ran no searches of its own —
it reads committed raw files — so no pin applies beyond the build I would have used.

## 5. Table
| step | done/partly/not | evidence file | result |
|---|---|---|---|
| locate the named report | done | `git cat-file -e` in the transcript | **missing**; branch has long1..long58 |
| confirm seat 10 did not take long58 | done | seat 10 FINDINGS (long56) | long58 clear |
| base twice | done | `checks/recount_long58.txt` | 12,377,717 twice, row-for-row identical |
| 32 settings × 2 ends, 100 rows each | done | same | all present, all 100 rows |
| top-10 ranking | done | same | identical to the report |
| |ratio−1| range | done | same | 0.0100 … 0.1914, equal |
| SingularMargin | done | same | 1.1914 / 0.8220, equal |
| best moves changed | done | same + hand `paste`/`awk` | **2 … 33**, report says 6 … 33 |

## 6. Findings
- **S-F9** (above). Shows it again:
  ```
  cd <long58>/runs
  paste -d'|' <(cut -d'|' -f3 BASE1.rows) <(cut -d'|' -f3 FutilityDepth_p.rows) | awk -F'|' '$1!=$2' | wc -l   # 2
  paste -d'|' <(cut -d'|' -f3 BASE1.rows) <(cut -d'|' -f3 FutilityDepth_m.rows) | awk -F'|' '$1!=$2' | wc -l   # 4
  paste -d'|' <(cut -d'|' -f3 BASE1.rows) <(cut -d'|' -f3 BASE2.rows)          | awk -F'|' '$1!=$2' | wc -l   # 0  (control)
  ```
- The named-file absence (section 2) is itself worth passing on: the brief's area-10 job 2 path
  is stale, and any seat following it literally will report "not found" and stop.

## 7. Suspicions, not proven
- The "6–33" is most likely a hand-typed summary of the table rather than a computed range; the
  table itself is right. I did not read deepseek6's scripts to confirm where it was typed.
- long58's numbers are self-consistent but I did not re-run the searches, so I cannot say the
  node sums are *correct* — only that they are *what the committed rows give*.

## 8. What I did NOT do
- Did not re-run any search (this job is a recount of raw files).
- Did not check long53's `G100_fresh_d14` cross-reference the report claims (a different item).
- Did not audit long56 (seat 10 did).

## 9. What I am NOT sure about
- Whether the brief meant a different helper branch by "deepseek6"; I used the branch it names.

## 10. Times
See `stamps.txt`.

## 11. Last command's output
```
$ ls checks/ | grep recount
recount_long58.txt
```
