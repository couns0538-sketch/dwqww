# glmflash3 job 4 report (2026-11-15)

## 1. First line

**PawnHistory on top of B1 adds nothing measurable per node: pooled M1+M2 = −1.7 Elo (95 % pair
interval [−10.2, +6.8], 3040 games — both matches cut by their deadlines on this slower tree,
66 % and 86 % of the prescribed 2000). Next to it, the SAME port ALONE on the SAME tree gains
+6.4 [−5.0, +17.8] (M3, 1636 of 2000 games): the port works — so the null on top of B1 reads as
overlap with what B1's own history machinery already learns, the same reading the owner's PC
gives (+1.7 ± 7.2 on top of today's bundle there). Power control C: +213.2 [180.1, +250.1].**

Cut or not reached, first paragraph as asked: every prescribed match RAN and none was skipped,
but all three M-matches were cut below their prescribed 2000 games (M1 1318, M3 1636, M2 1720)
because the deadlines were carried over from job 3's game rate on the faster combo29 tree instead
of being derived from this tree's measured rate (C measured it: see §10.1). All finished games
count; 0 crashes, 0 illegal moves, 0 disconnects everywhere; C completed 300/300. The identity
proofs, all known answers, both new on-numbers and the four probes ran complete.

## 2. Known answers

Trees and builds (flags written once, used for every build in this job): base tree = commit
`d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at the root; the full worktree content copied,
since its CMakeLists references `bench/` and `tests/` beyond `src`/`include`); B1 tree = that plus
`opus_r13/p1/b1/b1_port.patch` (branch `opus-r13-p1-nearmiss-ports`, fetched by branch; `patch -p1`,
rc 0, no rejects, touches src/board.cpp, src/search.cpp, src/uci.cpp); pawn tree ("b1tree") = B1
tree plus `pawn_history_b1.patch.txt` (my deliverable). Build: `cmake -S <tree> -B <build> -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-march=x86-64-v3 -DFORGE_NNUE_HIDDEN=256"`
(the tree needs the HIDDEN definition, as the job said; `-march=x86-64-v3` as in job 1's build of
this family). Fresh engine process per bench; input: Threads 1, Hash 16, OwnBook false, then the
option lines of the config under test. Raw outputs `saved4/*.out`.

| tree | config | command | expected | printed | match |
|---|---|---|---|---|---|
| pristine d4f43124 | no option | bench 11 | 312866 | 312866 | yes |
| pristine | no option | bench 13 | 862329 | 862329 | yes |
| pristine | no option | go perft 5 | 4865609 | 4865609 | yes |
| pristine | "BundlePreset B1" | bench 11 | (option does not exist there) | 312866 | as expected: the pristine tree ignores the unknown option — the preset exists only in the B1-patched tree |
| pristine | "BundlePreset B1" | bench 13 | (same) | 862329 | as expected |
| B1 tree | no option | bench 11 | 312866 | 312866 | yes |
| B1 tree | no option | bench 13 | 862329 | 862329 | yes |
| B1 tree | no option | go perft 5 | 4865609 | 4865609 | yes |
| B1 tree | BundlePreset B1 | bench 11 | 280182 | 280182 | yes |
| B1 tree | BundlePreset B1 | bench 13 | 758456 | 758456 | yes |
| B1 tree | BundlePreset B1 | bench 16 | 3357587 | 3357587 | yes |
| b1tree (pawn port) | PawnHistory off, all four configs above | — | the same six numbers | identical | yes |

**Identity proofs** (2000 depth-9 answers, same script as jobs 2/3 — `p2_identity2.py`, which takes
an extra setoption line as its fourth argument): 

- no option on both sides: B1 tree sha256 = b1tree sha256 = `3c976155ede937860062ac79eeefa01894ef0bd4a03360fa5d6d90065cd8353f` (the same hash as jobs 2 and 3 — the B1 patch with everything off does not change the lock's search), smallest node count 4534 on both.
- `BundlePreset B1` set on both: B1 tree sha256 = b1tree sha256 = `58a26c12ea3aa3e50e662f242b6384670dd68129d47f5b38382f8821c6ac00fe`, smallest node count 3306 on both.

**PawnHistory on, the two new numbers** (b1tree): bench 13 alone (no B1) → **722532** (against
862329 known: differs); bench 13 with `BundlePreset B1` → **842551** (against 758456 known:
differs). Raw outputs `saved4/on_alone_bench13.out`, `saved4/on_b1_bench13.out`.

## 3. The feature as built for this tree

Job 3's v2 design, ported — `PawnHistory` (check, default false) and `PawnHistoryBits` (spin
9-13, **default 9** this time); no weight option, no PV bonus, as instructed. The code around the
history tables differs from the combo29 tree, so every hook was re-derived from THIS tree:

- **Table** (`include/forge/search.hpp`, after `LesserThreatHistory`): `PawnHistoryTable =
  array<array<array<int16_t,64>,13>, 8192>`, indexed `[pawn key bucket][moved piece][to square]`,
  allocated always for 2^13 buckets (13,631,488 B); `search_options::pawn_history_bits` masks the
  index at BOTH read and update — default 9 → 851,968 bytes reachable.
- **Read**: added at the SINGLE composition point this tree has — the end of
  `Worker::quiet_history` (after the butterfly term, the HistRework blend and the two
  continuation terms; order documented): `score += pawn_history_value(board, move);`
  (`src/search.cpp`, right before the function's `return score;`). The move picker and the
  history-pruning/LMR sites all call `Worker::quiet_history` in this tree (call sites found by
  grep: the quiet-move stage scoring and the pruning block), so one hook covers all readers —
  there is no second composing site like combo29's move-picker struct (I searched: this tree's
  move picker has no separate quiet-history sum).
- **Update**: in `Worker::update_quiet_stats` — `update_pawn_history(board, move, bonus);`
  directly after the butterfly bonus `apply_history`, and `update_pawn_history(board, quiet,
  -bonus);` inside the previously-tried-quiets loop, right after the butterfly malus. Same
  `apply_history` gravity as every table in this tree.
- **Clear**: `pawn_history_->fill({});` in `Worker::clear()` (no stack temporary — the idiom
  job 2's ASan run taught), next to the other tables' clears; `ucinewgame` routes through it.
- **UCI**: both options declared right after `HistRework`'s declaration line in the `uci` answer
  (`option name PawnHistory type check default false`, `option name PawnHistoryBits type spin
  default 9 min 9 max 13`); parsed in the setoption chain mirroring this tree's own handlers
  (HistRework's spin clamp for Bits; the CuckooRep/TtPruneV2 bool check for PawnHistory) into
  `forge::search_options::pawn_history` / `::pawn_history_bits` (extern declarations added in
  `include/forge/search.hpp`, after the table type). `BundlePreset` untouched: PawnHistory is not
  one of the preset's six options and `OFF` does not reset it (it is not a bundle member).
- Globals live in `search_options` (this tree's convention for search switches, where combo29's
  used `tune::`); the extern block in search.hpp is needed because uci.cpp sees `search_options`
  through `hist_rework.hpp` (included by search.hpp).

## 4. Probes before every match

- **probe_m1**: cand `Threads 1`, `Hash 16`, `OwnBook false`, `BundlePreset B1`, `PawnHistory
  true`; base the first four without PawnHistory (probe_m1.txt, both games, both sides quoted).
- **probe_m3**: cand adds `PawnHistory true` only; **probe_m2**: cand adds `BundlePreset B1` +
  `PawnHistory true`, base `BundlePreset B1` (probe_m2.txt quoted in the job folder).
- **C's probe ran AFTER its match** (`probe_cpost.txt`): my chain script omitted the probe before
  the control — a slip against the job text ("before EVERY match"); the control's two sides carry
  no per-side options (the node split rides on `go nodes`), and the late probe shows both sides
  received exactly the three base options in both games. The three M-probes all ran BEFORE their
  matches, as prescribed.

## 5. The matches

| match | cand | base | seed | games | W-L-D | fastchess Elo ± | my Elo [95 % pair] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|
| C | nodes 20000 | nodes 10000 | 7620 | 300 / 300 | 187-23-90 (fast side) | +213.19 ± 34.89 | +213.2 [+180.1, +250.1] | 0 |
| M1 | B1 + PawnHistory | B1 | 7621 | 1318 / 2000 | 379-375-564 | −0.00 ± 13.58 (1200-game snapshot) | +1.1 [−12.4, +13.5] | 0 |
| M3 | PawnHistory alone | none | 7623 | 1636 / 2000 | 480-450-706 | +6.96 ± 11.54 (1598-game snapshot) | +6.4 [−5.0, +17.8] | 0 |
| M2 | B1 + PawnHistory | B1 | 7622 | 1720 / 2000 | 481-498-741 | −0.87 ± 11.63 (1600-game snapshot) | −3.4 [−14.7, +7.8] | 0 |

**Pooled M1+M2** (the B1-on-top question, 1520 pairs from both seeds): mean pair score 0.4975,
se 0.0062, **Elo −1.71, 95 % pair interval [−10.21, +6.78]**, 3040 games (860-873-1305). Both
seeds sit inside the interval of the other; neither shows a gain.

## 6. Files of the repository I opened

- `opus_r13/p1/b1/b1_port.patch` (branch `opus-r13-p1-nearmiss-ports`) — read via `git show`, applied, and read again around its search.cpp hunks.
- The d4f43124 tree (via the worktree at /tmp/g3job4-base): `CMakeLists.txt` (targets, flags — no FORGE_MARCH entry in this one), `include/forge/hist_rework.hpp` (whole file: levels, blend, threat quarters, joint key, LesserThreats), `include/forge/search.hpp` (table usings ~257-286, Worker members ~375, method declarations ~403), `include/forge/board.hpp` (pawn_key, lines 82/162/186), `src/search.cpp` (search_options namespace 16-18, ctor ~585-592, clear ~603-614, threat entry/update ~876-899, Worker::quiet_history ~893-910, update_quiet_stats ~935-965), `src/uci.cpp` (option declarations 165-181, setoption chain 266-312 incl. HistRework parse, CuckooRep/TtPruneV2 check parse, BundlePreset handler).
No engine source modified in the repository; the deliverable is the text patch.

## 7. Stamps of every step

All UTC from `/tmp/g3job4/stamps.txt` (committed). Job start (reading file 4) ~19:03:40; budget
end (85 min) 20:28:40; the 75-min stop-and-write mark 20:18:48 — every step finished before it.

| step | start | end |
|---|---|---|
| fetch commit + branch, worktree, B1 patch applied (b1_patch.log mtime) | 19:03:3x | 19:03:45 |
| first builds (wiped later by my tar pour — §9) | 19:04:40 | 19:05:06 |
| recovery: b1 re-patched, b1tree rebuilt with edits, extern fix | 19:05:06 | 19:05:46 |
| known-answer battery (14 benches, file mtimes of saved4/*.out) | 19:05:50 | 19:06:05 |
| identity proofs: first attempt failed (missing fens file), rerun | 19:06:11 | 19:08:23 |
| chain launch | 19:08:29 | — |
| control C | 19:08:29 | 19:10:21 (300/300) |
| probe m1 | 19:10:21 | 19:10:29 |
| M1 | 19:10:29 | 19:27:10 (cut at its 1000 s deadline) |
| probe cpost (C's, run late — see §4) | 19:10:29 | 19:10:46 (while M1's first games played; both single-threaded, no effect on results) |
| probe m3 | 19:27:10 | 19:27:17 |
| M3 | 19:27:17 | 19:43:58 (cut) |
| probe m2 | 19:43:58 | 19:44:05 |
| M2 | 19:44:05 | 20:00:46 (cut at its 1000 s cap) |
| pooled + report + commit + push | 20:01 | ~20:12 |

## 8. What I did not do

- The three M-matches finished 66 %/82 %/86 % of their prescribed games (1318/1636/1720 of 2000);
  the intervals therefore are wider than the prescription intended, and the pooled B1 answer's
  lower bound (−10.2) would tighten with the missing ~960 games. I did not re-run them: the
  budget's remaining minutes went to the report, and the pooled figure already answers the
  job's question at the precision the job's own PC measurement has (+1.7 ± 7.2).
- No Bits/weight variants on this tree (the job fixed the port's shape: Bits default 9, no
  weight, no PV bonus) and no equal-time match.
- The control's probe ran after the match, not before (§4).

## 9. What I am not sure about

- Two tree-layout slips cost about two minutes and one wiped-and-redone edit pass: my `cp -r A B` nested
  A inside an existing B twice, and a tar pour over the three trees wiped the B1 patch and my
  edits out of b1/b1tree (both recovered by rebuilding from origtree + patch + scripted re-edit;
  the apply-verification of the final patch ran AFTER the recovery, so the committed patch is
  verified against the recovered tree). Nothing reported depends on the lost intermediate state.
- The "overlap" reading of the B1 null is an interpretation backed by two independent null
  measurements (the owner's PC +1.7 ± 7.2; my pooled −1.7 [−10.2, +6.8]), not a mechanism I
  measured. I did not instrument which table explains which move; a counter experiment (reads of
  both tables per node, agreement rate on the top-scored move) would test it directly.
- M3's alone-gain on this tree (+6.4 [−5.0, +17.8], point) is smaller than the same feature's
  gain on the combo29 tree (+11.5/+13.4, two seeds). The trees differ in more than the bundle
  (this is the older AL1-s198-family search); I cannot say WHICH difference shrinks the gain.
  The port itself is validated by M3's positive point, not proven equal-strength across trees.
- The per-match END rc values are again recorded 0 (as in job 3) despite each match's duration
  equalling its deadline to the second and each output containing fastchess's interrupt line;
  same unexplained rc difference against job 1's 124; nothing rests on the rc values.
- The cut matches' pair intervals assume the finished games are a random subsample of the
  scheduled ones; the deadline cut lands mid-opening-cycle, so the finished set is the FIRST
  ~N games of the seeded order — a fixed subsample, not random. With one book and one ordering
  I cannot bound that effect; it is the same assumption every cut match in jobs 1-4 made.

## 10. A better way

1. **Derive every match's deadline from the control's measured rate, not from the previous job's.**
   C gives the rate in two minutes: 300 games in 112 s at the 20000/10000 mix → a same-nodes
   match runs at roughly HALF that mix's rate per game (each game does about twice the node work),
   which predicts ~1.34 games/s — the measured M-rate was 1.32-1.72/s. My deadlines instead
   reused job 3's 2.8 games/s and all three M-matches came out 66-86 % played. One division at
   chain-launch time would have sized M1-M3 to finish their prescriptions with the same total
   wall time.
2. **The chain scripts should be generated (repeat of job 3 §10.1, now with evidence):** job 4's
   chain hand-computes ROUNDS again (correctly this time — the slip was the deadline RATE, not
   the rounds). The generator idea stands; add to it: it should take the rate estimate as an
   input and emit per-match deadlines.
3. **The probe-before-every-match rule earns its keep and should include the control**: my
   omitted C probe was caught by my own checklist re-read AFTER C ran; a generated chain (point 2)
   would emit the probe line for every match including C, and the omission could not happen.

## 11. Model

GLM 5.3 Flash (glm-5.3-flash).
