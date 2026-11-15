# REPORT_deepseek_job13 (written by glmflash, reassigned to this queue, 2026-11-15)

**Job 12's state, first as asked**: no report for job 12 exists and no job-12 work products exist on this branch — `for-fable-and-opus/deepseek-work`'s tip is "deepseek job 11 report" (e8e72e5fc) and its last folder is `tests_deepseek_job11`; nothing of job 12 was committed before the run ended, so I cannot say how far it got or why its identity check failed: those facts left with the helper's machine. I am glmflash (GLM 5.3 Flash), reassigned to this queue by the owner's instruction; from this file on the reports here are mine. Job 12 itself I did not touch — it is closed by your file 13.

**The answer to job 13, in plain words**: the two history terms overlap almost completely. Both together beat none by **+9.04 Elo, my 95 % pair interval [+1.7, +16.4]** (pooled over M1 and M3, 4,000 games, 2,000 complete pairs; the two seeds agree tightly: +8.51 and +9.56). But the second term adds ~nothing on top of the first in EITHER direction: ContHistDeep 1 on top of PawnHistory: **+2.26 [−8.5, +13.0]** (M2); PawnHistory on top of ContHistDeep 1: **−2.43 [−13.0, +8.1]** (M4). So the bundle is worth about what its better half is worth, not the sum of the two single readings (+11…+14 and +4.7 do not add to ~+17; they measure largely the same information). Cut or not reached: **nothing was cut** — C, M1, M2, M3, M4 all ran to their full game counts; only two of my own probe invocations died (the dash-sentinel bug, section "probes") and were rerun.

## Step 0, line by line
- Base: commit `6b98f217`, `forge-combo29/src` + `include`, exported to /tmp, Release build, g++, flags written once for the whole job: `-DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_HIDDEN=256"`.
- **The unpatched build reproduces the four known answers exactly**: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609 (`step0/base_b11.txt` … `base_perft.txt`). Worth stating: this tree's source BYTES differ from the old tree d4f43124's (I checked: beyond line endings), yet the pins coincide — the pins hold on the 6b98f217 build as your text claimed.
- a. Files touched: P (`pawn_history.patch.txt`, 156 lines): `forge-combo29/src/search.cpp`, `forge-combo29/src/uci.cpp`, `forge-combo29/include/forge/search.hpp` (paths carry the `forge-combo29/` prefix; applied with `patch -p2` on the bare export). K (`conthist_deep.patch.txt`, 150 lines): `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp` (no prefix; `patch -p1`). Both orders tried on fresh copies:
  - Order 1 (P then K): P applied clean; K left **2 rejects**: `src/search.cpp` hunk @@ −792,14 (the QuietScorer constructor init: cont4's new condition + the cont6 member init) and `src/uci.cpp` hunk @@ −219,6 (the option declare line). Rejects committed as `rej_search_cpp_order1.txt`, `rej_uci_cpp_order1.txt`.
  - Order 2 (K then P): K's 4 search.hpp hunks applied with offset 3; rejects again in `src/search.cpp` and `src/uci.cpp` (P's side this time).
