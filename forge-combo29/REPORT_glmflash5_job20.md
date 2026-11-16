# REPORT glmflash5 — JOB 20 — the null-move gate's slope, by games under S14 (run A)

Branch `cursor/glmflash5-work-cb5c` — run A (branch file check: `git branch --show-current` =
`cursor/glmflash5-work-cb5c`; Part B belongs to the other run). Exe B9 = a CLEAN copy of
6b98f217 + kimi5's `tests_kimi5_job9/NodeLiterals.patch.txt` (114 lines; applied from the
REPOSITORY ROOT with `patch -p1 --fuzz=0`, dry-run and real outputs committed as
`patch_dryrun.txt` / `patch_apply.txt`, both rc=0). B9 sha256
f0daf1b6ec915311d998e1f0978befa77e3781bc54e0f91ee943668d0bcc1ead. Both matches COMPLETE.
times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: does the null-move static gate's slope that SHRINKS the tree on game positions (48) win
games at equal nodes, and does the slope that GROWS it (0) lose — under S14, 20,000 nodes.

Answer: **M42 (S14 + NullStaticSlope 48 vs S14): +5.21 Elo, 95 % PAIR interval [−4.87, +15.29],
1,000 pairs — level (one seed).** **M43 (S14 + NullStaticSlope 0 vs S14): −9.56 [−19.37, +0.25],
1,000 pairs — leaning negative; the interval just touches zero: disabling the gate costs
strength, at the edge of one seed's resolution. The default slope 24 sits between and is close
to slope 48 in strength.**

How sure: step 0 is exact to the node (the anchor 12,573,318; S14 9,500,069; S14+slope48
9,612,192 — the last equal to deepseek6's AND kimi5's rows); the uci line is exactly
`NullStaticSlope type spin default 24 min 0 max 100`; probes 2/2 with the right value and no
refusal line; 4,000/4,000 validation rows; identities printed under every table by the committed
command. Two single seeds.

## 2. Step 0 — the patch, the pins, the two rows (`job20_rows.txt`, driver `job20_rows.py`
COMMITTED; a first sed-mangled driver run produced void rows and was redone — the committed
driver and rows are the clean ones)

| setting | first-3 nodes | known | sum over 200 | known |
|---------|---------------|-------|--------------|-------|
| S14 | 41311, 24872, 28574 | same ✓ | 9,500,069 | ✓ |
| S14 + NullStaticSlope 48 | 18045, 19835, 39694 | same ✓ (deepseek6 = kimi5) | 9,612,192 | ✓ |

no option: bench 11 = 312,866, bench 13 = 862,329, bench 16 = 3,024,920, perft 5 = 4,865,609 —
all four exact (`b9_bench*.txt`, `b9_perft5.txt`); `uci`: NullStaticSlope count 1, line as
specified (`uci_note.txt`). Refusal lines: 0.

## 3. The probes (2 games each, per the first message's form; `probe_M42/M43.log`)

| probe | cand received | base received | refusals |
|-------|---------------|---------------|----------|
| M42 | `setoption name NullStaticSlope value 48` 2/2 | nothing (0) | 0 |
| M43 | `setoption name NullStaticSlope value 0` 2/2 | nothing (0) | 0 |

## 4. The matches (B9 both sides; S14 on both; the candidate's slope line on top; nodes=20000;
Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours swapped, `-pgnout` in my
folder; openings_job20.epd = book minus jobs 2,3,5–19 openings (48,859 distinct removed;
Random(11803); 2,200 lines; first line
`r2qk2r/ppp1bppp/3p1n2/4n3/4P3/2N2P1P/PPP2P2/R1BQKB1R w KQkq - 1 9`), order sequential; M42
lines 1–1000, M43 1001–2000; concurrency 4; `cmd_M42.txt` / `cmd_M43.txt` hold the exact
commands, written before each run)

Games by ending FIRST — from `gamelist_M*.txt` by the committed `job20_stats.py` (output
`job20_stats_out.txt`), identity printed by the same command (losses on time BY SIDE 0/0 —
fixed nodes; illegal/disconnect/crash 0):

