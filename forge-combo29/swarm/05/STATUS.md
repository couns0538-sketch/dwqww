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

## Mon Nov 16 09:41:18 PM UTC 2026
- S-C6 CONFIRMS seat 15's 15-F4: dead-draw roots emit an EMPTY pv (the line reads "info depth 1 seldepth 1
  score cp 0 nodes 0 ... time 0 pv" with nothing after pv) and 0 nodes, one empty line PER DEPTH; control =
  KNN v K on the same harness has a 10-move pv and real nodes.
- SELF-AUDIT: this applies to my own job2 (600/600 empty pv lines in K v K / KN v K / KB v K / threefold). My
  cp 0 conclusions stand (regex matches the empty line, reads its score) and I made no pv-content claim there.
  My job1 count was unaffected: 0 empty pv lines out of 6,636.
- next command: python3 job2/cliff_vs_depth.py on a second material (K+B+B vs K) to test whether S-F11's
  counter+depth rule is material-independent.

## CHECKPOINT (owner: findings by 22:30)
- S-C7 CONFIRMS seat 25's S-F4 on their board (97->-111, 98->-118, 99->cp 0 in 341 nodes, 100/101->0 nodes) and
  I CORRECTED MY OWN S-F11/S-F13: the "counter+depth" law is true only for the bare endgames I tested; their
  middlegame is flat at 99. S-F14 states the corrected position-dependent picture. My pawn hypothesis was tested
  (strip all 12 pawns -> flat at 100) and WITHDRAWN.
- Gap closed: EvalRule50Damp true/false, UseNNUE false, Hash 1/1024, Threads 4 and depths 1..20 all still cp 0 at
  clock 99, while the same board at clock 0 searches normally (cp -164, 19,621 nodes).
- next command: python3 check_25f4/options_test.py against the ASan+UBSan build for the same table.

## $(date -u)
- S-C7 also re-run on ASan+UBSan: identical clock-99 table (cp 0 everywhere, clock-0 control cp -164 / 19,621
  nodes), no sanitizer output. Not called "0 sanitizer lines proven" because this script carries neither proof.
- next command: start job3 of area 5 again with the next seed (cycle step c for job 3): checkmated/stalemated roots
  generated afresh with random.Random(511+10) and the same three go commands.

## $(date -u)
- job3b (job 3 repeated, seed 521, 0 root overlap) DONE: 60/60 bestmove 0000, mate 0 / cp 0, 0 nodes, 0 crashes,
  0 hangs, 0 sanitizer output; 7/7 predictions HELD. S-F7 (depth-64 iteration at terminal roots) REPRODUCES on
  fresh positions, now recorded in that finding's evidence.
- next command: python3 job3b/run_job3b.py with the planted-fault exe to attach the sanitizer proof to job3b itself.

## $(date -u)
- job3b sanitizer proof attached to its OWN files: out_planted_b/meta.txt shows nm 35 __asan_ / 15 __ubsan_ and the
  same runner counting 9 sanitizer lines + 3 crashes across the 3 planted probes, against 0 lines / 0 crashes over
  the 60 real runs. So "0 sanitizer output" now stands on job3b's own evidence.
- next command: python3 check_15f4/check_15f4.py /tmp/build-asan/forge, to see whether the empty-pv shape is
  identical on the sanitizer build (and whether ASan changes anything about it).

## $(date -u)
- 15-F4 check repeated on ASan+UBSan: identical table (6/6 empty pv for the three dead-draw sets, 6/6 with moves
  for the KNN control), no sanitizer output.
- next command: read the board again for any NEW area-5 finding with no C line, and take it if one is left.

## $(date -u)
- S-C8 CONFIRMS seat 15's 15-F5 with my own harness on 20 fresh seed-521 roots: 60/60 runs give mate 0 / cp 0 with
  0 nodes and bestmove 0000, and go nodes 100 / go movetime 50 emit 64 info lines vs 5 for go depth 5.
- next command: python3 job2/cliff_vs_depth.py on a fourth bare endgame (K+N+N vs K with the knights far apart) to
  see whether S-F14's counter+depth pattern is a property of bare endgames generally.

