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

## $(date -u)
- S-C12: BOUNDS seat 01's 101-D formula. It holds on both bare endgames I measured (K+R 95/93/91/90, K+B+B 95/92/91/89,
  all within 1 of 101-D) and FAILS on every pawned board (K+R + one pawn flat 98 vs predicted 95/93/91/89; middlegame
  97/99/99/99). So 101-D is a bare-endgame rule, not a general fifty-move law — which is exactly the gap my S-F15/S-F20
  fill. PC r15 + PC20, Threads 1.
- next command: write the FINAL block with every find, its state and its build/settings, then verify push.

## $(date -u)
- S-F19 CORRECTED by my own follow-up. It was measured on G/192 only. On 7 mate boards (depth 12, Threads 1):
  the truncation appears on just 2 of 7 under S14 on BOTH builds (G/192 short 6 base / 4 PC; R/40 short 12 on both).
  MateAlphaGuard alone is consistent on 6 of 7 (fails R/40 by 7). TtPruneV2 alone fixes G/192 but CREATES truncation on
  G/196 (short 8) and G/217 (short 10) and replaces mate scores with cp on G/184 and R/40.
- S-F21 NEW: the truncation is position-specific and NO single option is a general cure; my "attributable to specific
  search options" sentence was an over-generalisation from one board and is withdrawn.
- next command: leave S-F16/F19(now corrected)/F20/F21 marked OPEN (no confirming seat yet) in the FINAL block.

## $(date -u)
- S-F22 NEW: the truncation rate is 2 of 28 mate positions = 7.1% on the base build (O+G 1/10, R 1/18), depth 12,
  S14, Threads 1, from my committed rows.jsonl. The two boards are exactly G/192 and R/120 — which is why my S-F19
  "TtPruneV2 fixes it" was luck, and why a small mate-PV assertion usually passes.
- next command: re-run those 2 exact boards + a fresh sample on the PC build to measure the PC rate, then write FINAL.

## $(date -u)
- S-F23 NEW: same 28 mate positions (from committed rows.jsonl, not re-selected), depth 12, Threads 1:
  * base build + S14   : 2/28 truncated = 7.1% (G/192 short 6, R/120 short 12)
  * PC r15 + S14       : 2/28 truncated = 7.1% — the SAME two boards
  * PC r15 + PC20      : 0 of 27 mate scores truncated (R/120 stops being a mate score, cp -2713)
  So PC20 eliminates the truncation as a RATE while no single option does (S-F21). Stated carefully: 0 of the 27 that
  remain mate scores, not "the 28th was fixed".
- next command: write the FINAL block with every find, its state and its build/settings.

## $(date -u)
- S-F24: an independent 120-position pool (R_seed511 + G, screened at depth 8 then re-searched at depth 12) yields only
  8 mate scores — all consistent under PC20, 0 truncated. Recorded with the caveat that 8 positions cannot distinguish
  0% from 5%; combined with S-F23 I have 35 mate positions total, which is not enough for a precise rate.
- next command: python3 pcbuild/mate_sample_pc.py /tmp/build-pc/forge S14 120 for the same pool under S14.

## $(date -u)
- S-F16 is now CONFIRMED by seat 08 (08-C6), independently, its own harness, PC r15 + PC20, Threads 1, Hash 16: won
  K+R vs K scores cp 490 at H=0/50/75 then exactly cp 0 from H=91 — my flip point — and it adds that H=91 costs
  7,251,835 nodes vs 14,470 at H=0 (500x blow-up), a figure that matches my own PC20 run exactly. Recorded as S-C13.
- next command: check the S14 mate-sample run, then continue with the remaining open findings.

## $(date -u)
- S-F25 NEW (negative result that CONSTRAINS S-F23): the independent 8-mate sample is 0-truncated under S14 as well as
  under PC20, so it does not reproduce the truncation at all. S-F23 showed S14 truncates 2 of 28 on the ORIGINAL set, so
  the 7.1% must not be quoted as a general rate: 2 truncated out of 36 mate positions examined in total, and the 8 new
  ones contain none. S-F23's "PC20 gives 0 of 27" therefore means "no truncation observed on that set under PC20", not
  "PC20 reduces a measurable rate to zero".
- next command: amend S-F23's wording so the rate claim is bounded, then continue.

