# The vectorised four-way TT key compare: pins HOLD, and the win is NOT there

seat 19 · area 9 · build **PC r15** · **Threads 1** · patch `pcspeed/ttvec.patch.txt` (50 lines, 3 hunks).

## 1. The three lines

**What was asked.** 19-F39 named the four-way key scan as the target (~39 % of `probe_body`). Write the 64-byte
load plus vector compare of the four keys as a text patch and run bench 11/13/16 and perft 5. Two outcomes: pins
move → say by how much and that it needs a match; pins hold → measure instruction count and cold depth-16 node
rate against unpatched with paired discipline, and say whether the win is real at the measured noise floor.

**The answer.** **The pins HOLD exactly, and there is no measurable win.** All four honesty numbers are identical
on the patch-built binary (312,866 / 862,329 / 3,024,920 / 4,865,609) and the three PC20 pins are identical too
(278,024 / 587,276 / 2,343,893). The paired alternating timing gives ratio **0.9865, 95 % CI [0.9626, 1.0104]**
— the interval contains 1.0 — and a larger 20-run interleaved check gives **1.0001**. Instruction counts are
**unavailable** (valgrind dies on this engine's AVX-512 at static init), which I state rather than paper over.

**How sure.** Certain of "pins hold" (four numbers, patch-built binary) and of "no win shown" (two independent
paired designs, both spanning 1.0, and the second at 1.0001). Not able to say whether the change is *exactly*
neutral or merely below resolution — the CI still permits −3.7 % to +1.0 %.

## 2. The change

`pcspeed/ttvec.patch.txt` — `src/search.cpp` only, behind `FORGE_SPD_TT_VEC_SCAN` (default 1):

```
before: for (TTEntry& e : cluster.entries)
            if (e.key32 == key32 && e.occupied()) { found = &e; break; }

after : one __m128i built from the four key32 fields (offsets 0/16/32/48 of the 64-byte cluster),
        one _mm_cmpeq_epi32 against the broadcast key, one movemask, then occupied() tested
        only on the matching lanes with the LOWEST index winning (as the loop's `break` did).
```

The table's contents, replacement policy, generation handling and snapshot are untouched, which is why the pins
could plausibly hold — and they do.

## 3. The pins

| pin | unpatched PC r15 | patch-built | |
|---|---|---|---|
| bench 11 (none) | 312,866 | **312,866** | same |
| bench 13 (none) | 862,329 | **862,329** | same |
| bench 16 (none) | 3,024,920 | **3,024,920** | same |
| perft 5 | 4,865,609 | **4,865,609** | same |
| bench 11 (PC20) | 278,024 | **278,024** | same, 0 refusals |
| bench 13 (PC20) | 587,276 | **587,276** | same, 0 refusals |
| bench 16 (PC20) | 2,343,893 | **2,343,893** | same, 0 refusals |

The patch-built binary was compiled from the patch file itself (applied with `patch -p1`, no fuzz) in a separate
copy, so the pins above belong to exactly the artifact the owner would apply.

## 4. The timing — two designs, both negative

**Design A** (`pcspeed/pair_pc20.py`), 12 alternating pairs, one fresh process per run, PC20, `bench 13`:

| | unpatched | patch |
|---|---|---|
| mean | 333.1 ms | 328.6 ms |
| sd | 11.5 (3.5 %) | 8.0 (2.4 %) |

ratio **0.9865**, 95 % CI **[0.9626, 1.0104]**, i.e. **−1.35 % [−3.74 %, +1.04 %]**. The CI contains 1.0.

**Design B**, 20 runs each, interleaved one-for-one:

| | unpatched | patch |
|---|---|---|
| mean | 333.9 ms | 333.9 ms |
| median | 330 ms | 328 ms |
| sd | 13.0 | 14.5 |

ratio **1.0001**.

Two designs agree that the change is inside the noise. Per my own measured floor for this machine and workload
(±2.29 % at 10 rounds, ±2.91 % at 6 rounds — 19-F21/19-F27), **a change smaller than ~2 % cannot be resolved
here at practical cost**, and this one measures 0.0 % to −1.4 %.

## 5. Instruction count — NOT AVAILABLE, and why that matters

`valgrind --tool=callgrind` **cannot run this engine**: it terminates with `SIGILL` at
`_GLOBAL__sub_I__ZN5forge5BoardC2Ev`, i.e. during static initialisation, because valgrind 3.22 does not
implement this build's AVX-512 instructions. The "PROGRAM TOTALS 2,038,182" that callgrind printed is the
preamble before the crash, **not** a measurement of `bench 13`, and I am recording that so nobody mistakes those
numbers for instruction counts. (This is also why seat 29's callgrind numbers cited in 29-F5 must have come from
a differently-built binary — worth their knowing.)

So the second half of the requested measurement is **not done**: there is no instruction-count comparison. The
timing evidence above stands on its own, but it is timing, not instructions.

## 6. What this means

**The named target from 19-F39 does not pay off when attacked this way.** The scan's ~39 % is therefore most
likely dominated by the **memory access to the cluster line**, not by the four comparisons — because collapsing
four comparisons into one changed nothing measurable. That is a conclusion I can now state with more confidence
than in 19-F39, where I explicitly refused to separate load from comparison: the vectorisation experiment *is*
that separation, and it came back negative.

Consequence for the owner: the next attempt on the TT should be a **layout or access-pattern** question (does the
cluster line arrive before it is needed?), not a comparison-count question. My own earlier prefetch attempt
(19-F10) also failed, which narrows this to: the probe is already about as good as this structure allows, and
**the TT is not where the remaining PC-relevant time is** — move ordering (17–18 %) still is.

### The disassembly explains the null result, and it is the important part

I checked the obvious follow-up before finishing, and it settles *why* the ratio is 1.0001:

- The **unpatched** binary contains **0 `pmovmskb`** and only 5 `pcmpeqd` in the whole `.text` — i.e. the
  original four-way loop was **never vectorised**; it compiles to four scalar `key32` compares with an early
  exit, which is usually the *fastest* form when a hit is found in slot 0 (93 % of hits are, per job 4).
- The **patched** binary contains **0 `pcmpeqd` and 0 `pmovmskb`**: GCC took my explicit
  `_mm_cmpeq_epi32` + `movemask` + lane-scan and **compiled it back into scalar compares**, because with four
  lanes and a data-dependent early exit that is cheaper than vector setup. So the "vectorised" patch is not
  vectorised in the emitted code at all, and the two binaries are doing the same work — which is exactly what a
  ratio of 1.0001 looks like.

**So this experiment did not test "vector compare vs scalar compare"; it tested "scalar compare written two
ways".** The negative result therefore does **not** establish that the scan's cost is a load stall. It only
establishes that *this* reformulation is a no-op. That is a correction to §6 above, which I am not letting stand.

### Suspicions, not proven

- Whether the scan's ~39 % is a load stall or comparison work: **still open**, and the right way to force the
  compiler's hand is an inline-asm or `__builtin_ia32_*` formulation that it cannot scalarise, or a
  `-ftree-vectorize`-forced variant for comparison. That is the experiment a next seat should run.
- That four scalar compares with an early exit is already optimal for a cluster where most hits are in slot 0 —
  which is the more likely explanation of why nothing is available here.

## 7. What I did NOT do

- No instruction counts (tool unavailable, see §5).
- I did not disassemble the unpatched loop to see whether the compiler had already vectorised it — named above as
  the obvious follow-up.
- I did not tune beyond this one change, as instructed.
- I did not run the patch through a match; the pins holding means a match is not *required* to accept it as
  behaviour-preserving, but a speed claim would still need the paired protocol at more rounds.

## 8. Files

`pcspeed/fast_tt_scan.py` (the edit), `pcspeed/ttvec.patch.txt` (the patch), `pcspeed/pair_pc20.py`,
`pcspeed/vec/pairs/RESULT.txt` (design A).
