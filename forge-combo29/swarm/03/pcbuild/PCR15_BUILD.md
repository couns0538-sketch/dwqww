# PC BUILD (r15) — built, and all eight published numbers match

Source: `handoff/fable-opus-combo29-all-20261114`, file `forge-combo29/soak_all/FABLE_TO_swarm_5.md` (read in full,
after files 1-4). The patch is the block between its two fences.

## Extraction and integrity

The patch is lines 56..2374 of that file (line 56 is the first `diff -ruN` line; 2374 is the last content line; the
closing fence is 2375). Extracted with awk and checked against the sha256 prefix file 5 gives:

```
$ awk 'NR>=56 && NR<=2374' FABLE_TO_swarm_5.md > pc_r15.patch
$ sha256sum pc_r15.patch
d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a  pc_r15.patch
```

`d6bd72c531f785f4…` — matches the published prefix exactly. (My first attempt used 57..2374 and gave
`83ce05d8…`; the off-by-one is recorded here because a wrong extraction would have produced a silently
different engine.)

## Application

Applied in a SEPARATE worktree at /agent/repos/pccopy (never in the base build tree), with `patch -p1`:

```
$ patch -p1 --dry-run < ../pc_r15.patch     # all 11 files "checking file", exit 0, no fuzz/offset
$ patch -p1 < ../pc_r15.patch               # patching 11 files, exit 0
```

`include/forge/b4.hpp` sha256 2287bfbd8f67a24a631525002a9be448fcd898f21e6eb35f5d9d181f1a62f358
`src/search.cpp`          sha256 b5209ea5e05d5b9221a59806f1f7620ce9edd5345840a4fcbca0b5cfece04d0c

## Build

```
$ cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=native \
        -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 /agent/repos/pccopy/forge-combo29
$ make -j4        # built target forge
```

exe: /home/ubuntu/build-pc/forge (805,816 bytes). The build tree is ~/build-pc, outside every repository.

## The eight published numbers: all MATCH

`pc_build_check.py` reads the exe's own `uci` option list first (92 options) and refuses to proceed if any option
name it must send is absent — so `MateAlphaGuard` is verified to exist rather than assumed, which is exactly the
trap file 5 warns about ("without the flag the option MateAlphaGuard does not exist and is answered
`unknown option`"). It also stops on any `unknown option` / `invalid value` / `ERROR` line.

```
none  bench 11     expected   312866 got 312866 MATCH
none  bench 13     expected   862329 got 862329 MATCH
none  bench 16     expected  3024920 got 3024920 MATCH
none  go perft 5   expected  4865609 got 4865609 MATCH
s14   bench 11     expected   242796 got 242796 MATCH
s14   bench 13     expected   656517 got 656517 MATCH
pc20  bench 11     expected   278024 got 278024 MATCH
pc20  bench 13     expected   587276 got 587276 MATCH

MATCH 8 of 8
```

This is a strong result in itself: the PC's source, rebuilt on a different machine and compiler invocation, reproduces
the PC's bench numbers under all three regimes, including PC20 (the exact settings the owner's PC sends). It also
means S14 and PC20 on this build are reproducible baselines for any later work.

Raw transcripts: `pcbuild/{none,s14,pc20}.raw`, summary `pcbuild/pc_build_check.txt`, option list
`pcbuild/uci_options.txt`.

## What is different about this build (for my area)

`go perft 5` under default options is 4,865,609 on both builds — the move generator is untouched by the patch
(file 5 lists only fixes behind switches, four search toggles, net updates and the compiled-out pawn history). The
perft question — are node counts identical between base and PC build — is the next job; it is measured over my
thousands of positions rather than asserted from this one line.
