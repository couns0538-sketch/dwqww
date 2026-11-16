# Engine facts measured for job 2 (each with the command that shows it again)

F1. The engine prints EXACTLY ONE `bestmove` per `go` line, including malformed ones.
    `for c in "go banana" "go depth -3" "go" "go depth 0" "go nodes 0" "go movetime 0"; do
       printf "uci\nisready\nposition startpos\nisready\n$c\nisready\nquit\n" | forge | grep -c ^bestmove; done`
    -> 1 for each. Bulk: out_full/summary.json "go": 7538, "bestmoves": 7538.

F2. `ucinewgame` RESETS the board to the start position (src/uci.cpp:254-257).
    `printf "uci\nisready\nposition startpos moves e2e4\nucinewgame\nisready\nposition\nisready\ngo perft 1\nquit\n" | forge | tail -1`
    -> nodes 20 (start position), not the 29 after e2e4.

F3. A `go` sent during another search still yields one bestmove per go, in order.

F4. An illegal move inside `position ... moves` keeps the legal prefix.
    `printf "uci\nisready\nposition startpos moves e2e4 b5a8\nisready\ngo perft 1\nquit\n" | forge | tail -1`

F5. `isready` is answered within ~0.02 s even during `go infinite`, `go ponder`, `go depth 30`.
    (Tested with a 8 s window each; readyok always arrived.)
