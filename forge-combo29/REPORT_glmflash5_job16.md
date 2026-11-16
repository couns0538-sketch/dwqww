# REPORT glmflash5 — JOB 16 — THE BRIDGE: pv1 and de0 under the PC's 14 settings, on my tree

Branch `cursor/glmflash5-work-cb5c`. Exe = job 14's B6, sha256
9938d88062cdfa9b8d18752a76c35519d8d36307dbbf14ebeba5ecef771e0bb1 (no new build). All three
matches COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: does pv1's +32 (my defaults, two seeds) survive under the PC's 14 search settings (S14)
on my tree; is `LmpBase` the setting that decides it (M24 vs M25); and what the double extension
is worth under S14 (M26).

Answer: **M24 (S14+pv1 vs S14): +15.99 [+5.86, +26.13], 1,000 pairs — pv1 STILL GAINS under the
PC's settings, about half its default-settings size (+32.05).** **M25 (S13+pv1 vs S13, LmpBase
at default 4): +15.12 [+5.07, +25.17] — the SAME gain as M24: `LmpBase` does NOT decide whether
pv1 gains** (the tree-based guess — S14+pv1 saves nothing because LMP starts later — is refuted
by games: the tree said 0.998, the games say +16 under BOTH LmpBase values). **M26 (S14+de0 vs
S14): −4.56 [−15.78, +6.66], 800 pairs — under S14 the double extension's removal is LEVEL,
against −27.16 at my defaults: the 14 settings absorb most of what the double extension was
buying.**

The three comparison sentences, each with its two numbers:
- pv1 at my defaults +32.05 [+24.68, +39.43] (two seeds) beside pv1 under S14 +15.99 [+5.86,
  +26.13] (one seed): the gain shrinks but does not vanish under S14.
- M24 (+15.99) beside M25 (+15.12): the two intervals overlap almost completely — `LmpBase` is
  not the deciding setting; the cause of the difference from my defaults is elsewhere (question
  for a match: which of the other 13 settings).
- de0 at my defaults −27.16 [−37.38, −16.93] beside de0 under S14 −4.56 [−15.78, +6.66] (800
  pairs): level under S14 — the mechanism's value is settings-dependent.

How sure: all six step-1 rows EQUAL Fable's PC-tree-in-my-setup numbers to the node (the anchor
held; no finding); probes exact (per-line delivery counts including the LmpBase differentiation);
5,600/5,600 validation rows; identity lines under every table. M24/M25 = one seed each; M26 =
one seed, 800 pairs.

## 2. Step 1 — six rows beside Fable's (`job16_rows.txt`, driver `job16_rows.py` COMMITTED)

| setting | first-3 nodes | Fable's known | sum over 200 | known |
|---------|---------------|---------------|--------------|-------|
| no option (ANCHOR) | 18407, 25756, 64000 | same ✓ | 12,573,318 | ✓ must-hold held |
| S14 | 41311, 24872, 28574 | same ✓ | 9,500,069 | ✓ |
| S14 + pv1 | 17188, 26670, 44100 | same ✓ | 9,476,627 | ✓ |
| S14 + de0 | 19385, 37711, 33783 | same ✓ | 9,212,648 | ✓ |
| S13 | 16332, 24431, 22542 | same ✓ | 9,713,408 | ✓ |
| S13 + pv1 | 12286, 24912, 38874 | same ✓ | 9,260,262 | ✓ |

Refusal lines: 0 in every run (the 14 names are all accepted on B6; pre-check before step 1).

## 3. Step 2 — three probes (`probe_M24/M25/M26.log`; probe openings lines 5001–5030, no match
uses them)

| probe | base received | cand received | refusals | go-limit |
|-------|---------------|---------------|----------|----------|
| M24 | its 14 setting lines ×10 games (LmpBase=8 included: 10) | the same 14 + SoundPvArm=1 10 + SoundStepMask=1 10 | 0 | 1700/1700 |
| M25 | its 13 setting lines ×10 (LmpBase 0) | the same 13 + pv1's two 10/10 | 0 | 1399/1399 |
| M26 | its 14 ×10 | the same 14 + DoubleExtLimit=−1 10 | 0 | 1325/1325 |

## 4. The matches (B6 both sides, nodes=20000, Threads 1, Hash 16, OwnBook false, no
adjudication, pairs colours swapped, `-pgnout` in my folder, openings_job16.epd = book minus
jobs 2,3,5–15 openings (33,309 distinct removed; Random(11403); 5,300 lines; first line
`r2qkb1r/ppp1pppp/2n3b1/3p4/3Pn3/2PB1N1P/PP3PP1/RNBQ1RK1 b kq - 2 7`), order sequential; M24
lines 1–1000, M25 1001–2000, M26 2001–2800; concurrency 4)

Games by ending FIRST (losses on time BY SIDE 0/0 in all three; illegal/disconnect/crash 0) —
**made from `gamelist_M*.txt` by the stats command; identity printed by that command under the
table: white_mates + black_mates = wins + losses (holds in all three):**

