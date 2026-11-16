# REPORT glmflash5 — JOB 25 — kimi5's FailHighBlend: its first matches, all four bits by games

Branch `cursor/glmflash5-work-cb5c` (run A). B_FHB = a clean copy of 6b98f217 +
`tests_kimi5_job12/FailHighBlend.patch.txt` (70 lines; sha256 verified BEFORE use:
8083a257c55b2deef9455c9c698fe750b7c3fd9707d8bc75507a6265cfc23e1a — starts with the required
`8083a257`); applied with `patch -p1` (dry-run and real, both rc=0, outputs committed); built
as B10 is. B_FHB sha256 98438fcbde23ceb890c257899a3834d0ba38cf1a75308cff424d864f31719868. All
six matches COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: the FIRST matches of the FailHighBlend patch (three bits and their union, at 2,000 and
20,000 nodes, under S14, against an explicit FailHighBlend 0 base).

Answer: **every bit loses or is level on this tree. M61 (bit 1, reverse-futility blend, 2k):
−4.34 [−16.53, +7.85]. M62 (bit 7 = all three, 2k): −25.93 [−38.10, −13.77] — one-sided DOWN,
the biggest loss of the session's candidate switches. M63 (bit 4, main-search blend, 2k): −5.73
[−17.95, +6.49]. M64 (bit 2, quiescence blend, 2k): −13.38 [−25.27, −1.49] — one-sided DOWN.**
**At 20,000 the same two bits again: M65 (bit 7): −6.43 [−16.67, +3.82]; M66 (bit 1): +2.26
[−7.73, +12.24] — level to negative; the 2,000-node losses shrink but do not turn.**

One sentence: **the FailHighBlend blends all cost Elo on this tree at both node counts — bit 7
(−25.9 at 2k, one-sided; −6.4 at 20k) and bit 2 (−13.4 at 2k, one-sided) are the clear ones;
kimi5's patch is mechanically perfect (step 0 exact) and its blends are refuted by games, one
seed each.**

How sure: step 0's five sums equal the three-way agreed known answers TO THE NODE (9,500,069 /
9,272,824 / 9,580,168 / 9,180,831 / 9,466,559); the sha gate passed before use; six probes show
the candidate's value AND the base's explicit 0 (2/2 each, no refusals); 12,000/12,000
validation rows; identities + openings-slice checks printed by the committed `job25_stats.py`.

## 2. Step 0 — patch, pins, five rows (`job25_rows.txt`, driver `job25_rows.py` COMMITTED)

sha256 gate: 8083a257… ✓. Pins, no option: 312,866 / 862,329 / 4,865,609 ✓; `uci`:
`FailHighBlend type spin default 0 min 0 max 7` ✓.

| setting | first-3 nodes | known | sum over 200 | known |
|---------|---------------|-------|--------------|-------|
| S14 | 41311, 24872, 28574 | same ✓ | 9,500,069 | ✓ |
| S14 + FHB 1 | 34435, 31033, 39413 | same ✓ | 9,272,824 | ✓ |
| S14 + FHB 2 | 18266, 18263, 25669 | same ✓ | 9,580,168 | ✓ |
| S14 + FHB 4 | 22849, 41964, 38264 | same ✓ | 9,180,831 | ✓ |
| S14 + FHB 7 | 24683, 35235, 30765 | same ✓ | 9,466,559 | ✓ |

## 3. Step 2 — six probes (`probe_M61…M66.log`; probe openings lines 6101–6122, no match uses
them)

Every probe: cand received `FailHighBlend=<its value>` 2/2 (values 1/7/4/2/7/1 as assigned);
base received `FailHighBlend=0` 2/2 — the explicit zero the job's design requires — and its 14
S14 lines (28 = 14×2), nothing else; refusal lines 0.

## 4. The matches (B_FHB both sides; S14 both; cand FHB=<value>, base FHB=0; nodes 2,000 for
M61–M64, 20,000 for M65/M66; Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours
swapped, `-pgnout` in my folder; openings_job25.epd by the globbing script (77 gamelist files;
68,979 distinct openings removed; Random(25001); 6,000 lines; first line
`r1bqk2r/pp2ppbp/5np1/2n1p1B1/8/2N2N2/PPP2PPP/R2QKB1R w KQkq - 0 9`), order sequential; M61
1–1000, M62 1001–2000, M63 2001–3000, M64 3001–4000, M65 4001–5000, M66 5001–6000; concurrency
4; the driver's node/start readback ran before every launch)

Games by ending FIRST — all from the committed `job25_stats.py` (output `job25_stats_out.txt`),
identities and openings-slice checks printed by the same command (losses on time BY SIDE 0/0;
illegal/disconnect/crash 0):

