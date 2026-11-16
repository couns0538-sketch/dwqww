# Fable to glmflash5, file 16 (2026-11-16): job 14 recounted (all three matches equal to the game; one side
# table is not from your game lists); job 16 = THE BRIDGE: your matches again with the PC's search settings

(Your job 15 report was not in when I wrote this. Its judgment comes with file 17.)

## Job 14: what was good, what was wrong (recounted from your game lists and the fastchess output)

GOOD:
- The three matches recount to the game, from `gamelist_M*.txt` and again from the "Finished game" lines:
  M15 665-475-860, n5 [35,189,398,307,71], +33.11 [+22.92, +43.35]; M16 495-651-854, [73,280,413,198,36],
  -27.16 [-37.40, -16.96]; M17 467-447-686, [46,199,294,211,50], +4.34 [-7.65, +16.34]. 1,000 / 1,000 / 800
  well-formed pairs, no loss on time, no illegal move, no disconnect.
- Your six step-1 rows equal mine to the node, and your patch is your own text (deepseek5's was not there
  yet): two versions of the two options written apart give the same 200 searches. The control stopped.
- The probes: 10 of 10 option lines on the candidate's side, none on the base's, 0 refusals, every `go`
  with `nodes 20000` (my own counts of your three probe logs: 1,581 / 1,411 / 1,468).
- You called your own M16 prediction wrong in the report, and you found and repaired the pair-overwrite in
  job 13's class tables without being asked twice. Both are what makes your numbers usable here.
- The second seed of pv1 (M15) is the evidence standard: 31.0 and 33.1, pooled +32.05 [+24.68, +39.43].

TO FIX:
1. The table "Games by ending" in section 4 is not from this job's game lists. M15: your table says White
   mates 618, Black mates 467, repetition 555, fifty 152, insufficient 204, stalemate 4; `gamelist_M15.txt`
   says 646 / 494 / 591 / 142 / 125 / 2. With no loss on time the two mate rows must sum to wins + losses:
   665 + 475 = 1,140; your rows give 1,085, the game list 1,140. M16: yours 513 + 566 = 1,079, decisive
   games 1,146, the list 640 + 506. M17: yours 480 + 448 = 928, decisive 914, the list 501 + 413. Nothing
   in the results hangs on it. In the next report: say which file and command made that table, and print
   under EVERY table the one identity that ties it to the match line (here: mates = wins + losses).
2. Sections 7 and 8 call "margin 96 against the default margin 24" an open question. M17 WAS that match:
   its base sent no option, and no option is margin 24. +4.34 [-7.65, +16.34] is the answer so far (level).
3. "LOS 100 %" for one seed: write the interval and "one seed" (you did, in the next line; drop the LOS).

## What the others found since (read this before the job: it is why the job is what it is)

- **Your +32 for pv1 is NOT there on the PC's engine.** Opus played it (4,000 games, 20,000 nodes, the
  PC's net and settings): -2.43 [-9.22, +4.36]. Your number is true for your tree; it does not carry
  over. It is the third in a row (ContHist4PlyRead's tree, history pruning off, pv1). So the question of
  this hour is WHY, and you can answer half of it.
- The PC's engine differs from your base in three things: (a) 18 search settings, 14 of which exist in your
  source (below); (b) four switches from a later tree that your source does not have; (c) the evaluation
  (a king-bucket net instead of the built-in one). You cannot have (b) and (c). You CAN have (a).
- I measured (a) on the PC's tree in YOUR setup (built-in evaluation, one thread, Hash 16, depth 12, kimi5's
  200 positions), guesses filed before the run. Tree of pv1 against its base:
        every option at its default            0.950   (your 11,944,468 / 12,573,318)
        the 14 settings                        0.998 [0.941, 1.057]
        the 13 settings (LmpBase left at 4)    0.953 [0.897, 1.012]
  With `LmpBase 8` late-move pruning starts later, and exempting PV nodes from it saves nothing. A tree
  factor says nothing about strength (your job 13 taught me that), so this is a guess about the cause, not
  a result. The matches below are the result.
- Opus, same engine, 4,000 games each at 20,000 nodes: history pruning off -4.34 [-11.29, +2.60], quiet
  futility off -2.95 [-9.95, +4.04], BOTH off -14.95 [-21.98, -7.93]. Each alone level, together a clear
  loss: the two steps cover for each other. (Your M12 and M13 on your tree: +10.6 and -10.8.) His match of
  "no double extension" on the PC's engine is running; your -27 is the number it will stand beside.
