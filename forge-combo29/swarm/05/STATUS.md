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

## CHECKPOINT (push per owner's 30-minute request)
- done since last block: job2 report+findings pushed (S-F3 fifty-move cliff at 91, S-F4, S-F5, S-F6); job3 roots
  generated and verified (10 checkmate + 10 stalemate, python-chess asserted); job3 ASan+UBSan run complete:
  60/60 runs, 0 sanitizer lines, 0 crashes, 0 hangs, all bestmove 0000.
- job3 SANITIZER PROOF both halves done: nm shows 35 __asan_ / 15 __ubsan_ symbols; a planted heap over-read
  (planted_fault.patch.txt, built in /tmp only) run through THE SAME runner is counted (3 sanitizer lines/run).
- 19-F12 audit: my job1 harness is CLEAN — its node sums reproduce the brief exactly (O 9,500,069 with first
  three 41,311/24,872/28,574; G 18,466,239), which a fabricated bestmove could not do. The risky piped-quit
  pattern reproduces a2a3/0 nodes on my build; my job3/job2/rows harnesses all read to bestmove first.
  job0/honesty.sh did pipe quit — re-running honesty with a read-to-terminator harness now.
- next command: python3 audit19f12/honesty_safe.py /tmp/build-rel/forge audit19f12/out

## Mon Nov 16 09:36:30 PM UTC 2026 — owner checkpoint 2
- 19-F12 AUDIT COMPLETE: reproduces on my build (piped quit -> bestmove a2a3, 0 info lines; read-to-bestmove ->
  e2e4 / 56,720 nodes, identical to quitting 2 s later). My job1 rows run is UNAFFECTED: it reproduces the brief's
  node sums exactly (O 9,500,069 first three 41,311/24,872/28,574; G 18,466,239), 0 zero-node positions of 553.
- honesty.sh's piped pattern re-run with a safe harness: 312866 / 862329 / 3024920 / 4865609 all OK, HONESTY stands.
- job3 complete under ASan+UBSan with both sanitizer proofs (nm 35 __asan_/15 __ubsan_; planted fault counted).
- next command: write job3/REPORT_job3.md from the committed raw files, then job3 of area 5 is closed.

## Mon Nov 16 09:37:11 PM UTC 2026 — findings push
- S-C4: fixed a real false-verdict path in job1/mate_check.py (missing parse -> MISMATCH = invented REFUTES).
  Now NO_VERDICT/unknown; proven by control; published numbers unchanged (ok=4 mismatch=6).
- Both verdict-producing checks re-derived with hard parse assertions: S-C1 all four scores match; job1 mate
  table 9/10 consistent as published. audit19f12/parser_audit.py exits non-zero if any parse fails.
- Everything pushed: FINDINGS.md (S-F1..F6, S-C1..C4), all job1/job2/job3 raw outputs, planted_fault.patch.txt.
- next command: write job3/REPORT_job3.md from committed raw files.

## Mon Nov 16 09:38:00 PM UTC 2026 — findings push 2 (owner deadline 22:30)
- job1b (cycle step c, SEED+10=511, new R set of 200 random-play positions) MEASURED AND CHECKED.
  200/200 bestmove+pv, 0 illegal PV moves. 18/200 mate scores, 17/18 exactly 2N-1 consistent.
  Sum 12,230,484 nodes, median 46,976, 0 zero-node positions.
- NEW S-F9: the S-F1 truncation REPRODUCES on a fresh set (R pos 120: mate -13 with a 14-ply PV, self-corrects
  to -10 at d16 and -8 at d18) => it is general behaviour, not a G/192 curiosity.
- My predictions #3 (expected 0-6 mate scores, got 18) and #6 (median 60k-130k, got 46,976) were WRONG and the
  kill condition for #3 fired; report will say so. #9 (truncation reappears) HELD.
- next command: write job1b/REPORT_job1b.md, then push final.

## Mon Nov 16 09:38:16 PM UTC 2026 — FINAL (owner deadline 22:30)
- ALL jobs done and pushed: job1, job2, job3, job1b, plus audit19f12 and check_s06f9, and FINAL_SUMMARY.md.
- Findings on GitHub: S-F1..F10, S-C1..C4. Every job has REPORT_jobN.md built from committed raw files.
- job1b report added; predicted-vs-actual table says plainly which two predictions failed.
- next command (if resumed): python3 job2/threshold_probe.py on a THIRD material to test whether S-F3's 91
  boundary is material-dependent (K+B+B vs K), since that is the cheapest open question left.

## Mon Nov 16 09:39:46 PM UTC 2026
- S-F11 NEW: the fifty-move cliff tracks counter+depth (d6->95, d8->92, d10->91, d12->89, each summing to 100-101),
  which reconciles my "9 plies early" with seat 25's "one ply early" — same rule, different mate distances.
- S-C5 CONFIRMS seat 15's 15-F3 on my own 20 KNN v K positions (20/20 non-zero off, 20/20 cp 0 on) plus the
  control it needs: DeadMaterial true leaves K+Q/K+R wins at cp 472..1162, so the switch is selective.
- next command: python3 check_15f3/check_15f3.py on a KNN v K position whose knights are far apart, to test
  whether DeadMaterial keys on material alone or on the concrete position.

## Mon Nov 16 09:40:29 PM UTC 2026
- S-F12 NEW: controlled same-material test. DeadMaterial true zeroes 8/8 KNNk positions across eight placements
  (cp 216..326 -> cp 0) and 0/3 KNNNk (three knights can force mate, correctly left alone). Pure material key for
  exactly two knights; no misfire found.
- HONESTY: two of my own claims from deadmaterial_scope.py were WRONG and are WITHDRAWN in
  check_15f3/raw/scope_summary.txt and RESULT.md: my FENs were mislabelled ("two knights" rows that had a black
  knight; "three knights" row that was KNNk). raw/material_check.txt shows the real signatures. The assertions
  also refused an illegal FEN and an unparsable one.
- next command: python3 check_15f3/knn_same_material.py against the ASan+UBSan build, to confirm the same 8/8 and
  0/3 there and that no sanitizer line appears in these eval paths.
