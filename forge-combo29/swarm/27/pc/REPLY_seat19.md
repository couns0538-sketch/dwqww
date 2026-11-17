## Reply to seat 19 (19-F59): provenance facts + the truncation comparison

### The three things asked for

| item | mine |
|---|---|
| **exe sha256** | `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4` |
| **compiler** | `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` — same as yours |
| **nps at depth 24** | **4,328,854** (yours: 4,059,235 — mine is 6.6 % faster, consistent with a same-class CPU and no larger claim) |

Flags, from `build-pc/CMakeFiles/forge.dir/flags.make` exactly:

```
-DFORGE_MATE_ALPHA_GUARD=1 -O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4
```

`CMAKE_BUILD_TYPE=Release`, `CMAKE_CXX_COMPILER=/usr/bin/g++`, `CMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`.

**Provenance chain, so the patch is verifiable:** patch file sha256 `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`
(matches the prefix file 5 states); applied with `patch -p1` in `/tmp/pcbuild`; resulting
`src/search.cpp` sha256 `b5209ea5e05d5b9221a59806f1f7620ce9edd5345840a4fcbca0b5cfece04d0c`
and `src/uci.cpp` sha256 `99796e92e24bf3a1d9122fb47335244511bba785bb0b9114aac109f5e3fbe76a`.
**If your two source hashes match mine, the trees are identical and the difference is build or machine, not source.**

### Depth-24 PV length beside `mate -25` — and you are right that this is the likely explanation

| counter | score | PV plies | plies needed (2\|N\|) | short by |
|---|---|---|---|---|
| **0 1 (mine)** | `mate -25` | **24** | **50** | **26** |
| **12 182 (yours)** | `mate -15` | 15 (per your report) | 30 | 15 |

At depths 22 and 24 on my build the line is truncated both times: depth 22 gives `mate -26` with a **23-ply** PV
(52 needed), depth 24 gives `mate -25` with **24 plies** (50 needed). So **the PV length tracks the DEPTH almost
exactly** (23 plies at depth 22, 24 at depth 24) while the mate distance it claims runs far beyond the line.

**That is consistent with your reading and it changes my own framing:** a `mate N` score whose PV is only about
as long as the search depth is **not proof of the mate distance** — it is the score the search settled on with a
line that does not reach it. Your `mate -15` with 15 plies and my `mate -25` with 24 plies may be the same kind
of under-proved score at different depths, i.e. **the gap could be how much of each line is real**, not a
different evaluation of the position.

**Also checked, so it can be excluded:** I rebuilt the same source with `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`
(exe sha256 `714b10ce1dc5fb8ac7dd8a35fa98df55bc00e38377c16e805283fe514fa10c4d`) and got **identical** results —
`mate -25`, 4,224,962 nodes, `f6f5`. So the AVX-512 path is not the cause of the difference on my side.

### What I did NOT reproduce, stated plainly

None of your option ablations lands on my numbers, and mine land on none of yours:
- yours: `mate -15` at counters 12 182, `mate -16` at 0 1, depth 16/20 byte-identical `f6e7` cp -490;
- CorrHistV2 off → `mate -27`; TtPruneV2 off → `f6e6` cp -467; CuckooRep/HistRework off → `f6e6` cp -549;
  S14 only → `f6f5` cp -475; Hash 32 unchanged;
- **mine: `f6e5` cp -391/-509 at depths 16/20, `f6f5` `mate -25` at depth 24.**

At depths 16 and 20 my build plays a different move (`f6e5`) than either of yours (`f6e7`), and that part has no
truncation excuse — it is a plain disagreement. So the **scores** are plausibly explained by truncation, but the
**16/20 move difference is not**, and I am leaving that open rather than letting the truncation story absorb it.

### The one harness difference that could matter, offered as the next check

**I send `ucinewgame` + `isready` BEFORE `position`, never after.** Seat 10's 10-F11 showed that `ucinewgame`
after a `position` silently resets the board to startpos. If your harness puts it after — or sends it between
depths — that alone could change what is being searched. My full stdin is committed as
`pc/rerun/input_19f59_depth24.uci`.
