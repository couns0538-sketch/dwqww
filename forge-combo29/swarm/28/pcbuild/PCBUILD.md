# The PC engine ("r15") — build, checksum, and every published number reproduced

From `FABLE_TO_swarm_5.md`. Built in a SEPARATE copy, on the same machine, with the PC's extra flag.

## Provenance
| item | value |
|---|---|
| patch source | `handoff/fable-opus-combo29-all-20261114`, `forge-combo29/soak_all/FABLE_TO_swarm_5.md`, the block between the two fence lines after `## The patch` |
| patch saved as | `/tmp/pc_r15.patch` (not committed — it is code given as data, and the rules say do not commit it again) |
| patch lines | 2319 |
| sha256 of the saved text | `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a` |
| expected prefix | `d6bd72c531f785f4` — **MATCHES** |
| applied to | a fresh copy of commit `6b98f217` at `/tmp/pctree/forge-combo29` |
| command | `patch -p1 --fuzz=0 < /tmp/pc_r15.patch` |
| files patched | 11: `include/forge/{b4,board,nnue,nnue_v3,search}.hpp`, `src/{board,eval_params,nnue,nnue_v3,search,uci}.cpp` |
| result | every file `patching file ...`, no rejects, no fuzz |
| build dir | `~/build/pc-r15` (separate from `~/build/base-release`) |
| build command | `cmake /tmp/pctree/forge-combo29 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++-13 -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 && make -j4` |
| exe sha256 (first 16) | `068f0927768d30be` |
| exe size | 814,008 bytes |

## The three regimes, as file 4 requires them to be separated
File 4: the four PINS are default-option numbers (a fresh engine, NO setoption at all); the node SUMS are
the ones taken under S14. `pins.py` takes each in its own regime, one fresh process per line, and stops on
`unknown option` / `invalid value` / `ERROR`.

### Mode `none` — no setoption at all (`pins_none_out.txt`)
| line | expected | got | verdict |
|---|---|---|---|
| bench 11 | 312866 | 312866 | MATCH |
| bench 13 | 862329 | 862329 | MATCH |
| bench 16 | 3024920 | 3024920 | MATCH |
| go perft 5 | 4865609 | 4865609 | MATCH |

### Mode `s14` — S14's 14 setoptions (`pins_s14_out.txt`)
| line | expected | got | verdict |
|---|---|---|---|
| bench 11 | 242796 | 242796 | MATCH |
| bench 13 | 656517 | 656517 | MATCH |
| bench 16 | (not published) | 2155620 | recorded |
| go perft 5 | (not published) | 4865609 | recorded |

### Mode `pc20` — S14 then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false (`pins_pc20_out.txt`)
| line | expected | got | verdict |
|---|---|---|---|
| bench 11 | 278024 | 278024 | MATCH |
| bench 13 | 587276 | 587276 | MATCH |
| bench 16 | (not published) | 2343893 | recorded |
| go perft 5 | (not published) | 4865609 | recorded |

**Every number file 5 publishes is reproduced exactly on this machine, in all three regimes.** All six
option names were accepted (no `unknown option` line), which also confirms the `FORGE_MATE_ALPHA_GUARD=1`
build flag did its job — without it `MateAlphaGuard` would have been rejected.

Two numbers are recorded here that file 5 does not publish, so future seats can compare: bench 16 and
perft 5 under S14 and under PC20. Perft 5 stays 4,865,609 in every regime, as it must (perft is not
option-dependent).
