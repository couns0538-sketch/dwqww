# glmflash4, job 8 report (2026-11-15)

**The two new tables together do not gain what their members hinted at.** The
family's gain per node, `MinorCorrection=50 + ThreatCorrection=100` against
nothing, is **−3.16 with a 95 % pair interval of [−10.82, +4.50]** pooled over
M1 (cut at 1,718 finished games) and M3 (2,000) — beside the members' single
figures (minor about +3 over 16,000 games of two helpers; threat +1.0
[−6.4, +8.4] in my job 7). **What the threat table adds ON TOP of the minor
table (M2): +4.17 ± 10.61** — a lean, not established; and the mirror
direction (M4, minor on top of threat): **−5.73 ± 9.92**. **Step 0c says the
two tables do NOT say the same thing twice**: the Pearson correlation between
their terms is **0.26**, they agree in sign on only 21 % of evaluated nodes,
69 % of reads have at least one of the two terms zero, and where the threat
term speaks it is seven times the minor term's size (6.04 cp vs 0.86 cp
mean |term|; the pawn and material tables sit at 1.36 and 1.34). Two weakly
correlated tables, neither of which moves the needle — recorded as "the
family is not worth porting; the individual tables are not either".
**Nothing else was cut**: M2, M3 and M4 ran their full 2,000 games; only M1
was cut (by its own time limit, at 1,718 finished games — my limit came from
the control's pace and was too tight for the optioned side's slower search;
the job's cut-games rule applied).

## Step 0 — the merged tree, proven line by line

- **0a. Files and orders.** `MinorCorrection` patch (`tests_glmflash4_job4/minor_correction.patch.txt`,
  96 diff lines) touches `include/forge/search.hpp` and `src/search.cpp`;
  `ThreatCorrection` patch (`tests_glmflash4_job7/threat_correction.patch.txt`,
  129 lines) touches the same two files. `patch -p1 -F0` in BOTH orders on
  fresh copies FAILS (order minor→threat and threat→minor both exit 1 — the
  second patch's context is consumed by the first; outputs in `step0/merge_order_*.txt`).
  **Merged by hand**, as the job allows: the working tree /tmp copy of the
  minor-patched tree plus the eight threat edits (both externs, both members,
  both tunables entries, both ctor/clear hooks, both key helpers, both read
  and write sites — order inside each file: minor before threat).
- **0b. The merged tree is right.** Each line as the job asks:
  - both options 0 = the four known answers: **312866 / 862329 / 3024920 /
    4865609** (`step0/fam_off_*.txt`);
  - 2,000 positions (`go depth 9`) family-off vs unpatched: **both sides sha256
    55265dc258ebb8eac58b869f... — byte-identical; smallest node count 4534**;
  - `MinorCorrection=100` alone: **333818 / 922324 / 4596576** = my job 4
    numbers exactly (`step0/fam_minor100_*.txt`);
  - `ThreatCorrection=100` alone: **277700 / 876634 / 2854753** = my job 7
    numbers exactly (`step0/fam_threat100_*.txt`).
  The `uci` reply lists both options (2 lines). No line differs; the merge
  stands.
- **0c. The four tables together** (traced copy; diff
  `proofs/traced_family_diff.txt`; output `step0/S0c_traced_bench13_both100.txt`;
  bench 13, Minor=100 + Threat=100, 887,446 nodes, 85,679 corrected-eval
  reads): mean |pawn| **1.36 cp**, |material| **1.34 cp**, |minor| **0.86 cp**,
  |threat| **6.04 cp**, |sum of all four| **9.07 cp**. Sign relation of the
  two new terms: same sign 18,079 (21.1 %), opposite 8,098 (9.4 %), at least
  one of them 0 59,502 (69.4 %) — my counter's third bucket covers both-zero
  and one-zero together. **Pearson r(minor term, threat term) = 0.260** —
  weakly positively correlated: not one table twice, but far from
  independent either. Updates: minor 5,476 (5,475 changed), threat 5,476
  (5,443 changed); distinct keys seen: minor 730, threat 104.
- **0d.** bench 13 with `MinorCorrection=50 ThreatCorrection=100` (the match
  setting): **934,025** (`step0/S0d_bench13_minor50_threat100.txt`).
- **0e.** The merged tree as ONE diff against 6b98f217:
  `tests_glmflash4_job8/correction_family.patch.txt` (155 diff lines; the two
  member patches are committed beside it).
- **0f. Sanitizers:** the planted-fault program exits 1 under ASan
  (`step0/S0f_planted_stderr.txt`); the ASan+UBSan family build: bench 13
  both-on = **934,025 — exactly the release number — zero sanitizer/error
  lines**; 200 of the identity positions both-on: 200/200 answers, empty
  stderr (`step0/S0f_*`).

## The matches

Form: one exe both sides, `proto=uci nodes=20000 option.Threads=1
option.Hash=16 option.OwnBook=false` under `-each`, UHO openings
`order=random` with `-srand`, each opening twice with colours reversed, no
adjudication, `-concurrency 4`. A 2-game logged probe ran before every match
(`probes/probe_cand_setoption_lines.txt` for M1/M3's config,
`probes/probeM2_lines.txt`, `probes/probeM4_lines.txt`): both options seen
arriving on the cand side, the base side carrying exactly its own option,
zero "doesn't have option" warnings everywhere.

| match | cand | base | seed | games finished | W-L-D (cand) | pair counts | fastchess Elo ± err | my Elo [95 % pair interval] | faults |
|---|---|---|---|---|---|---|---|---|---|
| C | nodes 20000 | nodes 10000 | 8130 | 300 | 186-19-95 | [0, 3, 30, 64, 53] | +218.19 ± 31.90 | +218.19 [+186.6, +250.4] | 0 |
| M1 | Minor50+Threat100 | none | 8131 | 1718 (cut; my extraction 1739 rows) | 493-530-695 | [50, 231, 337, 188, 53] | −7.48 ± 11.42 | −7.39 [−18.77, +3.96] | 0 |
| M2 | Minor50+Threat100 | Minor50 | 8132 | 2000 | 598-574-828 | [59, 234, 393, 252, 62] | +4.17 ± 10.61 | +4.17 [−6.44, +14.78] | 0 |
| M3 | Minor50+Threat100 | none | 8133 | 2000 | 568-565-867 | [58, 240, 391, 263, 48] | +0.52 ± 10.37 | +0.52 [−9.85, +10.90] | 0 |
| M4 | Minor50+Threat100 | Threat100 | 8134 | 2000 | 548-581-871 | [51, 247, 427, 234, 41] | −5.73 ± 9.92 | −5.73 [−15.66, +4.19] | 0 |

(M2/M3/M4 "my Elo" figures computed from the per-game files; the exact
pair counts and intervals are in each `matches/<name>_games_and_tail.txt`.)

**How the games ended** (fastchess's own termination reasons, counted from
each match's output; every game is one of these, none on time, none by
fault):

| match | mate (both colours) | 3-fold | 50-move | insufficient material | stalemate |
|---|---|---|---|---|---|
| C | 205 | 61 | 22 | 10 | 2 |
| M1 | 1033 | 492 | 103 | 109 | 2 |
| M2 | 1172 | 570 | 118 | 134 | 6 |
| M3 | 1133 | 594 | 133 | 136 | 4 |
| M4 | 1129 | 631 | 115 | 123 | 2 |

(M1's tally counts the 1,739 extracted rows; fastchess's own table counts
1,718 finished — the 21 in-flight games at the cut are in my extraction and
not in its total.)

## Files of the repository I opened

- `handoff/...`: `FABLE_TO_glmflash4_8.md`.
- My own two patch files (committed in jobs 4 and 7) and the trees they
  produced; commit `6b98f217`'s `src/search.cpp`/`include/forge/search.hpp`
  (the same sites as jobs 4/7 — read then, re-read at the merge).
- The matches' UHO openings file (as before).

## Stamps (date -u / recorded)

- ~22:46 job file 8 fetched and read (budget start)
- 22:47:03 merge-order experiment done (both orders fail), hand merge built, family build finished, merged diff generated (155 lines)
- ~22:47:4x step 0b bench lines (off/alone ×3 settings) — all pass
- ~22:48:2x 2,000-position identity (family-off = unpatched, same sha)
- 22:48:21 traced family built; 0c counters taken (both-on) + off-state check
- ~22:48:4x 0d bench (934025); ASan family build finished
- ~22:48:5x 0f planted fault + ASan bench + 200 positions — all clean
- 22:48:5x probe (M1 config); 22:48:51-22:50:17 C
- 22:50:20-23:02:01 M1, cut by its own 700 s limit at 1,718 finished (my limit came from C's unoptioned pace — too tight for the optioned side; recorded)
- 23:02:1x M2 probe; 23:02:11-23:15:59 M2 (2,000, exit 0)
- 23:16:02-23:29:03 M3 (2,000, exit 0)
- 23:29:1x M4 probe; 23:29:19-23:43:57 M4 (2,000, exit 0)
- 23:44-23:55 tallies, pooled figures, this report, commit, push

## What I did not do

- I did not run the two member patches' original match programmes again
  (their numbers are quoted from my own jobs 4 and 7 reports).
- M1's 700-second limit was my planning error (it came from the control's
  unoptioned pace); the match was cut at 1,718/2,000 — the pooled figure
  carries that, and the cut's 21 in-flight games are reconciled in the table.
- I did not test other pairings (Minor100+Threat50, both at 50, three-way
  weight grids) — the job fixed the match setting at Minor50+Threat100.
- No SPRT; no PR; nothing outside my own branch was pushed or changed.

## What I am not sure about

- The family's pooled −3.16 [−10.82, +4.50] rests on one cut seed (M1) and
  one complete seed (M3); M1's cut seed is also the most negative single
  reading of the day (−7.5). A third seed could move the family number
  either way; the budget's cut-order (M4 before M3) was not triggered, so
  this is the one full set I have.
- M2 (+4.17) and M4 (−5.73) measure the two "add-on" directions with one
  seed each; their disagreement in SIGN with each other is not resolvable at
  one seed each.
- The 0c correlation (r = 0.26) is computed over 85,679 reads of EIGHT bench
  positions (bench 13's fixed set); over more varied positions the figure
  could move. The direction (not ~1) is what the report leans on.
- The traced means reuse the traced build's own counters; the traced binary's
  node count (887,446) differs from the plain family build's both-on bench
  (934,025 at Minor50+Threat100 — different weights in the two runs, so not
  comparable; the like-for-like check is the traced run's own OFF state =
  862,329 ✓).

## A better way

- The merge-order experiment should be part of every "combine two patches"
  job text with the EXPECTED outcome named ("they will not compose; merge by
  hand and prove each member's numbers inside the merge") — it took one
  command and converted an unknown into a checked plan.
- The step-0c battery (four mean |terms| + the pairwise correlation + the
  sign histogram) is the right FIRST look at any correction-table family: it
  separated "one table twice" from "two different tables" in one bench run,
  before any match. I will reuse it; suggest the job text standardise it.
- My own recurring planning error, twice now (job 6's playout cap, job 8's
  match limit): limits derived from an UNLOADED measurement break under
  self-inflicted load. Rule of thumb I will keep: match limits = measured
  pace × 1.3, and the FIRST optioned match gets the largest limit.
- fastchess's termination reasons are already printed per game; tallying
  them (one grep) closes the "how did the games end" hole the owner's
  warning described — worth making a standing column in every match table.

## Model

I am glmflash4. The model behind this agent is GLM, trained by Z.ai; the
runtime presents it as GLM 5.3 Flash. I cannot verify a precise version
string from inside the run.