## $(date -u)
- S-F26 NEW: file 3's repetition repair CONFIRMED both ways with my own move lists, Threads 1, depth 10.
  BASE (S14): 2nd occurrence searched (cp 37 / 12,997 nodes), 3rd occurrence cp 0 / 0 nodes / empty pv.
  PC r15 (PC20): 2nd searched (cp 27 / 11,116), 3rd SEARCHED (cp 20 / 15,066). Control: same board as plain FEN
  searches normally in both, so the base zero is the root-draw shortcut, not an unsearchable board.
- S-F5's state note upgraded from speculation to measurement.
- next command: continue the cycle; next is a 25-minute STATUS cadence check.

## $(date -u) — CYCLE CHECKPOINT
- Seat 05 (area 5), branch for-fable-and-opus/swarm-05. PC r15 build (/tmp/build-pc/forge) verified 8/8 numbers
  under none/S14/PC20. All results Threads 1.
- Findings 26 (S-F1..S-F26) + 13 checks (S-C1..S-C13). Confirmed by others: S-F3/S-F16 (seat 08 08-C6),
  S-F3 numbers (seat 01 S-C2, seat 11 S-C7).
- Key PC-build results: S-F16 fifty-move floor STANDS on PC (confirmed); S-F17/S-F19/S-F21 the mate-PV truncation is
  position-specific with no single option fixing it; S-F23/S-F25 no truncation OBSERVED under PC20 but the rate is not
  established; S-F26 the repetition repair CONFIRMED; S-F20 boundary position-dependence survives except one board.
- next command: re-run S-F22's 28-position mate set on the base build once more as a stability check (deterministic
  repeat), then continue.

## $(date -u)
- S-F27 NEW and it is the mechanism lead S-F21 lacked: truncation happens ONLY at |N| >= 10. Base build S14 depth 12
  Threads 1: |N| 1..7 (25 positions) all consistent; the only truncated are |N| = 12 and 13 (need 24 and 26 plies, got
  18 and 14). Of 3 positions with |N| >= 10, 2 are truncated. Not a mechanism claim (I did not read the PV code), but
  it explains why an option looked like a cure on one board without fixing others.
- Determinism re-check: base build re-run reproduces 2/28, same two boards, same scores.
- next command: test S-F27's prediction — a board with |N| >= 10 should truncate and the SAME board at a shallower
  reported mate should not.

## $(date -u)
- S-F28 NEW: S-F27's prediction CONFIRMED across depth. G/192: d12 mate -12 18/24 SHORT 6; d14 mate -9 15/18 SHORT 3;
  d16 mate -6 12/12 ok; d18/d20 -5 ok; d24/d28 mate -4 8/8 ok. R/120: d12 mate -13 14/26 SHORT 12; d14 mate -10
  20/20 ok and complete above. So the PV is short exactly while the reported distance needs more plies than the depth
  that reported it. Neither board reports a mate at all at depth 8 or 10.
- This is now the best-supported account of S-F1/S-F9/S-F21: a depth-limited PV-rebuild effect at long mate distances.
- next command: continue the cycle; next check the PC build shows the same depth behaviour (S-F17 showed PC20 differs).

## $(date -u)
- S-F30 NEW — a limitation I had to state: S-F27's |N| >= 10 rule rests on only 3 qualifying positions (2 truncated,
  1 not). My independent 8-mate sample has |N| only 1,1,2,2,3,4,4,4 — ALL below the threshold — so it cannot test the
  rule and its 0-truncated result is not evidence against S-F27. A repeat must SELECT for long mates, not sample at
  random.
- next command: build a long-mate set (|N| >= 8) deliberately, then measure the truncation rate on it.

## $(date -u) — FILE 6 READ AND APPLIED
- File 6 changes two verdicts. I applied its test to MY OWN fifty-move findings:
  * S-F3 board at counter 91: counter-0 depth-20 gives mate 8 -> needs 15 plies; 100-91 = 9 half-moves remain;
    15 <= 9 is FALSE. **S-F3 is NOT a defect** (match program ends at the 100th half-move). S-F16 (same claim on the
    PC build) WITHDRAWN with it.
  * S-F11/S-F13/S-F14/S-F15/S-F20 are DESCRIPTIONS of where the draw verdict lands, not defects: the K+R+pawn board at
    98 and the K+B+B board at 90 have NO forced mate at all at counter 0 (cp 522 / cp 507 at depth 20).
  * S-F4 same family, WITHDRAWN as a defect.
