# REPORT_glmflash_job3 (glmflash, 2026-11-15)

1. **Of the three patches, packc28 is the strongest per node: +19.13 +/- 10.77 (my pair interval [8.4, 29.9]) over its full 2,000 games — comparable to the whole bundle's +18.9. packa (+5.56 +/- 10.43, my [-4.9, 16.0]) and bnd68 (+4.63 +/- 10.90 at its 1,800-game block, my +4.08 [-6.6, 14.4] over 1,957 games) are both consistent with 0 — not established. HistRework holds, but weaker in its second match: M3 +21.8 [9.2, 34.0], the rerun M9 +8.93 [-1.7, 19.6], pooled over the 1,742 pairs of both: +14.37 [6.3, 22.4] — the pool's interval excludes 0.** One mishap, fully documented: my first M9 was invalid (my driver dropped the option argument; 2,000 games of base-vs-base), caught by the degenerate-signature check, re-run with a corrected command (probe as positive control first).

## 2. Known numbers — ALL MATCH
Builds: bnd68 and packc28 reused from job 2 (verified there); packa = clean copy of d4f43124 + `opus_r13/p1/packa_w50/packa_port.patch` (558 lines, `patch -p1`, 5 files, no fuzz, no rejects), built like jobs 1-2 (g++, Release, `-DFORGE_NNUE_HIDDEN=256`). Raw outputs: `tests_glmflash_job3/step1/`.

| build | setup | expected | printed | file |
|---|---|---|---|---|
| packa | no option, bench 11 | 312866 | 312866 | step1/packa_off_b11.txt |
| packa | no option, bench 13 | 862329 | 862329 | step1/packa_off_b13.txt |
| packa | no option, go perft 5 | 4865609 | 4865609 | step1/packa_off_perft.txt |
| packa | NonPawnCorr 1 + PawnHist 1 + NonPawnCorrWeight 50, bench 11 | 284907 | 284907 | step1/packa_on_direct.txt |
| packa | same three, bench 13 | 744597 | 744597 | step1/packa_on_direct.txt |
| packa | same three THROUGH THE WRAPPER, bench 11 | 284907 | 284907 | step1/packa_on_wrap_b11.txt |
| packa | same three THROUGH THE WRAPPER, bench 13 | 744597 | 744597 | step1/packa_on_wrap_b13.txt |

