# S10 screen rule v2 (QA fix-ups S10-1, S10-4, S10-5, S10-6) — applies to every later OFF-default search idea

1. **Order (cheap gates first, stop at the first FAIL).** d11 activation (ON d11 must differ from OFF d11) →
   5-depth node sweep with the deep-node guard (|ON/OFF - 1| > 0.20 at d20 or d22 = FAIL) → one WAC300 ON screen at
   1000 ms/position on Lprime (< 283/300 = FAIL) → only then full Std/ASan/UBSan on Lprime and B.
2. **A FAIL is final for the idea (S10-1).** WAC < 283/300 or a node-guard FAIL rejects the idea; its B
   qualification is SKIPPED (no B build, bench, CTest). A missing number is not a pass. Tool:
   `opus_s10_screen_verdict.py` (applied to Sol's four ideas: all FAIL, B should have been skipped for all four).
3. **Deadlines (from S10-3).** A fixed-depth bench deadline must allow for load: on Sol's box OFF d22 took
   76-166 s (NPS 188k-407k) under a 180 s deadline. Use at least 5x the slowest observed time of the same depth, or
   check CPU-time progress before calling a timeout a hang (`opus_s10_bench_rerun.py` logs both).
4. **Machine exclusive (S10-6).** Every screen (WAC, bench timing, NPS) records `machine exclusive: yes/no` plus the
   system load during the run; no `git push`, archive or build is started while a screen runs.
5. **Delivery hygiene (S10-4, S10-5).** Keep the final files plus ONE diff log for superseded versions; no
   `_before_<fix>` copies (`opus_s10_hygiene_check.py` exits 1 if one is found); list every `.tar.gz` with its size.
