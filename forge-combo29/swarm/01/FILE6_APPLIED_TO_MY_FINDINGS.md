# FABLE_TO_swarm_6's test, applied to my own fifty-move findings

**Seat 01, 2026-11-16. This retires my S-F5 and S-F17 as defect claims, and records the one case where
file 6's inequality is formally false but a mate is still reachable.**

## What file 6 says
A draw by repetition or by the fifty-move rule scored 0 is **not** a defect, because the owner's match
program ends the game at the third occurrence and at the 100th half-move. A `cp 0` at a high counter is a
defect **only** when a forced mate ends no later than the 100th half-move. The test: the same board at
counter 0, `go depth 20`+, read `mate N`; a defect only if `2N - 1 <= 100 - counter` **and** the real-counter
board still scores `cp 0`.

## The test run on my boards (PC r15, PC20, Threads 1, Hash 16, `go depth 20`)

| board | my claim | `mate N` at counter 0 | 2N−1 | 100−counter | inequality | base at the real counter | verdict |
|---|---|---|---|---|---|---|---|
| `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1` | S-F5 / S-F17 | `mate 1` | 1 | 0 | **false** | `cp 0` | **not a defect** |
| same board at counter 99 (control) | — | `mate 1` | 1 | 1 | true | `mate 1` | correctly handled |
| `8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1` | S-F22 | `mate 2` | 3 | 0 | **false** | `cp 0` | see below |
| `8/8/8/8/2K4Q/8/8/1k6 w - - 99 1` | S-F23 | `mate 2` | 3 | 1 | false | `cp 0` | not a defect |

**So file 6 retires my S-F5 and S-F17.** A mate that would land on the 101st half-move is past the point
where the match program ends the game, so scoring that node `cp 0` is right, and my patch is not needed for
it. The counter-99 control confirms file 6's own claim that the real exception (a mate ON the 100th
half-move) is already handled — both builds answer `mate 1` there.

## The one case the inequality misses: a counter-RESETTING mating line

`8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1`. White's mating line begins `h6h7` — a **pawn move** — and a pawn move
resets the fifty-move counter:

```
python3 -c "import chess;b=chess.Board('8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1');b.push(chess.Move.from_uci('h6h7'));print(b.halfmove_clock)"
-> 0
```

The game therefore **never reaches** "the 100th half-move without a capture or pawn move" on that line, so
the match program's cut-off never fires and the mate is real. File 6's inequality computes `2N−1 = 3 > 0`
and calls it "not a defect", but that arithmetic assumes the counter advances monotonically along the
mating line — which a pawn move or a capture breaks.

Base tree scores `cp 0` there; the PC build finds `mate 2`. So this is the narrow class where a `cp 0` at a
high counter on the BASE tree is still a missed mate, and **it is already repaired on the PC build**.

## What I do with my patch
Not applied anywhere, as instructed. Its only remaining justification would have been this resetting class,
and the PC build already covers it (`FORGE_FIX_ROOT_DRAWN` searches the root). File 6 states plainly that no
patch is needed, and I agree on the evidence above: on the base tree the class exists, on the tree the owner
actually plays it is already fixed.

## Record
- S-F5 and S-F17: **RETIRED as defect claims** by file 6's test (S-C6). The measurements stand; the reading
  "this is a defect in real play" does not.
- S-F22: still a true statement about the base tree, but its scope is now exactly "the counter-resetting
  class on base 6b98f217", not "a defect worth patching" (S-F48).
