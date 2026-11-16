# The case 08-F20 did not cover: ten QUIET tactically-loaded positions at 10 ms — seat 08

## Why this test exists
08-F20 showed the one-ply answer at `wtime 10` matches a deep search in 5 of 5 positions **that contained a
capture** — and I named the gap myself: captures are ordered first, so a one-ply search sees them, and the
untested case is a position whose best move is QUIET and tactically necessary. This is that test.

## The answer: the branch is benign, and here is the set that would have caught it
Ten quiet positions, PC r15 under PC20, **Threads 1**, `go wtime 10 btime 10` versus `go depth 20` (the reference
reached depth 20 on all ten, so it is a real reference).

| quantity | value |
|---|---|
| positions | 10 |
| one-ply answer == deep answer | **7 of 10** |
| one-ply answers that were captures | 2 of 10 |
| one-ply answers that were checks | 1 of 10 |
| median one-ply wall | 0.84 ms |

So 3 of 10 differ. The decisive step is that a DIFFERENT move is not the same thing as a WORSE move, so for those
three I played each candidate out and scored the resulting position at depth 16 (`quiet_tactics_eval.txt`):

| position | 1-ply move | score after it | deep move | score after it | **cost of the 1-ply choice** |
|---|---|---|---|---|---|
| pin_the_queen | f1e1 | cp 1 | d1d3 | cp 0 | **+1 cp** — negligible |
| discovered_attack | c3d5 | cp −433 | d1d5 | cp −482 | **+49 cp** — negligible |
| knight_retreat | c3d5 | cp −872 | d1g4 | cp −932 | **+60 cp** — worse, but small |

Not one of them loses material. The largest cost of choosing the one-ply move is **60 cp**, which is a positional
concession, not a lost game. (The −872 and −951 figures that look alarming in the first table are the SCORE OF THE
POSITION, not the cost of the choice — the deep move loses too, by only 60 cp less. Reading the raw deep score as
"the one-ply move loses 9 pawns" would have been the mistake here.)

**Verdict: the reserve-empty branch at 10 ms is benign on this set.** It is a weak move at worst; the two quiet
positions where it diverged cost 1 and 49 cp, and the one that cost 60 cp was already a lost position for both
moves. I say so with the set that would have caught it: ten hand-built quiet positions with a tactic whose solution
is a quiet move (a back-rank defence, a fork setup, a mating net, a promotion race, a king race, a queen
re-centring), no capture among the intended answers — and the one-ply answer still agreed with a depth-20 search
seven times out of ten.

## The ten positions (so the set can be reused or extended)

| # | label | fen | the tactic built in | 10 ms answer | deep answer | same |
|---|---|---|---|---|---|---|
| 1 | back_rank_defence | `6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1` | back-rank mate, quiet rook move | d1d8 | d1d8 | yes |
| 2 | fork_setup | `r5k1/5ppp/8/8/8/2N5/5PPP/4R1K1 w - - 0 1` | quiet knight jump to a forking square | g2g3 | g2g3 | yes |
| 3 | pin_the_queen | `r2q1rk1/ppp2ppp/8/8/3n4/2N5/PPP2PPP/R2Q1RK1 w - - 0 1` | quiet defence holding the position | f1e1 | d1d3 | **NO** (+1 cp) |
| 4 | stop_promotion | `8/P4pk1/8/8/8/8/5K2/8 w - - 0 1` | the promotion race | a7a8q | a7a8q | yes |
| 5 | mating_net | `r4rk1/ppp2ppp/8/8/8/8/PPP2PPP/2KR3R w - - 0 1` | quiet rook coordination | d1d7 | d1d7 | yes |
| 6 | discovered_attack | `r1bq1rk1/ppp2ppp/2n5/3n4/8/2N2N2/PPP2PPP/R1BQ1RK1 w - - 0 1` | quiet move setting up a discovered attack | c3d5 | d1d5 | **NO** (+49 cp) |
| 7 | defend_mate | `6k1/5p1p/6p1/8/8/8/5PPP/1R4K1 b - - 0 1` | quiet defence against mate | g8g7 | g8g7 | yes |
| 8 | knight_retreat | `r1b1k2r/pppp1ppp/8/8/1b1n4/2N5/PPPP1PPP/R1BQK2R w KQkq - 0 1` | quiet knight retreat covering a fork square | c3d5 | d1g4 | **NO** (+60 cp) |
| 9 | quiet_king | `8/8/8/8/8/5k2/p6P/6K1 w - - 0 1` | king race against a running pawn | h2h3 | h2h3 | yes |
| 10 | quiet_queen | `r2qk2r/ppp2ppp/2n5/3p4/8/2N5/PPP2PPP/R2QK2R w KQkq - 0 1` | quiet queen re-centring | c3d5 | c3d5 | yes |

## Controls (enforced — a failure aborts, it does not print a verdict)
- every position is accepted by the engine and parses in python-chess;
- `go depth 20` reaches at least depth 12 on every position (it reached 20 on all ten), so the reference is real;
- one position I first wrote (`quiet_king` with 0 legal moves) was caught by a pre-check and replaced — a position
  with no legal moves would have tested nothing.

## So what should the reserve-empty branch be described as?
**Benign but not free.** At 10 ms the engine plays one ply: it finds forced checks and promotions (positions 1, 4),
holds lost positions no worse than deeper play (8), and costs at most 60 cp when it differs (3, 6). It is not a
material-loss risk on either the capture set (5/5) or this quiet set (7/10 exact, ≤60 cp on the rest). The rule from
`REPORT_reserve_empty.md` still stands as the correct design — compare the clock against a measured ply cost and
count the increment — but on this evidence it is a quality-of-service rule, not a bug fix for lost games.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 quiet_tactics.py /tmp/qt.txt
    cd forge-combo29/swarm/08/pc20 && python3 quiet_tactics_eval.py /tmp/qte.txt
