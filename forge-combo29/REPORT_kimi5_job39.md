# kimi5 job 39 report — THE LONE-KING GUARD (fixed value for a lone king vs mating material, behind a switch, off by default)

The report's first lines, in file 39's order:

**(1) Step 0.** Eight of eight numbers exact on the plain build (`kimi5/job39/step0/none_bench11.txt`
312866, `none_bench13.txt` 862329, `none_bench16.txt` 3024920, `none_perft5.txt` 4865609,
`s14_bench11.txt` 242796, `s14_bench13.txt` 656517, `pc20_bench11.txt` 278024, `pc20_bench13.txt`
587276; inputs in `step0/*_input.log`, exe sha256 `step0/exe.sha256` = 068f0927…, byte-identical to
job 17's PC-build exe). K2 OFF: **25 of 25 rows equal theirs** (`step0/k2off_plain.rows`; e.g. Q1 907,
Q6 653, C1 212, S1 −574, N6 1066). K3 at go softnodes 2000: sha256
`040f957213f8a24ee7176d439e3a8adc0e3a42b391c968cd5e9e3f380f122e53` = theirs
(`k3/plain_sn2000.txt`; counts mate 82 (KQ 43, KR 35, KBN 4), fifty 96, repetition 2, plies 12,888).

**(2) Step 1** in `kimi5/job39/step1_reading.md` (chain 6b98f217 + pc_r15 d6bd72c5…,
`-DFORGE_MATE_ALPHA_GUARD=1`): DeadMaterial replaces the evaluation at `src/eval.cpp:587-592`
(`Evaluator::static_eval_components`, printed by `eval` at `src/uci.cpp:742-746`),
`src/search.cpp:1178-1181` (top of `Worker::static_evaluate`, before the net branch at 1182) and
`src/search.cpp:1292-1295` (top of `Worker::corrected_eval`); the option's `uci` line
`src/uci.cpp:345`, its parsing `src/uci.cpp:538-542` with `searcher.clear_hash()` on change (542);
every other static-eval path (quiescence stand-pat 1668-1669, main node 1871-1872, ProbCut
1827-1832 incl. the TT-stored eval, null move and razoring reading the node's `eval`) goes through
those two functions; clamps at `src/search.cpp:553-555`/`634-636` (int16 TT store — values
2,000–13,000 fit), 1231/1323 (±MateInMaxPly−1, after the early return), `search.hpp:74-79`
(is_mate_score ±31,872 — never crossed), plus AspDecisiveScore 640 (2445-2453), EvalSwingMax 200
(1894) and `rule50_damped_static` (`search.hpp:362-367`, identity while EvalRule50Damp is false,
which PC20 never sets). The PC line confirmed: `eval` with a v3 net prints the net's own value and
never reaches static_eval_components (`src/uci.cpp:730-740` `#if FORGE_NNUE_V3`, compiled out on
this chain), so on the PC the guard shows in a search, not in `eval`.

**(3) Step 2.** Patch `kimi5/job39/lone_king_guard.patch.txt` (unified diff against 6b98f217 +
pc_r15, applies with `patch -p1 -F0` zero fuzz; plant copy `lone_king_guard_plant.patch.txt`).
Switch OFF, go depth 12: **O 200 of 200 rows equal, G 353 of 353 rows equal** to my plain rows
(depth, nodes, bestmove; `s2/plainO.rows` vs `s2/patoffO.rows`, `s2/plainG.rows` vs
`s2/patoffG.rows`); K5 node sums on the plain build O 8,315,168 and G 17,611,204 exact. Switch ON,
set O: **200 of 200 equal** (their reading confirmed: no lone king within a depth-12 opening tree).
Switch ON, set G: **95 of 353 rows differ** — every one listed with its piece count per side in
`s2/on_g_diff.tsv` (a finding, not a stop: G holds positions few captures from a lone king, and the
guard fires inside those trees; e.g. pos 6 W6/B2 11,797→8,489 nodes, same best move).

**(4) Step 3.** K2 on the patched build: OFF **25 of 25 = my Step 0 rows** (`step0/k2off_pat.rows`);
ON **25 of 25 = K2's ON column** (`step0/k2on_pat.rows`: Q1 2960 … Q6 3300, R1 2560 … R6 2900, C1
3050, C2 2700, C3 3000, L1 −3300, S1 0 (stalemate), P1 3000, N1–N7 the OFF values). The patch is
the formula.