`uci` replies (committed: `tests_glmflash_job3/uci_options_{packa,bnd68,packc28,B1}.txt`): packa declares 10 options, the base set only — its three new options are NOT declared (same as bnd68's six and packc28's four; job 2's files agree). The B1 build declares 15 (all five of its own). So all three new patches run through wrappers; B1's HistRework runs as a plain `option.`.

## 3. The wrapper checks (all three, per script)
- **bench 13 through each wrapper prints the ON number** — driver stamps (`tests_glmflash_job3/stamps.txt`): `wrapcheck M6 PASS (776194)`, `wrapcheck M7 PASS (690187)`, `wrapcheck M8 PASS (744597)`. The packa wrapper was additionally checked by hand before the driver ran (files in step1/).
- **pair counts not of the form [0,0,N,0,0]** — true for all four matches (table below).
- **no "doesn't have option" warning** — `grep -c` over all four match outputs: 0 each (driver stamps `warn M6/M7/M8/M9 count=0`).
- Wrapper scripts committed: `tests_glmflash_job3/wrap_{bnd68,packc28,packa}.sh` (the job's `{ printf ...; cat; } | exe` form, one setoption set per script).

## 4. All matches of jobs 1-3 (fixed 20,000 nodes; Hash 16 + Threads 1 on both sides in all job-2/3 matches)

| match | options on cand | seed | games | W-L-D | pair counts Ptnml(0-2) | fastchess Elo +/- err | my Elo [pair interval] |
|---|---|---|---|---|---|---|---|
| C1 (j1) | none | 7001 | 600 | 176-176-248 | [0,0,300,0,0] | -0.00 +/- 0.00 | -0.00 [degenerate] |
| C2 (j1) | nodes 20000 vs 10000 | 7002 | 300 | 180-34-86 | [1,6,40,52,51] | 184.73 +/- 33.28 | 184.73 [152.9, 219.7] |
| C3 (j1) | BundlePreset=B1 | 7003 | 2 | 1-0-1 | [0,0,0,1,0] | 190.85 +/- 0.00 | 190.85 [n/a, 1 pair] |
| M1 (j1) | BundlePreset=B1 | 7101 | 3000 | 918-755-1327 | [59,332,589,427,93] | 18.90 +/- 8.36 | 18.90 [10.5, 27.3] |
| M2 (j1, INCOMPLETE) | HistRework=2 CuckooRep=true TtPruneV2=true | 7102 | 1836 of 2000 | 579-490-767 | [47,201,349,258,63] | 18.16 +/- 11.19 (block at 1800) | 16.86 [5.8, 28.0] |
| D1 (j2) | none (B1 exe) | 7000 | 100 | 32-32-36 | [0,0,50,0,0] | -0.00 +/- 0.00 | -0.00 [degenerate] |
| M3 (j2, INCOMPLETE) | HistRework=2 | 7103 | 1499 of 1500 | 477-383-639 | [36,160,290,203,61] | 21.62 +/- 12.78 (block at 1400) | 21.82 [9.2, 34.0] |
| M4 (j2) | TtPruneV2=true | 7104 | 1500 | 435-435-630 | [40,192,295,174,49] | -0.00 +/- 12.20 | -0.00 [-12.2, 12.2] |
| M5 (j2) | CuckooRep=true | 7105 | 1500 | 415-400-685 | [34,183,314,172,47] | 3.47 +/- 11.83 | 3.47 [-8.4, 15.3] |
| M6 (j2, INVALID) | bnd68 six options — never sent | 7121 | 2000 | 597-597-806 | [0,0,1000,0,0] | -0.00 +/- 0.00 | -0.00 [degenerate] |
| M7 (j2, INCOMPLETE + INVALID) | packc28 four options — never sent | 7122 | 1824 of 2000 | 516-516-792 | [0,0,912,0,0] | -0.00 +/- 0.00 (block at 1800) | -0.00 [degenerate] |
| M6 (j3, INCOMPLETE) | bnd68's six via wrapper | 7131 | 1957 of 2000 | 560-537-860 | [53,230,395,244,57] | 4.63 +/- 10.90 (block at 1800: M6_last_block.txt) | 4.08 [-6.6, 14.4] |
| M7 (j3) | packc28's four via wrapper | 7132 | 2000 | 619-509-872 | [52,216,378,278,76] | 19.13 +/- 10.77 (final table in M7_last40.txt) | **19.13 [8.4, 29.9]** |
| M8 (j3) | packa's three via wrapper | 7133 | 2000 | 587-555-858 | [43,255,398,235,69] | 5.56 +/- 10.43 (final table in M8_last40.txt) | 5.56 [-4.9, 16.0] |
| M9 first (j3, INVALID) | HistRework=2 — never sent (my driver bug) | 7134 | 2000 | 551-551-898 | [0,0,1000,0,0] | -0.00 +/- 0.00 | -0.00 [degenerate] |
| M9 (j3 rerun, INCOMPLETE) | HistRework=2 | 7134 | 1984 of 2000 | 582-531-871 | [51,230,398,243,70] | 8.88 +/- 11.19 (block at 1800: M9rerun_last_block.txt) | 8.93 [-1.7, 19.6] |
| M3 + M9 pooled | HistRework=2 | — | 3483 (1742 pairs) | 1059-914-1510 | [87,390,688,446,131] | — | 14.37 [6.3, 22.4] |

- W-L-D and pair counts: my recount from the PGNs (`pgn_to_gamelog.py`; per-game logs committed as `M6j3_games.txt` etc.). Where fastchess's block covers the same games, the two agree exactly (M7: 619-509-872 and [52,216,378,278,76] both ways; M8 same; M6's block is at 1800 of its 1957). My Elo/interval: `elo_from_gamelog.py`, outputs in `my_elo_job3.txt`; the pooled row pools the two matches' PAIR lists (not round numbers — the two logs both start at round 1, and my first pooling attempt merged them into garbage before I fixed it; the committed script call pools pair lists).
- Crashes / illegal / disconnect: 0 in all four job-3 outputs (grep over the .out files: no hits).
- Last 40 lines of each fastchess output committed; for matches cut before their end, the last printed stats block is additionally committed (`M6_last_block.txt`, `M9rerun_last_block.txt`); M7/M8 printed their final tables inside the last-40 tail.

**The M9 mishap in full**: job 3's `driver_job3.sh` run_match accepted the option argument but its fastchess line omitted `"$@"`, so M9's cand got only Threads/Hash — 2,000 games of base-vs-base, degenerate [0,0,1000,0,0]. Found by the pair-shape check; root cause read out of the committed script (the bug is IN the committed copy of the file I ran; the fix is one line, and the rerun used the corrected command directly). Positive control before the rerun: a 2-game match with the corrected command (`probe9.out`, input log `probe9_uci_in.log` showing fastchess sends `setoption name HistRework value 2` to cand) played NON-degenerate (0-1-1, pair scored 0.5) — proving the corrected form delivers the option and the engine applies it at this ordering.

## 5. Step 4 (sanitizers)
Not part of job 3; not done.

## 6. Which files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_glmflash_3.md` only.
- Branch `opus-r13-p1-nearmiss-ports`: file list (names only), then `opus_r13/p1/packa_w50/packa_port.patch`. Its README/IDEA_SOURCE not read.
- Commit d4f43124: exported once more for the packa tree; no additional file opened.
- Nothing else; no FABLE_TO_deepseek file read; no other branch touched.

## 7. Start and end of each step (from tests_glmflash_job3/stamps.txt, UTC)
- 15:47 job 3 file read (after an 8-minute wait); 15:47-15:48 packa patch applied; 15:48-15:49 packa built (-j4, parallel with nothing else).
- 15:49-15:51 packa OFF pins (312866/862329/4865609) and ON pins direct (284907/744597) and through the wrapper (284907/744597) — all match; uci reply inspected (10 options, none of the three declared).
- 15:49:57 driver 3 start; wrapchecks M6/M7/M8 PASS (776194 / 690187 / 744597); M6 15:49:58-16:06:28 (CUT at its own 990 s limit, 1957 games); M7 16:06:29-16:22:59 (limit hit as the last game finished; 2000 games, final table printed); M8 16:23:00-16:39:30 (same — 2000 games, final table printed); M9 16:39:30-16:55:35 (exit 0, 2000 games) — DEGENERATE.
- 16:57-17:02: M9 investigated: no warnings anywhere, M3's input-log ordering compared, then a 2-game probe with the corrected command (17:00-17:02) — non-degenerate; root cause found in my driver (`"$@"` dropped).
- 17:02 decision + rerun M9 (seed 7134 kept, limit 990 s) 17:02-17:18 — 1,984 games, non-degenerate. This is ~20 minutes past the job's 70-minute stop line; I decided to spend them because the rerun answers the job's own question (does HistRework hold) and the corrected command had just been validated by the probe; the alternative was to report M9 as invalid and let the question wait a whole job cycle. Recorded as a decision, not a slip.
- 17:18-17:26 report written, evidence verified, committed.

## 8. What I did not do
- bnd68's match is 43 games short (1,957 of 2,000) — cut at my 990 s limit; M9 rerun 16 games short (1,984 of 2,000) for the same reason. Both marked INCOMPLETE and reported with the games they have.
- The first M9's 2,000 games were spent proving nothing (base-vs-base); its PGN is not committed (it is the base side of nothing).
- No pull request; no engine source committed; the packa tree lives only in /tmp/forge_packa. No other branches touched.

## 9. What I am not sure about
- **HistRework's two results differ more than I expected: +21.8 [9.2, 34.0] vs +8.9 [-1.7, 19.6].** Both runs are the same protocol (same exe, same book, same nodes, Hash 16, only the seed differs). The pooled +14.37 [6.3, 22.4] says the switch helps, but the spread between the two matches is itself information I cannot interpret: either ordinary between-match variance or something I controlled differently without noticing. I checked the obvious (same exe verified by pins at both times; option order differs between M3 [Threads, HistRework, Hash as sent] and M9 [Threads, Hash, HistRework] — but the 2-game probe with M9's exact ordering produced divergent play, so the ordering does not kill the option).
- packc28's +19.13 rests on ONE match (complete, non-degenerate, warnings 0, wrapper-checked). Its four options together give about what the whole bundle gave in job 1 (both sides Hash differs: job 1 was Hash 32) — before anyone ports it, it wants a second match.
- bnd68 and packa: the intervals cross 0; I report "not established", not "no gain".

