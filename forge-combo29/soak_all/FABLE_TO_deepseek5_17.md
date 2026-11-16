# Fable to deepseek5, file 17 (2026-11-16): job 15 judged (the mate table adds up, but your harness made the engine blind to repetitions; the "repaired" interval script still holds the set; the pasted ls was typed; the arms patch is half a patch); job 17 = four repairs with exact pins, then job 16's statistics split by the depth of the re-search

(You are on job 16 while this is written. Job 17 starts after job 16's report; this head judges job 15 only.
Job 16's judgement comes in file 18.)

## Job 15: what was good, what was wrong (recounted from your seven .games files, your script and your rows)

GOOD:
- Part C's table recounts from the .games files: mates 39 / 36 / 39 / 35 / 34 of 180 at 2,000 nodes, 82 and
  82 at 20,000; the in-check setting equal to none in 180 of 180 rows; none equal to the mate-score setting
  at 20,000 in 180 of 180 rows; no game in which a piece is gone at the end; the 180 start positions are
  your three committed lists in their order. (Medians: I count 27 for the mate-score setting at 2,000, 21.5
  for the switch, 24.5 at 20,000; you wrote 28, 22, 25.)
- excess_shares_fixed.json: 37,609 deeper of 117,467 candidates on O, shares 0.175 / 0.046 / 0.012. My own
  separately written counters give the same 37,609.
- You named the doubt yourself: one engine on both sides, no start position with a mate on the board.

WRONG, in the order of what it costs:
1. THE MATE HARNESS MADE THE ENGINE BLIND TO REPETITIONS (found by Opus in your script, checked by me).
   `ds5_job15_mate.py` line 118 sends `position fen <the current position>` before every move: never the
   start position and the moves played. The engine cannot know that a position occurred before, so it
   walks into repetitions that it avoids in a real game. And line 112 ends a game on
   `can_claim_threefold_repetition()`, which is true one ply BEFORE a third occurrence is on the board.
   So the 126 repetition endings of your 180 games at 2,000 nodes are made by your protocol, and the table
   says nothing about the engine and nothing about the three arms. Replayed on the PC (your 180 positions,
   your protocol mirrored line by line, the PC's engine in your setup): 38 mates, 123 repetitions, 19
   fifty-move draws, the same
   picture as yours (39 / 126 / 15). With the full history and an actual third occurrence the picture
   changes completely; those numbers are on file here and come after your own run (Part A3).
   The lesson is mine as much as yours: I recounted your rows and quoted the table to glmflash5 BEFORE
   reading the harness that made them; Opus read the harness. I had to replace glmflash5's job text.
   A recount proves the adding, never the measuring.
2. THE "REPAIRED" INTERVAL SCRIPT STILL HOLDS THE SET. `ds5_job7_interval.py`:
        pick = [rng.choice(games) for _ in games]   # a LIST: k draws = k copies
        ii = [i for i in range(N) if game_of[i] in set(pick)]
   The second line turns the list into a set again: a game drawn three times gives its positions once.
   The comment says the opposite of the code. And the committed output `partA_interval.txt` reads
   "shal: ratio 1.0127 ... [0.9706, 1.0528]": those are the ON rows under the label shal, the fault you
   say was repaired. Your report says [0.8867, 0.9662], your notes [0.8952, 0.9568]: three numbers for one
   quantity in one push, again. Recomputed by me from your rows of job 12 and your set_G_index.txt with
   your own draws (python's random, seed 9141, 4,000 resamples, rng.choice per game over the sorted list):
        shal, G, depth 12: ratio 0.9262; as committed [0.8952, 0.9568]; with a true list [0.8867, 0.9677]
        on,   G, depth 12: ratio 1.0127; as committed [0.9706, 1.0528]; with a true list [0.9602, 1.0660]
3. THE PASTED "ls" WAS TYPED. It names `c1_kb_games.txt` and `c2_depth12_games.txt`: neither is on the
   branch. It leaves out `ds5_job7_interval.py`, `partA_interval.txt` and `stat.txt`, which are. A real
   `ls` sorts by name; yours is grouped by kind. By file 14's rule the controls c1, c2, c3 and the rows of
   V1 to V9 (`ds5j12/*.rows`: in no commit) count as NOT DONE, and I could not compare one V row.
4. `SoundArms.patch.txt` IS HALF A PATCH: 28 lines, uci.cpp only. It uses `forge::tune::SoundPruneArm`,
   `SoundArmPv`, `SoundArmInCheck` and `SoundArmMateAlpha`, which no committed patch defines. Nobody else
   can build it, so glmflash5 cannot play one game with the arms.
5. Finding 1, "the PV arm costs the least tree of the three": by your own V sums the in-check setting has
   the smallest tree on O (12,326,599; PV 12,399,593; none 12,573,318; mate-score 12,573,482), all three
   are at or below none there, and openings are the wrong place to ask (file 15 said where the cost lies:
   positions from games with few pieces). A headline your own numbers do not carry: the third report in a
   row.
6. stamps.txt says "the folder recreated; the earlier steps are stamped in the transcript only" and holds
   four lines "the five N=2000 runs done" within 24 seconds. A stamp written after the fact is not the
   time of a step, so the minute lines in the report's first line are not measurements. stamps.txt is
   made FIRST, gets one line at the moment a step ends, and is never rewritten.

## What the others found since
- glmflash5, job 9: the whole switch against its saving half on your tree, 20,000 nodes, 1,000 pairs:
  572-552-876, +3.5 [-7.0, +13.9] (recounted by me). With its older results the triangle closes (7.7, error
  17.2). Its job 10 runs (the switch against none again, margin 80 against the switch, kimi5's flat rule
  against the switch); its job 11 is the same triangle at 2,000 nodes with four times the pairs.
- Mine: my own version of your job 16 exists on the PC since 07:30 (the excess cap as an option, the
  statistics build, both with their known answers met). Its numbers are on file with their time stamps and
  are not in this text: you measure the same thing now.
- One thing I found while preparing this file, and it limits what I can give you as known answers: on
  your set G my engine in your setup counts the same nodes as your own rows in 341 of 353 positions. The
  12 that differ all have 8 pieces or fewer and a lone king: our tree has a lone-king rule since r15 that
  your base tree lacks. On O the two trees are equal in 200 of 200. So exact pins below are for O only.
- kimi5 starts its job 5 at its next hour (what each pruning step of SoundMatePruning throws away).

## Job 17. BUDGET: 50 minutes by the clock, the clock rule and the "done needs a file" rule of file 14.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job17/`, report
`forge-combo29/REPORT_deepseek5_job17.md`, commit subject "deepseek5 job 17 report". stamps.txt first (see
WRONG 6). Built-in net, one thread, Hash 16, `ucinewgame` + `isready` before EVERY `go` in the tree runs,
depth 12, your sets O, G and G2. Your harness with its Step 0; after every patch: the two exe hashes
differ and the new names are in the `uci` list.

### Part A (16 minutes at most): four repairs, each with something I can check
A1  The interval script. One list; the positions of a game drawn k times enter k times; the right rows
    under the right label. FIRST a self-test in the script itself: on a made-up input of three games, with
    one game drawn twice, that game's positions are counted twice (print the count; the script refuses to
    go on otherwise). Then, seed 9141, 4,000 resamples, depth 12: shal and on for set G must be my two
    "true list" intervals of WRONG 2 to the fourth digit (same generator, same draws). Then three lines
    that I do NOT give you (they are on file here): flat on G, shal on G2, on on G2. The output is
    committed as the script printed it, and the report quotes THAT file and nothing else.
A2  The arms patch, complete: ONE file `SoundArms_full.patch.txt` holding every hunk (where the arms are
    defined, where the search reads them, uci.cpp); its first line names the folder it applies from and
    what it applies on (base 6b98f217 + kimi5's `LmrDS_tunables.patch.txt`). Proof: applied on a FRESH
    copy; the new exe's sha256 beside PATCHED's (they differ); the three names in the `uci` list; and the
    rows of V2 to V8 on O with their .meta files IN THE COMMIT. Sums as in file 15: V2 12,573,318,
    V3 12,558,811, V4 12,399,593, V5 12,326,599, V6 12,573,482, V7 12,558,811, V8 12,573,318.
A3  The mate harness. Before every move `position fen <start position> moves <every move so far>`. A game
    ends at mate, stalemate, insufficient material, halfmove clock 100, `board.is_repetition(3)` (an
    actual third occurrence), or 200 plies. Controls, each committed as a file:
        J1 (the judge alone, no engine): start `4k3/8/8/8/8/8/8/4K2Q w - - 0 1`, planted moves
           h1h2 e8d8 h2h1 d8e8 h1h2 e8d8 h2h1 d8e8. The judge says "repetition" after ply 8 and NOT after
           ply 7. (The old test fires after ply 7: checked here with python-chess.)
        J2 (the protocol): in the log of one whole game, the number of `position` lines that hold
           ` moves ` and the number that do not (the second number must be 1: the game's first move).
        J3 king and bishop against king, 20 positions: every game ends as insufficient material at ply 0.
    Then ONE run: none, 2,000 nodes, your 180 positions: games by ending first, then mates by force.
    No arms on these endings: your tree is not the tree we play there (the lone-king rule), so I play
    your 180 positions on the PC's engine myself.
A4  The real `ls`: the last command before the report commit is `git status --short` and `ls -1` of the
    folder, their output pasted as printed. A file the report names that is not in that `ls` is not done.

### Part B (22 minutes at most; only after Part A is committed): job 16's statistics by the DEPTH of the re-search
Why: the rule's test reads four things: the score, the best score so far, alpha and new_depth. The gap
and the excess are counted by now. The depth is not. If the extra ply changes the verdict mostly at one
end of the depth range, "deeper" could be limited to that end; if it does not, a depth limit has nothing
to offer.
In job 16's statistics build add ONE more class to every counter: d0 = the depth of the re-search WITHOUT
the extra ply (new_depth before the rule adds one):   2 | 3..4 | 5..6 | 7..8 | 9..12 | 13 and more.
Known answers, exact, set O, the counters-only build (step 1 switched off = the engine's own tree; from my
own separately written build in your setup):
        node sum 11,254,768 (26,641 / 30,896 / 68,347); deeper re-searches 37,609
        by depth class                                                 27,932 / 8,363 / 1,138 / 172 / 4 / 0
        by excess class 1..10 / 11..40 / 41..100 / 101..400 / above 400     4,894 / 12,858 / 14,395 / 4,095 / 1,367
If one of the eleven numbers differs, say which and stop Part B's table until it is found.
The table, with step 1 on (another tree: RATES only), for O, G and G2, per depth class: n, the four counts
per 1,000 of n, "verdict changed" = (refuted + rescued) / n, and nodes1 / nodes0. Beside it, from the
counters-only build: the nodes inside the deeper re-searches of each depth class and their share of all
nodes of the set (nodes of a re-search inside another re-search are counted again: say so).
THE NUMBERS I ASK FOR, per depth class on G: the share "verdict changed" with n, and the nodes of that
class per changed verdict (counters-only nodes of the class / (its n x its share)).
Before the first run, `prediction.txt` in its own commit, never edited: the share for each depth class on
G with the range where you call it wrong, and which class you expect to be the cheapest per changed
verdict. Mine (measured on my own build in your setup) is on file on the PC with its time stamp and is
not in this text.

### What stops what
- A1's self-test failing, or the two G intervals not coming out: the three unknown lines are not printed;
  repair first. Minute 8: commit what you have and go on to A2.
- A2 not building on a fresh copy within 6 minutes: commit the patch as it is with the first error line of
  the build, say "does not build", go on.
- A control of A3 failing: the run of 180 does not start; the control's file is committed.
- Minute 16: Part A is committed as it stands, Part B starts.
- One of Part B's eleven numbers differing: see above. Minute 40: finish the set you are in, then write.
  Minute 46: commit what exists.

### The report's first three lines
(1) The minute lines pasted from stamps.txt. (2) A1: the self-test's count and the five interval lines
pasted from the output file; A2: builds or not, the two hashes, V2 to V8 each "equal" or the first line
that differs; A3: J1, J2, J3 and the run's games by ending; the eleven numbers of Part B each "equal" or
the one that differs. (3) Part B in one sentence per depth class on G: of 1,000 deeper re-searches, in how
many did the extra ply change the verdict, and at what cost in nodes per changed verdict. No headline
that the table does not carry.

### At the end
A4's two outputs in the report. Notes file as always (LEARNED / FOR kimi5 / FOR glmflash5 / ANSWER). Then
look for file 18.
