# Seat 17 — every finding with its status and GUI reachability

Every row states: my id, what it is, its current state after FABLE_TO_swarm_6, the build and settings it used,
and — the column the coordinator asked for — **whether a GUI can reach it in a normal flow**. A fault only
reachable by setting an option to a value no GUI sends is documentation; one reachable from normal play is a
defect. All scores Threads 1 unless stated.

| id | what it is | state | build / settings | GUI-reachable? | verdict |
|---|---|---|---|---|---|
| **S-F1** | `go depth N searchmoves <name matching no legal move>` answers `bestmove 0000` on a position with 20 legal moves, after five `info depth` lines at `nodes 0` | **LIVE on the PC build** (re-measured, PC20) | base 6b98f217 / S14 and PC r15 / PC20 | **Only with an empty/ill-fitting `searchmoves`.** No ordinary GUI sends `searchmoves` unless the user asks to restrict the root; a GUI that does (some analysis panels) and filters by a stale or wrong side triggers it. **Not on the owner's PC path.** | defect, low exposure |
| **S-F8** | `searchmoves` with no legal match ignores the node/movetime budgets and prints 64 `info depth` lines all `nodes 0 time 0` | **LIVE on the PC build** | PC r15 / PC20 | same trigger as S-F1 — needs `searchmoves`. Not reachable without it | reporting defect, low exposure |
| **S-F4** | `OwnBook` defaults TRUE, so clock/movetime measurements from the initial position are answered by the book in ~0 ms with no `info depth` | documentation (method trap) | base / default | Yes, any GUI on a book position — but it is correct behaviour, not a fault. Matters only for harness authors | not a defect |
| **S-F7** | history/LMR tunables at both advertised extremes: 0 sanitizer lines, 40x node spread proves they applied | negative | base / ASan+UBSan | Extremes are settable from any GUI, so reachable — and clean | no defect |
| **S-F9** | `Hash` 1/8/32/512/2048 changes only the pressure (hashfull 440/58/10/0/0), same bestmove; 18 ASan searches clean | negative | base / ASan | Yes, `Hash` is a normal GUI option | no defect |
| **S-F11** | the select()+buffered-`readline()` artefact that fabricates an unbounded run | method note | n/a | not engine | harness rule |
| **S-F3/S-F5/S-F6** | bench 13 pin immune to history drift; clock-plan multiply safe at max int64; deep search (seldepth 48-64) clean under ASan | negatives | base | Yes, all normal paths | no defect |
| **S-C11 / S-C12** | halfmove-100 mate scored `cp 0` | **WITHDRAWN as defects** per file 6 | base / S14, PC / PC20 | the rule is the owner's match program, so the engine is right | correct behaviour |
| **S-C0/S-C8** | 19-F12 and seat 10's warm/cold rule reproduced | confirmations | base | harness-relevant | — |
| **S-C1/S-C2** | 07-R1 and 07-F1 reproduced | confirmations | base | same `searchmoves` trigger | — |
| **S-C4/S-C5/S-C6** | 27-F2 (`go nodes` < 26 -> a2a3), 27-F4 (Clear Hash keeps histories; node counts change 20/20) | confirmations | base | `go nodes` is a normal GUI limit; Clear Hash is a normal button | note |
| **S-C9/S-C10** | a refused FEN still answers `readyok` and keeps the old board; `fullmove 0` refused while python-chess accepts it | confirmations | base | **YES — this is the one reachable from a plain GUI flow**: load a position, get `readyok`, engine plays the previous game's move. But it needs a GUI to send a FEN the engine refuses | potential defect, medium exposure |
| **NEW: mid-search setoption** | 13 switches to their worst value during a search (`go infinite` + `go nodes`): 26 of 26 cases gave a legal bestmove, readyok and 0 sanitizer lines, including Threads 256 | negative | PC r15 / PC20 / ASan+UBSan / Threads 1 | **Only if a GUI changes an option mid-search**, which the owner's match program and self-play never do | no defect; also observed that setoption publishes `bestmove` BEFORE `readyok` |
| **NEW: budget sensitivity** | across the match path's own budgets (20000 / 50000 / 250000), 9 of 10 positions keep the same bestmove and 1 changes it (`c8c3` at 20000 vs `d6e6` at 50000/250000) | new measurement | PC r15 / PC20 / Threads 1 / 10 G positions | **YES — these are exactly the budgets the owner's matches send** | not a fault; means 20000 and 250000 are not strictly the same opponent |
| **NEW: S-C9's realistic trigger** | a hand-written start FEN that is invalid in the SUBTLE way — the side to move left its own king in check (`6k1/5ppp/8/8/8/8/5PPP/1q4K1 b - - 0 1`) — is refused with `invalid FEN: side that moved left its king in check`, then the engine answers `readyok` and plays a legal move from the PREVIOUS board (startpos in a fresh process), so the caller gets a plausible move for a position that was never loaded | **now a measured trigger**, not a hypothetical | PC r15 / PC20 / Threads 1, and base tree | **YES — and it is easy to hit by accident: writing 30 start FENs by hand hit it twice (2 of 30)** | real hazard for any GUI or harness that builds positions by hand; the engine's refusal is correct, the silent continuation is the hazard |
| **NEW: 30-game clock test** | 30 games / 1,416 plies at the owner's 6 s + 0.06: **0 forfeits, 0 engine-caused illegal moves**, clock dipping to **194 ms** without a forfeit (5 games under 600 ms) | new measurement | PC r15 / PC20 / Threads 1 | **YES — the match clock itself** | no defect found; closest approach 194 ms still produced a normal move |
| **NEW: node tiers, depth logged** | across the self-play tier (2000) and the three match tiers, only 6 of 10 positions keep one move; 4 differ, and the depth reached spans 5-17 on the same board; position 6 gives three different moves across the four budgets | new measurement | PC r15 / PC20 / Threads 1 / 10 G positions | **YES — both the self-play and match tiers are the owner's** | not a fault; the tiers are 8-12 plies apart, which is the real meaning of "not the same player" |
| **NEW: non-monotone moves** | on one tactical position the best move changes at EVERY depth (d6 `h8f8`, d7 `d6e6`, d8 `c8c3`, d9 `f5h6`, d10 `d6e6`), so a position can look stable or wildly erratic purely as a function of where a node budget lands — **any A/B comparison at fixed nodes on a tactical position must record the depth reached as well as the move**, or the result is uninterpretable | resolved | PC r15 / PC20 / Threads 1 | method rule, applies to every harness (not an engine fault) | not a fault; the reason to log depth alongside move |
| **NEW: depth vs selection** | that one change is a pure DEPTH effect, proven by identical nodes: `go nodes 20000` == `go depth 8` (13,628 nodes, cp 7, `c8c3`) and `go nodes 50000` == `go depth 10` (45,673, cp 16, `d6e6`). The move is not monotone in depth: d6 `h8f8`, d7 `d6e6`, d8 `c8c3`, d9 `f5h6`, d10 `d6e6` | resolved | PC r15 / PC20 / Threads 1 | **YES — the match budgets** | no selection effect; a 20000 move is a depth-8 move here, a 250000 move is depth 15 |
| **NEW: softnodes** | `go softnodes N` deterministic 12/12, stops at a finished depth, overshoot 1.02x-2.06x (worst: 514,117 nodes for a 250,000 budget) | new measurement | PC r15 / PC20 / Threads 1 | **YES — this is the owner's own self-play path** (`go softnodes 2000`). The overshoot at N=2000 is 1.16x-1.66x | on the production path; design consequence, not a fault |

## What this column changes

Ranked by what the owner can actually hit:

1. **softnodes overshoot** — on the PC's real self-play path, measured, deterministic. Not a fault (the engine
   reports the true count) but it is a real budget overrun the owner should know about.
2. **S-C9** — a refused FEN + `readyok` + old board is reachable from a normal GUI flow (load position, engine
   plays a move from the previous game). Medium exposure, needs an invalid FEN to start it.
3. **S-F1 / S-F8** — real defects, but they need `searchmoves`, which the owner's match program and self-play
   never send. Documentation-grade for the PC, worth fixing for GUI users.
4. Everything else: clean, or documentation.
