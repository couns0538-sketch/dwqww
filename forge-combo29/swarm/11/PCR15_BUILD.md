# PC r15 BUILD — seat 11 verification of FABLE_TO_swarm_5.md

## The patch
`/tmp/pc_r15.patch` extracted from `forge-combo29/soak_all/FABLE_TO_swarm_5.md` between its two fence
lines (lines 56..2374 of the saved file).

sha256 of the extracted patch: `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`
file 5 says it "starts with d6bd72c531f785f4" — MATCH.

Applied in a SEPARATE copy (never in the base worktree):
    git worktree add /tmp/pcbase 6b98f2170a3210e71beed04bbd2553972c253ed7
    cd /tmp/pcbase/forge-combo29 && patch -p1 < /tmp/pc_r15.patch
All 11 files patched, no fuzz, no rejected hunk (b4.hpp board.hpp nnue.hpp nnue_v3.hpp search.hpp
board.cpp eval_params.cpp nnue.cpp nnue_v3.cpp search.cpp uci.cpp).

Built as file 5 says:
    cmake -S /tmp/pcbase/forge-combo29 -B /tmp/pcbuild -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1
    cmake --build /tmp/pcbuild -j4          -> exit 0, /tmp/pcbuild/forge (814,008 bytes)

## The known answers — ALL THREE REGIMES MATCH

Fresh process per line. `Threads 1` everywhere (the thread rule); Hash 16 as file 5 states.

### (1) no setoption at all — the four honesty pins
| what | expected | measured | match |
|---|---|---|---|
| bench 11 | 312866 | **312866** | YES |
| bench 13 | 862329 | **862329** | YES |
| bench 16 | 3024920 | **3024920** | YES |
| go perft 5 | 4865609 | **4865609** | YES |

### (2) S14 (the 14 settings of file 1), then bench
| what | expected | measured | match |
|---|---|---|---|
| bench 11 | 242796 | **242796** | YES |
| bench 13 | 656517 | **656517** | YES |

Option files committed beside this: `opts/S14_bench11.txt`.

### (3) PC20 = S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
###            MateAlphaGuard true, OwnBook false (Threads 1, Hash 16)
| what | expected | measured | match |
|---|---|---|---|
| bench 11 | 278024 | **278024** | YES |
| bench 13 | 587276 | **587276** | YES |

Option file: `opts/PC20_bench11.txt`. Every option name was accepted (no `unknown option`, no
`invalid value` line from any setoption), which also proves `MateAlphaGuard` exists — i.e. the
build really got `-DFORGE_MATE_ALPHA_GUARD=1`. A build WITHOUT that flag would answer the option
`unknown option`; that is the check file 5 asks for.

## Threads
Every number above is Threads 1. Per the swarm rule of 22:18Z, scores and node counts above
Threads 1 are provisional; none of the above uses more than one thread.

## What I did NOT do
- Did not commit the patch text (file 5 gives it as data and says not to commit it again); only
  this verification note and the small option files are in my folder.
- Did not build with the owner's trained net — file 5 says that net is not shared, so the
  built-in evaluation is used here and evaluation-dependent results remain questions for the PC.
- Did not test the four new search switches individually; PC20 turns all of them on together.