**(5) Controls.** C-ARRIVE: the ON run with `LoneKingGuardX` stopped at the engine's refusal line
`info string unknown option LoneKingGuardX` (`ctrl/carrive_full.txt`), no table written, exit 2 —
PASS. C-OFF: patched build, switch off, K3 sha256 `040f9572…122e53` at go softnodes 2000
(`coff/coff_sn2000.txt`) and `2b4c55fd…a67d07` at go nodes 50000 (`games/off_n50000.txt`) — both
equal my plain build's (= theirs) — PASS at both limits. C-PLANT: the planted exe (`100 * edge`,
the lone king driven to the centre) changes **exactly the 15 rows of K6 with K6's values** (Q1
3260, Q2 3300, Q3 2900, Q4 3000, Q5 2900, Q6 3000, R1 2860, R2 2900, R3 2500, R4 2600, R5 2500,
R6 2600, C3 2700, L1 −3000, P1 2700) and keeps the other 10 (C1 3050, C2 2700, S1 0, N1–N7)
(`ctrl/cplant_k2on.rows`) — PASS. Exe sha256s: plain 068f0927…, guard 4c08a568…, plant 1adc8631….

**(6) The prediction, graded cell by cell** (`kimi5/job39/prediction.txt`, own commit 21:11:37Z
after the controls, before Step 4's first ON game (21:11:54Z recorded mtime), never edited):

| cell | predicted | measured | inside? |
|---|---|---|---|
| KQ mates sn2000 | 58-60 | 60 | yes |
| KR mates sn2000 | 56-60 | 60 | yes |
| KBN mates sn2000 | 35-55 | 45 | yes |
| KQ mates n50000 | 58-60 | 60 | yes |
| KR mates n50000 | 59-60 | 60 | yes |
| KBN mates n50000 | 40-58 | 60 | NO — above |
| fifty endings sn2000 (180 games) | 5-30 | 13 | yes |
| ON KBN > DeadMaterial's 41 at sn2000 | yes | yes (45 > 41) | yes |

7 of 8 inside.

**(7) The Step 5 table and the readings** — `kimi5/job39/table_j39.py` (committed, prints how many
lines it read), output `kimi5/job39/step5_table.txt`:

| run | mates KQ /60 | KR /60 | KBN /60 | fifty | repetition | stalemate | insufficient | cap | plies sum | mean plies mated KQ | KR | KBN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFF (ours, K3) sn2000 | 43 | 35 | 4 | 96 | 2 | 0 | 0 | 0 | 12888 | n/a | n/a | n/a |
| OFF (yours) sn2000 | 43 | 35 | 4 | 96 | 2 | 0 | 0 | 0 | 12888 | 31.8 | 45.5 | 31.2 |
| DeadMaterial (ours, K4) sn2000 | 43 | 35 | 41 | 60 | 1 | 0 | 0 | 0 | 11707 | n/a | n/a | n/a |
| ON sn2000 | 60 | 60 | 45 | 13 | 2 | 0 | 0 | 0 | 6692 | 13.5 | 23.6 | 65.9 |
| C-PLANT ON sn2000 (KQ+KR only) | 52 | 51 | — | 16 | 1 | 0 | 0 | 0 | 5362 | 24.8 | 46.5 | — |
| OFF (ours, K3) n50000 | 59 | 60 | 23 | 35 | 3 | 0 | 0 | 0 | 8295 | n/a | n/a | n/a |
| OFF (yours) n50000 | 59 | 60 | 23 | 35 | 3 | 0 | 0 | 0 | 8295 | 18.9 | 32.9 | 61.1 |
| ON n50000 | 60 | 60 | 60 | 0 | 0 | 0 | 0 | 0 | 5696 | 12.6 | 21.7 | 60.6 |

Every ON game that did not end in mate: 15 at sn2000 (13 fifty + 2 repetition, all KBN, all at 100
plies — listed with start and final FENs in `step5_table.txt`); 0 at n50000.

The readings:
- ON sn2000 mates KQ 60/60 and KR 60/60 (bar ≥ 58 of 60 for both): **THE GUARD MATES.**
- C-OFF holds at both limits and Step 2's OFF rows are equal on O (200/200) and G (353/353):
  **THE GUARD IS FREE AT ITS DEFAULT.**
- KBN: ON 45 against DeadMaterial's 41 at sn2000 (counts; no verdict per file 39 — the 15 KBN
  non-mates all ran into the fifty-move rule at exactly 100 plies, mean mated plies 65.9).

---

## 1. Three plain lines
- Asked: build the lone-king guard as a text patch behind a switch that is off by default, prove it
  is the formula (25 `eval` rows OFF and ON), prove it free at its default (rows, games, both
  limits), survive three controls, predict, then measure the 180 bare-king games ON at two limits.
- Answer: done, everything passed. THE GUARD MATES (KQ 60/60, KR 60/60 at softnodes 2000; 180 of
  180 at nodes 50,000); it is free at its default; KBN 45 vs DeadMaterial's 41; the centre-plant
  mates fewer (52+51 of 120) than the true guard (120 of 120 on the same starts).
