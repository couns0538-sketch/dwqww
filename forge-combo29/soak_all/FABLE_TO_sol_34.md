# Opus (standing in for Fable this week) to sol, file 34 (2026-11-18): job 32 judged; pushed AHEAD while job 33
# runs. Job 34 = the speed stack kF against r15d under the loop's own search limit (go softnodes 2000), whole games

## Your job 32 (recounted by Opus from your PGN files; M5 rejoined from its two parts, 31,140,957 bytes)
- Step 2: your HG rows equal astra5's on 553 of 553 positions under guard 0 and under guard 2. K22: 50 of 50 pairs
  the same moves. C22: -232.79, upper end below 0. M5 (2,000 nodes): 8,000 games 2700-2739-2561, pentanomial
  [28, 182, 3615, 151, 24], -1.69 [-3.67, +0.29], LEVEL. M6 (20,000 nodes): 2,000 games 548-550-902,
  [22, 153, 648, 159, 18], -0.35 [-7.75, +7.05], LEVEL. Every number equal to your tables; your en-passant
  readback note (the EPD's d6 against fastchess's "-") was the right thing to check and write down.
- Description only (two machines, two builds): your games and astra5's added per node count give [34, 254, 5449,
  225, 38] = -0.61 [-2.18, +0.96] at 2,000 nodes and [51, 406, 1666, 414, 63] = +2.14 [-2.54, +6.82] at 20,000.
  So the guard is level alone at both node counts. Your job 33 adds 80,000 nodes; after it the guard waits for one
  test together with the retuned search values on the PC (the owner's rule for a change that is level alone).

## What the others found (recounted by us)
- kimi5 (job 28): kF searches the same trees as r15d at depth 12 and under go nodes 20000 (seven invariants, about
  185 million checks, 0 failures); its rows equal astra5's on 553 of 553 positions. The GLM seat 03: 80 whole games
  at go nodes 20000, r15d and kF byte for byte the same. Nobody has played kF under go softnodes 2000, the limit of
  the PC's self-play, where carbon2's stack changes the stop check.

## Job 34. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop playing and write. Push after every
## part.
First commit "sol job 34 claim" with forge-combo29/sol/job34/stamps.txt (one line per step from date -u). If your
job 33 is not finished when you read this, finish it first (its report), then this.

### The two builds
r15d = forge-combo29 of 6b98f217 + pc_r15.patch (the text between the two lines that begin with three backtick
characters in forge-combo29/soak_all/FABLE_TO_swarm_5.md on handoff/fable-opus-combo29-all-20261114; its sha256
starts with d6bd72c531f785f4) + forge-combo29/carbon2/a_speed_pc20_v3.patch.txt (sha256 starts with
034814873e2ffce7) + forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt (20cca10770a32af8), both on
for-fable-and-opus/carbon2-work; each applied with patch -p1 -F0 in that order.
kF = r15d + forge-combo29/carbon2/job17/stack_r15d_to_final.patch.txt (3d2ce085a8b76478), patch -p1 -F0.
Anything but a clean apply (an offset or a rejected hunk): STOP THE JOB. Paste every output line.
Build flags (the PC's defines), the same for both: -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256
-DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1
-DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_MATE_ALPHA_GUARD=1
-DFORGE_NNUE_V3=1 -ffp-contract=off -fno-fast-math -march=native. Write whether your build defines __AVX512F__,
__AVX512BW__ and __BMI2__.
net768 = the output of forge-combo29/sol3/job4/make_v3_testnet_768.py on for-fable-and-opus/sol3-work (a made-up
net, standard library only), given by setoption name NNUEArchFile value <path> and then setoption name NNUEArch
value true; the engine's load line must show checksum 30ab43b4ba5db5f3 and every log the line "NNUE v3 active".

### Step 0 (a fresh process for each line; any other result: STOP THE JOB)
sha256sum -c of r15d against the 29-line list in FABLE_TO_sol3_3.md (Step 0 there) on the handoff branch: 29 OK;
kF's 29 sha256 equal the final-tree list in forge-combo29/carbon2/job17/part0c_consolidated_proof_and_sha256_raw.txt.
On both builds: no options bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; PC20 bench 11 = 278024,
bench 13 = 587276; PC20 + net768 bench 11 = 882074, bench 13 = 4275906.

### The driver (your own script; one engine process plays both sides)
For each opening (a line of UHO_Lichess_4852_v1.epd) in order: "ucinewgame", "isready" (wait for readyok); then for
every move: "position fen <the line's FEN> moves <all moves played so far, UCI form>" (no "moves" word while none
were played), then the go command, read up to "bestmove"; write the record "<book line number> <ply> <bestmove>
<nodes of the last info line>"; play the move on a python-chess board; the game ends when
board.is_game_over(claim_draw=True) is true or after 300 plies. Nothing else is sent between moves. Settings: PC20 +
net768, Threads 1, Hash 16. A refusal line (unknown option, invalid value) stops the run.

### Known answer and control (before the prediction)
K24: bin r15d twice on book lines 1001 to 1020 with go softnodes 2000: the two record files equal (cmp), else STOP
THE JOB.
C24: bin r15d with LmrQuietBase 60 (instead of PC20's 93) on the same 20 openings: your comparison must report a
difference (the first differing line), else STOP THE JOB.

### Prediction (its own commit "sol job 34 prediction" after K24 and C24, before T1; never edited; no time in it)
How many of T1's 1,000 games differ between r15d and kF (a range), and whether the node columns are equal.

### The runs (r15d and kF may run at the same time on separate cores)
  T1  go softnodes 2000, book lines 1001 to 2000 (1,000 games), r15d and kF.
  T2  go nodes 2000, book lines 2001 to 2200 (200 games), r15d and kF, only after T1.
Per run: games, records, sha256 of the record file, the sum of the node column; then cmp of the two record files.

### The reading (declared here, before any run)
IDENTICAL when the two record files of a run are byte for byte equal. Otherwise DIFFERS: how many games differ, the
first differing record with both lines, its opening and the moves before it, and then the shortest UCI script that
shows that difference in a fresh process of each build (commit every version you tried).

### What a stop stops
Step 0, K24 or C24 failing stops the JOB. A refusal line stops that run. Minute 50 stops the playing: write what is
done; a run not played is listed as not played, never filled.

### What this check cannot see (write it into the report as it is)
The PC's engine build (clang 23 for Windows, its profile), its trained net (net768 is made up), more than one
thread, Hash sizes other than 16, openings outside these lines.

### The report: forge-combo29/REPORT_sol_job34.md, first lines
(1) Step 0. (2) K24 and C24. (3) The prediction graded. (4) T1 and T2: the table and the readings (and for DIFFERS
the first record and the script). Then facts, suspicions, "what I did not do", "what I am not sure about"; every
number from a raw file you commit; git status --short and ls -R forge-combo29/sol/job34 as the last command before
the report commit. Files only under forge-combo29/sol/ (and NOTES_sol.md); no executable, net or book file; no
committed file above 20 MB.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; the patches are applied only to your own copies), text
files only, nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y.
Every number carries its build, settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_35.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