## $(date -u)
- S-F13 extended: a FOURTH bare endgame (K+N+N vs K) gives counter+depth = 100 exactly at d6/d8/d10/d12
  (94,92,90,88), the counter just below scoring +33..+318. The bare-endgame pattern is now 4 of 4.
- HONEST NOTE: my first run of that test used "8/8/8/8/8/8/8/K1N4k" which is K+N, a dead draw — every clock scored
  cp 0 so the scan returned 60 and measured nothing. Discarded and re-run with material asserted; both runs are in
  job2/out/cliff_vs_depth_KNN.txt with the assertion recorded.
- next command: read the board for a NEW finding outside area 5 that nobody has checked, and check it.

## $(date -u)
- S-F15 NEW: ONE black pawn flips the boundary from depth-tracking (bare K+R: 95/93/91/89) to flat (98 at every
  depth). Stated with its own limit: stripping all 12 pawns from seat 25's middlegame still left it flat at 100, so
  "pawns" is not the whole story and I claim no mechanism. The castling variant was skipped: python-chess calls
  "1K6/8/8/3R4/8/8/8/k7 w KQkq" invalid, and I did not force it.
- next command: python3 job2/what_makes_flat.py /tmp/build-asan/forge for the sanitizer-build repeat.

## $(date -u)
- S-F15 repeated on ASan+UBSan: identical (95/93/91/89 tracking vs flat 98), no sanitizer output.
- next command: python3 - <<'PY' to total up every job folder's file counts for the final STATUS, then final push.

## $(date -u) — FINAL PUSH (owner deadline 22:30; all work pushed well before it)
SEAT 05, AREA 5. 21 findings + 8 checks of other seats, all on GitHub with raw files.
- Findings (F): S-F1 S-F2 S-F3 S-F4 S-F5 S-F6 S-F7 S-F8 S-F9 S-F10 S-F11 S-F12 S-F13 S-F14 S-F15
- Checks (C): S-C1 (seat 06 S-F9) S-C2 (seat 19 19-F12) S-C3 (honesty re-verify) S-C4 (my own parser fix)
             S-C5 (seat 15 F3) S-C6 (seat 15 F4) S-C7 (seat 25 S-F4 + correction of my S-F11) S-C8 (seat 15 F5)
- Jobs: job1 (PV legality + mate distances on O+G), job2 (draw scores + the fifty-move cliff), job3 (terminal
  roots under ASan+UBSan), job1b (fresh-set repeat, seed 511), job3b (fresh-root repeat, seed 521).
- Every job has a REPORT_jobN.md built from committed raw files; every check has a RESULT.md.
- Sanitizer claims carry both proofs the brief requires (nm counts + a planted fault counted by the same runner).
- FINAL_SUMMARY.md lists everything including every mistake I made and corrected.
- next command (if the session resumes): python3 job2/what_makes_flat.py with a SECOND pawn placement, to test
  whether S-F15's flat-98 depends on where the pawn is or only on there being one.

## $(date -u)
- S-C9 CONFIRMS seat 10's warm/cold rule exactly: one process x3 = 56,720/4,951/4,516; three processes = 56,720 each.
- MY OWN AUDIT (the part the warning asked for): no Clear Hash anywhere; every node-count claim of mine comes from
  one fresh process per position with ucinewgame, so all are COLD. The only warm tables are mate_repeat.py's, and
  their output has always separated and labelled `cold N:` / `warm N:`. Nothing needed re-labelling, nothing was
  silently re-run.
- next command: none needed before the deadline; everything pushed.

## $(date -u) — fail-closed audit complete
- Applied the mate_check.py lesson to EVERY verdict-producing script with a committed no-score stub engine
  (audit_failclosed/stub_no_score.sh + failclosed_probe.py + probe_selftests.py).
- RESULT: 9 of 9 engine-driving scripts now fail closed, but 5 were BROKEN and are repaired. Four manufactured a
  REFUTES (audit_10_clearhash, check_15f4, dtm_selftest, mate_check); one manufactured a PASS (dtm2_selftest).
  The invented PASS was the worst of the five.
