# T6 Lichess puzzles as a fixed-node tactical screen - exact commands

Base folder: `C:\opus_5h\oss_scout`. Idle priority, CPUs 2-3 (inherited); run after T1b, so that at most 2 heavy
threads of this job were busy.

## Data (CC0-1.0, https://huggingface.co/datasets/Lichess/chess-puzzles; 6,157,341 puzzles, card of 2026-10-07)
`python -I -B tools/t6_fetch_puzzles.py build/t6/puzzles_2000.jsonl --blocks 20 --per-block 100 --seed 20261106`
- 20 requests to the public dataset-viewer API (`https://datasets-server.huggingface.co/rows?dataset=Lichess/chess-puzzles&config=default&split=train&offset=<o>&length=100`),
  at seeded random offsets, with a generic User-Agent.
- Result: 2,000 puzzles, ratings 399-3025 (p25 1026, median 1400, p75 1881).
- The JSONL keeps PuzzleId, FEN, Moves, Rating, RatingDeviation, Popularity, NbPlays, Themes.

## Engine
`build/lock/forge_trial_w6.exe` (the lock, sha256 4181a589), options OwnBook false, Hash 16, Threads 1.

## Solve
`python -I -B tools/t6_solve.py C:/opus_5h/oss_scout/build/lock/forge_trial_w6.exe build/t6/puzzles_2000.jsonl --nodes 20000 --nodes 200000 --out repo/opus_oss_scout/trials/t6_puzzles/t6_result.json`
- Per puzzle: `ucinewgame`, `isready`, `position fen <FEN> moves <Moves[0]>`, `go nodes N`.
- Solved = bestmove equals Moves[1], the first solution move. Lichess also accepts other mates in one; a first-move
  check counts those as misses, which makes the rate a slight underestimate.
