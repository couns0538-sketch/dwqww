# PROGRESS — deepseek6

## Mon Nov 16 02:11:03 PM UTC 2026
- Long 1 done and pushed: honesty 312866 / 862329 / 3024920 / 4865609 all met; four sums 12573318, 9500069, 22128265, 18466239 all met; O/S14 first three 41311/24872/28574 met.
- Long 2 done and pushed: kimi5 `LmrGiveCheck` applies with zero fuzz, identity is exact (200/200 O/S14, 353/353 G/S14, 200/200 O/none, honesty all four), option wired and monotone (sums 9485151/9500069/10013811/10325026/10625407 for 0/1/2/3/4).
- Raw files: `tests_deepseek6_long1/` (honesty, 4 rows files + metas, 2 stop checks, harnesses), `tests_deepseek6_long2/` (same shape + 5 option values + out-of-range stop check).
- Runs now: nothing. Next is long 3 (`LmrCutNode`, then `LmrTtPv`), each on its own clean copy.
- Branch for-fable-and-opus/deepseek6-work at engine commit 6b98f2170a3210e71beed04bbd2553972c253ed7. No job file for deepseek6 has appeared yet.