- Sure: high — every known answer reproduced to the row/hash before the patch was judged, the
  harness proved itself on a real unknown option, and the plant proved the harness sees the term.

## 2. The known numbers of step 0 (raw files)
`kimi5/job39/step0/none_bench11.txt` 312866, `none_bench13.txt` 862329, `none_bench16.txt`
3024920, `none_perft5.txt` 4865609, `s14_bench11.txt` 242796, `s14_bench13.txt` 656517,
`pc20_bench11.txt` 278024, `pc20_bench13.txt` 587276 — all exact; `step0/exe.sha256`, inputs
`step0/*_input.log`. K2 OFF `step0/k2off_plain.{rows,txt}` 25/25; K3 `k3/plain_sn2000.txt` sha256
040f9572… = theirs.

## 3. Steps
| step | done | evidence | result |
|---|---|---|---|
| 0 eight numbers | done | `step0/*.txt` | 8/8 exact |
| 0 K2 OFF | done | `step0/k2off_plain.rows` | 25/25 = theirs |
| 0 K3 sn2000 | done | `k3/plain_sn2000.txt` | sha256 = theirs |
| 1 reading | done | `step1_reading.md` | file:line, committed before Step 2's runs |
| 2 patch + OFF proof | done | `lone_king_guard.patch.txt`, `s2/` | O 200/200, G 353/353 equal; K5 sums exact |
| 2 ON on O/G | done | `s2/patonO.rows`, `s2/patonG.rows`, `s2/on_g_diff.tsv` | O 200/200 equal; G 95 differ, listed |
| 3 K2 OFF/ON patched | done | `step0/k2off_pat.rows`, `step0/k2on_pat.rows` | 25/25 OFF, 25/25 ON = formula |
| C-ARRIVE | done | `ctrl/carrive_*` | refusal line, no table, exit 2 |
| C-OFF both limits | done | `coff/coff_sn2000.txt`, `games/off_n50000.txt` | sha256 = plain at both |
| C-PLANT K2 + 120 games | done | `ctrl/cplant_k2on.rows`, `games/plant_on_sn2000.txt` | exactly K6's 15 rows; 103 mates |
| prediction | done | `prediction.txt` | 7 of 8 inside |
| 4 four game runs | done | `games/*.txt` | all finished, none unfinished |
| 5 table + readings | done | `table_j39.py`, `step5_table.txt` | above |

## 4. Findings (each with file:line and a showing command)
- F1: the guard fires FIRST at all three replacement sites, before DeadMaterial's lines which stay
  as they are: `src/eval.cpp:586-597` (patched tree), `src/search.cpp:1178-1185`, `1292-1299`; the
  patch hunks are `lone_king_guard.patch.txt` lines 34-100. Show: `grep -n "lone_king_guard"
  src/eval.cpp src/search.cpp src/uci.cpp` on the patched tree.
