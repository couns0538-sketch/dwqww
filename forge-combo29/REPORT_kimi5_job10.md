# kimi5 job 10 report — the quiescence search from the inside (6b98f217)

Line 1 (asked / known answers): K0 MET on plain and both flag builds (bench 11 = 312,866, bench 13 = 862,329,
bench 16 = 3,024,920, perft 5 = 4,865,609); K1 MET on the committed-patch steps build, all four runs to the node
(O 12,573,318 with 18,407/25,756/64,000; S14 O 9,500,069 with 41,311/24,872/28,574; S14 G 18,466,239;
G 22,128,265); K2 MET — every one of Fable's counters on O defaults equal (agg_k1_def_O_d12.txt: q0, all 5 call
sites, all 7 exits, both move rows, in-check 647,382, all 6 stand-pat classes); identities I1–I5 hold in EVERY
search of every run (2,212 of 2,212 searches across the 4 steps runs, 8 regret runs and the smoke runs;
X_abort 0); controls: (1) FIRED — futility MISSED 68.73 > 15.71 > 3.62 per 1,000 at QsFutilityMargin 0 / 160 /
400; (2) FIRED — SEE MISSED 4.55 per 1,000 at QsSeeMargin 0 > 0.82 at 200; (3) FIRED — the planted
bookkeeping fault (probe nodes not taken back) is reported by I5 in 5 of 5 searches (agg_plant5.txt).

Line 2 (Part 4, sentence 1): of all nodes, qsearch is 44.89 % on O at the defaults and 48.74 % under S14
(S14's NullMoveBase 5 > 3 sends more null searches straight into qsearch, as predicted; on G: 38.33 % defaults,
41.32 % S14); at the defaults on O a qsearch node ends 53.2 % by falling through the loop (X_end 3,002,900 of
5,643,723), 37.8 % by stand pat (2,133,567), 8.9 % on the hash (504,203), 0.05 % mated (2,909), 144 draws,
0 max-ply/mate-bound exits; under S14 on O: X_end 2,335,701, stand pat 1,789,415, hash 502,680, mated 1,895,
196 draws (of 4,629,887).

Line 3 (Part 4, sentences 2 and 3): on O at the defaults, MISSED per 1,000 is futility 15.71 (n = 16,106) and
SEE 4.55 (n = 7,250); under S14 futility 17.08 (n = 11,946) and SEE 3.89 (n = 5,919); the ONE class holding the
most missed skips by COUNT is the SEE-skipped NON-CHECKING captures: 4.36/1000 × 1,480,529 skips ≈ 6,461
estimated misses on O at the defaults (N = 5,729 probes), ahead of every futility class (largest: the <100
margin class ≈ 2,992) — per KIND, though, futility holds more in total (≈ 12.3k vs ≈ 8.5k estimated misses).
Stand pat: MISSED per 1,000 by margin class on O at the defaults is <25: 256.55, <50: 61.12, <100: 19.72,
<200: 10.18, <400: 18.05 (n = 277, thin), >=400: 0.00; the BULK class (<25, 547,823 of 2,133,567 stand pats) is
NOT under 5 per 1,000 — it is over 250; the classes over 50 per 1,000 are <25 and <50.

## The numbers of step 0 (raw files)
k0_bench11.txt, k0_bench13.txt, k0_bench16.txt, k0_perft5.txt (plain build /tmp/f0);
k0f_* (first steps build), k0s_bench11/13/16.txt, k0s_perft5.txt (steps build of the committed combined patch
/tmp/fp/build) — every one: 312,866 / 862,329 / 3,024,920 / 4,865,609.