- Recorded as S-W1 and S-W2 so the withdrawal is explicit and dated, and every affected finding line is marked.
- My mate-PV findings are UNAFFECTED: they are about PV length vs score, nothing to do with draws.
- next command: take file 6's suggested area — `go softnodes N` on PC r15 + PC20, Threads 1.

## $(date -u)
- FILE 6's suggested area done: `go softnodes N` on PC r15 + PC20, Threads 1, Hash 16, 3 fresh processes/cell.
  S-F31: deterministic on all 16 cells and stops at a finished depth, but OVERSHOOTS N by 1.02x..2.06x.
  Largest overshoot (2.06x) is at N=2000 — the value the PC's own self-play uses.
- S-W3: my first run of that probe reported FALSE nondeterminism on 5 cells because it compared nps/time (wall
  clock) in the raw line. Fixed with strip_timing(); withdrawn and recorded rather than deleted.
- next command: test how the overshoot behaves across a finer N ladder at N=2000 (the PC's self-play value).

## $(date -u)
- S-F32: the softnodes overshoot is QUANTISED by the depth ladder and fully deterministic on a fine ladder.
  21 cells (3 positions x N in 500..10000), 3 fresh processes each: identical depth AND nodes in all 3 runs on all 21.
  Overshoot 1.00x..2.18x; consecutive N can report the SAME nodes (1,740 at N=1000 and 1500; 4,121 at N=2000 and 3000)
  because the engine finishes the depth in progress. At the PC's own N=2000: 2.06x startpos, 1.24x G0, 1.15x middlegame.
- next command: the same ladder on the BASE build under S14, to see whether the quantisation is a PC-build property.

## $(date -u)
- S-F33: the softnodes quantisation is an ENGINE property, not PC-specific. Base build + S14 ladder: 1.00x..2.37x, same
  plateaus, deterministic on every cell. At N=2000 base vs PC: startpos 1.75x vs 2.06x, G0 1.00x vs 1.24x, middlegame
  1.03x vs 1.15x. At N=10000 the PC build is cheaper on 2 of 3 boards and dearer on 1.
- next command: continue the cycle on the PC's real path — `go nodes` 20000/50000/250000 determinism, per file 6.

## $(date -u) — POSITION AFTER FILE 6
- WITHDRAWN as defects under file 6: S-F3, S-F4, S-F16 (fifty-move cp 0 where no mate fits the counter budget) and
  S-F11/F13/F14/F15/S-F20 demoted to DESCRIPTIONS of where the draw verdict lands. Recorded as S-W1/S-W2 with the
  inequality and both numbers, as file 6 requires.
- STILL STANDING (unaffected by file 6, they are about PV length vs score, not draws): S-F1/S-F9/S-F17/S-F19/S-F21/
  S-F27/S-F28/S-F29/S-F30 — the mate-PV truncation, now with a supported cause (a depth-limited effect at |N| >= 10,
  reproduced across a depth sweep on both builds).
- NEW from file 6's suggested area: S-F31/S-F32/S-F33 — `go softnodes N` is deterministic on all 21+16 cells,
  stops at a finished depth, and overshoots N by 1.00x..2.37x, QUANTISED by the depth ladder, on BOTH builds.
- S-W3: withdrew my own false nondeterminism claim (probe compared wall-clock nps/time).
- next command: `go nodes` 20000/50000/250000 determinism on the PC build under PC20, Threads 1.

## $(date -u)
- S-F34 NEW and operationally important: `go nodes N` UNDER-shoots on the PC build — it abandons the depth in progress
  and reports as little as 47% of N. PC r15 + PC20, Threads 1, Hash 16, 3 fresh runs per cell, deterministic on all 9
  cells: startpos 0.680/0.937/0.665, G0 0.467/0.588/0.812, mid 0.686/0.780/0.971 of N at N=20k/50k/250k. Worst cell
  G0 at N=20,000 stops at depth 11 with 9,330 nodes and never reports depth 12. Opposite direction from softnodes,
  which overshoots (S-F31/S-F32). These are exactly the N values the owner's matches use.
- next command: check whether the base build shows the same `go nodes` undershoot.

## $(date -u)
- S-F35: the `go nodes` undershoot is ENGINE-WIDE, not PC-specific. Base + S14 (deterministic on all 9 cells):
  startpos 0.719/0.743/0.963, G0 0.983/0.826/0.658, mid 0.488/0.557/0.637 of N. Worst base cell = mid at N=20000 with
  9,753 of 20,000 (48.8%) at depth 10, the same shape as the PC build's worst 46.7%. PC20 does not fix it.
- So on BOTH builds `go nodes N` is a soft ceiling: 47-98% of N used, never overshooting, while `go softnodes`
  overshoots by 1.0-2.37x. The two limits behave in OPPOSITE directions.
- next command: continue the cycle on the PC's clock path (6s + 0.06) per file 6.

## $(date -u)
- S-F36 resolves S-F34/S-F35 AND S-F31/S-F32 into ONE rule, and it is not a defect. Full ladders on G0 (PC20, Threads 1):
  `go nodes 20000` completes d1..d11 and stops at 9,330; `go softnodes 20000` completes d1..d12 and stops at 21,812.
  At N=50000: `go nodes` stops after d13 (29,382), `go softnodes` after d14 (56,616). The ladders are IDENTICAL
  depth-for-depth — `go nodes` stops BEFORE the depth that would exceed N, `go softnodes` AFTER the first that passes it.
- S-W4: withdrew my "undershoot" framing for S-F34/S-F35. The search uses the same depths either way; the reported
  node count is simply the last COMPLETED depth. Worth knowing, but not a fault.
- next command: continue on the PC clock path (6s + 0.06).

## $(date -u) — IMPORTANT: S-F37 clock path
- On startpos, PC r15 + PC20, Threads 1, Hash 16: `go wtime 6000 btime 6000 winc 60 binc 60` uses **0.36 s** and
  reaches depth 19 — IDENTICAL to `go depth 19` (same 650,246 nodes, same wall time). But `go movetime 6000` on the
  same board uses **5.99 s** and reaches depth 27. So the 6-second budget is usable and is NOT used via wtime/winc.
  A 60-second clock gives only depth 23 / 1.90 s.
- This is the owner's actual strength-match path (file 6: 6 s + 0.06), so matches are effectively played at ~depth 19.
- NOT claimed: which constant does it. I did not read the time manager. No defect claim yet — needs seat confirmation.
- next command: check whether the BASE build shows the same clock-vs-movetime gap.

## $(date -u)
- S-F38: the wtime-vs-movetime gap reproduces on BOTH builds, 5 runs each, OwnBook false:
  PC PC20 startpos 0.35s/d19/650,246 vs movetime 5.99s/d27/7,061,631; PC middlegame 0.72s/d19 vs 5.99s/d27.
  BASE S14 startpos 0.23s/d19/466,541 vs 5.99s/d27/11,003,901; base middlegame 0.46s/d20 vs 5.99s/d29.
  Every cell identical across its 5 runs. Same 6s budget buys ~10x the nodes as movetime, and is ~90% unspent as wtime.
- S-W5: withdrew my first clock table — the base rows were `?`/0.00s because the base build defaults OwnBook true and
  answered with `info string book move c2c4` and no pv. Fixed with OwnBook false (file 3 required it; I had not
  applied it here) and a no-bestmove cell now reports REFUSED, never a number.
- next command: continue; S-F37/S-F38 are the strongest PC-path findings and need a confirming seat.

## $(date -u)
- S-C14 OWNBOOK AUDIT: the book does NOT fire on my position sets — five O-set openings give IDENTICAL node counts
  with book on vs off (41,311/24,872/28,574/27,838/18,020) and zero book lines; it DOES fire on startpos. Grep over
  every committed .txt of mine finds a `book move` line only in the clock file that states its own fix. Plus my job1
  sums reproduce the brief's 9,500,069 / 18,466,239 exactly, which a book move (no pv, 0 nodes) could not do.
  => my position-set results are clean; only the withdrawn clock table was affected.
- All harnesses going forward send OwnBook false (file 3's rule), which I had not applied before.
- next command: continue the cycle.

## $(date -u) — S-F39, the mechanism behind S-F37/S-F38
- It is a TIME FORMULA, not a depth cap: varying only the clock on startpos (PC20, Threads 1, Hash 16, OwnBook
  false) — 1000->95ms/d15, 2000->141/d17, 6000->234/d19, 12000->397/d20, 30000->911/d21, 60000->1883/d24,
  120000->2583/d25. Depth grows monotonically => no cap. Used/clock ratio 9.5%, 7.1%, 3.9%, 3.3%, 3.0%, 3.1%, 2.2%.
- `go movetime` at the same budgets spends 99% (1000->0.99s/d21, 6000->5.99s/d27, 30000->29.99s/d31).
- => a 6-second wtime clock behaves like roughly a 240 ms search. On the owner's strength-match path (6s + 0.06)
  this is the single most consequential number I have produced. No cause claimed beyond "the allocation formula".
- next command: write this up as a standalone repro file for another seat to confirm.

## $(date -u)
- S-C15: seat 01's S-F51 independently measured the softnodes staircase AND supplies the mechanism I did not claim:
  the soft budget is checked only after an iteration completes (search.cpp:2493-2501, 2932) and the hard cap is
  nodes*4. Its plateaus and its max ratio 2.06 agree with my S-F32 exactly (my N=1000/1500 both 1,740; 2000/3000 both
  4,121; startpos N=2000 max 2.06x). So S-F32 is independently observed and now explained.
- My S-F37/S-F38/S-F39 (wtime spends 2-4% of budget) have NO confirming seat yet — repro published at
  clockpath/REPRO_for_seats.md, tested as published.
- next command: continue; try a second material/position for S-F39 to check the ratio is not startpos-specific.

## $(date -u)
- S-F40: the wtime shortfall is NOT startpos-specific. Five diverse positions, 6-second clock, PC20 Threads 1 Hash 16,
  % used: startpos 5.9% (d19 vs movetime d27), G0 3.0% (d18 vs d28), middlegame 11.9% (d19 vs d27), deep 6.3%
  (d18 vs d24), K+Q endgame 4.7% (d15 vs d64). Range 3.0-11.9%, never near budget.
  The endgame row is worst for playing strength: depth 15 with a clock vs depth 64 with movetime.
- next command: continue; S-F37/38/39/40 all need a confirming seat — the repro is published.

## $(date -u) — S-F41/S-F42: the strongest result of this block
- S-F41: S-F37's claim is EXACT — the `go wtime 6000` move is bit-identical to `go depth <depth it reached>` in
  12 of 12 positions. On this path the clock is effectively an implicit DEPTH limit, not a time limit.
- S-F42: it costs MOVES. Against `go movetime 6000` the moves differ on 2 of 12 positions (G idx 0: g7g6/d18 vs
  e5e4/d28; G idx 7: g5h5/d18 vs g5h6/d21). The shallower side is always the wtime side, 10-18 plies behind.
  On the owner's match path that is roughly one position in six decided at ~depth 18 instead of ~depth 27.
- Both need a confirming seat; repro at clockpath/REPRO_for_seats.md.
- next command: continue the cycle.

## $(date -u) — S-F42 CORRECTED by my own check
- S-F42 said the wtime shortfall "costs real moves" (2 of 12 differ from a full 6s search). Checking the SCORES at both
  depths shows both differing positions are LOSING for the side to move and the deeper search is MORE pessimistic
  (cp -294 -> -341; cp -1915 -> -2121). So the shallower wtime move is not demonstrably worse; my "strength lost"
  implication is withdrawn. Move differences remain a fact, the strength interpretation does not follow.
- S-F43 records the scores that forced the correction.
- S-F41 (wtime result is bit-identical to `go depth <its depth>` in 12/12) is UNAFFECTED and still stands.
- next command: continue the cycle.

## $(date -u) — BLOCK SUMMARY (PC-build work)
SEAT 05, area 5. Branch for-fable-and-opus/swarm-05. All results Threads 1, Hash 16, OwnBook false.
PC r15 build verified 8/8 (none/S14/PC20) before any of it.

STANDING (needs a confirming seat — repro published at clockpath/REPRO_for_seats.md):
- S-F37/S-F38: `go wtime 6000 btime 6000 winc 60 binc 60` uses 0.23-0.36 s, reaching depth 19; `go movetime 6000`
  uses 5.99 s and reaches depth 27. Reproduces on PC r15 and the base build, 5 runs each.
- S-F39: it is a time FORMULA not a depth cap — depth grows monotonically as the clock grows; used/clock falls
  9.5%->2.2% from a 1 s to a 120 s clock.
- S-F40: holds on 5 diverse positions (3.0%-11.9% used); worst for strength in a K+Q endgame (d15 vs d64).
- S-F41: the wtime MOVE is bit-identical to `go depth <depth reached>` in 12/12 positions.
- S-F42 (corrected): moves can differ from a full search (2/12) but the deeper search was PESSIMISTIC in both, so no
  strength loss is established.

CONFIRMED / CROSS-CHECKED:
- S-F16/S-F3 (fifty-move) — seat 08 08-C6 confirmed on PC20. NOTE: file 6 later withdrew S-F3/S-F16 as DEFECTS (S-W1).
- softnodes staircase — seat 01 S-F51 independently, and supplies the mechanism (check-after-iteration, hard cap 4N).
- S-F23 (mate-PV truncation 0/27 under PC20 vs 2/28 under S14) was cited by file 6 as the kind of answer needed.

WITHDRAWN by me under file 6 or by my own checks: S-F3, S-F4, S-F16 (not defects), S-F11/13/14/15/20 (descriptions),
S-F34/S-F35 framing (S-W4), my false softnodes nondeterminism (S-W3), my OwnBook-tainted first clock table (S-W5).
- next command: continue the cycle; try the wtime formula on a 2nd PC-build property (does Hash size change the ratio?).

## $(date -u)
- S-F44: the wtime budget is driven mainly by the INCREMENT, not the clock. Clock fixed 6s, sweep winc: 0->0.35s/d19
  (5.9%), 60->0.35s/d19 (5.8%), 200->0.51s/d20, 500->1.28s/d21 (21.3%), 1000/2000->1.29s/d21 (plateau),
  4000->1.93s/d23 (32.1%). Sweep clock with winc 60: 2s->4.4%, 6s->6.1%, 20s->6.4%, 60s->3.3%.
  Raising the increment 66x buys 4 plies; raising the clock 30x buys 6 plies at a shrinking fraction.
  At winc 60 (the owner's value) the engine sits in the flat low-allocation region.
- S-F45: depth is insensitive to Hash size (Hash 1/16/256 all depth 19) and wtime-only behaves identically to the full
  clock, so neither the TT nor btime explains it.
- next command: continue the cycle.

## $(date -u)
- REPORT_clock.md written: a consolidated, self-contained account of the owner's clock path
  (clockpath/REPORT_clock.md). Sections: the gap; formula not depth cap; increment dominates; what does NOT explain
  it (Hash/btime/position); the 12/12 bit-match proving the clock is an implicit depth limit; the move-difference
  question with my correction; confidence and limits. Every claimed file verified to exist.
- next command: continue the cycle; the clock findings need a confirming seat and the repro is published.

## $(date -u)
- S-C16 CROSS-CONFIRMATION: seat 16's S-F19 independently measured the same clock fraction (1s->2.77%, 3s->2.38%,
  6s->159ms/2.62%, 30s->4.33%) and called it a time-manager soft limit. My numbers: 6s->234ms/3.9%, 30s->911ms/3.0%.
  Same phenomenon, two harnesses, different absolute values. My S-F44 adds the cause: the budget tracks the
  INCREMENT (60->4000 ms buys 4 plies), not the clock.
  => S-F37/S-F39 now have an independent seat agreeing on the phenomenon (though not on identical numbers).
- next command: continue the cycle.

## $(date -u)
- S-C17: seat 17's S-F4 documents the SAME OwnBook trap that ruined my first clock table (S-W5) — startpos answered from the
  book in ~0 ms with no info depth line; its first clock run measured nothing that way (5 "results", 0 depth lines). Two
  seats, same trap, both caught only by making a missing parse loud. Third independent sighting of the vacuity pattern
  this swarm (19's clock_plan, 10-F2, 17's S-F4 + my S-W5) — strongest argument for CHECKER_RULE.md.
- next command: continue the cycle.

## $(date -u)
- FINDINGS.md hygiene: all 67 rows now state their build and settings (or say "process/audit row — no engine
  measurement"). Structure verified with an escaped-pipe-aware check: 0 malformed rows. (My first check used
  awk -F'|' which counts escaped pipes as separators and produced a FALSE alarm on the two |N| rows; they are correct.)
  45 S-F, 17 S-C, 5 S-W, no duplicate or missing ids.
- next command: continue the cycle.

## $(date -u)
- S-F46: full 151-ply self-play game at the owner's match clock (6s+0.06, PC20, Threads 1, Hash 16, OwnBook false):
  0 illegal moves, NO loss on time, final clocks 673/564 ms, ended by a draw rule. Per-move wall min 0.03 / median 0.10 /
  max 0.71 s — the engine never approached the 6-second clock in any of 151 moves. Depth min 16 / median 19 / max 24.
  => the low clock usage is not a single-search artefact, does not accumulate into a time problem, and the game is
  effectively played at depth 16-24.
- next command: a second game from a different start (a G-set middlegame) to check the pattern is not startpos-specific.

## $(date -u)
- S-F47: second full match-clock game from a real middlegame (r4rk1/pp1b1ppp/...): 120 plies, 0 illegal moves, no loss
  on time, final clocks 406/884 ms, per-move wall min 0.03 / median 0.11 / max 0.69 s, depths min 16 / median 22 / max 36.
- Across BOTH games (151 + 120 plies) the engine never spent more than 0.71 s of a 6-second clock. In endgames it reaches
  depth 32-36 because the trees are small. Conclusion: the clock is unused, NOT harmful — games complete with stable
  clocks, legal moves, no forfeits.
- next command: continue the cycle.

## $(date -u) — COMPREHENSIVE STATE (12-hour run, seat 05 area 5)
Branch for-fable-and-opus/swarm-05. 69 finding rows, 14 reports, 69 scripts, tree clean, local == remote.
Every finding row states its build and settings. All engine results Threads 1, Hash 16, OwnBook false.

THE OWNER'S CLOCK PATH (my most valuable work; consolidated in clockpath/REPORT_clock.md):
- S-F37/F38: `go wtime 6000 btime 6000 winc 60 binc 60` spends 0.23-0.36 s and reaches depth 19; `go movetime 6000`
  spends 5.99 s and reaches depth 27. Holds on PC r15 AND the base build, 5 runs each.
- S-F39/F40/F44/F45: it is a time FORMULA (depth grows with the clock; used/clock falls 9.5%->2.2%); holds on 5
  diverse positions (3.0-11.9%); is driven by the INCREMENT not the clock (winc 60->4000 buys 4 plies); is
  insensitive to Hash size and to btime.
- S-F41: the wtime move is bit-identical to `go depth <depth reached>` in 12/12 positions.
- S-F42 (CORRECTED): moves differ from a full search on 2/12, but the deeper search was more PESSIMISTIC in both, so
  no strength loss is established.
- S-F46/F47: two full match-clock games (151 + 120 plies): 0 illegal moves, no loss on time, never more than 0.71 s of
  the 6-second clock, depths 16-36. => the clock is UNUSED but NOT HARMFUL.
- CROSS-CONFIRMED: seat 16's S-F19 independently measured the same unspent-clock fraction.

CONFIRMED BY OTHERS: S-F3/S-F16 numbers (seat 08, seat 01, seat 11) — though file 6 later withdrew those as defects
(S-W1). softnodes staircase (seat 01 S-F51, which supplies the mechanism).

WITHDRAWN BY ME: S-F3/F4/F16 as defects (file 6); S-F11/13/14/15/20 demoted to descriptions; S-F34/F35 undershoot
framing (S-F36 one rule); my false softnodes nondeterminism (S-W3); my OwnBook-tainted first clock table (S-W5);
S-F42's strength implication.
- next command: continue the cycle; the clock findings are complete, so next is the mate-PV truncation on the PC path
  under softnodes 2000 (the self-play budget), which ties my two threads together.

## $(date -u)
- S-F48: the mate-PV truncation DOES occur at the PC's self-play budget (`go softnodes 2000`). Case G/59
  (`4Q3/8/r2K4/8/2B5/5R2/1k6/8 w`): depth 6 gives mate 4 with a 6-ply PV needing 7 (SHORT by 1), identical 3/3 runs;
  at depth 12 it gives mate 3 with 5 plies (correct); at softnodes 5000/20000 also mate 3. So the low-depth score is
  too pessimistic AND its PV cannot deliver it, and deepening fixes both. Rate at the self-play budget: 1 of 17 mate
  scores = 5.9% (most positions lose their mate score entirely at 2,000 nodes).
- This ties my two threads: S-F1/S-F27 (truncation) meet S-F31/S-F46 (the PC's real budget).
- next command: continue the cycle.
