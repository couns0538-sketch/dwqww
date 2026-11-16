# SEAT 15
- seat: 15
- branch: for-fable-and-opus/swarm-15
- area: 5 (PRINCIPAL VARIATIONS AND SCORES)
- seed: 1501

## 2026-11-16T21:36:46Z — job 2 measured, findings pushed (deadline 22:30 UTC)

Done:
- STEP 1 + STEP 2: seat 15; Release build of 6b98f217, sha256 e06310ec…16a83; all four honesty numbers exact.
- AREA 5 **job 1 COMPLETE** (report pushed): 553 positions depth 12 S14; 0 illegal PV moves, 0 bestmove/PV
  mismatches, 9/10 mate Pvs obey the length rule, 1 violation. Findings 15-F1, 15-F2.
- AREA 5 **job 2 measured, analysis done**: 120 positions (KvK, KNvK, KBvK, KNNvK, threefold, halfmove 99)
  at depth 10 S14. Results: KvK/KNvK/KBvK/threefold all exactly cp 0 (prediction P1-P5 held);
  KNN v K NOT 0 in 19 of 20 => P4 REFUTED (finding 15-F3).
  halfmove-99: 14 of 20 nonzero, min 0 max 390 => P6 REFUTED as written (my kill band was |score|>200).
  My prediction was the thing that was wrong there: every position scoring >200 has a capture or pawn
  move available, which resets the fifty-move counter, so a nonzero score is defensible. I record
  P6 as refuted and the engine as not at fault.
  Findings 15-F3, 15-F4. REPORT_job2.md being written now.
- Measurement integrity: after seat 19's warning every parser asserts the parsed token exists and fails
  loudly (job2/analyze_draw.py raises on a missing 'score'); this caught a bug of my own — an empty PV
  prints as "time 0 pv", which my first filter dropped, making 80 positions look like no-output.

Running now: nothing.

Next exact command:
  cd /agent/repos/dwqww/forge-combo29/swarm/15/job2 && python3 analyze_draw.py out_d10.jsonl > analyze_d10.txt

Then: REPORT_job2.md, push, then AREA 5 job 3 (checkmated/stalemated roots under ASan+UBSan).
