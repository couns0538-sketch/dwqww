# ⚠ ANALYSIS WARNING — Hash 2048 MB with MultiPV above 1 collapses analysis to depth 1

**(and can occasionally return a move with no search at all)**

**Read this before your next analysis session. It does not affect your matches.**

> **CAUSE KNOWN. Every fix attempt FAILED; the recommendation below is the only safe configuration.**
> (Seat 30's `tt.clear()` patch is a real, verified improvement — but it does **not** close the large-Hash case on its
> own: four variants were tested and all four fail, see `job71/CLOSE.md`. **MultiPV 1 at any Hash, or Hash 16 MB with
> multiple lines** is still the answer, and it is not a workaround — it is the correct configuration.)

> **One cause, and a patch that fixes only that much.** The collapse is one
> redundant line: `src/search.cpp:2879 alt_shared->tt.clear();` inside the per-line loop at 2851, i.e. a full
> transposition-table clear once per extra PV line *per depth*. A patch that deletes it restores depth 12–13 at
> Hash 256–512 with all four honesty pins unchanged and the MultiPV 1 path byte-identical (verified on my own build,
> `job57/CONFIRM_30C36.md`). It is a genuine improvement worth having, but it is **not sufficient** for the large-Hash
> case: see the closure above. Its strength effect in play is **unmeasured**.

## Four fixes were tried; all four fail (each for a different reason)

| variant | depth at large Hash | alternate lines | why it fails |
|---|---|---|---|
| repaired only (alt table = main) | **collapses to depth 1** | faithful | does not restore depth |
| fixed 64 MB cap | 14 ✓ | move ≤775 cp, both directions | unpredictable |
| share one table | 11–15 ✓ | move ≤~900 cp | bounds come from a different root restriction |
| own 8 MB table | 14 ✓ | 0 cp median shallow | **p90 112 cp at depth 23** — evicts what the reference kept |

**Why all four fail, in one sentence:** the alternate line **needs a large table for deep searches** (a smaller one
evicts) and **the engine cannot afford to allocate one**, because it allocates a second full-size table synchronously
and that allocation eats the clock. So a real fix must attack **the cost of allocating, not the size** — lazy zeroing
of a large table, a smaller cluster format, or one allocation reused across lines with disjoint generations.
**All three are search-engine design work, and nobody has done it** — not me, not any seat. What this thread delivers is
the diagnosis plus four ruled-out directions, not a patch.

> **Until then, the short answer: if you want multiple lines, set `Hash 16 MB` — it is the least-lossy MultiPV
> choice. If you want a big Hash, use `MultiPV 1`. Do not combine a big Hash with multiple lines.** (Measured limits
> below: MultiPV 3 is safe to 128 MB, MultiPV 8 only to 64 MB; 256 MB and above is unusable for any MultiPV above 1.)

## The configuration that fails

| setting | value |
|---|---|
| engine | PC build (r15), Threads 1 |
| `Hash` | **2048 MB** |
| `MultiPV` | **2, 3 or 8 — every value tested collapses** |
| clock | any — measured with `go wtime 5000 btime 5000` |

## Scope — measured on TEN positions, not two (5 fresh processes per cell, 50 runs per cell)

| cell | zero-node runs | positions with a zero-node answer | **positions with a depth collapse** |
|---|---|---|---|
| **Hash 16 + MultiPV 1** (healthy) | **0/50** | **0/10** | **0/10** |
| **Hash 2048 + MultiPV 2** | 2/50 | 2/10 | **10/10** |
| **Hash 2048 + MultiPV 3** | 0/50 | 0/10 | **10/10** |
| **Hash 2048 + MultiPV 8** | 0/50 | 0/10 | **10/10** |

**Collapse means the search reached depth 1** on that position — against depth 14–17 for the healthy setting. Every
one of the ten positions collapsed at every MultiPV value tested. Node counts in the collapsed cells were **22–595**,
against **176,257–613,767** healthy: the engine uses about a thousandth of the search it should.

So the warning is **broader** than my earlier two-position version and the scope is now certain:
**Hash 2048 MB with any MultiPV above 1 gives depth-1 analysis on every position tested.** The zero-node failure
remains real but RARE (2 of 50 runs, only at MultiPV 2); the reliable, reproducible problem is the collapse.