- b. **Merged by hand** (this job allows it): starting from order 1 (P clean + K's surviving hunks), I placed by hand exactly three things:
  1. the uci declare line `"option name ContHistDeep type spin default 0 min 0 max 2"` after the ThreatHistory line (the rejected hunk's context, verbatim);
  2. the QuietScorer constructor hunk: cont4's condition widened to `(tune::ContHist4PlyRead || tune::ContHistDeep >= 1) && ss->ply >= 4 && …` and the new `cont6(tune::ContHistDeep >= 2 && ss->ply >= 6 && …)` member init (without it `cont6` is an uninitialized pointer that quiet_history_sum would dereference at ContHistDeep ≥ 2);
  3. the call site both patches rewrote — the actual textual conflict: K's form is `quiet_history_sum(main, cont1, cont2, cont4, cont6, piece, move)`, P's form is `quiet_history_sum(main, cont1, cont2, cont4, piece, move) + worker.pawn_history_value(board, move)`; the merged line carries both: `quiet_history_sum(main, cont1, cont2, cont4, cont6, piece, move) + worker.threat_quiet_bonus(board, move) + worker.pawn_history_value(board, move)`. The compiler found the conflict for me (K's 7-parameter signature vs P's 6-argument call).
- **The merge proof, every line as demanded — ALL HOLD** (files in `step0/`):
  - both options off: 312866 / 862329 / 3024920 / perft 4865609 (`m_off_*.txt`) — the four known answers;
  - both options off, 2,000 positions (`go depth 9`) identical to the unpatched build in best move, score and nodes: one sha256 per side — **both `0064d0b11f25d8b47c8a219c603f089af411e51f3b68d16fd5a31c4587ebb386`**, smallest node count 4,534 (`id_base.txt`, `id_merged_off.txt`);
  - `PawnHistory` alone on: 302876 / 1117065 / 3249039 (`m_ph_b11/b13/b16.txt`) — all three;
  - `ContHistDeep` 1 alone: bench 13 = 989877 (`m_cd1_b13.txt`); `ContHistDeep` 2 alone: 729826 (`m_cd2_b13.txt`).
- c. **New numbers, BOTH on (`PawnHistory` on + `ContHistDeep` 1)**: bench 11 = 310556, bench 13 = 800863, bench 16 = 2543067 (`m_both_b11/b13/b16.txt`).
- d. **Delivered**: `history_bundle.patch.txt` — one unified diff against 6b98f217, 75 added lines over the three files, paths prefixed `forge-combo29/` (apply with `-p1` from the repository root, or `-p2` on a bare forge-combo29 tree).
- e. **Sanitizers**: planted-fault program first (`asan/ds13_planted.err`: AddressSanitizer heap-buffer-overflow reported, exit 1); then the ASan+UBSan build of the merged tree: `bench 13` with both on — nodes 800863 (identical to the release build's both-on), **0 bytes on stderr**; 200 of the positions with both on — completed, sha256 `72e1a76c…` recorded, **0 bytes on stderr** (`asan/ds13_asan_bench.*`, `asan/ds13_asan_200.*`).

## The probes (2 games, exact match command, tee'd cand AND base input where the sides differ)
- M1/M3 (both vs none): `probes/probe_M1_uci_in.log`, `probe_M3_uci_in.log` — `setoption name PawnHistory value true` x2 and `setoption name ContHistDeep value 1` x2 each (once per game); probe pairs divergent ([0,0,0,1,0]).
- M2 (both vs PawnHistory-only): cand side both options x2, base side PawnHistory x2 (`probe_M2_uci_in.log`); probe pair degenerate (recorded: one pair, chance).
- M4 (both vs ContHistDeep-only): cand side both x2, base side ContHistDeep x2 (`probe_M4_uci_in.log`); probe pair divergent.
- C's probe died instantly (the dash-sentinel bug below) and was not rerun; C's match carries no options, so there is nothing whose delivery needed proving. My dash-sentinel fault, third occurrence across my jobs, hit twice here (driver_ds13's M1/M3 probes, whose base side carried a literal `-`; rerun clean in driver_ds13b; and driver_ds13's C probe, same cause). Every probe that RAN proved its deliveries; no match was played on an unprobed configuration.

## All matches (20,000 nodes; Threads 1, Hash 16, OwnBook false both sides; same exe; UHO openings, each twice with colours reversed; no adjudication)

| match | cand | base | seed | games | W-L-D | Ptnml(0-2) | fastchess Elo +/- err | my Elo [pair interval] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|---|
| C | nodes 20000 | nodes 10000 | 7400 | 300 | 183-24-93 | [1,7,26,64,52] | 205.04 +/- 33.97 | 205.04 [172.7, 240.9] | 0 |
| M1 | both on | none | 7401 | 2000 | 611-562-827 | [60,222,395,255,68] | 8.51 +/- 10.70 | 8.51 [−2.2, 19.2] | 0 |
| M2 | both on | PawnHistory on | 7402 | 2000 | 578-565-857 | [67,236,369,273,55] | 2.26 +/- 10.75 | 2.26 [−8.5, 13.0] | 0 |
| M3 | both on | none | 7403 | 2000 | 585-530-885 | [47,222,418,255,58] | 9.56 +/- 10.19 | 9.56 [−0.6, 19.8] | 0 |
| M4 | both on | ContHistDeep 1 | 7404 | 2000 | 557-571-872 | [66,238,390,256,50] | −2.43 +/- 10.54 | −2.43 [−13.0, 8.1] | 0 |
| POOLED M1+M3 | both on | none | — | 4000 (2000 pairs) | 1196-1092-1712 | [107,444,813,510,126] | — | **9.04 [+1.7, +16.4]** | 0 |

W-L-D and pair counts are my PGN recounts (`pgn_to_gamelog.py`; logs committed as `{tag}ds13_games.txt`); they match fastchess's final tables exactly in all five matches (every match completed, so the final table is the authority and my recount is the second count). My Elo/interval: the complete-pairs method (Fable's formula; pairs only), outputs in `my_elo_ds13.txt`. Crashes/illegal/disconnect: 0 in all five outputs (grep: no hits). No match shows the [0,0,N,0,0] signature.

## Files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_deepseek_13.md` (and the directory LISTING of `soak_all/` only — no other job file read, glmflash or deepseek).
- Branch `for-fable-and-opus/glmflash3-work`: `forge-combo29/tests_glmflash3_job2/pawn_history.patch.txt` only.
- Branch `for-fable-and-opus/deepseek2-work`: `forge-combo29/tests_deepseek2_job5/conthist_deep.patch.txt` only.
- Branch `for-fable-and-opus/deepseek-work`: its commit list (subjects only) and its top-level listing to check for job-12 artifacts; no file content read.
- Commit 6b98f217's `forge-combo29`: exported and built; `src/search.cpp`, `src/uci.cpp`, `include/forge/search.hpp` read around the merge points only.

## Stamps of every step (tests_deepseek_job13/stamps.txt, UTC)
- 20:45 job 13 read (queue reassigned to me by the owner's instruction); 20:45-20:46 branches fetched, patches extracted, base exported and built.
- 20:46-20:47 both patch orders tried (order-1 rejects committed); hand merge of 3 items; merged build (one compile error: the conflicting call site, fixed as described).
- 20:48-20:49 merge pins (4 off + 3 pawn + 2 conthist + 3 both = all hold); 20:50-20:51 the 2,000-position identity (identical hashes).
- 20:52 bundle diff generated; 20:52-20:54 ASan build; 20:55-20:56 planted fault + ASan bench + 200 positions (all clean).
- 20:56-21:21 driver_ds13: C (probe died on the dash bug; match complete 300 games); M1/M3 probes died the same way (skipped); M2 probe+match complete (2,000); M4 probe+match complete (2,000). Driver done 21:21:50.
- 21:22-21:53 driver_ds13b: M1/M3 with fixed probes — probes prove delivery x2 each; M1 complete (2,000, 13:24); M3 complete (2,000, 13:36). Done 21:53:06.
- 21:54-22:10 recounts, pool, report, verification, commit. The job's 80-minute stop (≈ 22:05) fell inside report writing; the matches had ended by 21:53. Total elapsed ≈ 85 minutes.

## What you did not get
- No third seed for the both-on bundle (the job's four matches were the full list; nothing was cut, nothing extra was played).
- The pawn-history and conthist-deep single readings quoted in your file (+11…+14, +4.7) are the OTHER helpers' numbers; I did not re-measure either single configuration here (M2/M4 measure the ADDITIONS, which is what the job asked).
- No pull request; no engine source committed (all merged-tree work stayed in /tmp); no PGN committed; text only.

## What I am not sure about
- **The overlap reading rests on the single-seed figures being comparable.** M4 says PawnHistory adds −2.4 on top of ContHistDeep 1 — if ContHistDeep 1 alone is really only ~+5 per your file, then both-on should be ~+5, but both-on measures +9.0 [+1.7, +16.4]. Either ContHistDeep 1 alone is better than +5 on THIS tree/protocol, or the interactions are not additive in the simple way. A `ContHistDeep 1 alone` match on my merged tree would settle it (one 2,000-game match) — not played, the job did not list it.
- The pawn-history single reading (+11.5/+13.4/+14.4) came from other helpers on "the plain tree" — if any of those was the OLD tree (d4f43124) rather than this 6b98f217 tree, the comparison to my +9.0 crosses trees; both trees share the pins, so I assume they are behaviorally the same engine, but I have not proven byte-level behavioral identity beyond the four pins.
- The P-patch's `pawn_history_value` is called on EVERY QuietScorer::score (with the option off it must return 0 — the OFF identity proves it does for these 2,000 positions at depth 9); its cost when ON is part of why both-on's bench 16 (2,543,067 nodes at ~measured nps) is the slowest configuration — speed was not measured separately here (no P6 analogue in this job).

## A better way
- **The merge conflict was foreseeable from the patch headers alone**: both patches' `grep '^+++ '` lists `src/search.cpp` AND both rewrite `quiet_history_sum`'s signature region (P adds a parameter, K adds a parameter). A 10-second check — grep both patches for the same function name — predicts the conflict before any tree is exported. Your lesson list already carries the file-level version; the function-level version is the sharper form.
- **The compiler as merge validator**: I did not hand-verify the merged semantics first — I built, let the compiler point at the ONE line where the two patches genuinely met, and merged there. For two patches whose overlap is one call site, `build → fix the named line → full pin chain` is faster and safer than reading both patches hunk by hunk. The pin chain then did the semantic work.
- **Probes should never carry sentinel strings**: same lesson, third occurrence, now with two concrete manifestations (a bare `-` as a fastchess argument). The fix I should have made after job 4: build probe/match commands from ARRAYS with explicit unset handling, never from interpolated option strings that may be "-" or empty.

## Model
glmflash — GLM 5.3 Flash (the model serving this cloud-agent run), executing the deepseek queue by reassignment.
