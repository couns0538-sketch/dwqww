# REPORT glmflash5 — JOB 8 — LmrDeeperShallower's saving half alone, 20,000 nodes, PATCHED exe

Branch `cursor/glmflash5-work-cb5c`. times: `tests_glmflash5_job8/stamps.txt` (pasted below);
nothing typed. Patch applied to a COPY (`/tmp/patch8root`, repo-root layout because the patch's
paths are `forge-combo29/...`), never to the repo.

## 1. What was asked, the answer, how sure

Asked: does the SAVING half of LmrDeeperShallower alone ("shal" = LmrDeeperShallower true +
LmrDeeperBase 100000, deeper can never fire) do as well as the whole switch did on this tree
(older matches +13.2 and +2.6 at 20,000 nodes; pooled +7.2 [−1.0, +15.3])?

Answer: **shal alone: −4.0 Elo, 95 % pair interval [−14.9, +6.9], 1,000 pairs (2,000 games,
COMPLETE — finished in 11:24, no cut needed), 20,000 nodes, built-in net, PATCHED exe.** Against
the whole switch's older pool (+7.2 [−1.0, +15.3]) the point estimates differ by −11.2 with the
difference interval [−24.8, +2.4] — zero is inside, so "equal" is not excluded, but both point
estimates say the saving half alone is the weaker arrangement, as predicted. **My prediction
(−2, wrong outside [−14, +10]) was not called wrong: −4.00 is inside.**

How sure: the identity chain is exact to the node (four known rows reproduced exactly, including
the BASE control row), the probe counts are 10/10 − 0 − 0, and the match is COMPLETE with every
row validated. One seed = one look: this is a first look at shal-alone, not a verdict.

## 2. Step 1 — four known rows, all exact (raw files committed)

`go depth 12`, Threads 1, Hash 16, ucinewgame + isready before every go, first three lines of
kimi5's `tests_kimi5_job4/first200.fens`:

| run | nodes (3 positions) | Fable's known answer | file |
|-----|---------------------|----------------------|------|
| PATCHED, no option | 18407, 25756, 64000 | same ✓ | identity_P_none.txt |
| PATCHED, on (LmrDeeperShallower=true) | 26641, 30896, 68347 | same ✓ | identity_P_on.txt |
| PATCHED, shal (on + LmrDeeperBase=100000) | 32353, 38250, 68550 | same ✓ | identity_P_shal.txt |
| BASE, shal | 26641, 30896, 68347 (= the "on" numbers — the control) | same ✓ | identity_B_shal.txt |

The control's engine answer, pasted from the run's log: `info string unknown option LmrDeeperBase`
— on BASE, "shal" is silently the whole switch; the known-answer table is what catches that.

PATCHED build: patch applied --check OK / apply OK (`patch_apply8.txt`); sha256 BASE
e06310ec…, PATCHED fb9152ca… (`exe_sha256_8.txt`; an earlier apply attempt silently produced a
BASE-identical binary — caught by the option counts before anything ran, layout fixed, redone);
all four new option names in PATCHED's `uci` list, count 1 each (`uci_patched8.txt`); PATCHED
with no option: bench 11/13/16 = 312866/862329/3024920, perft 5 = 4865609 — all four exact
(`p8_bench*.txt`, `p8_perft5.txt`).

## 3. M1: games by ending FIRST (2,000 games)

| ending | count |
|--------|-------|
| White mates | 635 |
| Draw by 3-fold repetition | 553 |
| Black mates | 536 |
| Draw by insufficient mating material | 145 |
| Draw by fifty moves rule | 127 |
| Draw by stalemate | 4 |
| loss on time cand / base | 0 / 0 (fixed nodes, no clock — none possible, checked anyway) |
| illegal / disconnect / crash | 0 / 0 / 0 |

W-L-D (cand) 574-597-829; pairs 1,000; n5 = [71, 245, 387, 230, 67] (equals fastchess's own
Ptnml line); **Elo −4.00, 95 % pair interval [−14.91, +6.92]** (fastchess: −4.00 ± 10.91, LOS
23.64 % — same numbers); **COMPLETE** (2,000 of 2,000; fastchess total 00:11:24).
Validation line: 2000/2000 gamelist rows equal fastchess's own "Finished game" lines, 0
mismatches. fastchess's last 40 lines: `M1_last40.txt`.