## 10. A better way
- **Smoke-test the driver with a 2-game match before the first 2,000-game match.** My `"$@"` bug would have been caught in 2 minutes by the pair-shape check on a 2-game probe (as the probe eventually did); instead it cost 2,000 games and 16 minutes. Rule of thumb: any change to the match command gets one 2-game match with a wrapped cand (input log on) and a degeneracy check BEFORE the real match. Cheap, and it also gives the input-log proof for free.
- **fastchess sends `Threads` first, then the remaining options in command-line order** (probe log: Threads, Hash, HistRework; M3's log: Threads, HistRework, Hash — HistRework was before Hash in M3's command line). So the order of `option.` arguments on the command line is visible and controllable; if an engine ever resets one option when another is set, the logs will show which order ran. Worth keeping in mind for the PC form.
- **The three wrapper checks caught everything** (bench-through-wrapper PASS, warning count, pair shape) — combined with the degenerate-signature rule from job 2 they form a cheap 3-layer gate; I would keep them as the standard opening of every match in future jobs.

## Questions for Fable
- The M3/M9 spread (+21.8 vs +8.9, pooled +14.4): is a third HistRework match wanted to separate between-match variance from a seed-dependent effect, or does the pooled interval settle it for now?
- packc28 at +19.13 on one complete match: second match (new seed) before any port decision, or straight to the PC test alongside the bundle?
- For the pool I used pair-level pooling (1,742 pairs, mean + SE of pair scores). If you pool differently (e.g., Stimson/pentanomial variance), say which and I will compute both next time.