## The zero-node failure specifically — and its load sensitivity
(10 fresh processes per arm, one position, `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b`)

| configuration | idle PC | **busy PC (3 CPU hogs)** |
|---|---|---|
| **Hash 2048 + MultiPV 8** | **1 of 10** runs returned a 0-node answer | **6 of 10** runs returned a 0-node answer |
| **Hash 16 + MultiPV 1** (healthy control) | **0 of 10** | **0 of 10** |

A "0-node answer" means the engine returned a `bestmove` with **zero nodes searched** — the move has nothing behind
it. Note the ten-position run above put this at **2 of 50 runs** (MultiPV 2 only), so on an idle machine the 0-node
answer is rare; the load test below is what makes it common. In the failing configuration the returned **move also
varies** between runs (`b8a8` / `d5d4`), so the same position can give different recommendations on consecutive
analyses.

## Why it happens
With MultiPV above 1 the engine clears the transposition table for each additional line. At 256–2048 MB that clearing
costs more than the move's whole time budget, so on a contended machine the clock expires before any depth is
published and the engine falls back to its first move. Measured depths in the failing cells: **1 to 7 instead of 17**
(and sometimes 0 nodes).

## A second, milder warning — 256 MB with MultiPV 3 is much SHALLOWER (no zero-node failure)

At **Hash 256 + MultiPV 3** the engine never returned a move with no search (0/5 idle, 0/5 under load, two
positions), but it searches a small fraction of what the healthy setting does:

| setting | nodes used on P1 | nodes used on P2 | vs healthy |
|---|---|---|---|
| Hash 16 + MultiPV 1 (healthy) | 288,912 | 237,233 | — |
| **Hash 256 + MultiPV 3** | **5,395 – 47,818** | **1,132** | **2–50 % of the search** |

So at this setting you get a **materially shallower analysis** (and a move that can differ from the healthy one,
e.g. `e5e4`/`g7g6` instead of the healthy move) without any no-search failure. It is a quality-of-analysis problem,
not a reliability one — but at 5,395 nodes against 288,912 it is not a small difference either.

## The fix — measured boundary, per MultiPV (10 positions per Hash, median depth; healthy = 17)

| Hash | MultiPV 3 median | MultiPV 8 median | verdict |
|---|---|---|---|
| **16 MB** | **13.5** | **11.0** | **both usable — least-lossy choice** |
| 64 MB | 11.5 | **9.0** | usable |
| 128 MB | **11.0** | **6.0** | safe at MPV 3 only |
| **256 MB** | **4.0** | **2.0** | **UNUSABLE for any MultiPV > 1** |
| **512 MB** | **1.0** | **1.0** | **UNUSABLE** (all 10 positions depth 1) |

The safe limit **depends on MultiPV**: **128 MB at MultiPV 3, but only 64 MB at MultiPV 8** — the more lines you ask
for, the earlier it breaks. The collapse is a **cliff between 128 and 256 MB** (at MPV 8, between 64 and 128), not a
gradual decay, and below the cliff there is still a gentle gradient: MultiPV 3 gives up ~3.5 plies and MultiPV 8
~6 plies even at 16 MB.

**So, in order of preference:**
1. **MultiPV 1 at any Hash** — unaffected at every size (depth 14–19).
2. **Multiple lines: Hash ≤ 128 MB at MultiPV ≤ 3, or Hash ≤ 64 MB at MultiPV 8.** Accept that you lose depth versus
   MultiPV 1; **16 MB loses least**.
3. **Never Hash ≥ 256 MB with MultiPV > 1** — that is where analysis becomes depth 1–4 and, on a busy machine, can
   return a move with no search at all.

## Related, and worth knowing if you use restrictions: two different `searchmoves` answers

- **A satisfiable restriction is repaired** on the PC build: `searchmoves <legal mating move>` at halfmove 100 finds the mate (8 nodes) where the base tree gives `cp 0` / 0 nodes.
- **An empty or illegal restriction is NOT**: `go searchmoves` naming nothing legal still answers `0000` with 0 nodes, on the PC build too.

**Quote these together.** Either alone misleads: the first would suggest the `0000` case is fixed, the second would deny a repair that works.

## Your matches are NOT affected
The matches run **MultiPV 1**, so none of this applies to game play. It is an **analysis-path** problem only.

## RULE for every clock-based table: state the process discipline

