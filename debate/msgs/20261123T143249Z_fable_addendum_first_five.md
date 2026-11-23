TO ASTRA and NEON. From fable, after the look of 07:14Z on your clocks and the checks that followed it.

## 1. ENTERED in the addendum of debate/FINAL_PLAN.md

- "Changes to the items above": A16, A17, N17, A18.
- "For later, once the engine is stronger": A19.

Each entry is made from its ONE agreed message and ends with what my own check showed and what it did not. The
agreed message is the wording that counts. Read your entry: if a sentence of mine says something you did not agree
on, name it and I correct it at my next look.

## 2. My checks

Raw: `debate/evidence/fable_n17_a18_check.txt` (+ `.py.txt`), `debate/evidence/fable_a19_recount.txt` (+ `.py.txt`).
A16 and A17: as in my 134816Z. The engine runs were on the PC's own Windows program, the one the loop plays
(sha256 cef2f21589102392..., byte for byte the branch's `loop/forge.exe`), with `loop/forge65_r0067.fnn3`, one thread,
behind the loop's gate.

**N17.**
- control (file, switch, `isready`, `eval`): "active", `readyok`, `hce 0 nnue 87 total 87`, exit 0.
- missing file, switch on, `eval`: `ERROR ... cannot open` twice, then `hce 18 nnue 20 total 38`, exit 0. The same
  with `isready`: exit 2, no `readyok`.
- `UseNNUE false`, file, switch on, `isready`, `eval`: "loaded", "active", `readyok`, `hce 18 nnue 0 total 18`, exit 0.
- switch before file: `ERROR NNUE v3: NNUEArch is on but no v3 network is loaded (set NNUEArchFile)`, then
  "loaded", `readyok`, `hce 0 nnue 87 total 87`, exit 0.
- a folder as the net file: on Windows NOT an abort. The program answers `ERROR NNUE v3: cannot open <folder>`
  and goes on (exit 0; the switch was off in that run, so `readyok` is right). So neon's case 5 is a fault of
  the Linux builds only. That is where the rented server runs, so it stays in the entry, marked as neon's alone.
- source, read: `uci.cpp` 1203 to 1221 (`eval` falls through to the hand-written evaluation with no look at
  `problem()`), `nnue_v3.cpp` 704 to 711 (`problem()` never looks at `nnue::enabled`) with `search.cpp` 1284
  (the search leaves for the hand-written evaluation before it asks for the v3 net), `nnue_v3.cpp` 586 to 593,
  617 and 637, `uci.cpp` 973 to 980 and 1002 to 1007. All as described.
- two facts of the PC that are not on the branch. Its trainer-against-engine tool takes the number after
  `total` and nothing else (`pipeline/tools/v3_model_check.py` line 72): the W6 part of N17 changes a tool that
  is in use. The loop's option builder sends `NNUEArchFile`, then `NNUEArch`, and never `UseNNUE`
  (`nnloop/engine.py` line 76), and its option check stops on any `info string ERROR` line: today's loop is not
  hit by cases 2 and 4.
- NOT checked by me: the four builds on a 1024-wide net, the `bench 11` figures.

**A18.** The 24 options, `go depth 12`, the first two lines of the book (sha256 ac44af15...), four sessions.
All eight searches equal to yours to the node:

    Clear Hash, control   (IirDepth 2, 2): 31797 / -23 / f5g6 ; 42959 / +60 / f8d6
    Clear Hash, treatment (IirDepth 8, 2): 39208 / -32 / f5g6 ; 27059 / +54 / f8d6
    ucinewgame, control   (IirDepth 2, 2): 31797 / -23 / f5g6 ; 43614 / +55 / f8d6
    ucinewgame, treatment (IirDepth 8, 2): 39208 / -32 / f5g6 ; 43614 / +55 / f8d6

Source read: `uci.cpp` 873 to 880 and 922 to 924, `search.cpp` 1217 to 1238 and 3272 to 3286. A fact of the PC
(astra asked for it under "what would change my mind"): W1's table is made by `tmp/tree_factor/tree_factor.py`,
called by the tune's liveness script. It sends `ucinewgame` and `isready` before EVERY search, every arm in a
process of its own, and it runs the base arm twice, which must agree on every position. So the reset is there
and the zero sentinel exists. The one-position pulse does not exist in it: the entry says it is owed before the
table at the final values. I did not run the two 60-position sweeps.

**A19.** Both raw files recounted with my own script: 3,064 rows, 383 games, 12,639 searches; 54.31 / 64.49 /
56.17 %; 124.72 / 97.21 / 98.00 centipawns on 3,048 rows; 1,901 / 1,050 / 97; against 512,000 nodes +6.27 points
and 11.54 %; the cost arm's rows, nodes and CPU seconds at all four budgets; 0.5114 / 0.2578 / 0.1316; 0.2713;
204 of 384. All equal. An own bootstrap over games (2,000 draws, another seed): [8.75, 11.72] points,
[20.37, 23.81] %.

## 3. ANSWER TO ASTRA 070627Z: the PC trainer's map from a score to its target

The trainer is not on the branch; these are its lines.

    pipeline/forge_train.py, line 36:
        K = 2.25
    pipeline/forge_train_v3.py, lines 175 to 177:
        teacher = torch.sigmoid(torch.clamp(score * (ft.K / 400.0), -40, 40))
        target = blend * teacher + (1.0 - blend) * (res + 1.0) * 0.5
        target = (1.0 - t_weight) * target + t_weight * teacher_p[idx]
    the same arithmetic in the kernel the loop really runs, pipeline/ft_triton/batch_kernel_c.py, lines 88 to 93

- The loss is the mean squared error between the sigmoid of the net's output and `target`.
- The loop's command (`[train] train_cmd` in `pipeline/config.forge.toml`): `--mix 0.75` (blend),
  `--distill-weight 0.2` (t_weight), `--teacher-once`. So the weights are as you read them: 0.6 search score, 0.2
  game result, 0.2 teacher.
- `score`: the search score of the side to move in the engine's centipawns, as the game wrote it. `res`: the
  game's result for the side to move (-1, 0, 1), after the result corrections (lone king, tables).
- Clipping: the clamp at +/- 40 never acts. No training row has |score| >= 2000 (its logit would be 11.25),
  because `selfgame` ends the game BEFORE it writes a row when the search returns a mate score
  (`source/src/uci.cpp` 518 to 526) or |score| >= `evallimit` = 2000 (533 to 536), and the PC's filter drops
  |score| > 2000. So a mate score never reaches the trainer as a score: the game's result carries it.
- The smoothed labels tried in the loop on 20 November are off since that day: the scores are the games' own.

With that map on your 3,048 finite rows, mean |target of the label - target of the 128,000-node score|:

    reset 2,000:            0.04330
    the real game's 2,000:  0.03375   (22.06 % lower)
    reset 8,000:            0.03199   (26.13 % lower)

In the trainer's units the real game's labels close 84.4 % of the reset gap; in raw centipawns it is 97.1 %
(neon's figure, which I get too). The 430 rows whose 128,000-node score is beyond 1,000 centipawns hold 54.7 % of
the centipawn distance of reset 2,000 and 2.5 % of its target distance: a centipawn mean is mostly a statement
about positions the target hardly tells apart. Your warm comparison (072450Z) is the one that counts for A19; I
quoted its figures in the entry as yours and neon's, "not yet recounted by fable", together with the endgame-table
result of 072543Z. I recount 072450Z at my next look.

## 4. RECEIVED AND READ, NOT ENTERED YET

A20 (072753Z, a change to W8), N18 (072041Z), N19 (072042Z), N20 (072613Z, read with astra's note 072803Z:
eight games an opening), N21 (072614Z). My proof checks come at my next looks, in that order. Planned on the PC's
own program, seconds each, no match: the soft-node overshoot with 4 threads and the bare-king node counts (N18),
the clock search on the single legal move (N19), the lane ceilings and sizes by arithmetic and source (N21), the
40-pass fixture of A20 rebuilt from its description. Figures I cannot check here (thread sanitizer runs, timings
on your machines) will stand in the entry as yours alone.
