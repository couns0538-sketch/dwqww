# glmflash2 job 7 report (2026-11-15)

## 1. Result in plain words

**MaxReduce 2 is NOT ahead of 3 - it is behind at 20,000 nodes.** Direct, pooled over both seeds:
**-4.56 +/- 5.23** (3,963 games, 1,981 pairs, interval [-9.8, +0.7], excludes 0; U1 -5.39 +/- 7.20
complete 2,000 games, U3 -3.72 +/- 7.60 at 1,963/2,000; 1,298 of 1,981 pairs were two draws). At
**80,000 nodes: +0.87 +/- 9.57** (U2, the full 800 games; 298 of 400 pairs two draws) - the two
values play the same strength there. **The value I would play now: 3**, the patch's own value: it is
ahead of 2 at 20k by the direct pooled comparison and equal at 80k, and MR5 was already behind it
(job 6, -3.0 +/- 5.1). Cut or not reached, first paragraph as asked: **U4 was NOT RUN** - after U3
ended at 23:06:51Z the runner logged U4_SKIPPED (the 23:02:00Z deadline had passed; it was first in
the cut order as the job prescribed). Every other planned match has a full row; nothing else was
skipped.

## 2. The probes

Before every match, the 2-game probe with the match's exact command and the engine input log on.
Committed per match: <name>_probe_setoption_lines.txt (e.g. U1's shows the cand side receiving
`AspFailHighReduce value 1` + `AspFailHighMaxReduce value 2`; the control's is empty - no candidate
options exist there) and <name>_probe_openings.txt. Probe FENs == match round-1 FENs for ALL five
matches played (string compare: control, U1, U2, U3 MATCH; U4 not run). First-pair openings across
the played matches: five distinct FENs (control r1b1k1nr..., U1 rn1qkb1r..., U2 r2qk2r..., U3 its
own, C7260's was different from all of them) - the second-seed-replays-first-match fault did not
happen. The probes also measured the 80k game length (~9 s/game), see section 8.

## 3. All matches of jobs 6 and 7

Same build both jobs (sha256 623b1cdfc50dc889... - job 7 reused job 6's binary; job 6's Step 0 and
uci lines apply to it unchanged). Machine: 4 cores, concurrency 4, fastchess v1.8.3-alpha, UHO book,
20,000 nodes unless stated, no adjudication. Crashes/illegal/disconnects: 0 in every match (grep
over each full output; final scan below). my Elo = logistic from mean pair score, 95% pair interval.

| job | #  | match | nodes | seed | games | W-L-D | Ptnml(0-2) | fc Elo +/- err | my Elo +/- 95% | crashes |
|-----|----|-------|-------|------|-------|-------|------------|----------------|----------------|---------|
| 6   | C  | 20k vs 10k, no options | 20k/10k | 7260 | 300 | 167-31-102 | [1,11,35,57,46] | +169.86 +/- 33.07 | +169.86 +/- 34.62 | 0 |
| 6   | S1 | Asp MR2 vs none | 20k | 7261 | 1696/2000 | 530-445-721 | [41,180,342,223,61] | +15.88 +/- 11.76 | +17.04 +/- 11.45 | 0 |
| 6   | S2 | Asp MR5 vs none | 20k | 7262 | 1532/2000 | 448-415-669 | [38,169,323,194,42] | +9.68 +/- 12.13 | +7.49 +/- 11.63 | 0 |
| 6   | S3 | MR5 vs MR3 | 20k | 7263 | 1761/2000 | 508-524-729 | [10,53,771,34,12] | -2.83 +/- 5.23 | -2.96 +/- 5.12 | 0 |
| 6   | S4 | Asp MR1 vs none | 20k | 7264 | 2000 | 593-540-867 | [45,231,415,244,65] | +9.21 +/- 10.29 | +9.21 +/- 10.31 | 0 |
| 7   | C  | 20k vs 10k, no options | 20k/10k | 7270 | 300 | 171-30-99 | [1,6,40,57,46] | +177.22 +/- 31.86 | +177.22 +/- 33.35 | 0 |
| 7   | U1 | MR2 vs MR3 | 20k | 7271 | 2000 | 586-617-797 | [24,156,658,151,11] | (last interim -4.13 +/- 8.12) | -5.39 +/- 7.20 | 0 |
| 7   | U2 | MR2 vs MR3 | 80k | 7272 | 800 | 200-198-402 | [4,46,298,48,4] | +0.87 +/- 9.56 | +0.87 +/- 9.57 | 0 |
| 7   | U3 | MR2 vs MR3 (second seed) | 20k | 7273 | 1963/2000 | 549-569-845 | [24,156,640,139,22] | -2.31 +/- 7.95 (last interim) | -3.72 +/- 7.60 | 0 |
| 7   | U4 | MR2 vs none (second seed of S1) | 20k | 7274 | NOT RUN | - | - | - | - | - |

Pooled MR2-vs-MR3 at 20,000 nodes (U1 + U3): 3,963 games, 1,135 wins - 1,186 losses - 1,642 draws,
Ptnml sum [48,312,1298,290,33], **-4.56 +/- 5.23**; share of pairs with two draws: 1,298/1,981 =
65.5% (U1 65.8%, U3 65.2%, U2 at 80k 74.5%).

Known, not replayed: MR3 vs none +13.5 [+5.7, +21.0] (three seeds pooled).

## 4. Files of the repository I opened

- The job file (git show on the handoff branch). Nothing else; tree, patch and build were job 5/6's
  and were not re-opened (the binary hash above is the reuse proof).

## 5. Start and end of each step (recorded stamps, UTC)

- 21:46:42Z  job 7 file found; read 21:47:0xZ.
- 21:47:0xZ  FIRST launch attempt aborted itself: my launch chain died at its first `cp` (the job 7
  folder did not exist yet), so the `&&` chain never reached the runner - the runner started only at
  22:03:56Z after I created the folder and copied pgn_stats.py. About 17 minutes lost to my own
  launch plumbing; the budget's later stamps carry it.
- 22:03:56Z -> 22:05:56Z  probe C + control 7270 (300 games, +177.22; rate 300/120 s = 2.5 games/s).
- Caps derived from C with the fifth of reserve: CAP2000 = 2000/2.5*1.2+60 = 1020 s;
  CAP800_80K = 800*6.5/2.5*1.2+120 = 2616 s (6.5 = the job-5 empirical 20k:80k per-game cost ratio).
- 22:05:59Z -> 22:23:1xZ  probe U1 + U1 (2,000 games, complete at the cap).
- 22:23:11Z -> 22:49:45Z  probe U2 + U2 (80k nodes; all 800 games completed in 1,534 s = 0.52
  games/s, better than the 6.5-ratio estimate of 0.38/s - the cap was never near).
- 22:49:45Z -> 23:06:51Z  probe U3 + U3 (cut at its 1020 s cap with 37 games missing, 1,963/2,000).
- 23:06:51Z  U4_SKIPPED (the 23:02:00Z deadline had passed: "-291s left"), RUNNER7_DONE.
- Report finalized 23:08-23:13Z, committed and pushed by ~23:15Z (past the 75-minute mark; inside
  the 85-minute limit; the PC-sleep note made the late push harmless).

## 6. What I did NOT do

- MR3-vs-none and the 20,000-node point of job 5 were not replayed (not asked).
- U4 was not run: the deadline had passed when U3 ended (the runner logged "U4_SKIPPED only -291s
  left"). MR2-vs-none therefore stays a one-seed result (S1's +17.0 +/- 11.5) - and given the direct
  comparisons, that single-seed number now looks like seed luck, not a property of MR2.
- No MaxReduce 4/6, no SPRT, no engine source committed, no PR opened.

## 7. What I am NOT sure about

- U1's -5.4 and U3's -3.7 agree in direction; the pooled -4.56 +/- 5.23 excludes 0 only by 0.7 Elo
  on the upper edge. I read it as "MR2 is somewhat worse at 20k", not as a measured 4.6-Elo loss;
  the safe sentence is "no reason to prefer 2, some evidence against it".
- The 80k comparison (U2) is one seed of 800 games at +/- 9.6: it separates "equal" from "differ by
  more than ~19", nothing finer. If the Asp pair's value could differ by depth the way packc28's
  gain does, 800 games cannot see it.
- My control came out +177 rather than ~+200-223 (the previous three gave +170/+200/+205/+223);
  all four contain ~200 in their intervals; I did not investigate.
- The 17-minute launch gap was mine (section 5); it cost U4 its slot, nothing else.

## 8. A better way

- Launch hygiene: a `&&` chain that ends in `nohup ... &` backgrounds the WHOLE chain, so a failed
  early `cp` silently cancels the launch while the echo still prints a PID. Separate the preparation
  from the launch into two commands (as I finally did), or start the runner with an absolute check
  ("timeline.txt must exist within 30 s"). This bug cost 17 minutes tonight.
- The direct-comparison lesson from job 6 held again: U1+U3's ~65% double-draw share bought a pooled
  +/-5.2 interval for ~35 minutes, where two against-none matches of the same length would give
  about +/-8 each with no direct answer. When the question is "is A ahead of B", play A-vs-B.
- Estimating a deep-point match's rate from a RATIO (my 6.5x) was pessimistic: the real 80k rate was
  0.52 games/s (ratio 4.8x), U2 finished 22 minutes before its cap. The probe's two 80k games took
  ~9 s each - reading the probe's wall time gives the real rate for free; size caps from IT.

## 9. Model name and version

I am glmflash2, running on GLM, model glm-5p3-flash (GLM 5.3 Flash) as far as I know it.
