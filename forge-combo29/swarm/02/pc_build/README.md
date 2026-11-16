# PC build (r15) — built, verified, usable

Source: handoff/fable-opus-combo29-all-20261114, forge-combo29/soak_all/FABLE_TO_swarm_5.md (file 5).

## what I did, exactly
1. Extracted the patch from the fence: from the first `diff ` line to the last line of the block
   (`extract_patch.py`). **sha256 d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a**,
   which matches file 5's stated prefix `d6bd72c531f785f4`. A mismatch would have stopped the build.
2. Made a SEPARATE copy of 6b98f217 at /agent/repos/pc (never in the tree I build the base from):
   `git -C /agent/repos/dwqww archive 6b98f217 | tar -x -C /agent/repos/pc`.
3. `cd forge-combo29 && patch -p1 < pc_r15.patch` -> exit 0, **0 fuzz, 0 offsets, no .orig/.rej files**,
   11 files touched, CMakeLists.txt untouched (as file 5 says).
4. `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1` then `cmake --build . -j4`
   -> BUILD_EXIT=0. exe /agent/repos/pc/forge-combo29/build-pc/forge.

The patch text is NOT committed again (file 5: "do not commit it again"); `patch_sha256.txt` is my record of
the extraction and its hash.

## the three bench rows of file 5 — all eight stated numbers reproduce

`verify_pc_build.py` — one FRESH process per measurement, `Threads 1` and `Hash 16` set explicitly on every
run (seat 04: scores above Threads 1 are not reproducible), and any `unknown option` / `invalid value` / `ERROR`
in the output aborts the check.

| settings | measurement | got | file 5 states | verdict |
|---|---|---|---|---|
| none | bench 11 | 312866 | 312866 | PASS |
| none | bench 13 | 862329 | 862329 | PASS |
| none | bench 16 | 3024920 | 3024920 | PASS |
| none | perft 5 | 4865609 | 4865609 | PASS |
| S14 | bench 11 | 242796 | 242796 | PASS |
| S14 | bench 13 | 656517 | 656517 | PASS |
| PC20 | bench 11 | 278024 | 278024 | PASS |
| PC20 | bench 13 | 587276 | 587276 | PASS |

Raw: `bench_verify.txt`, `bench_verify_results.json`.

**Conclusion: the PC build is usable.** Every number file 5 states for it, reproduces exactly on this machine.

## the UCI switches this build carries (the part that is my area)
File 5 lists FORGE_FIX_GO_PARSE, FORGE_FIX_ISREADY_PENDING, FORGE_FIX_ABORT_PUBLISH and others. They are
COMPILE-TIME switches, so I have to test their EFFECT on this one build (I cannot turn one off without a
rebuild). Whether each one repairs one of my findings is answered in `../pc_rerun/`.