| ending | M42 (2000) | M43 (2000) |
|--------|------------|------------|
| White mates | 580 | 597 |
| Black mates | 492 | 486 |
| 3-fold repetition | 630 | 622 |
| fifty moves | 159 | 162 |
| insufficient material | 131 | 129 |
| stalemate | 8 | 4 |
| **identity: mates = wins + losses** | 580+492 = 551+521 = 1072 ✓ | 597+486 = 514+569 = 1083 ✓ |

| match | cand | base | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|------|------|-------|-------|----|-------------------------|----------------------|
| M42 | S14+slope48 | S14 | 20042 | 1000 | 551-521-928 | [47,234,409,262,48] | +5.21 [−4.87, +15.29] | COMPLETE (12:09) |
| M43 | S14+slope0 | S14 | 20043 | 1000 | 514-569-917 | [53,248,436,227,36] | −9.56 [−19.37, +0.25] | COMPLETE (12:15) |

predictions.txt (before M42): M42 −2 [−14, +10] — held (+5.21); M43 −6 [−18, +6] — held
(−9.56).

## 5. From my partners

- deepseek6's NodeLiterals rows (its job on kimi5's patch) reproduce to the node on my B9 —
  three builds now agree on this patch's tree effects.
- kimi5's job-9 tree data (slope 48 → 0.908 on 353 game positions; slope 0 → 1.159) vs my BOOK
  rows (slope 48 → 1.012; slope 0 → not measured on book by me): the two position sets disagree
  in sign for slope 48 — the book-vs-game-position pattern again, now on the slope lever.
- Run B's lessons (file 20's head) apply to me too: pair intervals only; `-rounds` = pairs; a
  prediction + report for every match; PGNs stay outside the repo with a committed converter.

## 6. What I did NOT do

- No slope between 24 and 48 (the ladder question for this lever is open: 24 vs 48 head-to-head
  was not asked).
- No second seeds (one seed each, as planned).
- No games-position tree rows on MY side for slope 48 (the PC's 0.908 is kimi5's number on its
  353 positions; my 200 book positions said 1.012 — I did not build the G set).

## 7. What I am NOT sure about

- Whether slope 48's +5.2 is a real small gain or seed noise (interval crosses zero).
- Whether M43's −9.6 is the gate's full value or partly the tree's +15.9 % spending nodes
  differently at fixed nodes (the mechanism question is kimi5/deepseek5's to count).
- The book-vs-game position-set disagreement for slope 48's tree — I measured only book.

## 8. A better way

- The slope ladder (24 / 36 / 48 / 0) at 2,000 nodes would cost ~8 minutes total at my 2k rate
  and answer "is the default slope optimal" directly — the same ladder logic job 19 used for
  pv1's node dependence, here on a tuning constant.

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 15:10:40Z, after
the pin files were copied in)

```
=== git status --short:
?? forge-combo29/REPORT_glmflash5_job20.md
?? forge-combo29/tests_glmflash5_job20/
=== ls tests_glmflash5_job20:
b9_bench11.txt
b9_bench13.txt
b9_bench16.txt
b9_perft5.txt
cmd_M42.txt
cmd_M43.txt
config_M42.json
config_M43.json
exe_sha256_20.txt
gamelist_M42.txt
gamelist_M43.txt
job20_rows.py
job20_rows.txt
job20_stats_out.txt
job20_stats.py
job20_summary.txt
M42_last40.txt
M42_stdout.txt
M43_last40.txt
M43_stdout.txt
make_openings_job20.py
openings_job20.epd
patch_apply.txt
patch_dryrun.txt
prediction.txt
probe_M42.log
probe_M43.log
stamps.txt
uci_note.txt
```
(the two `??` lines are the report and the job folder before this commit.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c` — cloud agent apprentice to
Fable (away), read by Opus, paired with deepseek5, kimi5, deepseek6, and my own second run
(glmflash6, run B).
