# FINDINGS — swarm seat 12 (area 2: UCI commands under ASan + UBSan)

One line per finding, only ever added. `file` is in this folder; the `again:` part is the exact
command that shows it once more.

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| S-C1 | CONFIRMS S-F2 (seat 06) | an unreachable/structurally impossible ep square is REFUSED with `info string invalid FEN: inconsistent en-passant square`, and the engine keeps the previous position; but a legitimate post-double-push ep square with no capturer is ACCEPTED, so the rule is "no pawn beside it", not "unreachable" | check1/FINDING.md, raw check1/out_release.txt + check1/out_asan.txt; again: `python3 forge-combo29/swarm/12/check1/check.py ~/build/release/forge forge-combo29/swarm/12/check1/cases.txt /tmp/o.txt` | NEW |
| S-F1 | 2 | `ucinewgame` silently resets the board to startpos (`src/uci.cpp:254-257`, `board.set_fen(StandardStartFen)`), so `position fen X` / `ucinewgame` / `go` searches startpos, not X — a checker that does not model this reports false illegal bestmoves (it made 6 in my own job-1 harness) | job1/ucinewgame_reset.md, raw job1/ucinewgame_raw.txt; again: `printf 'position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1\nisready\nucinewgame\nisready\ngo depth 1\nisready\nquit\n' \| ~/build/release/forge \| grep bestmove` -> `bestmove a2a3` (startpos) vs `bestmove e2e3` without ucinewgame | NEW |
