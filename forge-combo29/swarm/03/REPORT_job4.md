# REPORT — seat 03, job 4: the same perft sets on the PC (r15) build vs the base build

**What was asked.** Re-run my perft sets on the PC build and say whether the node counts are identical to the base
build (owner's TEXT 2, first job for my area: "your perft and move generation work is the one area that does not
depend on the evaluation, so your numbers transfer to the PC build directly").

**The answer.** Identical, everywhere. **62,406 of 62,406 (position, depth) values match the base build exactly**,
across five sets and depths 1..5, plus 320/320 on the en-passant-pin move sets with the slider-removal control. The
perft-4 sum on each set and the perft-5 sum on set D reproduce to the node. Sending the full PC20 option set changes
nothing either.

**How sure.** Very: every file was asserted to hold an integer at every depth for every expected position before any
comparison (`assert_measured.py`), the comparison refuses mismatched position sets, and the perft-1 values are
non-zero (a fabricated/zero answer cannot pass). `Threads 1` and `Hash 16` are now sent explicitly (swarm rule of
22:20Z), and the log records exactly which options each process received.

## Builds and settings

| build | path | purpose |
|---|---|---|
| base 6b98f217 | /home/ubuntu/build-rel/forge | my earlier results (the base-side files below) |
| PC r15 | /home/ubuntu/build-pc/forge | patch from FABLE_TO_swarm_5 lines 56..2374, sha256 `d6bd72c531f785f4…` (published prefix), `patch -p1` in /agent/repos/pccopy, built with `-DFORGE_MATE_ALPHA_GUARD=1` |

Settings: `Threads 1`, `Hash 16`, `ucinewgame` + `isready` before every `go`. For the leak test, all 18 further
PC20/S14 options were sent too (recorded in `engA_pc20.json`'s `options_sent`).

## The table

| set | positions | depths | values compared | identical | differing | perft-4 sum (both) | evidence |
|---|---|---|---|---|---|---|---|
| A `job1/set_R.fens` (SEED 301 R) | 5,000 | 1-4 | 20,000 | **20,000** | 0 | 2,196,757,662 | `cmpA.txt` |
| B `job1b/set_R311.fens` (SEED 311 R) | 5,000 | 1-4 | 20,000 | **20,000** | 0 | 2,159,914,969 | `cmpB.txt` |
| C `job2/set_special.tsv` (A-E classes) | 314 | 1-4 | 1,256 | **1,256** | 0 | 283,188,329 | `cmpC.txt` |
| D `job3/set_all230.fens` (200 R + 30 G) | 230 | 1-5 | 1,150 | **1,150** | 0 | 119,698,590; perft 5 = **3,925,995,728** | `cmpD.txt` |
| E `job2/ep_constructed.tsv` (ep pins) | 320 | 1 (move sets) | 320 positions | **320** | 0 | — (move-set compare) | `ep_pin_pc.txt` |
| A again under **PC20** | 5,000 | 1-4 | 20,000 | **20,000** | 0 | 2,196,757,662 | `cmpA_pc20.txt` |
| **total** | | | **62,406** | **62,406** | **0** | | |

The PC build's own startpos perft 5 is 4,865,609 (default options, `pcbuild/`).

## Prediction against result

| # | predicted | killed? | measured |
|---|---|---|---|
| 1 | 0 positions differing on A-D | no | 0 |
| 2 | 0 differing pairs | no | 0 of 62,406 |
| 3 | perft-4 sum A = 2,196,757,662 | no | exact |
| 4 | perft-5 sum D = 3,925,995,728 | no | exact |
| 5 | ep pins 320/320 on the PC build | no | 320/320, control 320/320 |
| 6 | PC20 does not change perft 4 | no | 20,000/20,000 identical |
| 7 | all eight published bench numbers match | no | 8/8 |
| 8 | 0 crashes/refused/error lines | no | 0 across every run |
| 9 | PC/base wall ratio 0.9..1.1 on set A | **killed (mildly)** | PC 13.3 s vs base 12.7 s = 1.047 on a different, busier machine state; inside the kill band 0.5..2.0 but outside my stated 0.9..1.1 |

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F6 | The PC (r15) build's move generation is node-for-node identical to the base build: 62,406 of 62,406 (position, depth) values over five sets at depths 1..5, including the 320 en-passant-pin positions and the perft-5 sum 3,925,995,728 — so every perft result in my area transfers to the PC unchanged. | `cd forge-combo29/swarm/03/job4 && python3 compare_builds.py ../job1/eng_R.json engA.json /tmp/c.txt` (and cmpB/cmpC/cmpD) |
| S-F7 | Under the full PC20 option set the PC build's perft counts are unchanged (20,000/20,000 identical to base on set A, perft-4 sum 2,196,757,662), so none of the four new search options (CuckooRep, HistRework, TtPruneV2, CorrHistV2) nor MateAlphaGuard touches move generation. | `cd forge-combo29/swarm/03/job4 && python3 engine_perft_t1.py ~/build-pc/forge ../job1/set_R.fens 4 /tmp/a.json 250 "CuckooRep=true,HistRework=2,TtPruneV2=true,CorrHistV2=true,MateAlphaGuard=true,OwnBook=false" && python3 compare_builds.py ../job1/eng_R.json /tmp/a.json /tmp/c.txt` |
| S-F8 | The PC r15 patch applies cleanly against 6b98f217 (`patch -p1`, 11 files, no fuzz) and the resulting build reproduces all eight published numbers exactly — 312866/862329/3024920/4865609 with no settings, 242796/656517 under S14, 278024/587276 under PC20 — so the patch text in FABLE_TO_swarm_5 lines 56..2374 (sha256 `d6bd72c531f785f4…`) is the PC's engine and is reproducible off the PC. | `cd forge-combo29/swarm/03/pcbuild && python3 pc_build_check.py ~/build-pc/forge .` |

## Suspicions, not proven

- The patch is described as "about 1,200 lines added" and my application shows 11 files changed, but I did not
  independently verify byte-for-byte equality with the PC's own source tree (I cannot: I have no access to the PC).
  What I verified is the patch's published sha256 prefix, a clean application, and eight matching bench numbers —
  which is strong but not the same as a byte comparison against the PC's files.

## What I did NOT do

- Did not run the PC build under a sanitizer (not asked here).
- Did not test search scores at all; per the swarm rule of 22:20Z scores are only reported at Threads 1, and my area
  reports none.

## What I am NOT sure about

- Whether identical perft counts also imply identical *search* behaviour: they do not, and S-F6/S-F7 claim nothing
  about search. The patch's fixes (root drawn, go parse, isready pending, abort publish, hard limit, bare-king LMR)
  are all search-side and invisible to perft, so a clean perft comparison says only that the move generator and the
  board code are untouched.

## Times

`job4/stamps.txt`, `pcbuild/` raw files.
