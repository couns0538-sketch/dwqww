# Lone-king endings scored by RESULT: 0 of 40 defects, and the zero is shown to be meaningful

seat 19 · area 9 · build **PC r15** · **PC20** · **Threads 1** · Hash 16 · cold · `go depth 16` and `go nodes 20000`.

## 1. The three lines

**What was asked.** A second independent measurement of the lone-king class. 40 positions from real lone-king
endings, each move scored by its **RESULT** rather than its ply count, using python-chess
`is_insufficient_material()`, `is_checkmate()` and `is_game_over()`, at depth 16 and at `go nodes 20000`. Report
only the count of positions where the engine's move produces a worse result than an available alternative.

**The answer.** **0 of 40, at both budgets.** No position in the sample had an immediate mate that the engine
failed to play.

**The zero is worth something because of the control.** Exactly one of the 40 positions *had* an immediate mate
available (`6K1/8/1r4k1/8/8/2p5/8/8 b`), and the engine played it — `b6b8`, `score mate 1` — at **both** depth 16
and `go nodes 20000`. So the harness demonstrably detects a missed mate, and having found none, the zero is a
measurement rather than a vacuous pass.

**And the honest limit, which is the important part of this report:** **this does not answer the "loses six plies
sooner" question the coordinator framed, and no measurement here can.** See §4.

## 2. What the sample is

`make_loneking.py`, seed 19101:

- starting positions: set G (353 game positions) plus my `R_1911` set — 11,545 distinct starts;
- one random legal continuation from each, up to 200 plies, with python-chess;
- every position along the way where **exactly one side has only its king**, and the **side to move still has
  material** (the interesting case), deduplicated on board+side+castling+ep;
- **103,150 candidates**, of which **40 sampled** deterministically.

**These are positions that arise in legal play from real game positions — not positions from human games.**
A human game would have been resigned long before most of them. That is the main limitation of the sample and I
am not going to describe them as "real-game endings".

All 40 were verified before use: exactly one king-only side, and the side to move has material.

## 3. The result

| quantity | value |
|---|---|
| positions | 40 |
| **positions where the engine's move is a worse RESULT** | **0** |
| … at depth 16 | 0 |
| … at `go nodes 20000` | 0 |
| positions where an immediate mate was available | **1** |
| did the engine play it, at both budgets? | **yes — `b6b8`, `score mate 1`** |

Per-position rows (legal-move count, best available status, both moves, both statuses) are in
`loneking/out3/RESULT.txt`.

## 4. What this does and does not establish — the limitation stated plainly

With **no tablebases** (none on this machine; the lichess mirror returns 403 / an SSL failure) and no deeper
oracle, a "result" can be established **only at the terminal position**. That means:

- **`is_checkmate()` is exact** — I can tell that a move mates at once.
- **`is_insufficient_material()` and `is_game_over()` are exact** — I can tell that a move ends in a dead draw.
- **A won-but-not-yet-decided position is `unknown`** — I cannot tell whether the side to move is winning, nor
  how many plies a win takes.

So the question I actually answered is: *"did the engine miss an immediate mate, or choose a drawn line where
another move mates at once?"* The answer is no, 0 of 40.

**It is NOT the question "does the engine's move lose six plies sooner than the best move".** That question needs
a distance-to-mate oracle, which needs tablebases. Anyone reading "0 of 40" as "the engine never throws away a
win in lone-king endings" would be over-reading this by a wide margin — the sample had only **one** position
where a win was provable at all.

## 5. A bug in my own first version, kept in the record

My first two runs reported **2 of 40**, and both were **false positives caused by my own ordering bug**. I had
written `defect = alt_best > engine_result` with the scale `WIN=2, DRAW=1, UNKNOWN=0`, which treats a
non-terminal position as *worse than a draw*. The two flagged positions were both **correct queen promotions**:

- `8/8/8/1K6/8/5b2/k2p4/8 b` — engine `d2d1q`; the only alternative that "terminates" is `d2d1b`, which leaves
  KvK, **a draw**. The engine's queen promotion is right and the flagged alternative is the blunder.
- `8/5P2/8/8/7k/8/1K6/8 w` — engine `f7f8q`; `f7f8b` and `f7f8n` both leave **KvK**, draws.

So the first version reported **the correct move as a defect and the throwing-away move as the reference**. The
tell was that both "defects" were queen promotions in positions with a lone king — an obvious pattern I should
have questioned before writing anything. The fix restricts the defect test to **"an alternative mates at once
and the engine's move does not"**, which is the only comparison this oracle can support. `out/` and `out2/` are
kept beside `out3/` so the error is visible.

## 6. Finding

**19-F54 — on 40 lone-king endings (103,150 candidates, seed 19101, drawn from legal play out of set G and
R_1911), the PC build at PC20 / Threads 1 / Hash 16 produced a worse RESULT than an available alternative in
0 of 40 positions, at both `go depth 16` and `go nodes 20000`.** The one position with an immediate mate
available was played correctly (`b6b8 mate 1`) at both budgets, which is the control that makes the zero
non-vacuous. **Scope: this tests missed immediate mates and drawn-instead-of-mating choices only** — with no
tablebases, a won-but-undecided position is not adjudicable, so it does **not** test the "loses N plies sooner"
question.

### Suspicions, not proven

- That the single mate position is unrepresentative and a larger sample would find a missed mate. 0 of 40 with
  one testable case means the rate is unmeasurable from this sample; the honest interval from one observation is
  very wide.
- That the engine would do worse on lone-king positions with the weaker side to move (my filter requires the
  side to move to hold material). Untested: that is a different and probably more interesting sample.

## 7. What I did NOT do

- **No tablebase oracle.** Attempted and blocked (403 / SSL). Without it the ply-distance question is not
  answerable and I did not pretend otherwise.
- 40 positions, not 50, as instructed (a second seat is running the same job and two independent rates beat one
  large sample).
- I did not test the mirror case (the king-only side to move), nor the fifty-move counter near 100, which seat
  05/25's work covers on this same build.

## 8. Files

`loneking/make_loneking.py`, `loneking/loneking40.fens` (the sample), `loneking/score_results.py`,
`loneking/out3/RESULT.txt` (the corrected run), and `loneking/out/`, `loneking/out2/` (the two runs with my
ordering bug, kept deliberately).