- F2: the switch arrives and clears the hash on change only: patched `src/uci.cpp` option line
  after DeadMaterial's (`"option name LoneKingGuard type check default false"`), parse block
  mirroring DeadMaterial's (`searcher.clear_hash()` in the change branch). Show: `printf 'uci\nquit\n'
  | build-guard/forge | grep LoneKingGuard`; C-ARRIVE's `ctrl/carrive_full.txt` shows the misspell
  refused.
- F3: stalemate is the guard's own line: S1 (`7k/5Q2/6K1/8/8/8/8/8 b`) evaluates to exactly 0 with
  the switch ON (`step0/k2on_pat.rows`), because the lone side to move, not in check, no legal move
  → 0 (`board.legal_moves().size() == 0` in the guard).
- F4: ON changes 95 of 353 G rows at depth 12 (0 of 200 O rows): `s2/on_g_diff.tsv`. The changed
  positions are not themselves guarded; their trees reach guarded positions within 12 plies (piece
  counts per side in the file; e.g. pos 33 W3/B4 changed by one node).
- F5: ON at sn2000, the 15 KBN non-mates ALL end at exactly 100 plies (13 fifty, 2 repetition;
  `step5_table.txt`): the corner drive mates (mean 65.9 plies) but the tightest starts brush the
  fifty-move clock, exactly file 39's warning.
- F6: the planted centre drive still mates 103 of 120 KQ/KR (52 KQ, 51 KR) — driving the king to
  the centre is worth −17 mates of 120 against the true guard's 120 of 120 on the same starts
  (`games/plant_on_sn2000.txt` vs `games/on_sn2000.txt`).
Suspected, not proven:
- S1: the two ON sn2000 repetition endings (`step5_table.txt`) look like the drive oscillating
  between two equally-valued squares near the corner; not analyzed per-move (no per-move evals
  recorded). A repetition penalty inside the guarded region would presumably cure it, at a price.

## 5. From my colleagues
- deepseek5 (branch tip 731fc808, NOTES read, newest report `REPORT_deepseek5_job30.md` read): its
  stand5 runner (`tests_deepseek5_stand5/stand5_run.py`) is the template of my `games_k3.py` —
  moves from the START position every move, python-chess re-derives every ending; applied, with file
  39's judging order (repetition before fifty). Its job-15 file `run2000_none.games` (sha256
  abd97e81…, verified) is this job's 180 starts. Its note that CounterMove's history entry rates
  worse than Killer2 (298-302 vs 170-206 per 1,000) does not touch this job.
- glmflash5: branch `for-fable-and-opus/glmflash5-work` does not exist ("couldn't find remote ref";
  checked at step-2 time). Nothing to read; said here as the job asks.

## 6. What I did NOT do
- No per-move analysis of the 2 repetition endings (S1 above). No tune of the guard's weights (the
  job fixes the formula). No run with DeadMaterial AND LoneKingGuard both on (not asked; the guard
  fires first wherever both would). No match against the engine as it is — that is the PC's step.
- pc20_all1024.opt was NOT usable on my chain: its four HistoryAge* lines do not exist here
  (`info string unknown option HistoryAgeMain`, recorded in the first refused K3 attempt's logs);
  per job 37's MET base I used pc20.opt (the 20 PC20 options) + Threads 1 + Hash 16 everywhere the
  job says PC20. Job 38's K7 cells matched theirs with the all1024 file because the engine ignores
  the unknown lines with an info line; my runners treat that line as a stop.

## 7. What I am NOT sure about
- Whether a guard value between 2,000 and 13,000 stored in the TT as `eval` (int16, fits) can
  mislead a LATER search whose root position is not itself guarded but reads that stored eval in a
  different material context (the key includes the board, so only transpositions reach it; the
  value is the position's true guard value then — I see no leak, but I did not construct a test).
- The KBN n50000 prediction miss (60, range 40-58): I under-read how much 50,000 nodes plus the
  corner drive dominate the fifty clock (mean mated plies 60.6, max under 100). Not a defect in
  the guard; a too-narrow range.

## 8. A better way
- The job's own K1 corner case keys the corner pair to the bishops' colour but the push weight is
  the same for a WRONG-colour corner as for no corner when bishops cover both colours; a
  two-line change (in the corner case, split `cd` over the two same-colour corners only — already
  done — and in the non-corner minor case with one bishop, drive to that bishop's colour corners)
  would extend the corner drive to K+B+N with mixed bishops. How to check it is better: replay the
  15 KBN non-mate starts (`step5_table.txt` lists them) at sn2000 against this patch; the count of
  fifty-endings must drop without any K2 row changing except C1/C2's corner-case twins. Not done:
  the job fixes the formula; written here for Fable.
- The ON-G 95-position list (`s2/on_g_diff.tsv`) is a free regression set for any future fixed
  value: run it at depth 12 ON/OFF, the diff must be contained in those 95 rows.

## What this check cannot see (file 39's text, as asked)
The PC's net and its engine build (with a v3 net `eval` shows the net's value, not the guard; the
PC tests the guard in its own games); go nodes beyond 50,000; more than one thread; Syzygy tables
(with them the PC's engine already mates 180 of 180); the clock; and whether it plays better: 20 of
12,000 gate games of rounds 73 to 75 (drawn with 16 bishop + knight, 3 two bishops, 1 bishop + rook
against a lone king) are the most it could change on the PC's net, about 0.1 % of the score, and
the PC's match decides that.

## 9. UTC stamps
See `kimi5/job39/stamps.txt` (start of the run first: claim commit 2026-11-20 21:03:03Z; two typed
lines corrected in-file with recorded .meta/mtime values).

## 10. Model
kimi-k3 (Kimi K3, runtime name as given).

`git status --short` and `ls -R` of the job folder as the last command before the report commit:
`M NOTES_kimi5.md`, `M kimi5/job39/stamps.txt`, untracked `REPORT_kimi5_job39.md`,
`kimi5/job39/games/`, `kimi5/job39/step5_table.txt`, `kimi5/job39/table_j39.py` — nothing else;
the job folder `forge-combo29/kimi5/job39/` holds `coff/ ctrl/ games/ k3/ s2/ step0/`,
`eval_k2.py`, `games_k3.py`, `table_j39.py`, `lone_king_guard.patch.txt`,
`lone_king_guard_plant.patch.txt`, `O.epd`, `G.epd`, `pc20.opt`, `pc20_lkg.opt`, `pc20_all1024.opt`,
`s14.opt`, `run2000_none.games`, `run2000_kqkr.games`, `step1_reading.md`, `prediction.txt`,
`step5_table.txt`, `stamps.txt`.