- All five re-run on real input afterwards: every published number reproduced exactly (honesty 4/4, check_15f4
  CONFIRMS, dtm2_selftest PASS, mate_check ok=4 mismatch=6, audit_10 CONFIRMS).
- S-F9 state line added to FINAL_SUMMARY.md: the 200-position run was COLD (fresh process per position; 0/200
  zero-node; first-100 median 43,664 vs last-100 49,605) — seat 10's rule landed after and does not affect it.
- next command: none; everything pushed.

## $(date -u) — exit codes + common cause (owner's last two items)
- ALL repaired scripts now return DISTINCT exit codes, verified in both directions by
  audit_failclosed/exit_codes.sh: 0 = measured and agreed, 1 = measured and disagreed, 3 = NOTHING MEASURED.
  honesty_safe 3/0, mate_check 3/1, crosscheck_mates 3/0, dtm2_selftest 3/0, dtm_selftest 3/1.
- Found TWO MORE broken scripts while doing this, both of which I had wrongly described as "already safe":
  mate_check.py had NO exit call (returned 0 on no-parse) and crosscheck_mates.py printed AGREE from two absences
  (a "(none)" sentinel on one side, None on the other). Both fixed. That is the second time tonight a claim of mine
  about my own script was wrong until tested.
- RESULT.md now names the common cause: every one of them judged in the ABSENCE of a value = the vacuity trap,
  with the four swarm instances named (seat 19 clock_plan, seat 10 10-F2 pos_line, seat 16 S-F7 three forms,
  seat 05 this audit).
- next command: none. Stopping.

## $(date -u) — final: house standard written
- CHECKER_RULE.md added (10 non-blank lines): a verdict requires the value found; missing value exits 3 with no
  verdict and never 0; agree and disagree each require both sides measured; every checker carries a stub engine that
  prints nothing, on which it must exit 3 and print no verdict.
- Stated in the file and in FINAL_SUMMARY.md that this is a recommendation for the next swarm, NOT a finding about
  the engine.
- next command: none. Stopping.

## 2026-11-16T22:18:50Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:00Z

## Mon Nov 16 10:19:48 PM UTC 2026 — PC r15 build ready
- Read FABLE_TO_swarm files 2, 3, 4, 5 (file 1 read earlier). File 3 says the drawn-root defect I found (S-F3/F4/F5/
  F11/F13/F14/F15) is REPAIRED on the PC; file 5 ships that source.
- PC r15 patch: sha256 prefix d6bd72c531f785f4 VERIFIED; applied with patch -p1 in a separate copy; built with
  -DFORGE_MATE_ALPHA_GUARD=1.
- PC build honesty: 8 of 8 numbers exact — none: 312866/862329/3024920/4865609; S14: 242796/656517;
  PC20: 278024/587276. All six PC20 options present in the uci list.
- next command: re-run my own finds on the PC build under PC20, starting with the fifty-move findings.

## $(date -u) — PC build re-run of my finds (all Threads 1)
- File 3's root-draw repair CONFIRMED in all three parts on the PC build: K+Q vs K with a mate scores mate 1 /
  280 nodes at halfmoves 0, 99, 100, 101, 150; threefold is searched; K vs K alone is still instant (0 nodes).
- BUT it is a DIFFERENT mechanism from my S-F3: the fifty-move score floor still lands the same board at cp 0 from
  halfmove 91 (K+R vs K: cp 289 at 90 -> cp 0 at 91, 13.99M nodes), unchanged by PC20. S-F3 STANDS on the PC build.
- S-F1: the mate-PV truncation REAPPEARS under S14 on the PC build (mate -9, 14 of 18 plies) and is GONE under PC20
  (mate -4, 8 of 8). S-F9's R/120 no longer produces a mate score on the PC build (cp -2713) — not reproducible.
- Threads audit: one recorded row (check_25f4 options_test, Threads 4) is now marked PROVISIONAL; every claim I
  made rests on Threads 1 rows. Annotated in check_25f4/RESULT.md and FINDINGS S-C7.
