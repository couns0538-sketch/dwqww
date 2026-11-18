# Prediction — seat 03, group 1, part 3

Written after the known numbers (all matched, both programs, including the net768 pair), after the
determinism check (two r15d traces on book lines 2001-2010 byte-equal) and after the control
(LmrQuietBase 60 changes the trace), and before any r15d-vs-kF measured run. Not edited afterwards.

## The quantity my group asks for

How many of my 80 games (book lines 2001-2080, `go nodes 20000`, PC20 + net768) differ between
bin_r15d and bin_kF.

| quantity | prediction |
|---|---|
| games of 80 that differ in any record | **2 to 30** (my single guess if forced: about 12) |

## Reasoning, written down before the run

`go nodes 20000` is a fixed-node limit, so a pure speed package — one that changes only how fast
the same tree is searched — cannot change a trace: the same 20,000 nodes are searched in the same
order and the same move comes back. Under this limit the question "does kF play the same moves"
is really "does the stack patch change the search's shape", and any shape change (different
reductions, different move ordering, different pruning) shows up as a different allocation of the
20,000-node budget, which flips moves in some positions.

The kF checksum list differs from r15d in `search.cpp`, `board.cpp`, `eval.hpp`, `b4.hpp`,
`board.hpp`, `nnue_v3.hpp`, `search.hpp`, `nnue_v3.cpp` and `uci.cpp` — the search core is touched,
so "pure speed" is not guaranteed. The brief's own framing ("meant to play every move exactly as
before") is the intent, not a measurement.

The known numbers cannot decide this: the four bench pins are the same on both programs, and the
morning run of this swarm established that 6 of 9 real behaviour changes pass a green pin set —
so equal pins do not mean equal play.

I put the lower bound at 2 rather than 0 because a byte-identical outcome would need the patch to
be provably shape-preserving, which the touched-file list makes unlikely; I put the upper bound at
30 because a shape change that flips more than a third of games at a 20,000-node budget would be a
much larger behaviour change than a "6 to 8 % less engine time" package suggests.

## A second, structural prediction

If ANY game differs, then the node columns differ in the large majority of records of the differing
games (a shape change shows in node counts before it shows in moves). If NO game differs, the two
traces are byte-identical including node counts. There is no middle: with a fixed node limit and
deterministic search, node columns either agree everywhere or the search shape differs.