Any measurement taken on a **clock** depends on whether the engine ran the positions in a **fresh process each** or in
**one long-lived process**, and the difference is not small: on the same cell (6 s + 0.06, MultiPV 1, Hash 16, 10
game positions) a fresh process per position gave **median depth 18** and one warm process gave **median depth 20** —
**+2 plies at the same wall time**. This is the same class as the known rule that node counts are only comparable
between cold runs; it turns out depth on a clock moves with it too.

So: **"depth N at clock T" is not a number unless it says cold or warm.** A cold figure answers "how deep does a
fresh engine get on this position"; a warm figure answers "how deep does it get in a game, where it has been thinking
for many moves". The PC's matches are warm (one process, many moves), so **warm is the match-realistic reading**.
Details and raw rows: `job58/CROSSCHECK_05.md`.

## A cause and a repair exist (independently verified)
The collapse is **not inherent** — it is a redundant full-table clear. `src/search.cpp:2879`
`alt_shared->tt.clear();` sits inside the per-line loop opened at line 2851, so it runs once per extra PV line **per
depth**. Seat 30 wrote a patch that deletes it; I applied it to my own build and reproduced their figures exactly
(5 fresh processes per cell, MultiPV 3, `go wtime 5000`, Threads 1):

| Hash | shipped | repaired |
|---|---|---|
| 256 MB | depths **[11,11,11,7,11]**, nodes **47,818 / 5,395** (unstable) | depth **13**, nodes **106,863**, 5/5 stable |
| 512 MB | depth **1**, **220** nodes | depth **12**, **71,070** nodes, 5/5 stable |

The repaired build keeps **all four honesty pins** (312,866 / 862,329 / 3,024,920 / 4,865,609) and the **MultiPV 1
path is byte-identical** to the shipped build, so it changes only what it claims to. Whether to adopt it is the
owner's decision; this page only records that its evidence reproduces on an independent build. **What is measured on the analysis side: the patch costs NOTHING at the safe Hash sizes and gains depth
there** — Hash 16 median 13.5 -> 14.0, Hash 64 11.5 -> 14.0, Hash 128 11.0 -> 14.0 (10 positions, MultiPV 3, 5 s
clock, Threads 1; `job64/REPAIR_AT_SAFE_HASHES.md`). The repaired build is flat at ~14 plies from Hash 16 to 128 (14.0/14.0/14.0) but **still declines above that**
(256 -> 12.0, 512 -> 10.0), so the multi-PV gradient is **mostly** the per-line `clear()` — about 3 of the 4-5 plies at
Hash 128 — with a further ~2 plies per doubling above 256 MB coming from table size itself. **The patch does not make a
2 GB table as good as a 16 MB one**, so "huge Hash with MultiPV" stays a bad idea even repaired.

**What is NOT measured: whether the patch makes the engine stronger in PLAY.** Depth at a fixed clock is not a match
result; a strength claim would need interleaved matches, which I did not run.
Details: `job57/CONFIRM_30C36.md`.

## How sure this is
- Counts are exact: 5 processes per cell across **10 positions** for the collapse table (50 runs per cell); 10
  positions per Hash for the boundary table; 10 processes per arm on one position for the load table. Fresh process
  each, `Threads 1`, one clock.
- The healthy control never failed (0/10 in both conditions), so the failure belongs to the configuration and not to
  the machine or the harness.
- Full per-run data and raw output: `job53/ZERO_NODE_UNDER_LOAD.md`, `job53/zero_node.json`, `job53/run.log`.
- Supporting runs: `job50/MULTIPV_HASH.md` (the depth collapse grid), `job51/MOVE_QUALITY.md` (the move is 46 cp
  worse in one cell), `job52/CLASS_TEST.md` (2 of 6 positions materially worse; the rest unchanged).
- Limits: the **collapse** is established on 10 positions (10/10 at every MultiPV), so it needs no further sample.
  The **0-node** rate under load (1/10 → 6/10) is still measured on **one** position; on ten idle positions it was
  2/50. So: collapse = certain and universal at 2048 MB; 0-node = rare idle, common under load.
- Hash 256 + MultiPV 3 was tested on two positions earlier and gave no 0-node answer, which is why the *no-search*
  claim is scoped to 2048 MB — while its depth collapse (5,395–47,818 nodes vs 288,912) is the milder warning below.
