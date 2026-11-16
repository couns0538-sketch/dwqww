# REPORT glmflash5 — JOB 22 — R1's second seed at 2,000 nodes, its two halves, and the CED8 variant

Branch `cursor/glmflash5-work-cb5c` (run A). Exe = B10 (job 21's; sha256
7621bdfbb3b85f5e5ea37e9a7365adf2be27423e16d55d7b470d8cb7a513a1a6 — re-verified this job's
step 0). All five matches COMPLETE — nothing cut. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: (a) does R1's 2,000-node gain hold with a second seed (M46); (b) which half carries it
(M47 = the extension alone, M48 = the two reduction terms alone); (c) the research plan's CED8
variant (M49); plus R1's second seed at 20,000 (M50).

Answer: **M46 (R1 @2k, seed 20046): +0.52 [−11.86, +12.90] — the second seed COLLAPSES M45's
+16.86; the two-seed pool R1@2k is +8.69 [+0.12, +17.26] (2,000 pairs) — a small gain, barely
one-sided.** **The halves at 2k: M47 (CheckExtensionDepth 30 alone) +5.91 [−6.21, +18.03]; M48
(LmrGiveCheck 0 + LmrInCheck 0 alone) +7.82 [−3.80, +19.44] — both halves lean positive, neither
one-sided.** **M49 (CheckExtensionDepth 8 + the two terms): +14.43 [+2.59, +26.27], 1,000 pairs —
the BEST of the four and the only one-sided interval this job: keeping the extension near the
root while dropping it deeper, with the reduction discounts off, is the variant that shows a
gain (one seed).** **M50 (R1 @20k, seed 20050): −0.87 [−11.38, +9.65]; the pool R1@20k (M44+M50)
is +2.00 [−5.33, +9.32] — level, two seeds.**

How sure: step 0 re-verified (pins + the S14 row exact); the four probes exact (per-option
delivery with the right VALUES); 10,000/10,000 validation rows; identities under every table;
the two pools by the committed `job22_stats.py`. M49 is one seed with a one-sided interval —
the same strength of evidence job 13's histoff had, which its second seed then halved: believe
the sign provisionally, demand the second seed for the size.

## 2. Step 0 — re-verified (`job22_rows.txt`, driver `job22_rows.py` COMMITTED)

Pins: 312,866 / 862,329 / 3,024,920 / 4,865,609 ✓ (`b10r_*.txt`). S14 row: first-3
41311/24872/28574, sum 9,500,069 ✓ (the other three rows — R1/gc0ic0/ced30 — also reprinted,
all equal to job 21's).

## 3. Step 2 — four probes (`probe_M46…M49.log`; probe openings lines 4101–4108, no match uses
them)

Every probe: base received its 14 lines ×2 games (28) and nothing else; the candidate the same
14 plus its own with the right values (M46: CED=30 + GC=0 + IC=0, 2/2 each; M47: CED=30 only;
M48: GC=0 + IC=0 only; M49: CED=8 + GC=0 + IC=0, 2/2 each); refusal lines 0; every `go` carried
nodes 2000 (counts equal to all `go` lines).

## 4. The matches (B10 both sides; S14 both sides; the candidate's lines on top; nodes=2000 for
M46–M49, 20000 for M50; Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours
swapped, `-pgnout` in my folder; openings_job22.epd built by the committed GLOBBING script
`make_openings_job22.py` — it reads EVERY `gamelist_*.txt` in my tests folders (62 files), so
the used-set is complete by construction; 55,959 distinct openings removed; Random(22001);
4,000 lines; first line `r1bqkbnr/ppp2pp1/2n4p/4p3/3pP1P1/3P3P/PPP2PB1/RNBQK1NR w KQkq - 0 6`;
order sequential; M46 1–1000, M47 1001–2000, M48 2001–3000, M49 3001–4000; M50 1–1000 again at
20,000 nodes (a different SHUFFLE than M44's job-20 file, so the openings are fresh — the seed
itself is inert under sequential order, see the fault note); concurrency 4; `cmd_<M>.txt` files
hold the exact commands, written before each run)

Games by ending FIRST — from `gamelist_M*.txt` by the committed `job22_stats.py` (output
`job22_stats_out.txt`), identities printed by the same command (losses on time BY SIDE 0/0 in
all five; illegal/disconnect/crash 0):

| ending | M46 (2000) | M47 (2000) | M48 (2000) | M49 (2000) | M50 (2000) |
|--------|------------|------------|------------|------------|------------|
| White mates | 711 | 699 | 743 | 708 | 628 |
| Black mates | 656 | 653 | 640 | 705 | 463 |
| 3-fold repetition | 346 | 342 | 324 | 310 | 604 |
| fifty moves | 177 | 190 | 199 | 169 | 156 |
| insufficient material | 104 | 107 | 90 | 98 | 148 |
| stalemate | 6 | 9 | 4 | 10 | 1 |
| **identity: mates = wins + losses** | 711+656 = 685+682 = 1367 ✓ | 699+653 = 693+659 = 1352 ✓ | 743+640 = 714+669 = 1383 ✓ | 708+705 = 748+665 = 1413 ✓ | 628+463 = 543+548 = 1091 ✓ |

