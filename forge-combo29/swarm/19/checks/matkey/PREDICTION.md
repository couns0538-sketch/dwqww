# PREDICTION - committed BEFORE measuring (19-C64: does the material-key cache do anything on real positions?)

## What I am testing
**19-F9 (mine)**: caching the material key keeps all four node counts identical and is correct (4,736 positions,
0 mismatches) but is **NOT measurably faster: ratio 1.0059, 95 % CI [0.9680, 1.0454]**, measured as **nps on
`bench 13`, n = 10 per side**.

**Two problems with that measurement, both found tonight:**
1. It is a **per-node claim on `bench`**, the class 19-C53/C55/C58 showed cannot be trusted for per-node cost
   (bench was 6x optimistic for PC20, and gets the aggregate node sign wrong on 2 of 3 benches).
2. Its CI **[-3.2 %, +4.5 %]** is far too wide to test the effect that should exist: **19-F6 measured the material
   key at 2.71 % of total self time** (750,427 re-derivations per `bench 13`). A 2.71 % cost is inside that
   interval on both sides.

**So the null in 19-F9 was never able to detect its own effect.** That is the trap-16 shape (a sample that cannot
discriminate), and it is exactly what an underpowered null looks like.

## Setup fixed before running
- Trees: unpatched `6b98f217` (CTRL) vs same tree + `job2/optimize_material_key.patch.txt` (PF), g++ 13.3.0,
  `-DFORGE_MATE_ALPHA_GUARD=1`, `FORGE_MARCH=x86-64-v4`.
- **Both pass all four honesty pins with IDENTICAL node counts** — verified before running, so this is a pure
  per-node-cost comparison with **the same control structure as 19-C58**.
- Real positions (`their_600.fens`, first 130), **fixed `go nodes 50000`**, Threads 1, Hash 16, ABBA,
  fresh process per search, **n >= 120 pairs**.
- Report the **per-position distribution and sign-share**, not just a pooled ratio.

## My prediction, stated before any number exists
1. **The cache will be measurably faster on real positions, pooled ratio ~0.965-0.985 (1.5-3.5 % faster).**
   Reason: 19-F6 puts the re-derivation at 2.71 % of self time, and eliminating it should recover most of that.
2. **The sign-share will be HIGH (>= 80 %)** — unlike the PC20 switches, this removes pure redundant arithmetic
   with no effect on the search tree, so it should be a uniform per-node saving rather than a per-position coin
   flip. **If the sign-share comes out near 50 %, the 2.71 % figure from 19-F6 is wrong rather than the cache being
   ineffective.**
3. **Kill condition:** if the pooled CI includes 1.0 at n >= 120, then the material key is not a meaningful cost on
   real positions and **19-F6's 2.71 % must be qualified as bench-specific** — I will say so.

## What each outcome means
- **ratio ~0.97 with high sign-share** -> the patch is a real, uniform speed win and 19-F9's "not measurably
  faster" was an underpowered null. **That would make the patch shippable and would be the first positive speed
  result of my run.**
- **CI includes 1.0 at n >= 120** -> 19-F9 stands and 19-F6's cost share is bench-specific.
- **ratio > 1.0** -> the cache costs more than it saves; would refute 19-F6's premise.