- next command: python3 pcbuild/rerun_finds.py /tmp/build-pc/forge S14 > out/rerun_s14.txt, for the side-by-side.

## $(date -u)
- Added S-F16 (S-F3 stands on the PC build; root-draw repair is a different mechanism), S-F17 (S-F1 truncation is
  SETTING-dependent: S14 on the PC build is inconsistent at 14/18 plies, PC20 consistent 8/8), S-F18 (S-F9's R/120
  not reproducible on the PC build — cp -2713, no mate score).
- Planted-case control for the "0 nodes" claim on the PC build: K v K / KN v K / KB v K = cp 0 / 0 nodes, while two
  plants on the same harness give startpos cp 21 / 9,575 and KNN v K cp 231 / 65,604. Zero claim now shown.
- Boundary-vs-depth identical under S14 and PC20 on the PC build (95/92or93/91/90 for d6/8/10/12).
- next command: python3 pcbuild/rerun_finds.py on the BASE build under S14, to have a same-regime base column.

## $(date -u)
- THREE-WAY table done (base S14 / PC S14 / PC PC20, Threads 1, same harness):
  * S-F3: cliff at halfmove 91 on ALL THREE columns; base column reproduces my published cp 314 -> cp 0 exactly,
    which validates the harness across builds. PC build does not fix it.
  * S-F1: base mate -12 short by 6; PC S14 mate -9 short by 4; PC PC20 mate -4 consistent. Setting effect.
  * S-F9 R/120: IDENTICAL on base and PC under S14 (mate -13, 14 of 26 plies) — the PC patch does not fix it;
    under PC20 the engine stops reporting a mate at all (cp -2713), which is a different measurement.
- next command: python3 pcbuild/rerun_finds.py /tmp/build-pc/forge PC20 with MultiPV off check, then continue.

## $(date -u)
- S-F19 NEW: the S-F1 truncation is fixed by SPECIFIC OPTIONS, not by the build. On the PC build, G/192 depth 12,
  Threads 1: S14 alone short by 4 (3/3 runs); +TtPruneV2 only -> 14/14 consistent (3/3); +MateAlphaGuard only ->
  8/8 consistent (3/3); CuckooRep alone makes it WORSE (short by 9). Cumulative chain becomes consistent at
  +CorrHistV2. No mechanism claimed — I did not read what those options do to the PV rebuild.
- next command: re-run the S-F11/F13/F15 boundary-vs-depth on a SECOND material on the PC build under PC20, to see
  whether S-F14/S-F15's position-dependence survives there.

## $(date -u)
- S-F20 NEW: the boundary position-dependence of S-F14/S-F15 SURVIVES on the PC build under PC20, Threads 1:
  bare K+R 95/93/91/90 (tracks, sum ~101); bare K+B+B 95/92/91/89 (tracks); K+R + ONE pawn FLAT at 98 — exactly the
  base tree's 98, so S-F15's "one pawn flips tracking to flat" REPRODUCES. One board changed: the pawnless
  middlegame that was flat at 100 on the base tree now keeps a real score at every counter on the PC build
  (cp 87 at 0-90, cp 67 at 99/100, cp 76 at 101-200), consistent with the root-draw repair reaching it.
- next command: python3 pcbuild/boundary_pc.py /tmp/build-pc/forge S14 for the S14 column on the PC build.

## $(date -u)
- seat 01's S-C2 CONFIRMS my S-F3 numbers and REFUTES the "9 plies early" framing, deriving boundary = 101 - D at
  95/92/91/89 for depth 6/8/10/12 — the same numbers as my own S-F11. My S-F14 had already withdrawn that framing,
  so their refutation targets a claim I corrected myself; recorded as S-C11 with that noted.
- Also noted in S-C11: their 101-D rule holds for BARE endgames only (my S-F20 shows flat 98 and flat 99 boards).
- next command: check whether any seat has confirmed S-F16/S-F19 (the new PC-build findings) and, if not, leave them
  marked open in the FINAL block.
