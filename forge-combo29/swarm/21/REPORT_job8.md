# REPORT job8 — area 1 job 2 AGAIN (SEED 2111 values) + the mate-at-100 control

**What was asked.** The cycle's repeat of area 1 job 2 with a new seed's values, and — because
it is the sharpest consequence — the terminal-root searches (`go depth 5`, `go nodes 100`,
`go movetime 50`) on positions where a mate in 1 exists at halfmove 100 versus 99.

**The answer.** All nine predictions held. Every halfmove value ≥ 100 — including five values
drawn from SEED 2111 up to 161,959 — is accepted and answers `score cp 0 nodes 0`. **A mate in
1 is missed by all three search forms in both colours at counter 100, and found by all three
in both colours at counter 99** (control: same board, only the counter differs). 0 crashes,
0 sanitizer lines, 0 perft disagreements, and the `nodes`-line integrity assertion never fired.

**How sure.** High. The mate existence is verified independently with python-chess by copying
the board per candidate move; the engine answers are read to `bestmove` under the safe driver
with `OwnBook false` and with an assertion that the FEN was accepted before any search
answer is trusted. The 99 control proves the positions are fine and only the counter matters.

## A harness bug I found and fixed in this job (worth telling the others)

My first version of the black-side case used `6k1/5ppp/8/8/8/8/5PPP/4r1K1 b - - 100 60`,
which **Forge refuses** (`side that moved left its king in check`) and python-chess also calls
illegal. The searches then ran on the stale startpos board and answered `c2c4` / `d2d4` — which
looks exactly like "the engine searched a different tree" but is really the sticky-board trap of
21-F2 combined with a bad FEN. I replaced it with a legal position (`r5k1/5ppp/8/8/8/8/5PPP/6K1
b - - 100 60`, mate `a8a1`) and added an assertion that raises if `position fen` is refused.
Anyone else testing terminal roots at high counters should assert acceptance first.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job8/prediction.txt` | 9 predictions, all held |
| extreme values from SEED 2111 | done | `job8/out/summary.md` | 29 cases |
| mate-in-1 at counter 100 vs 99, both colours, 3 search forms | done | `job8/out/summary.md` (mate100) | 6/6 missed vs 6/6 found |
| mate verified independently | done | `job8/mate100.py` (`mates_in_one`) | copy-per-move |
| acceptance asserted before searches | done | `job8/mate100.py` | raises on refusal |

## Tables (pasted from `job8/out/summary.md`)

Halfmove ≥ 100, all accepted, all `nodes 0`:

| value | depth-4 info | bestmove |
|---|---|---|
| 100, 150, 9999, 65535, 65536, 91102, 128221, 98147, 119640, 161959, 2147483648 | `score cp 0 nodes 0` | a2a3 |

Terminal-root searches (pasted from `job8/out/summary.md`, mate100 table):

| case | python-chess mate in 1 | go depth 5 | go nodes 100 | go movetime 50 |
|---|---|---|---|---|
| white, hm 100 | e1e8 | f2f3 (missed) | f2f3 (missed) | f2f3 (missed) |
| white, hm 99 | e1e8 | e1e8 (FOUND) | e1e8 (FOUND) | e1e8 (FOUND) |
| black, hm 100 | a8a1 | f7f6 (missed) | f7f6 (missed) | f7f6 (missed) |
| black, hm 99 | a8a1 | a8a1 (FOUND) | a8a1 (FOUND) | a8a1 (FOUND) |

Other cases: `fullmove 0` refused again (stale 400 vs true 625); 65535/65536/10^9/955/3800/1869
accepted; `ep_e0` refused; `ep_e3`/`ep_e6` refused as inconsistent; `ep_d6` legal and 807 = 807;
two-kings and no-kings refused; pawn on rank 1 refused; 0 perft mismatches.

## Prediction outcome

All 9 held (P1–P9).

## Findings

No NEW finding: 21-F9 already records the halfmove ≥ 100 shortcut, and this run is its repeat
plus the terminal-root consequence. It strengthens 21-F9 in one respect worth recording — the
fault is not merely "a drawn root": at counter 100 in both colours, a mate in 1 is missed by
`go depth`, `go nodes` and `go movetime` alike, while the same positions at 99 find it. I have
appended that to 21-F9's line rather than creating a new id.

## Suspicions, not proven

- Whether the 99-vs-100 boundary is the only trigger: I did not test 100 with a `winc`/clock
  search (only depth/nodes/movetime). `go wtime` on a mate-at-100 root is untested.

## What I did NOT do

- Did not test `searchmoves`-restricted roots at counter 100.
- Did not test stalemate-at-100 with these three search forms (only mate).

## What I am NOT sure about

- The seed-drawn halfmove values are arbitrary large numbers; I did not verify that the engine
  stores them exactly (no command prints the FEN back), only that every one behaves the same.

## Times

see `job8/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job8
mate100.py  out  prediction.txt  stamps.txt
```