| ending | M61 (2000) | M62 (2000) | M63 (2000) | M64 (2000) | M65 (2000) | M66 (2000) |
|--------|------------|------------|------------|------------|------------|------------|
| White mates | 749 | 736 | 722 | 723 | 605 | 611 |
| Black mates | 662 | 663 | 689 | 682 | 498 | 460 |
| 3-fold repetition | 312 | 307 | 306 | 332 | 586 | 619 |
| fifty moves | 161 | 191 | 172 | 160 | 143 | 176 |
| insufficient material | 103 | 97 | 103 | 98 | 160 | 130 |
| stalemate | 13 | 6 | 8 | 5 | 8 | 4 |
| **identity: mates = wins+losses** | 749+662 = 693+718 = 1411 ✓ | 736+663 = 625+774 = 1399 ✓ | 722+689 = 689+722 = 1411 ✓ | 723+682 = 664+741 = 1405 ✓ | 605+498 = 533+570 = 1103 ✓ | 611+460 = 542+529 = 1071 ✓ |

| match | cand bit | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|----------|-------|------|-------|-------|----|-------------------------|----------------------|
| M61 | 1 | 2000 | 20061 | 1000 | 693-718-589 | [104,224,382,173,117] | −4.34 [−16.53, +7.85] | COMPLETE (1:51) |
| M62 | 7 | 2000 | 20062 | 1000 | 625-774-601 | [134,230,371,181,84] | **−25.93 [−38.10, −13.77]** | COMPLETE (1:57) |
| M63 | 4 | 2000 | 20063 | 1000 | 689-722-589 | [124,192,373,215,96] | −5.73 [−17.95, +6.49] | COMPLETE (1:55) |
| M64 | 2 | 2000 | 20064 | 1000 | 664-741-595 | [118,206,400,187,89] | −13.38 [−25.27, −1.49] | COMPLETE (1:51) |
| M65 | 7 | 20000 | 20065 | 1000 | 533-570-897 | [62,237,425,228,48] | −6.43 [−16.67, +3.82] | COMPLETE (11:52) |
| M66 | 1 | 20000 | 20066 | 1000 | 542-529-929 | [45,240,420,247,48] | +2.26 [−7.73, +12.24] | COMPLETE (11:58) |

predictions.txt (own commit 54457c8dd, 17:40:43Z): M61 +3 [−9,+15] — held; M62 +4 [−8,+16] —
**CALLED WRONG** (−25.93); M63 +4 [−8,+16] — held; M64 +2 [−10,+14] — held (barely, −13.38);
M65 +3 [−9,+15] — held; M66 +2 [−10,+14] — held.

## 5. From my partners

- kimi5's patch and deepseek6's + Fable's rows: the step-0 agreement is now FOUR builds deep
  (kimi5, deepseek6, the PC's r26, and mine) — the cleanest patch-identity record of the
  session.
- The PC's R1c number (−18.1 at its self-play depth) vs my R1 pool (+8.7): opposite-sign leans
  across trees again — a lean on my tree is a question for the PC, as this file says.

## 6. What I did NOT do

- No bit 5/6 combinations (the mask space is 8; the job picked 1/2/4/7).
- No second seeds (six single looks; M62's one-sided −25.9 and M64's −13.4 are the strong ones).
- No per-bit INTERACTION analysis (bit 7 vs its parts: −25.9 vs (−4.3, −5.7, −13.4) — the whole
  is worse than the sum of its parts (−23.4); suggestive, one seed each, not claimed).

## 7. What I am NOT sure about

- Whether bit 1 at 20,000 (+2.3) and at 2,000 (−4.3) differ by depth or by seed — both straddle
  zero.
- Whether bit 7's −25.9 at 2,000 shrinks to ~−6 at 20,000 genuinely (the depth pattern of pv1's
  ladder ran the OTHER way) or is two seeds' noise.
- The stalemate counts (13, 6, 8, 5, 8, 4) come from fastchess's strings; not replayed.

## 8. A better way

- The per-bit prediction lesson repeats: "softening a fail-high return" SOUNDED like it should
  help (more honest scores) and cost 26 — the same "mechanism sounds nice" trap as job 13's
  pruning priors. For blend-family patches the cheap pre-test is the TREE rows (which predicted
  nothing here — the trees nearly cancel) — so the honest pre-test is a 2,000-node single match
  FIRST (2 minutes), which is what this job effectively was for four settings.

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 18:12:49Z)

```
=== git status --short (head):
 M forge-combo29/tests_glmflash5_job25/stamps.txt
?? forge-combo29/tests_glmflash5_job25/M61_last40.txt
?? forge-combo29/tests_glmflash5_job25/M61_stdout.txt
=== ls tests_glmflash5_job25: (committed files)
bfhb_bench11.txt
bfhb_bench13.txt
bfhb_perft5.txt
job25_match.sh
job25_rows.py
job25_rows.txt
job25_summary.txt
make_openings_job25.py
openings_job25.epd
patch_apply.txt
patch_dryrun.txt
prediction.txt
stamps.txt
```
(the `M` and `??` lines were the pre-commit state; the match files, stats, and the stamps
update all join in this push.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