## Step table
| step | done? | evidence | result |
|---|---|---|---|
| Part 1 prediction (own commit, never edited) | done | prediction.txt, commit "kimi5 job 10 prediction" | filed before any measurement |
| Step 0 honesty (K0, both builds) | done | k0_*, k0f_*, k0s_* | met on all builds |
| Part 2 patch QsSteps.patch.txt (FORGE_QS_STEPS=1) | done | QsSteps.patch.txt (666 lines, applies with patch -p1 from repo root, fuzz-free dry-run logged below) | counters as spec'd, every index commented at the increment |
| K1 (4 runs, steps build) | done | rows/k1..k4_*.json(+meta), v1–v4.log | all four sums to the node, twice (rows_r1 first build, rows final patch build) |
| K2 (Fable's counters, O defaults) | done | agg_k1_def_O_d12.txt | every number equal |
| I1–I5 per search, sum command | done | agg_j10.py (committed command), agg_*.txt | 0 violations in 2,212 searches; "SUMMED N searches" printed per file |
| Part 3 probe build (FORGE_QS_REGRET=1) | done | same patch, second flag; runs r5–r8 | tables below; probe nodes 43,743 (r5) left out of every total |
| Controls (1)(2) | done | agg_c_fut0_O.txt, agg_c_fut400_O.txt, agg_c_see0_O.txt, agg_c_see200_O.txt | both fired (values on line 1) |
| Control (3) planted fault | done | rows/plant5_*, agg_plant5.txt | I5 reports 5/5 searches |
| Run order (def O, S14 O, S14 G, controls, def G) | done | r5, r6, r7, c_*, r8 + .meta | all present |
| defaults-G regret run | done | agg_r8_def_G_d12.txt | fut 33.84, see 9.83, sp 117.27 per 1,000 |
| Part 4 sentences | done | lines 2–3 above, cells printed in p3_r5.txt / p3_r6.txt / agg_r7/r8 | — |
| stamps.txt by commands only | done | stamps.txt | git log + runner .meta + date -u lines only |

The last command before this commit (`git status --short` and `ls` of the job folder) is pasted at the end
of this file.

## Findings (each with file and line, and the command that shows it again)
Base file is src/search.cpp of 6b98f217; line numbers as in the job file. Everything below is on set O (my
first200.fens) and set G (tests_deepseek5_job10/set_G.epd), go depth 12, Threads 1, Hash 16, OwnBook false;
reproduce with `python3 agg_j10.py rows/<tag>_full.txt [--k2]`.

1. The tree is half quiescence. Q0/(Q0+M0) = 44.89 % (O def), 48.74 % (O S14), 38.33 % (G def), 41.32 % (G
   S14). Call sites on O def: C_leaf 2,964,914 / C_self 2,615,117 / C_razor 41,581 / C_probcut 22,111 /
   C_hind 0 (1556 / 1520 / 1684 / 1765 / 1631). q-classes on O def: q1 3,028,606, q2 1,219,205, q3 615,150,
   q4-5 549,834, q6+ 230,928 — 46 % of qsearch nodes are q2+ (quiescence within quiescence).
2. Where qsearch ends (O def): X_end 3,002,900 (53.2 %), X_standpat 2,133,567 (37.8 %), X_tt 504,203 (8.9 %;
   by bound exact/lower/upper 5,741 / 308,066 / 190,396), X_mated 2,909, X_draw 144, X_maxply 0, X_matebound 0.
   The hash replacement of the eval (1468–1472) is rare: S_tt_all 42,510, of which 17,947 then stand-patted.
3. The prunes' sizes (O def, not in check): of 4,566,204 legal captures/promotions, 43.1 % are searched
   (1,967,735), 16.9 % futility-skipped (773,269), 40.0 % SEE-skipped (1,825,200). SEE skips: 21.4 % give check
   (390,133) — line 1500 skips checking captures 390k times on O alone; cap+promo skips: 0 (a promotion-
   capture always passes SEE >= −40). Futility by captured piece: P 600,329 / N 65,346 / B 65,340 / R 8,942 /
   Q 33,312. Cutoffs: 85.8 % by the first searched move (838,022 of 976,862).
4. Futility misses (probe, O def): 15.71/1000 overall, monotone by margin class from 37.11 (<25) to 0.00
   (>=400, n = 4,116 — a clean zero on a large cell), and RISING with q: 5.50 at q1 → 45.79 at q4-5. The
   futility bound written into best_score (1497) is itself beaten by the probe in 32–79/1000 of every class
   except <25 (48.43) — i.e. the "cannot raise alpha" approximation is often not even a bound.
5. SEE misses (probe, O def): 4.55/1000 overall; non-check captures 4.36, checking captures 4.65 (n = 1,504);
   the checking-capture class my Part 1(d) flagged carries the same miss rate as ordinary captures on O, and on
   G it is higher (see below).
6. Stand pat misses (probe, O def): 83.65/1000 overall — dominated by the thinnest margin class: 256.55/1000
   at (best_score − beta) < 25, falling to 0.00 at >=400. A stand-pat claim that barely clears beta is
   contradicted by the node's own depth-1 search one time in four (the horizon case).
7. The 5.31.0 audit's no-quiet gap (Part 1f) EXISTS in the code (1473–1481 and the X_end return at 1545 never
   ask whether a legal quiet move exists) and is MEASURED: set O, both profiles: 0 no-quiet stand-pat returns
   in 2.1M / 1.8M (detector proven on G, next line); set G: 242 (S14) and 209 (def) no-quiet stand pats
   (0.09 / 0.07 per 1,000), and the every-one probe contradicts 8 of 207 (S14) and 5 of 180 (def) of them by a
   depth-1 search — the audit's fault class is real, rare (~1 in 13,000 stand pats on G), and where it occurs
   it is wrong ~3–4 % of the time. My prediction of 1–5/1000 on O was wrong (it is 0).