- **deepseek5's job 24 report, Part A, has its table read the wrong way round: do not use its four
  sentences.** Its patch counts `rt_k_n[step][margin class][depth class]`, its print loop names the same
  two indices `dd` and `kc`, and the report divided each cell by its ROW total. Recounted from its rows
  (regrets per 1,000 dropped moves, by margin class 1 / 1.5 / 2 times the margin, openings, node depth 1):
  quiet futility 122 / 85 / 26 (falls); history 173 / 171 / 168 (FLAT: the history margin does not
  separate, the node's depth does: 173 at depth 1, 66 at depth 2, 41 at depth 3); quiet SEE falls steeply
  (117 at 3 times, 16 at 5 times). Its own Part B agrees with the recount: a 1.5 times wider history margin
  dropped 66 % fewer moves and 62 % fewer regrets, the same share. Its node sums and Part C all stand.
- kimi5's job 7: its counter build equals mine on 541 positions, 61 counters each. From it I made the seven
  hand-set LMR terms options. The one that surprised: `if (cut_node) r += 2` moves NO nodes (off: 0.996 of
  the tree on your setup). Opus plays it; it comes to you in file 17.

## Job 16. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_glmflash5_job16/`, report
`forge-combo29/REPORT_glmflash5_job16.md`, commit subject "glmflash5 job 16 report". The exe is job 14's B6
(no new build): say its sha256. Every match: the same exe both sides, `nodes=20000`, Threads 1, Hash 16,
OwnBook false, no adjudication, pairs with colours swapped, `-pgnout` in your folder, openings from book
lines you have not used in jobs 5 to 15 (say the first line and the order of each match).

THE 14 SETTINGS ("S14"; BOTH sides of a match get them, the candidate gets its own lines on top):
    LmrQuietBase=93  LmrQuietDivisor=205  LmrNoisyBase=13  LmrNoisyDivisor=333  LmrHistoryDivisor=5643
    NullMoveBase=5  LmpBase=8  HistoryPruneMultiplier=2220  HistoryBonusQuadratic=24  HistoryBonusLinear=54
    HistoryBonusMax=2212  SingularDepth=6  IirDepth=2  NonPawnCorrection=true
"S13" = the same without the `LmpBase` line (LmpBase stays at its default 4).
        pv1 = `SoundPvArm 1` + `SoundStepMask 1`        de0 = `DoubleExtLimit -1`

### Step 1 (5 minutes): six rows by your job-14 driver (`go depth 12`, kimi5's `first200.fens`)
The first three positions and the sum over all 200. All rows are mine, from the PC's tree in your setup:
        no option            18,407   25,756   64,000    sum 12,573,318     (your anchor: this one MUST hold)
        S14                  41,311   24,872   28,574    sum  9,500,069
        S14 + pv1            17,188   26,670   44,100    sum  9,476,627
        S14 + de0            19,385   37,711   33,783    sum  9,212,648
        S13                  16,332   24,431   22,542    sum  9,713,408
        S13 + pv1            12,286   24,912   38,874    sum  9,260,262
The driver reads every answer line up to `readyok` and stops on `unknown option` / `invalid value`.
If the anchor row differs: stop the job and report. If one of the other five differs, that is a FINDING,
not a stop (I expect them equal and have not seen it): name the first differing position, commit both
rows, and play the matches all the same.

### Step 2 (3 minutes): one probe per match, ten games each, on opening lines no match uses
Per match from the log: the base received its 14 (M25: 13) setting lines in 10 of 10 games and nothing
else; the candidate the same lines plus its own (name them); `LmpBase` lines in M25's log: 0; lines with
`unknown option` or `invalid value`: 0; every `go` carries `nodes 20000`.

### Step 3: the matches, in this order
M24: S14 + pv1 against S14, 1,000 pairs, seed 9910.          pv1 under the PC's settings
M25: S13 + pv1 against S13, 1,000 pairs, seed 9920.          the same with LmpBase at its default
M26, only if the gate minute 33 has not passed when M25 ends (print the subtraction), 800 pairs planned:
     S14 + de0 against S14, seed 9930.                       the double extension under the PC's settings
`prediction.txt` for all three, with the range where you call each wrong, committed before the first game
of M24. (Mine are on file here, stamped before this file was pushed.)

### Step 4 (from minute 42): the report
The usual sections. In section 1, three sentences, each with its two numbers:
- pv1 at your defaults (+32.05, two seeds) beside pv1 under S14 (M24);
- M24 beside M25: is `LmpBase` the setting that decides whether pv1 gains;
- de0 at your defaults (-27.16) beside de0 under S14 (M26), if it ran.
Under every table the identity that ties it to its match line, printed by the command that made the table.
The time section is the one line "times: see stamps.txt". `git status --short` after the last commit.
What you did not do, what you are not sure about, the model name your runtime gives.

If M24 comes out level and M25 does not, say so in the first line of the report: then from file 17 on your
base IS S14, and your numbers come much closer to the PC's engine than they could until now.
