# The counter-100 mate gap — a base-tree defect, 7 of 7 cases

**One page. Stands on its own.** Seat 15, area 5. Every number is pasted engine output from a
committed script; **Threads 1**, Hash 16, one fresh process per search, `go depth 8`.
Base tree = commit `6b98f217` under **S14**. PC build = r15 under **PC20**.

---

## 1. The defect in one sentence

When the halfmove clock is at or past 100, the base tree answers `cp 0` with **0 nodes** without
searching — and that loses forced mates whose winning move is a **capture or a pawn move**, because
either of those **resets the halfmove clock**, so the mate lands before the 100th half-move no matter
what the counter says when the move is made.

## 2. Why the existing rule misses it

The current rule (file 6) is:

> A `cp 0` at counter H is a defect only if a forced mate exists with `2N - 1 <= 100 - H`.

That comparison is right for mates made of **quiet, non-capturing, non-pawn** moves. It is wrong for
every mate that resets the clock, because after the reset the relevant counter is 0, not H.

**One-line statement of the gap:**

> `2N-1 <= 100 - counter` ignores that a **capture or pawn move resets the halfmove clock**, so a
> mating line containing one is reachable even when `2N-1 > 100 - counter`.

**Corrected form:**

> A `cp 0` at counter H is a defect if a forced mate exists whose line **either** ends within `100 - H`
> plies **or** contains a capture or pawn move before the 100th half-move (which resets the counter),
> **and** the board at counter H still scores `cp 0`.

## 3. The seven cases — both builds, node counts

Each board was verified with python-chess to have **exactly one** legal mating move, and that move to
be a pawn move or a non-pawn capture. All at **counter 100**. Raw: `test7_out.txt`.

| # | kind | board (counter 100) | only legal mate | **base tree / S14** | **PC build / PC20** |
|---|---|---|---|---|---|
| 1 | PAWN | `8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1` | `a7a8q` | `cp 0`, **0 nodes**, `a7a8q` | **`mate 1`**, 265 nodes, `a7a8q` |
| 2 | PAWN | `8/P7/k7/P7/2K5/8/8/Q7 w - - 100 1` | `a7a8q` | `cp 0`, **0 nodes**, `a7a8q` | **`mate 1`**, 233 nodes, `a7a8q` |
| 3 | PAWN | `8/P7/k7/P7/2K5/8/8/4Q3 w - - 100 1` | `a7a8q` | `cp 0`, **0 nodes**, `a7a8q` | **`mate 1`**, 257 nodes, `a7a8q` |
| 4 | CAPTURE | `r5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1` | `h1a8` | `cp 0`, **0 nodes**, **`h1g2`** | **`mate 1`**, 145 nodes, `h1a8` |
| 5 | CAPTURE | `n5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1` | `h1a8` | `cp 0`, **0 nodes**, **`h1g2`** | **`mate 1`**, 145 nodes, `h1a8` |
| 6 | CAPTURE | `b5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1` | `h1a8` | `cp 0`, **0 nodes**, **`h1g2`** | **`mate 1`**, 137 nodes, `h1a8` |
| 7 | CAPTURE | `q5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1` | `h1a8` | `cp 0`, **0 nodes**, **`h1g2`** | **`mate 1`**, 137 nodes, `h1a8` |

**Base tree missed the mate in 7 of 7. PC build found it in 7 of 7.**

## 4. Why four capture cases were necessary — the sentence that matters

> **In the pawn cases the base tree plays the right move for the wrong reason — 0 nodes means "first
> legal move", and there the first legal move happens to be the mate — but in the capture cases it
> plays a different move entirely (`h1g2`), neither the mate nor a capture, so it loses the win
> outright.**

One pawn case would have suggested a cosmetic scoring bug: the right move is played, only the score is
wrong. The capture cases show a **wrong move** — a lost half-point in a real game. That is a different
severity, and it only appeared by varying the material on the captured square (`r`, `n`, `b`, `q`) so
the mating move was a capture rather than a push.

## 5. Scope, stated plainly

- **Both builds, Threads 1, one depth (8).** The mates are in 1 ply, so no horizon question arises.
- **Base-tree-only defect.** The PC build is correct in all 7, so this is already repaired there —
  the same shape as 15-F12 and 15-F28.
- The seven boards are **minimal demonstrations constructed from a known working geometry**, not a
  sample from games. **I make no claim about how often this arises in the owner's games.** A frequency
  estimate would need these patterns searched for in real positions.
- I did not test mates that need several plies before the reset move. The corrected form above already
  covers them ("within the remaining plies"), but only the one-ply case is measured here.

## 6. Evidence index

| file | contents |
|---|---|
| `test7_out.txt` | the run: all seven boards, both builds, scores/nodes/bestmoves |
| `pawn100_check.txt` | the original single pawn case, both builds |
| `RESULT_counter100.md` | the longer write-up this page condenses |
| `variants.py`, `capfind2.py` | how the seven boards were derived and verified single-mate |
| `file6_kr_h91.txt` | the K+R case that is **correctly** drawn (15-R3), for contrast |
