# REPORT — seat 07, job 18: a validated SEE oracle, replacing the job7 non-result

## What was asked / the answer / how sure

**Asked:** continue the area-7 read. Job 7 left SEE explicitly unresolved ("my oracle was wrong twice,
I claim nothing"). This job closes it with an oracle that is **validated before it is used**.

**Answer:** with a python-chess-only swap-list oracle that passes five hand-settled cases, **150
positions of set O at depth 1 produced 0 illegal bestmoves and 0 cases of a negative-SEE capture
being chosen while a quiet move existed**. The honest scope: this exercises the engine's depth-1
choice, not `see_ge`'s return value directly, because `see_ge` is not reachable through UCI.

**How sure:** high that the oracle now computes the textbook static exchange — five known-value
assertions, three of which corrected mistakes in my *own expectations*, not just my code.

## Honesty numbers

Base build: 312866 / 862329 / 3024920 / 4865609 (job0/raw/summary.txt). No engine source changed.

## How the oracle was validated (this is the point of the job)

`job18/oracle_selftest.py` asserts values settled by hand with python-chess move lists:

| case | move | expected | why (settled with python-chess) | oracle |
|---|---|---|---|---|
| `4k3/8/8/8/8/8/4r3/4K3 w` | `e1e2` | **+500** | `attackers(BLACK, e2)` is empty → undefended rook | +500 |
| `2b1kbn1/...` (job7's case) | `e4f5` | **+100** | after exf5 Black's captures are only h3e3/d4e3 | +100 |
| `r1bqkbnr/.../2P5 w` | `b2b4` | **0** | b4 Nxb4 cxb4 — White wins a knight with a pawn *and loses that pawn* | 0 |
| `4k3/8/8/8/8/3p4/4Q3/4K3 w` | `e2d3` | **+100** | `attackers(BLACK, d3)` is empty | +100 |
| `4k3/8/8/8/2p5/3p4/4Q3/4K3 w` | `e2d3` | **−800** | Qxd3 cxd3 → +100 − 900 | −800 |

    RESULT: every self-test case matched the hand-settled value

**Three of my own beliefs were wrong along the way**, and each was caught by checking with
python-chess instead of trusting the oracle or myself:

1. my first recursive minimax scored `Kxe2` +500 — I claimed it should be negative, but the rook is
   *undefended*, so +500 is correct and my expectation was wrong;
2. I claimed `b2b4` was +200 (knight for pawn) — it is **0**, because White's capturing c-pawn is
   itself lost in the recapture;
3. I expected `Qxd3` to be −800 in a position where the pawn was undefended — it is +100.

That is why this oracle is trustworthy and the job7 one was not: the job7 version was tuned until it
agreed with the engine in places, which is circular; this one is pinned to externally settled values
first and only then pointed at the engine.

## Result against the engine

    positions checked 150
    illegal bestmoves 0
    losing captures chosen while a quiet existed at depth 1: 0

Raw: job18/run.txt, job18/raw/differences.txt (empty).

**Deliberately not counted as a fault:** at depth 1 a negative-SEE capture can legitimately be the
engine's choice, because the opponent's recapture may be pruned at that depth. The metric is therefore
reported as informational, and the pass/fail part of the run is the illegal-bestmove count.

## Findings

**07-C15** in FINDINGS.md.

## Suspicions, not proven

- `see_ge` is used with thresholds derived from depth (`-SeeQuietMultiplier * lmr_depth * lmr_depth`,
  `-SeeNoisyMultiplier * depth`) in search.cpp; those thresholds are tunables I did not exercise.
- `promotion_recapture_exchange` (board.cpp:28) is a separate rare path for promotion captures and was
  not covered by this depth-1 probe.

## What I did NOT do

- Did not call `see_ge` directly (it is not exported to UCI and I will not add a test hook to engine
  source).
- Did not test promotion-with-capture or en-passant SEE paths explicitly.

## What I am NOT sure about

- Whether a depth-1 probe can reveal a wrong `see_ge` at all in most positions: move ordering effects
  on a 1-ply search are weak, so a clean result here is weaker evidence than the invariant-style tests
  in jobs 13-15.

## Times

See job18/stamps.txt.
