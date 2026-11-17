# CHECK of seat 21's 21-F8b — `fullmove 0` is refused and leaves the stale board — seat 08

Their claim:
> 21-F8b: "`fullmove 0` is still REFUSED (`invalid FEN: invalid FEN fields`) and leaves the stale board (perft 1 = 20
> where the position would give something else)."

## Verdict: CONFIRMS, both links

My own harness, PC r15 under PC20, Threads 1, Hash 16.

| quantity | value |
|---|---|
| python-chess **accepts** the `fullmove 0` FEN? | **yes** — so the engine is the stricter party, which is what makes this a strictness finding rather than a bad-FEN one |
| that board's legal-move count (python-chess) | **33** |
| the PREVIOUS position (startpos) | **20** |

| step | result |
|---|---|
| `position fen … w - - 0 0` | **`info string invalid FEN: invalid FEN fields`** |
| `go perft 1` afterwards | **20 nodes** |

| their claim | my measurement |
|---|---|
| `fullmove 0` still refused on the PC build | **YES**, with exactly the info string they quote |
| the refusal leaves the **stale** board | **YES** — perft 1 = 20, which is the previous board; the refused board would give 33 |

**The stale-board half is proved with synchronous perft**, which cannot be faked by a closed pipe or a reader pattern
— that is deliberate, given the season's harvest of reader traps.

## Controls (all enforced — the script aborts rather than reporting)
1. **python-chess must accept** the fullmove-0 FEN, else the engine's refusal is not strictness and the test is
   meaningless. It does (legal moves 33).
2. **The two boards must have different legal-move counts**, else "which board is held" is unanswerable. My first
   attempt used a middlegame as the previous position and both boards had 33 legal moves — the control **failed and
   the script aborted** rather than printing an ambiguous "confirms". I changed the previous position to startpos (20
   moves), which discriminates.
3. Every step's lines are read to `readyok`; the refusal line is captured rather than assumed.

## Why the control catch matters
The first version would have reported "CONFIRMS" while the perft number was **identical either way** — the exact
"test that cannot fire" failure this swarm has been documenting all night. The control turned it into an abort, and
the re-run has a number that can only come from one of the two boards.

## What this means practically
A GUI or match program that sends `fullmove 0` — python-chess will happily produce such a FEN, and some tools count
fullmoves from 0 — gets a **silent refusal and a search of the previous position**, with only an `info string` line as
notice. Combined with 08-C3 (a refused FEN still answers `readyok`) this is the same hazard from a second corner of
the FEN parser: **the engine answers on the wrong board and nothing in the protocol says so.**

## What I did NOT do
- Did not enumerate the full set of FENs the engine refuses but python-chess accepts — that is seat 21's S-F3
  territory (they measured 39 of 1,225 mutations).
- Did not test `fullmove` values between 1 and the point of acceptance, or the uint16 clamp (seat 01's S-F8).
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s21f8b.py /tmp/s21f8b.txt
