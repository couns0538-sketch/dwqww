# PC r15 build — verified (seat 20, job 25)

## Provenance
| item | value |
|---|---|
| source file | `handoff/fable-opus-combo29-all-20261114` @ `a61d7de2c24e433dbef7c1e36f584565900c2107`, `forge-combo29/soak_all/FABLE_TO_swarm_5.md` |
| patch extracted | the fenced block under `## The patch` (2,319 lines) |
| patch sha256 | **`d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`** — matches the prefix `d6bd72c531f785f4` that file 5 states |
| base tree | `6b98f217` in a SEPARATE worktree `/agent/repos/pc-src` (the base build worktree was not touched) |
| applied with | `cd forge-combo29 && patch -p1 < pc_r15.patch` — all 11 files, no fuzz, no rejects |
| files changed | include/forge/{b4.hpp (new), board.hpp, nnue.hpp, nnue_v3.hpp, search.hpp}, src/{board.cpp, eval_params.cpp, nnue.cpp, nnue_v3.cpp, search.cpp, uci.cpp} |
| build | g++ 13.3.0, `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1` |
| exe | `/agent/repos/build-pc/forge` (814,008 bytes) |
| uci options | 92 listed; **every option PC20 needs is present**, none missing |
| patch kept | `/agent/repos/pc15/pc_r15.patch` — outside the repository, per the rules ("do not commit it again") |

## The published numbers, checked one by one (fresh process per line)

| settings | check | got | expected | verdict |
|---|---|---|---|---|
| none | bench 11 | 312,866 | 312,866 | **MATCH** |
| none | bench 13 | 862,329 | 862,329 | **MATCH** |
| none | bench 16 | 3,024,920 | 3,024,920 | **MATCH** |
| none | go perft 5 | 4,865,609 | 4,865,609 | **MATCH** |
| S14 | bench 11 | 242,796 | 242,796 | **MATCH** |
| S14 | bench 13 | 656,517 | 656,517 | **MATCH** |
| PC20 | bench 11 | 278,024 | 278,024 | **MATCH** |
| PC20 | bench 13 | 587,276 | 587,276 | **MATCH** |

**8 of 8 reproduce exactly.** No `unknown option`, `invalid value` or `ERROR` line appeared in any run (the runner
raises if one does, and the option list is checked against the exe's own `uci` answer before any measurement).

Note the two facts this establishes for the whole swarm:
1. The PC build's DEFAULT pins are identical to the base tree's (312866 / 862329 / 3024920 / 4865609), so all four
   honesty numbers in every seat's HONESTY.txt remain comparable across both builds.
2. **S14 changes the pins on this build too** (bench 11 = 242,796, bench 13 = 656,517), which is exactly the
   regime rule of file 4: pins are DEFAULT numbers, sums are S14 numbers. A harness that applies S14 and then
   checks a pin will see a false mismatch — 242,796 instead of 312,866.

Raw: `job25/pc_honesty.json`. Script: `job25/pc_honesty.py`.
