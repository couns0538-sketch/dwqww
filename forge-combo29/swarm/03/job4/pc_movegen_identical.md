# CLAIM: the PC (r15) build's move generation is node-for-node identical to the base build

**The claim.** For every position I have tested, the PC build (`r15`, the source in
`soak_all/FABLE_TO_swarm_5.md` lines 56..2374) produces exactly the same perft node counts, and the same perft-1
root move sets, as the base tree `6b98f217`. Therefore every perft and move-generation result in this folder
transfers to the owner's PC build with no caveat.

**The measurement.** 62,406 of 62,406 (position, depth) values identical; 0 differing; plus 320/320 on the
en-passant-pin move sets with a slider-removal control passing 320/320.

## The five sets, their sums, and where the base-side file lives

| set | positions | depths | perft-1 sum | perft-2 sum | perft-3 sum | perft-4 sum | perft-5 sum | base file | PC file |
|---|---|---|---|---|---|---|---|---|---|
| A R SEED 301 | 5,000 | 1-4 | 113,656 | 2,647,591 | 75,639,746 | **2,196,757,662** | — | `../job1/eng_R.json` | `engA.json` |
| B R SEED 311 | 5,000 | 1-4 | 112,193 | 2,606,301 | 74,557,281 | **2,159,914,969** | — | `../job1b/eng.json` | `engB.json` |
| C special A-E | 314 | 1-4 | 8,555 | 266,744 | 8,642,784 | **283,188,329** | — | `../job2/eng_special.json` | `engC.json` |
| D 200 R + 30 G | 230 | 1-5 | 5,644 | 137,090 | 4,013,465 | 119,698,590 | **3,925,995,728** | `../job3/eng.json` | `engD.json` |
| E en-passant pins | 320 | 1 (move sets) | — | — | — | — | — | `../job2/ep_pin_all.txt` | `ep_pin_pc.txt` |
| A under PC20 | 5,000 | 1-4 | 113,656 | 2,647,591 | 75,639,746 | **2,196,757,662** | — | `../job1/eng_R.json` | `engA_pc20.json` |

Set E control: `../job2/ep_pin_control.txt` (base) and `ep_pin_control_pc.txt` (PC), both 320/320 passed.

All sums above are equal on both builds. Comparison outputs: `cmpA.txt`, `cmpB.txt`, `cmpC.txt`, `cmpD.txt`,
`cmpA_pc20.txt`.

## Builds (rebuild instructions)

Base: `git worktree add ../base 6b98f2170a3210e71beed04bbd2553972c253ed7`, then in `forge-combo29/`:
```
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=native .   # in a build dir outside the tree
make -j4
```
sha256 of the base exe: `68825bd5dbe004f58b2e3b22a197711e835c8de379e495502d85529ba90ed47a`.

PC r15: extract the patch from `FABLE_TO_swarm_5.md` lines 56..2374 and CHECK THE HASH FIRST:
```
awk 'NR>=56 && NR<=2374' FABLE_TO_swarm_5.md > pc_r15.patch
sha256sum pc_r15.patch     # must start d6bd72c531f785f4
```
then in a SEPARATE worktree of 6b98f217, from `forge-combo29/`:
```
patch -p1 < ../pc_r15.patch
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=native \
      -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 .
make -j4
```
Warning worth keeping: extracting at 57..2374 instead of 56..2374 gives sha256 `83ce05d8…`, applies, and builds —
a silently different engine. Always check the hash prefix.

## Exact commands to reproduce the whole claim

```bash
cd forge-combo29/swarm/03/job4
# 1. engine side of every set on the PC build (settings: Threads 1, Hash 16, ucinewgame+isready before each go)
python3 ../job1/engine_perft.py ~/build-pc/forge ../job1/set_R.fens      4 engA.json 250
python3 ../job1/engine_perft.py ~/build-pc/forge ../job1b/set_R311.fens  4 engB.json 250
python3 ../job1/engine_perft.py ~/build-pc/forge set_C.fens              4 engC.json 100
python3 ../job1/engine_perft.py ~/build-pc/forge ../job3/set_all230.fens 5 engD.json 250
# 2. assert every file is a real measurement before trusting it
python3 ../assert_measured.py perft engA.json 4 5000
python3 ../assert_measured.py perft engB.json 4 5000
python3 ../assert_measured.py perft engC.json 4 314
python3 ../assert_measured.py perft engD.json 5 230
# 3. compare against the base files (fails if the position sets differ or a value is missing)
python3 compare_builds.py ../job1/eng_R.json      engA.json cmpA.txt
python3 compare_builds.py ../job1b/eng.json       engB.json cmpB.txt
python3 compare_builds.py ../job2/eng_special.json engC.json cmpC.txt
python3 compare_builds.py ../job3/eng.json        engD.json cmpD.txt
# 4. the en-passant-pin move sets on the PC build, with the control
cut -f3 ../job2/ep_constructed.tsv > set_E.fens
python3 ../job2/ep_pin_compare.py ~/build-pc/forge ../job2/ep_constructed.tsv ep_pin_pc.txt
python3 ../job2/ep_pin_control.py ~/build-pc/forge ../job2/ep_constructed.tsv ep_pin_control_pc.txt
# 5. the PC20 leak test (perft must not care about search options)
python3 engine_perft_t1.py ~/build-pc/forge ../job1/set_R.fens 4 engA_pc20.json 250 \
  "LmrQuietBase=93,LmrQuietDivisor=205,LmrNoisyBase=13,LmrNoisyDivisor=333,LmrHistoryDivisor=5643,NullMoveBase=5,LmpBase=8,HistoryPruneMultiplier=2220,HistoryBonusQuadratic=24,HistoryBonusLinear=54,HistoryBonusMax=2212,SingularDepth=6,IirDepth=2,NonPawnCorrection=true,CuckooRep=true,HistRework=2,TtPruneV2=true,CorrHistV2=true,MateAlphaGuard=true,OwnBook=false"
python3 compare_builds.py ../job1/eng_R.json engA_pc20.json cmpA_pc20.txt
```

`set_C.fens` = `cut -f3 ../job2/set_special.tsv`; `set_E.fens` = `cut -f3 ../job2/ep_constructed.tsv` (both are
committed, so the cut is only needed if they are lost).

## Why this is expected, and what it does NOT claim

`Board::perft` (`src/board.cpp:1205-1222` in both trees) is a plain recursive walk over
`generate_pseudo_legal` + `is_legal`, with no hash probe, no thread and no evaluation. The r15 patch's fixes are
all search-side (root drawn, go parsing, isready pending, abort publish, hard-limit emergency, bare-king LMR) or
are options that are off by default, so nothing in it can reach move generation.

This claim says nothing about search: identical perft counts do not imply identical scores, node counts or
bestmoves at a given depth. The separate question — whether the move the engine actually *plays* is unaffected — is
measured in `bestmove_parity.md`.