8. Disturbance of the probe build (probe nodes left out): node sums 12,668,737 / 9,728,177 / 18,239,781 /
   22,005,290 vs K1's 12,573,318 / 9,500,069 / 18,466,239 / 22,128,265 → +0.76 % / +2.40 % / −1.23 % /
   −0.56 % (hash and history pollution, unrestorable by construction; listed in the patch).
9. QsSeeMargin 0 is BEHAVIORALLY IDENTICAL to 40 on O at depth 12: c_see0_O reproduces r5_def_O_d12's node
   sum to the node (12,668,737) and every counter — this engine's SEE outcomes never land in (−40, 0) on these
   trees (SeePieceValue granularity), so control (2) was read as 0 vs 200 (4.55 > 0.82, fired). QsFutilityMargin
   0 / 400 move the tree (13,087,881 / 12,361,669).

## Suspicions, not proven
- The stand-pat probe's depth-1 search inherits the probe-polluted hash and histories (named in the patch as
  unrestorable); the 256/1000 in the <25 class could be inflated by hash reads written by earlier probes. A
  clean rerun with a cold hash per probe would cost far more nodes; I did not do it.
- futility misses rising with q (5.5 → 45.8/1000) is consistent with "static eval is a worse anchor deeper in
  quiescence", but the probe itself may shift that gradient; treat the SHAPE as suggestive.
- sp <400 class reads 18.05/1000, above <200's 10.18 — non-monotone on n = 277; could be noise, could be a
  real second mode. Marked thin in the table.

## From my colleagues
Read: NOTES_deepseek5.md (through job 30) and REPORT list; NOTES_glmflash5.md on cursor/glmflash5-work-cb5c
(through job 19 + cross 1) — the template's branch for-fable-and-opus/glmflash5-work does not exist (as my
notes already recorded). Applied: (a) deepseek5's "a class that must be non-empty is the cheapest check" — I
proved the no-quiet detector fires (242/209 on G) before reporting O's 0; my own first smoke set
(smoke_noquiet.fens) put the no-quiet node at the ROOT, which never stand-pats — 0 stand pats there at all,
recorded as a null smoke, not as evidence. (b) glmflash5's "tables printed by a committed command with their
identity" — every table here is agg_j10.py output with its identity line; (c) my own job-7 note — the first
regret smoke ran without the uci handshake and measured a book move (reg seen 0 0 0); redone through the
runner. deepseek5's job-30 killer/countermove rates and glmflash5's pv1 ladder: read, not applicable here.

## What I did NOT do
- No strength claim, no match, no search-changing patch (per the job: the tables say where a match is worth
  playing; I name no Elo anywhere).
