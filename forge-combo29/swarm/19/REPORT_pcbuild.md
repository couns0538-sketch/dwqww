# PC build (r15) — built and verified against file 5's known answers

seat 19 · area 9 · branch `for-fable-and-opus/swarm-19`

## What was asked (FABLE_TO_swarm_5.md)

The engine the owner's PC really plays, given as ONE unified diff against base `6b98f217`, to be built in a
SEPARATE copy with `-DFORGE_MATE_ALPHA_GUARD=1`, and checked against the known bench numbers.

## Build, step by step

1. Extracted the patch block from `FABLE_TO_swarm_5.md` between its two fence lines to `/tmp/pc_r15.patch`
   (2,319 lines).
2. **Verified the patch text before using it**: `sha256sum /tmp/pc_r15.patch` =
   `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`, which starts with the
   `d6bd72c531f785f4` the file states. Match.
3. Separate copy: `~/pcbuild/forge-combo29` (copied from the pristine `~/base/forge-combo29`). The base build
   at `~/build_rel` is untouched, so both builds exist side by side as the file requires.
4. `patch -p1 --dry-run` then `patch -p1` — applied cleanly, 11 files, no fuzz, no rejects:
   `include/forge/b4.hpp` (new), `src/board.cpp`, `src/eval_params.cpp`, `src/nnue.cpp`, `src/nnue_v3.cpp`,
   `src/search.cpp`, `src/uci.cpp`, plus the headers the patch carries.
5. Configured with the PC's extra flag:
   `cmake -S . -B ~/pcbuild/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`
6. `make -j4` → built.

Nothing of the patch was committed: it is code given as data, used in `~/pcbuild` only.

## The known answers — all eight reproduce exactly

`bash pcbuild/pc_honesty.sh ~/pcbuild/build/forge pcbuild/out`. One fresh process per line; every `setoption`
followed by `isready` with every answer line read and scanned.

| regime | line | measured | expected | |
|---|---|---|---|---|
| **none** (no setoption at all) | bench 11 | 312,866 | 312,866 | **OK** |
| none | bench 13 | 862,329 | 862,329 | **OK** |
| none | bench 16 | 3,024,920 | 3,024,920 | **OK** |
| none | `go perft 5` | 4,865,609 | 4,865,609 | **OK** |
| **S14** (the 14 settings of file 1) | bench 11 | 242,796 | 242,796 | **OK** |
| S14 | bench 13 | 656,517 | 656,517 | **OK** |
| **PC20** (S14 + the six) | bench 11 | 278,024 | 278,024 | **OK** |
| PC20 | bench 13 | 587,276 | 587,276 | **OK** |

**Stop conditions: zero.** No `unknown option`, no `invalid value`, no `ERROR` in any stream — which also
confirms `MateAlphaGuard` exists (with the flag) and that all six PC20 option names are real in this exe.

Exe sha256 and `id name` in `pcbuild/out/pc_honesty.meta`.

## Note on file 4, which I had not read until now

File 4 states that the four honesty pins are **default-option** numbers while the known node sums (O/G at
depth 12/14) are taken **under S14**, and that seat 10 measured bench 11 = 242,796 under S14. My table above
reproduces that 242,796 independently, which is a second confirmation of 10-F6/10-F10 on the PC build.

Relevant to my own earlier work: my honesty checks always ran with **no setoption at all**, so they were
compared against the correct regime. My job-1b profile and the R_1911 counters applied S14 (and `OwnBook
false`), which is the correct regime for node *sums*, not for the pins — so nothing of mine needs relabelling
as a regime error. The warm/cold error of 19-F18 was a different mistake and stays retracted.

## What is next

Re-run my own findings on this PC build under PC20, each finding line naming build and settings. The
evaluation families stay questions for the PC (file 5: the PC plays its own trained net, which is not shared,
so my build uses the built-in evaluation) — that is file 2 Rule 2, unchanged.

## Files

`pcbuild/pc_honesty.sh`, `pcbuild/out/pc_honesty.txt`, `pcbuild/out/raw_*`, `pcbuild/out/stream_*`,
`pcbuild/out/pc_honesty.meta`, `pcbuild/out/perft5_none.txt`, `REPORT_pcbuild.md`.
