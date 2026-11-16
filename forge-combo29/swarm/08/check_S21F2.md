# CHECK of seat 21's finding 21-F2 — seat 08 (area 8)

Their finding, as written on branch for-fable-and-opus/swarm-21, FINDINGS.md:

> 21-F2 | 1 | Beyond "after a refused FEN it keeps the previous position" (known, file 1): the refused command
> STILL answers `readyok`, so a GUI that syncs on readyok is handed a move of the previous game — a [...]
> hazard.

## Verdict: CONFIRMS

My harness is my own: `forge-combo29/swarm/08/check_s21f2_v2.py`. It is a long-lived engine process that reads
stdout until `bestmove` before sending anything else, because my FIRST version of this check piped `quit` into
the engine right after `go` and got a fabricated `a2a3` — seat 19's 19-F12 fault, in my own check, caught by
myself before this file was written. The first version and its invalid output are committed as
`check_s21f2.py.v1_INVALID` so the mistake is visible.

The claim is a chain of three links and I measured each one separately.

| link | their claim | my measurement | agrees? |
|---|---|---|---|
| 1 | a refused `position fen` still answers `readyok` | refusal line `info string invalid FEN: invalid FEN fields`, then exactly **1** `readyok` for that command — same count as an accepted position | yes |
| 2 | after the refusal the engine keeps the PREVIOUS position | `position GOOD2` -> `position BAD`(refused) -> `go perft 1` gives **51** nodes; `position GOOD2` -> `go perft 1` also gives 51; the earlier board would have given 400 | yes |
| 3 | a GUI is handed a move of the previous position | `position GOOD2` -> `position BAD2`(refused, "castling right without king and rook") -> `go depth 1` answers **b6b5**, which is **legal in GOOD2 and ILLEGAL in the board the GUI asked for** | yes |

Link 2 uses synchronous `perft`, which cannot be faked by a closed pipe, so it does not depend on the
`bestmove` path at all. Link 3 records the info-line count (1) so a fabricated answer (0 info lines) cannot pass.

## Controls (enforced by assertion, so a vacuous pass aborts instead of reporting)
- the two good positions must give **distinct non-zero** perft 2 numbers: 400 and 1574 — they do;
- engine perft 2 must not be below the position's legal-move count — it is not;
- the FEN I expect to be refused must actually be refused, else the script exits with
  "the check has nothing to test" — it is refused.

## A correction to my own first attempt, worth recording
My first BAD2 was `...R1B1K2R w Q - 2 8` — a `Q` castling right with a rook on a1. The engine ACCEPTED it,
correctly, because a1 holds a rook: `Q` was a *valid* right in that position. I had assumed any single-letter
right was bogus and nearly wrote "the engine accepts an impossible castling right, contradicting seat 21".
The correct bogus case is theirs: `...RNBQKBN1 w KQ` where h1 is EMPTY, refused with `castling right without
king and rook`. My error, not the engine's.

## Show it again

    cd forge-combo29/swarm/08 && python3 check_s21f2_v2.py ~/builds/release/forge /tmp/out_s21f2.txt

Raw output committed as `check_S21F2_raw.txt`.

## Why this matters to my own area
Every timing harness I run sends `position fen` and then syncs on `readyok`. If a FEN I feed it were ever
refused, the search would silently be on the previous position and my "latency for position X" would really be
latency for position X-1. My clock harnesses use 200 fixed FENs from O and G and one generated set; none were
refused (a refusal would have raised in `read_until`, and the `nlines >= 2` audit rules out silent zeros), so
no result of mine is affected. This finding is exactly the failure mode that would have produced a wrong number
without any error message.
