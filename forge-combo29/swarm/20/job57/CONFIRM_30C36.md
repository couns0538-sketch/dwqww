# seat 20 — job 57: independent confirmation of seat 30's cause (30-F47) and repair (30-C31 / 30-C36)

Seat 30 reported that MultiPV > 1 calls `TranspositionTable::clear()` once per extra line **per depth**, that this
full-table write destroys the clock budget, and that deleting it repairs the Hash threshold. I verified all three
independently, with my own build and my own harness.

## 1. The code claim (30-F47) — CONFIRMED, read myself
`src/search.cpp:2879` is `alt_shared->tt.clear();`, and it sits inside the per-line loop opened at **line 2851**
(`for (int index = 2; index <= line_count && !aborted_; ++index)`), which runs once per additional line **at every
depth iteration**. `clear()` walks every cluster, so the cost scales as (MultiPV − 1) × depth × table size. I read
the file myself rather than taking the citation.

## 2. The repair reproduces (30-C31 / 30-C36) — CONFIRMED, exact numbers
I applied their `check6/ttclear_no_alt_clear.patch.txt` to a fresh PC r15 tree (`pc_r15.patch`, sha256
`d6bd72c531f785f4…`, then their patch with `patch -p1 --fuzz=0`, clean), built it with
`-DFORGE_MATE_ALPHA_GUARD=1`, and ran **5 fresh processes per cell**, MultiPV 3, `go wtime 5000 btime 5000`,
Threads 1, on `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b`.

| Hash | build | depths (5 runs) | nodes (5 runs) | stable |
|---|---|---|---|---|
| **256 MB** | shipped | **[11, 11, 11, 7, 11]** | **[47818, 47818, 47818, 5395, 47818]** | **NO** |
| **256 MB** | repaired | **[13, 13, 13, 13, 13]** | **[106863 ×5]** | **YES** |
| **512 MB** | shipped | **[1, 1, 1, 1, 1]** | **[220 ×5]** | yes (reliably useless) |
| **512 MB** | repaired | **[12, 12, 12, 12, 12]** | **[71070 ×5]** | **YES** |

These are **seat 30's exact figures** — depth 13 / 106,863 nodes at Hash 256, depth 12 / 71,070 at Hash 512, and the
shipped instability `{11,11,11,7,11}` with the 5,395/47,818 spread. Reproduced from their patch alone, on my build.

## 3. The honesty gate (30-C31's reviewer check 1) — CONFIRMED, 4/4
The repaired build, no setoption at all: **bench 11 = 312,866; bench 13 = 862,329; bench 16 = 3,024,920;
perft 5 = 4,865,609 — all four unchanged.** So the repair does not move the pinned node counts.

## 4. The control that matters for the owner — MultiPV 1 is untouched
The patch must not change ordinary single-line analysis. Both builds at MultiPV 1:

| Hash | shipped | repaired | identical? |
|---|---|---|---|
| 16 MB | depth 17, 288,912 nodes ×3 | depth 17, 288,912 nodes ×3 | **yes, depth and nodes** |
| 512 MB | depth 17, 288,912 nodes ×3 | depth 17, 288,912 nodes ×3 | **yes, depth and nodes** |

So the repair changes exactly the MultiPV > 1 path, which is the path it claims to fix, and nothing else I can see.

## What this means for the owner
1. **The cause is real and identified in the source**: a redundant full-table clear inside a loop that runs per line
   per depth.
2. **A repair exists, keeps all four honesty pins, and fixes both the collapse and its instability** — at Hash 256 the
   shipped build gives 11/11/11/7/11 depths and the repaired build 13 on every run.
3. **Ordinary play is unaffected**: MultiPV 1 gives byte-identical results on both builds.

**I am not advising the owner to adopt a patch I did not design** — that is Opus's call — but I can say the patch's
stated evidence is reproducible on an independent build, which is what a confirmation is for.

## Limits
- One position for the threshold table (their board), 5 runs per cell; their wider sweep covers more.
- I did not re-run their speed table (2.0×–4.2×) — a timing claim on a shared machine needs their interleaved
  method, and I did not want to add a weak timing number.
- Repaired build: separate worktree `/agent/repos/pc-fix`, exe `/agent/repos/build-pcfix/forge`.
