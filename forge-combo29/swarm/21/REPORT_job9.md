# REPORT job9 — CHECK of 30-F7, seat 21

**What was asked.** THE CYCLE 2(a): reproduce an unchecked finding from another seat, from
its command text alone, with a harness of my own. 30-F7 (seat 30, area 10) was unchecked.

**The answer.** **CONFIRMS 30-F7.** All three of its claims hold on boards I chose myself,
with both controls holding: a black mate-in-1 and a white mate-in-1 are both missed at
halfmove 100 (`cp 0`, 0 nodes, non-mating move) and both found at 99 (`mate 1`, 105 nodes);
a quiet board where White is a clean rook up answers 0 nodes and `cp 0` at counter 100 and
searches 759 nodes with a real score at 99.

**How sure.** High. The controls are the same boards at counter 99, so the harness demonstrably
sees the difference; every case asserts the FEN was accepted (the 21-F2 stale-board trap) and
asserts a `nodes` value was parsed (so an empty parse cannot pass as confirmation).
The mate existence is verified independently with python-chess using a board copy per move.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job9/prediction.txt` | 6 predictions, all held |
| my own harness on my own boards | done | `job9/check_30f7.py` | 12 rows |
| acceptance asserted before each search | done | same | raises on refusal |
| `nodes` parse asserted non-empty | done | same (`parse_nodes`/inline) | would raise |
| counter-99 controls for every claim | done | `job9/out/summary.md` | all held |

## Table (pasted from `job9/out/summary.md`)

| board | hm | python mate in 1 | search | engine bestmove | nodes | verdict |
|---|---|---|---|---|---|---|
| black_mate | 100 | a8a1 | go depth 5 | f7f6 | 0 | MISSED |
| black_mate | 100 | a8a1 | go nodes 100 | f7f6 | 0 | MISSED |
| black_mate | 99 | a8a1 | go depth 5 | a8a1 | 105 | MATE FOUND |
| black_mate | 99 | a8a1 | go nodes 100 | a8a1 | 84 | MATE FOUND |
| white_mate | 100 | e1e8 | go depth 5 | f2f3 | 0 | MISSED |
| white_mate | 100 | e1e8 | go nodes 100 | f2f3 | 0 | MISSED |
| white_mate | 99 | e1e8 | go depth 5 | e1e8 | 105 | MATE FOUND |
| white_mate | 99 | e1e8 | go nodes 100 | e1e8 | 84 | MATE FOUND |
| quiet_white_up | 100 | none | go depth 5 | e2e3 | 0 | 0 NODES |
| quiet_white_up | 100 | none | go nodes 100 | e2e3 | 0 | 0 NODES |
| quiet_white_up | 99 | none | go depth 5 | e2e4 | 759 | searched |
| quiet_white_up | 99 | none | go nodes 100 | e2e4 | 100 | searched |

## Prediction outcome

All 6 held; the direction (CONFIRMS) was right.

## Findings

`21-C3 | CONFIRMS 30-F7` — added to FINDINGS.md.

## Suspicions, not proven

- 30-F7's phrase "even +13 cp" is seat 30's own board, which I did not use; my quiet board is
  a rook up and behaves the same way, so the claim does not depend on that particular value.
- In `go nodes 100` at counter 100 the score line still reports `seldepth 64` while `nodes 0`.
  That looks like the terminal-root path emitting a fixed seldepth. Not proven; I did not read
  the emitting code for that figure.

## What I did NOT do

- Did not test 30-F7's `movetime` variant (my 21-F9 already covers `go movetime 50` and it
  behaves the same).
- Did not check 30-F8 (the proposed patch), which is a different finding.

## What I am NOT sure about

- Whether counters below 100 but above the actual fifty-move count on a board matter; the
  shortcut is a plain `>= 100` test, so I did not explore 90–99 beyond the 99 control.

## Times

see `job9/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job9
check_30f7.py  out  prediction.txt  stamps.txt
```
