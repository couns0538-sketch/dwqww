# REPORT_pc0 - the PC r15 build, reproduced and verified

what was asked (TEXT 2 / FABLE_TO_swarm_5): fetch the handoff branch, read `FABLE_TO_swarm_5.md` before the next
step, build the engine the owner's PC really plays as a patch against 6b98f217 in a SEPARATE copy with
`-DFORGE_MATE_ALPHA_GUARD=1`, and check the known bench numbers it must give. Then continue area 9 with BOTH builds.
the answer: the patch's sha256 matches the one the file states, it applies cleanly to all 11 files, the build
succeeds, and **all eight known numbers match exactly in all three regimes** (none / S14 / PC20). This build is
trustworthy and is used for the rest of the 12-hour continuation.
how sure: very high — these are exact node counts, each from a fresh process, compared against values the file
gives, with all four default pins reproduced as a control.

## integrity of the input
| check | expected | got |
|---|---|---|
| sha256 of the saved patch text | starts `d6bd72c531f785f4` | `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a` — MATCH |
| patch body extracted | everything between the two fence lines | 2,319 lines, first `diff -ruN a/include/forge/b4.hpp`, last a `uci.cpp` hunk |
| files touched | 11 files, CMakeLists unchanged | 11 files: `b4.hpp`, `board.hpp`, `nnue.hpp`, `nnue_v3.hpp`, `search.hpp`, `board.cpp`, `eval_params.cpp`, `nnue.cpp`, `nnue_v3.cpp`, `search.cpp`, `uci.cpp` — MATCH |
| applies with `patch -p1` from `forge-combo29/` | clean, no fuzz | all 11 "checking file" lines, no rejects |

Note on the apply path: the patch's paths are `a/include/...` relative to `forge-combo29/`, so `patch -p1` must run
**inside** `forge-combo29/` (or `git apply --directory=forge-combo29` from the root). Running it from the repository
root without the directory hint fails at the second file — I hit that first and record it here.

## build
Separate worktree `/agent/repos/pc` at 6b98f217 (never the tree I build the base from), build dir `~/build/pc`:

```bash
cd /agent/repos/pc/forge-combo29 && patch -p1 < ~/pcwork/pc_r15.patch
mkdir -p ~/build/pc && cd ~/build/pc
cmake /agent/repos/pc/forge-combo29 -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_COMPILER=/usr/bin/g++-13 -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1
make -j4            # exit 0
```
`-DCMAKE_CXX_COMPILER=/usr/bin/g++-13` is needed on this machine because `/usr/bin/c++` is clang-18 whose link step
cannot find `-lstdc++` (recorded in HONESTY.txt). `MateAlphaGuard` exists only with the guard flag, so the flag was
not optional.

## the known numbers — all eight match

```bash
cd forge-combo29/swarm/29/pc0 && python3 verify_pc_build.py ~/build/pc/forge
```

| settings | check | expected | got | |
|---|---|---|---|---|
| none (no setoption at all) | bench 11 | 312866 | **312866** | MATCH |
| none | bench 13 | 862329 | **862329** | MATCH |
| none | bench 16 | 3024920 | **3024920** | MATCH |
| none | go perft 5 | 4865609 | **4865609** | MATCH |
| S14 | bench 11 | 242796 | **242796** | MATCH |
| S14 | bench 13 | 656517 | **656517** | MATCH |
| PC20 | bench 11 | 278024 | **278024** | MATCH |
| PC20 | bench 13 | 587276 | **587276** | MATCH |

The exe lists 92 options and **every option PC20 needs is present** (`CuckooRep`, `HistRework`, `TtPruneV2`,
`CorrHistV2`, `MateAlphaGuard`, `OwnBook`, plus all 14 of S14). The harness aborts on any `unknown option`,
`invalid value` or `ERROR` line, and aborts rather than treating a missing node count as zero.

## what this settles for me
- **29-F6 is independently corroborated.** File 4 says a default-option harness sees a false mismatch, and seat 10
  measured `O depth 12 = 12,573,318` under defaults; I measured exactly 12,573,318 as my control in `raw_rows_sums.txt`
  before file 4 arrived, and `bench 11 = 242796` under S14 is confirmed here on the PC build and matches seat 10's
  base-tree figure.
- The default pins (312866 / 862329 / 3024920 / 4865609) are unchanged by the PC patch, so any base-tree node figure
  I published remains comparable at the *pin* level; the S14/PC20 numbers are different trees and are not.

## a table: step | done-partly-not done | evidence | result

| step | done? | evidence | result |
|---|---|---|---|
| read every unread FABLE file, lowest N first | done | files 4 then 5 | file 4 clarifies pins vs sums; file 5 is the PC engine |
| verify patch sha256 | done | `raw_verify_pc.txt` header + `sha256sum` | MATCH |
| apply to a separate copy | done | `/agent/repos/pc` | 11/11 files, no fuzz |
| build with the guard flag | done | `~/build/pc` | exit 0 |
| check all known numbers | done | `raw_verify_pc.txt` | **8/8 MATCH** |
| PC20 option availability | done | `raw_verify_pc.txt` | all present, 92 options listed |

## findings
| id | area | one sentence | file | type |
|---|---|---|---|---|
| 29-F16 | 9 | The PC r15 patch reproduces exactly on this machine: sha256 `d6bd72c531f785f4...`, 11 files, builds with `-DFORGE_MATE_ALPHA_GUARD=1`, and all eight of the file's known numbers match in all three regimes (none 312866/862329/3024920/4865609; S14 242796/656517; PC20 278024/587276) — build base, settings as named, **Threads 1**, fresh process per line. | `forge-combo29/swarm/29/pc0/verify_pc_build.py`, `raw_verify_pc.txt` | NEW |

## what I did NOT do
- No net file: the PC plays with its own trained net, which the file says is NOT shared. So every PC-build result is
  the built-in evaluation, exactly as file 2 rule 2 warns, and evaluation-dependent questions stay open.
- Did not test the four new search switches' individual effects (CuckooRep / HistRework / TtPruneV2 / CorrHistV2);
  PC20 enables them together, which is the configuration the owner actually uses.

## what I am NOT sure about
- Whether `bench 16` under S14/PC20 exists as a known value: the file leaves those cells blank, so I did not invent
  them. If a later seat needs them, they must be measured fresh, not assumed.

times: see `stamps.txt` in `pc0/`.