| match | cand | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|------|-------|-------|----|-------------------------|----------------------|
| M46 | S14+R1 | 20046 | 1000 | 685-682-633 | [113,206,360,207,114] | +0.52 [−11.86, +12.90] | COMPLETE (2:06) |
| M47 | S14+CED30 | 20047 | 1000 | 693-659-648 | [94,224,346,226,110] | +5.91 [−6.21, +18.03] | COMPLETE (1:54) |
| M48 | S14+GC0+IC0 | 20048 | 1000 | 714-669-617 | [84,207,390,218,101] | +7.82 [−3.80, +19.44] | COMPLETE (1:56) |
| M49 | S14+CED8+GC0+IC0 | 20049 | 1000 | 748-665-587 | [79,207,386,208,120] | **+14.43 [+2.59, +26.27]** | COMPLETE (1:55) |
| M50 | S14+R1 | 20050 | 1000 | 543-548-909 | [57,251,389,246,57] | −0.87 [−11.38, +9.65] | COMPLETE (11:59) |

**The pools (one committed command):**

| pool | pairs | n5 | Elo, 95 % pair interval |
|------|-------|----|-------------------------|
| R1@2,000 (M45 job21 + M46) | 2,000 | [200, 389, 751, 431, 229] | +8.69 [+0.12, +17.26] |
| R1@20,000 (M44 job21 + M50) | 2,000 | [104, 496, 779, 515, 106] | +2.00 [−5.33, +9.32] |

predictions.txt (own commit eedc32db4, 16:09:34Z, before M46): M46 +14 [0,+28] — held (+0.52);
M47 +4 [−8,+16] — held; M48 +8 [−4,+20] — held; M49 +8 [−4,+20] — **CALLED WRONG** (+14.43,
above +20? NO — +14.43 is INSIDE [−4,+20]... re-checked by command: the range held); M50 +4
[−8,+16] — held (+2.00... −0.87 INSIDE). Correction of my first mental scoring: ALL FIVE ranges
held; verified against the file by reading it, not from memory.

## 5. From my partners

- Opus's PC pair for R1@20k (+10.57 SPRT seed 1; −1.22 seed 2) — my two-seed pool +2.00
  [−5.33, +9.32] sits between them: three-tree agreement on "level to small" at 20,000.
- Opus's tuning note (three of 35 settings move no search) — my step-0 re-verification is the
  same idea applied to the patches.
- The four keeps from this file's head are now standing discipline: S14 everywhere; prediction
  commits for standing/cross too; file-check immediately before standing/cross choices; stamp
  every step's start and end.

## 6. What I did NOT do

- **A FAULT, owned: my first M50 attempt (16:19–16:21) was INVALID — it replayed M46's games
  exactly** (order=sequential + fixed nodes make the SEED INERT: same file, same start line ⇒
  the same games regardless of `-srand`), and my driver call also misrouted a `nodes=20000`
  token. The run is discarded; the real M50 (hand-written, nodes=20000, the same lines but a
  20,000-node search) ran after. Consequence recorded for the whole session: **a "second seed"
  is only a second LOOK when the OPENINGS differ — under sequential order the freshness comes
  from the file/shuffle, never from the seed.**
- No second seed of M49 (its one-sided interval makes it the top candidate for one).
- No CED-value ladder (8 / 15 / 30) — the natural extension of M49's finding; not asked.

## 7. What I am NOT sure about

- M49's +14.4: one seed, one-sided interval — the same evidence grade job 13's histoff had
  before its second seed halved it.
- Whether the R1@2k pool's +8.7 (barely one-sided) is the bundle's real value now that its
  seeds straddle (16.9 then 0.5).
- Whether CED8's gain comes from the extension cap or its interaction with the reduction terms
  (M47/M48 alone vs M49's combination suggests an interaction; three single seeds cannot
  decompose it).

## 8. A better way

- The globbing openings builder (`make_openings_job22.py`, committed) replaces every hand-list:
  it reads ALL my gamelist files (62), so "used" is complete by construction — the sed chains
  had silently missed 7,000+ openings' worth of matches. It should be THE builder from now on,
  with only the Random seed and the line count changing per job.

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 16:32:01Z)

```
=== git status --short (head):
?? forge-combo29/tests_glmflash5_job22/M46_last40.txt
?? forge-combo29/tests_glmflash5_job22/M46_stdout.txt
?? forge-combo29/tests_glmflash5_job22/M47_last40.txt
?? forge-combo29/tests_glmflash5_job22/M47_stdout.txt
?? forge-combo29/tests_glmflash5_job22/M48_last40.txt
=== ls tests_glmflash5_job22: (42 files)
b10r_bench11.txt b10r_bench13.txt b10r_bench16.txt b10r_perft5.txt
cmd_M46.txt cmd_M47.txt cmd_M48.txt cmd_M49.txt cmd_M50.txt
config_M46.json config_M47.json config_M48.json config_M49.json config_M50.json
gamelist_M46.txt gamelist_M47.txt gamelist_M48.txt gamelist_M49.txt gamelist_M50.txt
job22_match.sh job22_rows.py job22_rows.txt job22_stats.py job22_stats_out.txt job22_summary.txt
M46_last40.txt M46_stdout.txt
M47_last40.txt M47_stdout.txt
M48_last40.txt M48_stdout.txt
M49_last40.txt M49_stdout.txt
M50_last40.txt M50_stdout.txt
make_openings_job22.py openings_job22.epd prediction.txt
probe_M46.log probe_M47.log probe_M48.log probe_M49.log
stamps.txt
```
(the `??` lines at listing time were the job folder's uncommitted files; all join in this push.
The full `git status --short` listed 26 untracked files of this folder plus nothing else
outside it.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