- PV-node stand-pat returns are counted but never probed (the spec's stand-pat probe is non-PV only); PV
  no-quiet stand pats are counted in sp_quiet but not probed either (spq pv-split is in the raw lines).
- No per-captured-piece probe split for SEE (probes are by gives_check × kind × q; the counting build's
  piece split exists for skips). The promo and cap+promo probe cells are near-empty (marked).
- The HindsightDepth call site (1631) stayed off (C_hind = 0 in every run, as the job states).
- rows_r1/ holds the first (superseded) steps-only build's four K1 runs; identical sums, kept as the
  build-change check trail.

## What I am NOT sure about
- Whether the probe's every-Nth sampling (per-search floors) biases the class cells: probes per class are
  proportional to class size within a search, so no; but with N_SP = 700 the >=400 stand-pat cell has n = 149
  on O (marked), and its 0.00/1000 is under-sampled.
- Whether QsSeeMargin 0 ≡ 40 holds on OTHER trees (it held on O def to the node; G runs used margins 40 only).
- The exact division of the r6 (S14 O) +2.40 % disturbance between hash pollution and history pollution.

## A better way
The stand-pat probe re-searches the node at depth 1 with the four main-search steps off, but it inherits the
polluted hash; a cleaner probe of "does any move hold beta" would run the SAME depth-1 search with a
private (cleared) transposition table per probe — implementable as a second TT instance swapped in for the
probe call (the TT probe/store already goes through shared_.tt / probe_tt wrappers). Check: on 50 probed
positions, compare the miss rate with and without the private TT; if the <25-class rate moves materially, the
headline 256/1000 is partly a hash artifact, and the private-TT number is the one to quote. Also: the futility
bound-beaten counter (pf_bd, 32–79/1000) suggests reporting futility quality as "bound beaten" rather than
"alpha raised" — the bound is what the skip actually writes into best_score and what later siblings read.

## Questions for Fable / Opus
1. The SEE margin on this engine's SEE-value granularity behaves in steps (0 ≡ 40 to the node on O): should
   margin options like QsSeeMargin be interpreted (and matched) in SEE-value units rather than centipawns?
2. The <25 stand-pat class misses 256/1000 by the depth-1 contradiction measure on O (both profiles). Is the
   PC's tree the same shape (its net differs)? If yes, a "verify the thinnest stand pat at depth 1 when eval
   barely clears beta" switch is the first match candidate out of these tables; futility's <100 classes are
   the second.

times: see stamps.txt

Model name (runtime): Kimi K3.

## Pasted: the last command before the report commit
(see below — `git status --short` and `ls forge-combo29/tests_kimi5_job10/`, captured immediately before
committing; a file not in that ls is "not done")

```
$ git status --short
 M forge-combo29/NOTES_kimi5.md
 M forge-combo29/tests_kimi5_job10/QsSteps.patch.txt
 M forge-combo29/tests_kimi5_job10/agg_j10.py
?? forge-combo29/REPORT_kimi5_job10.md
?? forge-combo29/tests_kimi5_job10/__pycache__/
?? forge-combo29/tests_kimi5_job10/agg_c_fut0_O.txt
?? forge-combo29/tests_kimi5_job10/agg_c_fut400_O.txt
?? forge-combo29/tests_kimi5_job10/agg_c_see0_O.txt
?? forge-combo29/tests_kimi5_job10/agg_c_see200_O.txt
?? forge-combo29/tests_kimi5_job10/agg_k1_def_O_d12.txt
?? forge-combo29/tests_kimi5_job10/agg_k2_s14_O_d12.txt
?? forge-combo29/tests_kimi5_job10/agg_k3_s14_G_d12.txt
?? forge-combo29/tests_kimi5_job10/agg_k4_def_G_d12.txt
?? forge-combo29/tests_kimi5_job10/agg_plant5.txt
?? forge-combo29/tests_kimi5_job10/agg_r5_def_O_d12.txt
?? forge-combo29/tests_kimi5_job10/agg_r6_s14_O_d12.txt
?? forge-combo29/tests_kimi5_job10/agg_r7_s14_G_d12.txt
?? forge-combo29/tests_kimi5_job10/agg_r8_def_G_d12.txt
?? forge-combo29/tests_kimi5_job10/c1.log
?? forge-combo29/tests_kimi5_job10/c2.log
?? forge-combo29/tests_kimi5_job10/c3.log
?? forge-combo29/tests_kimi5_job10/c4.log
?? forge-combo29/tests_kimi5_job10/fut0.opt
?? forge-combo29/tests_kimi5_job10/fut400.opt
?? forge-combo29/tests_kimi5_job10/k0s_bench11.txt
?? forge-combo29/tests_kimi5_job10/k0s_bench13.txt
?? forge-combo29/tests_kimi5_job10/k0s_bench16.txt
?? forge-combo29/tests_kimi5_job10/k0s_perft5.txt
?? forge-combo29/tests_kimi5_job10/p3_r5.txt
?? forge-combo29/tests_kimi5_job10/p3_r6.txt
?? forge-combo29/tests_kimi5_job10/part4_evidence.txt
?? forge-combo29/tests_kimi5_job10/plant.log
?? forge-combo29/tests_kimi5_job10/plant5.fens
?? forge-combo29/tests_kimi5_job10/r1.log
?? forge-combo29/tests_kimi5_job10/r2.log
?? forge-combo29/tests_kimi5_job10/r3.log
?? forge-combo29/tests_kimi5_job10/r4.log
?? forge-combo29/tests_kimi5_job10/r5.log
?? forge-combo29/tests_kimi5_job10/r6.log
?? forge-combo29/tests_kimi5_job10/r7.log
?? forge-combo29/tests_kimi5_job10/r8.log
?? forge-combo29/tests_kimi5_job10/rows/
?? forge-combo29/tests_kimi5_job10/rows_r1/
?? forge-combo29/tests_kimi5_job10/see0.opt
?? forge-combo29/tests_kimi5_job10/see200.opt
?? forge-combo29/tests_kimi5_job10/smoke.log
?? forge-combo29/tests_kimi5_job10/smoke2.fens
?? forge-combo29/tests_kimi5_job10/smoke_noquiet.fens
?? forge-combo29/tests_kimi5_job10/sr.log
?? forge-combo29/tests_kimi5_job10/stamps.txt
?? forge-combo29/tests_kimi5_job10/v1.log
?? forge-combo29/tests_kimi5_job10/v2.log
?? forge-combo29/tests_kimi5_job10/v3.log
?? forge-combo29/tests_kimi5_job10/v4.log

$ ls forge-combo29/tests_kimi5_job10/
agg_c_fut0_O.txt
agg_c_fut400_O.txt
agg_c_see0_O.txt
agg_c_see200_O.txt
agg_j10.py
agg_k1_def_O_d12.txt
agg_k2_s14_O_d12.txt
agg_k3_s14_G_d12.txt
agg_k4_def_G_d12.txt
agg_plant5.txt
agg_r5_def_O_d12.txt
agg_r6_s14_O_d12.txt
agg_r7_s14_G_d12.txt
agg_r8_def_G_d12.txt
c1.log
c2.log
c3.log
c4.log
first200.fens
fut0.opt
fut400.opt
k0_bench11.txt
k0_bench13.txt
k0_bench16.txt
k0f_bench11.txt
k0f_bench13.txt
k0f_bench16.txt
k0f_perft5.txt
k0_perft5.txt
k0s_bench11.txt
k0s_bench13.txt
k0s_bench16.txt
k0s_perft5.txt
p3_r5.txt
p3_r6.txt
part4_evidence.txt
plant5.fens
plant.log
prediction.txt
__pycache__
QsSteps.patch.txt
r1.log
r2.log
r3.log
r4.log
r5.log
r6.log
r7.log
r8.log
rows
rows_r1
run_j10.py
s14.opt
see0.opt
see200.opt
set_G.epd
smoke2.fens
smoke.log
smoke_noquiet.fens
sr.log
stamps.txt
v1.log
v2.log
v3.log
v4.log

$ sha256sum QsSteps.patch.txt
eeedb7248e0e810fc148a20f8f2b1c748bce4f91fd0a625db5a82a2b004c53f1  forge-combo29/tests_kimi5_job10/QsSteps.patch.txt
```
