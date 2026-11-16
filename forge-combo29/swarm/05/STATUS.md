# STATUS seat 05

## seat
- seat: 05
- branch: for-fable-and-opus/swarm-05
- area: 5 (PRINCIPAL VARIATIONS AND SCORES)
- seed: 501

## Mon Nov 16 09:24:16 PM UTC 2026
- done: HONESTY 4/4; job1 complete — 553/553 rows, 0 illegal PV moves, 9/10 mate PVs exact, control PASS 6/6.
- finding S-F1 NEW: G/192 depth-12 `mate -12` has an 18-ply PV that does not end in mate, and the score itself
  collapses to -4 by depth 20; mate in 6 plies provable by hand.
- next command: python3 job2/split_draw_positions.py   (job 2: draw scores, 20 positions each of K v K, KN v K,
  KB v K, KNN v K, 20 threefold, 20 with the fifty-move counter at 99, score at depth 10)
- report: job1/REPORT_job1.md ; findings: FINDINGS.md

## Mon Nov 16 09:25:00 PM UTC 2026
- done: S-C1 CONFIRMS seat 06's S-F9 (both mirror pairs exact), plus beyond it: both mate-side PVs truncated.
- next command: python3 job2/split_draw_positions.py  (job 2: draw scores K v K / KN v K / KB v K / KNN v K,
  threefold, fifty-move 99; score at depth 10)

## Mon Nov 16 09:27:01 PM UTC 2026
- done: job2 complete. K v K / KN v K / KB v K = cp 0 (0 nodes) 20/20; KNN v K non-zero 20/20; threefold cp 0
  (0 nodes) 20/20 and correct (control: same FEN with no history = mate -11); fifty99 AND fifty98 all cp 0 while
  the same boards at counter 0 are +470..+1259.
- NEW S-F3: fifty-move draw fires ~9 plies early — cliff between halfmove 90 (cp 314) and 91 (cp 0), same for K+Q.
- next command: python3 job3/run_job3.py /tmp/build-asan/forge out3  (job 3: checkmated and stalemated root
  positions, 10 each, go depth 5 / go nodes 100 / go movetime 50, under ASan + UBSan)