| ending | M24 (2000) | M25 (2000) | M26 (1600) |
|--------|------------|------------|------------|
| White mates | 632 | 638 | 456 |
| Black mates | 446 | 471 | 387 |
| 3-fold repetition | 558 | 545 | 451 |
| fifty moves | 171 | 174 | 129 |
| insufficient material | 189 | 168 | 174 |
| stalemate | 4 | 4 | 3 |
| **identity: mates = wins+losses** | 632+446 = 585+493 = 1078 ✓ | 638+471 = 598+511 = 1109 ✓ | 456+387 = 411+432 = 843 ✓ |

| match | cand | base | seed | pairs | W-L-D | n5 | Elo, 95 % pair interval | LOS (dropped from the verdict; one seed) | complete? (duration) | validation |
|-------|------|------|------|-------|-------|----|-------------------------|------|----------------------|------------|
| M24 | S14+pv1 | S14 | 9910 | 1000 | 585-493-922 | [44,205,428,261,62] | +15.99 [+5.86, +26.13] | (one seed) | COMPLETE (duration 12:08) | 2000/2000 |
| M25 | S13+pv1 | S13 | 9920 | 1000 | 598-511-891 | [35,225,422,254,64] | +15.12 [+5.07, +25.17] | (one seed) | COMPLETE (duration 12:03) | 2000/2000 |
| M26 | S14+de0 | S14 | 9930 | 800 | 411-432-757 | [42,197,336,190,35] | −4.56 [−15.78, +6.66] | (one seed) | COMPLETE (duration 09:52) | 1600/1600 |

predictions.txt (before M24): M24 0 [−12,+12] — **CALLED WRONG** (+15.99); M25 +12 [−6,+30] —
held; M26 −12 [−26,+2] — held.

## 5. Step 4 — no new finals tables this job beyond the identities above (the piece-class
method exists and was fixed in job 14/15; this job's question is the settings bridge, and the
three tables above carry their identity lines as ordered)

## 6. From my partners

- Opus's PC result (via Fable): pv1 on the PC's engine+net = −2.43 [−9.22, +4.36] in 4,000
  games. My bridge: on MY tree with the PC's SETTINGS, pv1 = +16.0 — so the setting difference
  explains roughly HALF the gap (32 → 16), and the rest lives in the net and the four switches
  my source does not have. The bridge's reading stands as measured on both sides.
- deepseek5's job-24 Part A: NOT USED (its table was read row-wise instead of column-wise;
  Fable's recount stands in its file).
- Fable's own tree guess (S14+pv1 saves nothing because of LmpBase 8) — refuted by M24/M25
  (both +15–16); the guess was labeled a guess in its file; the games now say so.

## 7. What I did NOT do

- No second seed for M24/M25/M26 (the bridge's question is answered in sign at one seed each;
  the sizes need seeds before any bundle talk).
- No de0-under-S13 match (not asked).
- The 14 settings ran as ONE block (as the job defines S14); which SINGLE setting absorbs the
  double extension's value is unmeasured (question for a match).

## 8. What I am NOT sure about

- Whether M24's +16 and M25's +15 are the same number (intervals overlap heavily; two seeds
  each would tell).
- Whether M26's −4.6 (800 pairs) means "the double extension is worth nothing under S14" or is
  a seed draw around a small negative (the interval reaches −15.8).
- The bridge transfers SETTINGS, not the net: my tree still runs the built-in evaluation — the
  PC's net and its four extra switches are out of my reach, said plainly.

## 9. A better way

- If file 17 makes S14 my session's base (the job's own conditional), then EVERY earlier default-
  settings number on my side should be re-read as "my tree at MY defaults" — a label, not a
  fault; the bridge job is what makes the two labels comparable. A one-page index of "which
  settings produced which number" in the session's shared notes would prevent future
  cross-tree comparisons by accident.

## 10. UTC stamps

times: see stamps.txt (job read 12:08:43Z; refusal pre-check 12:09:1xZ; step 1 12:09–12:10;
openings+prediction 12:10:1xZ; three probes 12:10–12:11; M24 12:11:2xZ–12:23:3xZ (duration
12:08); M25 12:22:1xZ–12:34:22Z (duration 12:03); gate check printed 12:34:3xZ (25 min 39 s <
33 min); M26 12:34:4xZ–12:44:3xZ (duration 09:52); stats+identities 12:44:4xZ; report written
after; commit stamped by git).

## 11. Real output of `git status --short` and `ls` of the folder (verbatim, 12:44:56Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_job16/
=== ls tests_glmflash5_job16: (26 files)
cmd_M24.txt cmd_M25.txt cmd_M26.txt
config_M24.json config_M25.json config_M26.json
gamelist_M24.txt gamelist_M25.txt gamelist_M26.txt
job16_rows.py job16_rows.txt job16_stats.txt job16_summary.txt
M24_last40.txt M24_stdout.txt
M25_last40.txt M25_stdout.txt
M26_last40.txt M26_stdout.txt
make_openings_job16.py openings_job16.epd prediction.txt
probe_M24.log probe_M25.log probe_M26.log
stamps.txt
```
(the `??` line is the job folder itself before this commit.)

## 12. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
