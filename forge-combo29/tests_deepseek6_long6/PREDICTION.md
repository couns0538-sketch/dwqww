# PREDICTION — deepseek6, long 6 (the root of internal iterative reduction)

Written before the first measuring command of long 6. Never edited after this commit.

## The patch I wrote: `IirNoRoot.patch.txt` (in this folder, plain text, `patch -p1` from the repo root)

It was made by editing a clean copy of `forge-combo29/src/search.cpp` at
6b98f2170a3210e71beed04bbd2553972c253ed7 and running `diff -u` against the original, with the two path
headers rewritten to `a/forge-combo29/src/search.cpp` and `b/forge-combo29/src/search.cpp`. It touches
nothing but that one file and adds three things:

1. `int IirRootExclude = 0;` next to `LmrCutoffThreshold` (the tunables block, line ~78)
2. `{"IirRootExclude", &IirRootExclude, 0, 1},` in the parameters table
3. the condition at line 1784 gains `&& !(tune::IirRootExclude && root_node)`

At `IirRootExclude = 0` the condition is exactly the original (the added conjunct is always false), so the
default is an identity by construction.

## Honesty at the default

Already run, all four met: 312866 / 862329 / 3024920 / 4865609 (`honesty_*.txt`).

Build `/agent/repos/work/build-l6/forge`, sha256
`5baa14998255d3c322eb1586536dc367549da4542d68246a9dac43d4942269a7`; option read from the binary:
`option name IirRootExclude type spin default 0 min 0 max 1`.

## (a) Rows on O under S14, option 0 vs option 1, no searchmoves

**The brief's expectation is EQUAL.** My prediction: **200 of 200 equal**.

Reason to expect equal, read from the code: the root is entered once per iteration, and the reduction fires
only when `tt_move.is_none()`. The root's first iteration has no hash move; but the root's own `go depth 12`
search is an aspiration loop over iterations 1..12, and from iteration 2 on the root TT entry for the same
position holds the previous iteration's best move. So at most ONE root visit per search can be affected, and
only in a way that changes the tree if the first iteration's reduced depth changes which move is best — which
then changes every later iteration. **That is exactly the risk**, so "equal" is a genuine prediction, not a
formality.

**Killed by:** any row differs. Every differing position is a finding and I will name it (index, fen, and the
two node counts) in the report rather than counting it.

## (b) `go depth 12 searchmoves <first two legal moves>` on the first 50 positions of O under S14, 0 vs 1

The root restriction changes what "a hash move at the root" means: with `searchmoves` the root's move list is
smaller, and the TT may hold a move that is not in the restricted list, which makes `tt_move` non-none but
unusable by the move picker. I predict:

| quantity | prediction | killed by |
|---|---|---|
| rows equal between 0 and 1 | **NOT all equal** — I expect at least one position to differ | 50 of 50 equal (would mean the option cannot matter even under a restricted root) |
| direction of the node sum | unknown; I predict the option-1 sum is **larger**, because refusing the reduction searches the root a full ply deeper on the affected iteration | a smaller option-1 sum (recorded as a missed direction, not as a failure) |
| the depth of the last info line | equal in most rows; I expect the option-1 run to reach depth 12 in every row it finishes, and the option-0 run to reach depth 12 as well (a `go depth N` stops at N) | any row reporting a final depth other than 12 in either run |

## (c) `setoption name MultiPV value 2`, no searchmoves, same 50 positions, 0 vs 1

With MultiPV the root is searched once per PV line, so the root is visited two extra times per iteration and
`tt_move` behaviour at the root differs from (a). I predict:

| quantity | prediction | killed by |
|---|---|---|
| rows equal between 0 and 1 | **at least one position differs** | 50 of 50 equal |
| sums | different | equal |

I state plainly: for (b) and (c) my "at least one differs" is a weak prediction — it is what I expect from the
code, but a 50-position subset of O may simply not contain a position where it bites. If 50 of 50 come back
equal I will say the test is inconclusive on this subset rather than claim the option is unwired, and I will
say what a decisive version would need (a larger subset, or a position whose root TT entry survives a
`searchmoves` restriction).

## What is a finding here

The brief says the expectation for (a) is EQUAL and every differing position is a finding. I will list every
one with its fen, not just the count, and I will not explain a difference away as noise: the determinism
check in long 1 was 200 of 200 equal between two separate processes, so on this machine a differing row is a
real difference.
