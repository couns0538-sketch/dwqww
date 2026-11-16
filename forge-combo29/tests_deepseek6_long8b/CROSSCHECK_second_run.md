# CROSS-CHECK — long 8b, a second independent sweep on a different machine

2026-11-16T17:04:10Z · written by the deepseek6 instance whose first stamp is 2026-11-16T16:27:50Z
(DEEPSEEK6_START.txt). The other deepseek6 instance (job clock 16:20:48Z) pushed REPORT_deepseek6_long8b.md
(87d6865f1) while my own sweep of the same item was running. Nothing was overwritten: this file records the
second, independent execution and its agreement.

- My build: clean copy of 6b98f2170 + LmrFine.patch.txt (zero fuzz), RelWithDebInfo g++ 13.3.0
  -fsanitize=address,undefined -fno-omit-frame-pointer, exe sha256 c08535bd7b64c86c… (a DIFFERENT binary from
  the other instance's 978f22fb245c621b…).
- My honesty pins on that sanitizer build: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920,
  perft 5 = 4865609 (honesty_*.txt salvaged alongside this file).
- 18 runs (fine1 + eight F options moved once × O,G), depth 10, S14, sanrun.py/sancount.py: 0 sanitizer
  lines, exit 0, all 9,954 positions.
- My sums, and their equality with the other instance's long8b_table.txt cell for cell:

| config | O sum | G sum | other instance O | other instance G |
|---|---|---|---|---|
| fine1 | 3,809,466 | 7,290,580 | 3,809,466 | 7,290,580 |
| round0 | 3,809,466 | 7,290,580 | 3,809,466 | 7,290,580 |
| tpf2048 | 5,226,413 | 9,376,251 | 5,226,413 | 9,376,251 |
| nif0 | 4,721,134 | 8,799,294 | 4,721,134 | 8,799,294 |
| cnf0 | 3,955,281 | 6,995,244 | 3,955,281 | 6,995,244 |
| tcf0 | 4,059,760 | 7,066,656 | 4,059,760 | 7,066,656 |
| gcf0 | 3,763,279 | 6,510,006 | 3,763,279 | 6,510,006 |
| icf0 | 3,738,757 | 6,924,114 | 3,738,757 | 6,924,114 |
| caf0 | 4,909,001 | 8,784,942 | 4,909,001 | 8,784,942 |

- fine1 vs the long-8 defaults rows: nodes AND bestmove equal 200 of 200 (O) and 353 of 353 (G) — the same
  identity the other instance reports.
- Full compare log: CROSSCHECK_compare_out.txt (my compare_part0.py output against runs/LmrFine_*_fine1.rows
  and the long-8 defaults rows, from MY runs).
- Consequence worth keeping: two differently-built binaries (different sha256, different machines) produced
  bit-identical node counts on 18 configs × up to 553 positions — the search is build-reproducible, which is
  the fact Part 0 of job 1 needed and long 7 assumed.
