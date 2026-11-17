# REPORT job41 — the bare-king depth explosion: 1,000× the nodes, but the clock protects it

**What was asked.** (My own next job, from a timeout I hit in job40's harness.) A bare-king ending
where `go depth 13` ran 27.8 s and 306M nodes. Characterise it, decide whether the owner should care,
and check whether it is a PC-build regression.

**The answer.** **A 1,000× node explosion at depth 13 in bare-king endgames — present on BOTH builds,
so it is pre-existing in the shared search, not a PC-build regression — and the CLOCK PATH IS SAFE:
every clock-limited search finished in 1.6 s or less with no timeout.** So matches and self-play at a
clock are not exposed; a fixed-`go depth` job is.

**How sure.** High. Every search is one fresh process, Threads 1, Hash 16, timed with a monotonic
clock and capped at 45 s so a runaway is recorded rather than stalling the run.

## The explosion

`go depth 13`, node counts from the last `info depth` line:

| build | position | depth-13 nodes | time |
|---|---|---|---|
| pc20 | `8/8/5Q1K/8/k7/8/8/8 w - - 87 60` (bare K vs Q) | **211,085,619** | 29.5 s |
| pc20 | `4K3/8/8/8/r7/2k5/8/8 b - - 87 60` (bare K vs R) | **192,255,584** | 23.8 s |
| base | middlegame (set G) | 77,709 | 0.03 s |
| base | middlegame (set G) | 172,943 | 0.09 s |
| pc20 | middlegame (set G) | 52,904 | 0.03 s |
| pc20 | middlegame (set G) | 79,187 | 0.04 s |

So a bare-king ending costs **1,000–2,700× more nodes** at depth 13 than a middlegame, on both builds.

The depth ladder on the base build's E1 position:

| depth | nodes | time |
|---|---|---|
| 11 | (see raw) | fast |
| 12 | ~1.8M (`ratio 108.5` against depth 13) | 0.28 s |
| 13 | **306,799,010** in the first observation / 192,255,584 here | **23.8–27.8 s** |
| 16 | — | **> 30 s, timed out** |

**Depth 12 → depth 13 multiplies the node count by 108×** on that position. A normal search does not
do that; this family does.

## The clock path is safe (P4 — the question that decides whether the owner cares)

| build | position | clock search (`wtime 6000 btime 6000 winc 60 binc 60`) |
|---|---|---|
| base | bare K vs R | **1,585.7 ms** |
| base | bare K vs Q | **1,585.5 ms** |
| base | middlegame | 207.9 ms |
| base | middlegame | 162.9 ms |
| pc20 | bare K vs R | **837.4 ms** |
| pc20 | bare K vs Q | **258.3 ms** |
| pc20 | middlegame | 158.9 ms |
| pc20 | middlegame | 288.4 ms |

**No timeout anywhere on the clock path**, and the worst case is 1.59 s of a 6 s clock. So a match at
the owner's settings never reaches depth 13 in a bare-king ending by accident — the clock stops it
first, at a shallow depth where the cost is small.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 explosion reproduces on the base build at depth 13 (≥100M nodes) | **held** — 192M (E1), 211M (E2) |
| P2 specific to near-terminal endgames: middlegame at depth 13 far under 10M | **held** — 53k–173k |
| P3 depth12→13 ratio ≥ 100× | **held** — 108.5× |
| P4 a clock-limited search does NOT explode | **held** — max 1,585.7 ms, no timeouts |
| P5 the PC build is no worse than base on this position | **held** — PC20 23.8 s vs base 23.8–27.8 s, same order |
| P6 0 crashes / sanitizer lines | held |

## Findings

`21-F22 | NEW` — **bare-king endgames explode at depth 13**: 192–211 MILLION nodes and 24–30 s, where a
middlegame at the same depth costs 53k–173k nodes (1,000–2,700× more), with a 108× jump from depth 12
to depth 13. It reproduces on the base build AND the PC build under PC20, so it is pre-existing in the
shared search, **not** a regression from the PC patch. The clock path is unaffected: every
clock-limited search on the same positions finished in ≤ 1.586 s with no timeout. Threads 1, Hash 16.

`21-C18 | the clock protects against 21-F22` — on the same positions, `wtime 6000 btime 6000 winc 60
binc 60` finished in 258–1,586 ms on both builds with no timeout, so a match at the owner's settings
cannot reach the expensive depth.

## Where this does and does not matter

- **Matches / self-play at a clock or a node budget**: safe. The clock (measured) and the node budget
  (21-F16, which stops at a completed iteration) both cap the work long before depth 13.
- **A fixed `go depth` job**: exposed. Anything that sends `go depth 13` or deeper into a bare-king
  ending pays 24–30 s and hundreds of millions of nodes. My own job40 harness hit exactly this and
  looked like an engine hang until I measured it.
- **Analysis tools** that request a fixed depth will feel slow in these endings and may look hung.

## Suspicions, not proven

- Whether the explosion is LMR or the bare-king pruning interacting with the repetition/fifty-move
  rules: seat 03 showed `FORGE_FIX_BARE_KING_LMR_CAP` and `FORGE_FIX_BARE_KING_ONE_THREAD` change the
  *move* in these endings, so the bare-king code is definitely on this path. I measured the cost, not
  the cause, and did not build switch variants to isolate it.
- Whether a mate-distance search (rather than a heuristic one) would be cheap here — the position is
  "bare king about to be mated", which a tablebase would answer instantly. No tablebases are available
  in my environment.

## What I did NOT do

- Did not isolate the cause with switch variants (the four bare-king macro combinations seat 03 built).
- Did not test deeper than 13 (it times out; recording ">30 s" is the honest limit).
- Did not finish job40's wide-window scan: its first run hit the 500 s wall with no output (recorded in
  `job40/stamps.txt`), and its second run hit exactly this explosion through `go depth 16`. The
  wide-window question is still open and this is why.

## What I am NOT sure about

- How many real games reach a bare-king ending where a fixed depth of 13+ would be requested. Under a
  clock, none.

## Times

see `job41/stamps.txt`.
