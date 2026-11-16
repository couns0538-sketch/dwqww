# THE PC BUILD (r15) — built, and every known number reproduced — seat 08

## What was done
`FABLE_TO_swarm_5.md` holds the PC's engine as one patch against 6b98f217. I extracted the patch block, checked its
sha256, applied it to a SEPARATE copy (`~/repos/pcbase`, a worktree at 6b98f217 — never the copy I build the base
from), and built it with the PC's flag.

| step | command | result |
|---|---|---|
| extract patch | python3, from the first `diff -ruN` line to the closing fence | 2,319 lines |
| sha256 of patch text | `hashlib.sha256` | **d6bd72c531f785f4**... — matches the file's stated prefix |
| separate copy | `git worktree add ~/repos/pcbase 6b98f217` | not the base build tree |
| apply | `cd forge-combo29 && patch -p1 --fuzz=0 < pc_r15.patch` | 11 files, **zero fuzz, no rejects** |
| files patched | b4.hpp, board.hpp, nnue.hpp, nnue_v3.hpp, search.hpp, board.cpp, eval_params.cpp, nnue.cpp, nnue_v3.cpp, search.cpp, uci.cpp | 11, as the file says |
| configure | `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1` | ok |
| build | `cmake --build . -j4` | forge built |

exe: `/home/ubuntu/builds/pc/forge`, sha256 in `pcbuild/out/sha256.txt`.
`id name Chess Engine Forge 6.4.24 candidate` (same as the base).

## Every known number, and whether it reproduced

Regimes exactly as FABLE_TO_swarm_4/5 define them: **pins = no setoption at all**; **S14** = the 14 settings;
**PC20** = S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false
(Threads 1, Hash 16). One fresh process per line.

| regime | check | file says | I measured | verdict |
|---|---|---|---|---|
| none | bench 11 | 312866 | **312866** | match |
| none | bench 13 | 862329 | **862329** | match |
| none | bench 16 | 3024920 | **3024920** | match |
| none | go perft 5 | 4865609 | **4865609** | match |
| S14 | bench 11 | 242796 | **242796** | match |
| S14 | bench 13 | 656517 | **656517** | match |
| PC20 | bench 11 | 278024 | **278024** | match |
| PC20 | bench 13 | 587276 | **587276** | match |

**8 of 8 exact.** Raw per-line output in `pcbuild/out/`.

## The options are real, not silently ignored
`grep -E 'unknown option|invalid value'` over every output file: **none**. The exe's own `uci` list contains
`CuckooRep` (check, default false), `HistRework` (spin 0..3, default 0), `TtPruneV2`, `CorrHistV2`,
`MateAlphaGuard` (all check, default false), and `OwnBook`. So PC20 is applied for real — a typo would have been
answered `unknown option` and I would have seen it.

Proof that the settings actually change the tree, rather than being accepted and ignored: the same build gives
**312866** with no setoption, **242796** under S14, and **278024** under PC20 at bench 11 — three different
numbers from one exe.

## A cross-check that also settles my own HONESTY.txt
- The base build (6b98f217, `/home/ubuntu/builds/release/forge`) under S14 gives **242796** — the same as the PC
  build under S14, and the same as seat 10's number in FABLE_TO_swarm_4. Expected: every added switch defaults
  OFF, so the two builds are the same engine at default options.
- My `HONESTY.txt` pins were measured with **no setoption at all** (`honesty/honesty.sh` sends only
  `uci/isready/ucinewgame/isready/bench N`), which is exactly the "pins = default options" regime FABLE_TO_swarm_4
  requires. So my pin block is correct as filed and needs no re-run.

## What this build is used for from here
Every one of my existing findings is re-run on this exe under **PC20**, and each finding line will name the build
(base or PC r15) and the settings (none / S14 / PC20). A find that is gone on PC20 is "repaired on the PC"; a find
that survives is worth more.

## What I did NOT do
- Did not commit the patch or any binary (both stay outside the repository; the patch is code given as data).
- Did not build a sanitizer variant of the PC build yet.
- Did not test the PC's own net file — it is not shared, so every evaluation-dependent result here uses the
  built-in evaluation (`OwnBook false` in PC20, but the net is the built-in one).
