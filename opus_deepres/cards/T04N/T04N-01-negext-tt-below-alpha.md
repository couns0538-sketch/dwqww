# T04N-01: negative extension of the TT move when the TT score is at or below alpha (non-cut nodes)
Status: COMPLETE

## Source
- Ethereal f71ac4769a "Negative Singular Extensions when ttValue <= alpha" (2023-03-17), commit text with three
  OpenBench results: https://github.com/AndyGrant/Ethereal/commit/f71ac4769a ; http://chess.grantnet.us/test/31668/
  (STC), http://chess.grantnet.us/test/31672/ (LTC), http://chess.grantnet.us/test/31682/ (SMP).
- Context from commit titles and dates only: Ethereal got its cut-node flag later (3071b40, 2023-04-23, "Introduce
  cutnodes, and perform IIR on them"), so f71ac47 was measured with no cut-node negative extension in place.
- Overlap check: notes/T04F/TABLE.md row 21 (Caissa fd723a2 bundle "-3 non-PV; -1 when TT score <= alpha") was filed
  as "DIFFERS: -2 / -1, s:1107-1111; -3 non-PV PREPARED in SingularV2 | evidence for T04-06 / SingularV2, no card"
  (corrected by verify: the row made no card and did not say SingularV2 has the below-alpha branch). Own check of our code: SingularV2 (fable-fb2-j3:src/search.cpp:1222-1231) has the multicut on
  the singular score, -3 at non-PV on TT score >= beta and -2 at cut nodes, but no TT-score-below-alpha branch. This
  card is that missing piece alone, with a single-change source number and an LTC pass.

## Licence
Ethereal GPL-3.0 (tools/licence_at.py at f71ac4769a: LICENSE GPL-3.0, row in notes/T04N/licences.md): ideas only.
Commit text and OpenBench result blocks were read, never source.

## Mechanism
The singular test searches all moves except the TT move at reduced depth against a bound below the TT score. When
that search reaches the bound (the TT move is not singular) and no multicut return applies, the lock shortens the TT
move only if its TT score already beats beta (-2) or the node is an expected cut node (-1); otherwise the TT move
keeps full depth. The idea: also take one ply off the TT move when its stored score is at or below alpha. The table
then says the TT move does not raise alpha and other moves are about as good, so its subtree gets less depth.
At non-PV nodes (alpha = beta - 1) this covers every non-cut node whose TT score is below beta; at PV nodes it fires
only when the TT score does not improve alpha. Own design, no constants taken from the source.

## Forge fit
`bash tools/forge_has.sh 'cut_node'`: 10 hits; the extension chain is src/search.cpp:1100-1111 (singular +1 / +2,
`singular_beta >= beta` returns, `tt_score >= beta` -> -2, `cut_node` -> -1, else 0). The singular test already
requires `tt_bound != BoundUpper` (s:1089), so the TT score is a lower bound or exact. Change: one more branch after
the cut-node branch, `tt_score <= alpha` -> minus NegExtTtAlpha plies. With SingularV2 ON the same branch goes after
its cut-node -2, so the two options stack and can be gated in either order.

## Expected gain
Ethereal f71ac47: STC 10+0.1 Threads=1 +4.66 +- 3.19, SPRT [0,3] LLR 2.96, 22,208 games (W 5,589 L 5,291
D 11,328); LTC 60+0.6 Threads=1 +2.44 +- 1.95, SPRT [0,3] LLR 2.95, 57,696 games (W 13,931 L 13,526 D 30,239); SMP
5+0.05 Threads=8 +3.16 +- 2.96, SPRT [-1,2.5] LLR 2.95, 25,803 games. Book: not in the commit text (corrected by verify: OpenBench pages 31668 / 31672 / 31682 all list Pohl.epd).
Forge estimate: +0.5 to +2 Elo at STC **UNPROVEN** - below the source, because the lock already shortens cut nodes,
which the source did not do when it measured; the source LTC interval is +0.5 to +4.4.

## Effort
Crew 1.5 h (option, about 6 lines, OFF pins, ON smoke). CPU: one STC SPRT [0,5] up to ~6.6k games, about 13-15 h
at the measured 430-502 games/h; an LTC confirm costs the same or more. GPU 0.

## Test plan
1. OFF: bench and perft pins equal the lock (default 0, branch never taken). 2. ON: bench node count changes (option
is live); go perft 1 legality smoke; mate probe OFF/ON; in a scratch build only, count how often the branch fires
per 1M nodes. 3. Gate: UHO SPRT [0,5] at STC Threads=1, then LTC. If SingularV2 is gated first, re-run on top of it.

## OFF-by-default design
UCI option `NegExtTtAlpha`, spin, default 0 (off), range 0-2 = plies taken off the TT move; start value 1 (own
choice; 2 only as an SPSA upper bound). At 0 the new branch is skipped, so the extension decision, node counts and
the bench signature stay those of the lock.
