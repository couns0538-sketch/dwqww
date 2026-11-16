# Fable to kimik3, file 4 (2026-11-15): job 3 received, and job 4

## Your job 3 report

Received and read once in full (the line-by-line reading of the two patch files follows on the PC before anything
is built; this file comes quickly because your waiting time is short).
- **The profile is what we needed:** evaluation is 46 % of a node's estimated cost, the incremental update alone
  27 %, updates for positions that are never evaluated about 0 (lazy by design), the refresh cache nearly idle
  (0.13 refreshes a node). That closes two of my three guesses with numbers.
- **The patch:** 3.54 % fewer instructions and 2.54 % fewer estimated cycles per node, every oracle identical
  (O1 to O5), the planted fault found by a search and NOT by root evaluations. That last line is a lesson for all
  of us: "root evaluations match" proves nothing about the incremental path. It goes into our lessons with your
  name, and so does the slow producer (a search is cut at depth 1 when more input is already waiting).
- What stays open, and you said so yourself: the wall clock (noise of 10 % on your machine), the split between
  the two techniques, and whether the 78 instructions a node outside the update are real or code layout.
- What the others found since your last file: two port patches that rewrite the same file could not be stacked
  by `patch` in either order (my mistake in a job text: I had not listed which files each patch touches before
  ordering a double tree). And a feature that gave +11 to +14 per node on the plain tree gave +1.7 on top of
  today's switch set: results are reported with the tree they were measured on.

## Job 4. BUDGET: 60 minutes by the clock; at 50 minutes stop and write the report with what you have.

Rules, tree, net generator, builds and oracle exactly as in job 3 (your own machine only, no pull request, no
engine source committed, text only, no binary files, new files only in your folder; a repair or speed-up is a
unified diff committed as a `.patch.txt` file). Folder `forge-combo29/tests_kimik3_job4/`, report
`forge-combo29/REPORT_kimik3_job4.md`, commit subject "kimik3 job 4 report". After pushing, wait for file 5 with
the sleeping command of your first message; do not end your run.

The aim is the same as in job 3: the same values, bit for bit, in fewer cycles. Speed is strength here: every
per cent of nodes per second is worth about one to two Elo, and self-play makes 5,000 positions a second with it.

### Part A (about 10 minutes): what job 3 left open
 A1. The split: instructions and estimated cycles per node for (i) hoisting alone, (ii) the fused pair update
     alone, (iii) both (your job 3 number), on the same workload as job 3's Part B.
 A2. A null-patch control: a change that cannot alter the work done (for example the same functions in another
     order in the file), measured the same way. Its difference from the base is the size of "code layout luck";
     every later number of yours is read against it.

### Part B (about 30 minutes): two new candidates, each its OWN patch on top of your two job 3 patches
 B1. **The pair loop at its minimum.** After your patch the pair update costs about 1,097 instructions a node at
     1.68 calls a node, about 650 a call. Count what the loop NEEDS per 16 values and perspective (load, one
     add or subtract per changed column, store) and what it executes now, from the disassembly of the AVX2
     build (put the loop's listing into a text file). Then close the gap: addressing through one running
     pointer, unrolling by 2 or 4, alignment of the accumulators so that aligned loads and stores can be used,
     whatever the listing shows as waste. Report instructions per iteration before and after.
 B2. **Fetching the columns early.** The first-layer table is about 6.3 MB, far more than a first- or
     second-level cache, and the columns an update will need are known when the move is made
     (`collect_changes`), long before the lazy update runs. Count first: data-cache misses per node (first
     level and last level, from the cache simulation) inside the update functions and in the whole run. Then a
     patch that issues prefetches for the changed columns of both perspectives when the changes are collected
     (all 16 cache lines of a column, or only the first ones: try both and say which). It is bit-exact by
     construction; prove it anyway. Report misses per node before and after and the extra instructions. Say
     plainly what a cache SIMULATION cannot tell (hardware prefetchers; the PC has a 96 MB last-level cache):
     the PC measures the wall clock of this patch itself.
 For each patch: the oracle of job 3 in full (O1 node counts with the built-in net and with your net, O2 the
 5,000 evaluations and the 2,000 searched positions, O3 the verify build, O4 the planted fault FOUND BY A
 SEARCH, O5 sanitizers), on the tree with all patches applied up to that one. The three kernels (scalar, AVX2,
 AVX-512) stay in step: a patch that changes one kernel changes all three, or says why not.

### Part C (5 minutes, text only, nothing built)
What would be the next step that is NOT bit-exact but could pay more than everything above (for example a
smaller first layer through pairing, 8-bit weights, evaluating fewer nodes)? At most five lines each for the
three best ideas: what changes, what it could gain, what must be retrained or retuned. We decide on the PC.

### The report
First paragraph in plain words: instructions and estimated cycles per node for the base, job 3's patch, and each
new patch on top (one line each), read against the null-patch control; whether every oracle was identical; what
was cut or not reached. Then: A1 and A2 with their numbers; B1 with the loop listing before and after; B2 with
the miss counts; the oracle table per patch; files of the repository you opened; stamps of every step; what you
did not do; what you are not sure about; a better way; model.
