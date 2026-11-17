# CHECK of seat 03's S-F13 — divergence happens only at lone-king roots — seat 08

Their claim:
> S-F13: "The divergence set is EXACTLY a subset of the positions with a lone king at the ROOT: 9 of 200 positions have
> one and all 4 differing positions are among those 9 (0 of the other 191 differ) — the predicate the r15 code gates
> on (`root_bare_king_`), not the material proxy I first used."

## Verdict: SUPPORTS the exclusivity on my own independent sample

My harness (`check_s03f13.py`), both builds, default options + Threads 1 + Hash 16 + `OwnBook false`, `go depth 8`,
on my R positions split by whether a side has a lone king at the root:

| class | boards | differing moves | rate |
|---|---|---|---|
| **lone king at the root** | 40 | **11** | 27.5 % |
| **no lone king** | 60 | **0** | **0 %** |

**Every divergence I found is at a lone-king root, and none of the 60 non-lone-king positions differed.** That is the
exclusivity claim, reproduced on a position set their measurement never touched, with my own harness and my own
lone-king predicate (a side with exactly one piece, a king).

Their counts (9 of 200 lone-king, 4 differing) and mine (40 of 100 lone-king by construction, 11 differing) are not
comparable in magnitude — their sample was not stratified, mine deliberately over-samples the rare class — so what
reproduces is the **structural rule**, not the rate. I say that plainly rather than quoting "11 of 40" as if it
confirmed their 4 of 200.

## The boards, for the record
All 11 differing boards are K+material-vs-bare-king endings, e.g.:
`1R6/8/k7/8/8/P7/8/2K5 b` → base `a6a7`, PC `a6a5`; and `8/8/8/4R3/2k5/P7/8/2K5 w` → base `a3a4`, PC `c1c2`.

Several are also positions where the PC build's bare-king fixes change a probing move into a waiting move, which is
consistent with the mechanism they name (`root_bare_king_`).

## Why this is a useful confirmation and not just a repeat
Seat 03 first used a **material proxy** for "endgame" and got a weaker statement (S-F9: "4 of 26 endgame positions
differ"); they then found the correct predicate was the **lone-king flag at the root** (S-F13). My check tests the
corrected predicate on independent material and finds the same sharp boundary — **0 of 60 outside it**. A rule that
holds at 100 % outside its stated condition is much stronger evidence than a rate inside it.

## What I did NOT do
- Did not determine WHICH of the two bare-king switches causes each divergence (their S-F11/S-F14 do that with
  build variants).
- Did not test other depths; depth 8 as they used.
- My lone-king sample is 40 boards; a wider sample could in principle find a divergence outside the class, and I
  would report it if so.
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s03f13.py /tmp/s13.txt