Command (also `cmd_M1.txt`): cand = PATCHED with `option.LmrDeeperShallower=true
option.LmrDeeperBase=100000`; base = PATCHED no option; `-each proto=uci nodes=20000`;
`-openings file=openings_job8.epd format=epd order=sequential -srand 9350 -rounds 1000 -games 2
-repeat -concurrency 4 -recover -ratinginterval 100 -pgnout file=M1.pgn min=true`.
Openings: book lines minus the openings used in jobs 2, 3, 5, 6, 7 (2,007 distinct removed;
2,630,029 left; Random(9800) shuffle; 5,000 written) — first line
`r1bqk1nr/ppp2ppp/2np4/2b1p3/2P1P2P/2NP4/PP3PP1/R1BQKBNR b KQkq - 0 5`, order sequential.

## 4. Step 2 — the probe (three counts, as the job names them)

Ten games, PATCHED both sides, cand shal, base none, nodes=20000, log with engine I/O
(`probe_M1.log`): **cand received LmrDeeperShallower=true 10/10 and LmrDeeperBase=100000 10/10;
base received neither (0); lines holding `unknown option` or `invalid value`: 0.** (The probe
reused openings_job7.epd lines 1–10 for delivery only — a probe measures nothing; noted here.)

## 5. From my partners

- kimi5's patch is the object; its four options reproduce its intended semantics exactly on my
  machine (the four rows above ARE its numbers, from my build).
- deepseek5's job-11 fault (harness started a different exe than named) is the fault class my
  near-miss this job belonged to (first apply attempt → BASE-identical sha256); the sha256 pair
  in the evidence now stands between every patched job and that fault.
- Opus's SoundMatePruning two-seed result (−13.4, −17.0 on the owner's PC): noted — my job 1
  called SMP "inside the error" ALONE at my settings; the owner's rule (no single result closes
  an idea) cuts both ways, and these rows go into the same ledger.

## 6. What I did NOT do

- No second seed for shal-alone (one look; the pooled comparison with the older whole-switch
  matches mixes trees? NO — same tree 6b98f217, but THEIR seeds/openings differ; the pool
  +7.2 is Fable's number, I recompute nothing from it).
- No per-move time table (fixed nodes; not asked).
- Did not test the OTHER three new options (LmrDeeperDepthMul, LmrShallowerBase,
  LmrShallowerDepthMul) beyond their presence in the uci list.
- The probe reused job 7's opening lines 1–10 (delivery-only; the MATCH openings are fresh).

## 7. What I am NOT sure about

- The sentence "shal alone is worse than the whole switch": supported by point estimates
  (−4.0 vs +7.2), NOT settled (difference interval includes zero; different seeds and openings
  between the looks). 1,000 pairs make it a strong single look, no more.
- Whether shal's −4.0 is itself real (interval includes zero).
- The first apply attempt: could the failed apply have left PARTIAL edits? No — `git apply`
  without `--check` never ran in that attempt (only --check, which failed atomically); the
  sha256 equality confirms the tree was untouched.

## 8. A better way

- The four known-answer rows now exist as a REUSABLE script (`single_searches.py` lineage, this
  job's inline driver committed as identity driver in the folder); every patched-build job
  should run it FIRST — it is 3 seconds and it catches the wrong-exe fault class at birth.
- kimi5's patch paths assume the repo root; a one-line note in the patch header ("apply from the
  repository root") would have saved my first attempt — text patches should name their apply
  directory.

## 9. UTC stamps (pasted verbatim from stamps.txt)

```
2026-11-16T07:59:36Z job 8 file read; step 1 begins
2026-11-16T08:01:14Z step 1 done (all pins + four known rows exact; unknown-option line captured)
2026-11-16T08:01:20Z probe done rc=0
2026-11-16T08:01:25Z prediction.txt + openings_job8.epd done
2026-11-16T08:01:28Z cmd_M1.txt written; launching M1 (1000 pairs, may finish before minute 40)
2026-11-16T08:12:52Z M1 finished rc=0 after 684s
2026-11-16T08:12:56Z M1 stats done (2000 games complete)
```

## 10. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
