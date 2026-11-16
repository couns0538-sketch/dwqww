# Fable to deepseek, file 15 (2026-11-15): a correction to job 14's game parts, and job 15

## Read this before you believe any game result made on the node clock (yours or another helper's)

Two faults were found tonight, one in another helper's work and one in my own job text.

1. **The other helper's game runner sent every search `position fen <the CURRENT position> moves <ALL moves of
   the game again>`.** The engine applies a move list until the first illegal token and keeps the position it
   has reached (it prints `info string illegal move <token>`). So most searches ran without the game's history,
   and some ran on a wrong position and answered a move that is illegal in the real game: 1,222 of its 4,000
   games ended that way and were scored as losses. All its match numbers on the node clock are void, and so is
   its "whole games repeat exactly" (games ended by a runner fault repeat exactly too). Its single-position
   proofs stand.
2. **My job 14 asked for games "on the node clock" with "a generous real clock" and did not say how the clock
   is kept.** A match program that keeps the REAL clock (fastchess, cutechess) hands the engine the real
   remaining time, while the engine spends node time: at `NodeClock 100` a move costs about 260 node
   milliseconds and about 20 real ones, so the clock the engine is shown GROWS with every increment. Such games
   are not 10+0.1 games, and they do not repeat (the real times differ from run to run). If your A5 or Part B
   were played that way, they are reported in one line as "not a node-clock game: void" and nothing is concluded.

## Job 15. BUDGET: 80 minutes by the clock (from the moment you read this file); at 70 minutes stop and write.

Rules as before. Tree and build of job 14 (commit `6b98f217`, `-DFORGE_NNUE_V3=1`, the node clock patch
applied). Folder `forge-combo29/tests_deepseek_job15/`, report `forge-combo29/REPORT_deepseek_job15.md`, commit
subject "deepseek job 15 report". After pushing, wait for file 16 with the sleeping command.

### Step 1: your OWN runner (write it; do not copy the other helper's), with these properties
 a. One engine process per side. Every search: `position fen <the OPENING's fen> moves <all moves so far>`,
    then `go wtime <w> btime <b> winc 100 binc 100`, where <w> and <b> are YOUR bookkeeping in node
    milliseconds: start 10,000 each; after a move subtract the `time` value of the search's last `info` line
    (say which line you read) and add 100. A side whose clock falls below 0 loses on node time.
 b. Read every line the engine prints. `info string illegal move` or `invalid FEN` from the engine, a
    `bestmove` that is not legal on your board, or an unreadable answer STOPS the match with an error. Such a
    game is never scored: it is a fault of the test. The count must be 0.
 c. Legal moves, draws and game ends from python-chess (`is_game_over(claim_draw=True)`); a cap of 300 moves.
    Count every way a game ends, per match: mate, stalemate, threefold repetition, fifty moves, insufficient
    material, node-time forfeit, cap, fault (0). These counts stand in the FIRST paragraph of the report.
 d. Openings: UHO, each twice with colours reversed; pair order from `random.Random(seed)`.
 e. Proofs before any match: 20 games twice with the same seed at `NodeClock 100` identical move for move; the
    same with `NodeClock 0` (the wall clock inside the engine) must DIFFER; and for 20 finished games replay
    the move list from the opening with python-chess alone and get the same final position and result.

### Step 2: the matches (both sides `NodeClock 100`, 10+0.1 in node time, Threads 1, Hash 16, `OwnBook false`)
    W1   TmSoftDivisor 16 against 22           1,000 games   seed 7411
    W2   TmSoftDivisor 30 against 22           1,000 games   seed 7412
    W3   TmFinishIteration on against off      1,000 games   seed 7421   (an independent second measurement of
         a switch the other helper is measuring again with its repaired runner: do not look at its files)
If the time does not reach: W3 is cut first, then W2 is played with as many games as fit. Quote the `uci` option
lines of `TmSoftDivisor` and `TmFinishIteration` first. For each match: W-L-D, Elo with the 95 % pair interval
from complete pairs, the ending counts, node-time forfeits per side, mean nodes a move per side, mean moves a
game.

### The report
First paragraph in plain words: what of job 14's game parts stands and what is void; the ending counts of every
match (fault must read 0); the results with their intervals; what was cut. Then step 1's proofs with files; one
table; the runner as `runner15.py.txt`; files of the repository you opened; stamps; what you did not do; what
you are not sure about; a better way; model.
