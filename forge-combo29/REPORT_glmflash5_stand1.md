# REPORT glmflash5 — STANDING 1 — LmrDeeperShallower + ThreatHistory against none, two seeds

Branch `cursor/glmflash5-work-cb5c`. Exe = the session's plain default build (`/tmp/forgebuild/forge`,
sha256 e06310ec…, base tree 6b98f217; both switches exist on it — uci-checked in the probes).
Both matches COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked (the standing list's S1, first in line): the bundle LmrDeeperShallower=true +
ThreatHistory=true against none, twice — 1,500 games (750 pairs) per seed, 20,000 nodes.

Answer: **S1a (seed 9201): +6.02 [−5.91, +17.95]; S1b (seed 9202): +0.93 [−11.08, +12.93]; the
two-seed pool: +3.47 [−4.98, +11.93] over 1,500 pairs — the bundle is LEVEL on this tree at
20,000 nodes, built-in net, one seed pair.** Both seeds' point values sit inside my filed
prediction range ([−10, +14] per seed, point +2).

How sure: the probes delivered both option lines to the candidate 2/2 per match, base 0, refusal
lines 0; every table below comes from the committed `stand1_stats.py` with identities; 3,000/3,000
validation rows. The pool is the session's belief unit; it straddles zero.

## 2. Known numbers of step 0

The session's pins (312,866 / 862,329 / 3,024,920 / 4,865,609) hold on this exe (verified in
jobs 1, 5, 12, 17, 20 — same binary, sha256 e06310ec…). No new bench this job (the control-C
rule: one per session day — job 1's C ran today on this same exe).

## 3. Games by ending FIRST — from `gamelist_S1*.txt` by the committed `stand1_stats.py`
(output `stand1_stats_out.txt`); identity printed by the same command (losses on time BY SIDE
0/0 — fixed nodes; illegal/disconnect/crash 0):

| ending | S1a (1500) | S1b (1500) |
|--------|------------|------------|
| White mates | 464 | 460 |
| Black mates | 398 | 386 |
| 3-fold repetition | 421 | 441 |
| fifty moves | 111 | 99 |
| insufficient material | 99 | 109 |
| stalemate | 7 | 5 |
| **identity: mates = wins + losses** | 464+398 = 444+418 = 862 ✓ | 460+386 = 425+421 = 846 ✓ |

## 4. The matches (same exe both sides; cand = LmrDeeperShallower=true + ThreatHistory=true;
base = no option; nodes=20000; Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours
swapped, `-pgnout` in my folder; openings_stand1.epd = book minus ALL openings used in jobs
2,3,5–19 (50,859 distinct removed; Random(12003); 3,100 lines; first line
`r2qkb1r/pp1b1ppp/2np1n2/2p5/2P1P3/2N2P2/PPN3PP/R1BQKB1R b KQkq - 3 8`), order sequential; S1a
lines 1–750, S1b 751–1500; probes 1551–1554; concurrency 4; exact commands in `cmd_S1a.txt` /
`cmd_S1b.txt`, written before each run)

| match | seed | pairs | W-L-D | n5 | Elo, 95 % pair interval | complete? (duration) |
|-------|------|-------|-------|----|-------------------------|----------------------|
| S1a | 9201 | 750 | 444-418-638 | [35,179,309,179,48] | +6.02 [−5.91, +17.95] | COMPLETE (9:06) |
| S1b | 9202 | 750 | 425-421-654 | [41,185,292,193,39] | +0.93 [−11.08, +12.93] | COMPLETE (9:16) |
| **pool** | — | **1500** | 869-839-1292 | [76,364,601,372,87] | **+3.47 [−4.98, +11.93]** | — |

Context beside it (my tree, 20,000 nodes, defaults): the whole switch LmrDeeperShallower alone
pooled +1.3 ± 6.5 (Opus's recount of jobs 8–11's direct looks); this bundle (the switch PLUS
ThreatHistory) pools +3.5 [−5.0, +11.9] — same story: level.

## 5. From my partners

- No new partner numbers were used this job (no file arrived; the standing job ran from the
  original list). The probes' refusal-count guard stayed 0.

## 6. What I did NOT do

- No third seed (the pool straddles zero; S1 is "level" as measured — the standing list does not
  ask for more).
- No ThreatHistory-ALONE match (the bundle was the job; the switch's own halves are mapped in
  jobs 8–11).
- No 2,000-node variant of the bundle (not asked; the ladder method exists if wanted).

## 7. What I am NOT sure about

- Whether the bundle's +3.5 hides a small real gain (interval [−5.0, +11.9] — one seed pair).
- Whether ThreatHistory adds anything ON TOP of the switch (no switch-alone-vs-bundle match —
  that would be the sharper question; not asked by the standing list).

## 8. A better way

- Standing jobs that name a BUNDLE should name the head-to-head against the bundle's biggest
  component (here: bundle vs LmrDeeperShallower-alone) — "does the second switch add anything"
  is the question a tuning session actually needs; vs-none answers a different one.

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 15:40:47Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_stand1/
=== ls tests_glmflash5_stand1:
cmd_S1a.txt
cmd_S1b.txt
config_S1a.json
config_S1b.json
gamelist_S1a.txt
gamelist_S1b.txt
make_openings_stand1.py
openings_stand1.epd
prediction.txt
probe_S1a.log
probe_S1b.log
S1a_last40.txt
S1a_stdout.txt
S1b_last40.txt
S1b_stdout.txt
stamps.txt
stand1_stats_out.txt
stand1_stats.py
```
(the `??` line is the job folder before this commit; the report file joins it in this push.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
