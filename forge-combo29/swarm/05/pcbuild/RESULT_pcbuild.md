# PC r15 build: re-running seat 05's own finds (Threads 1 everywhere)

Patch sha256 prefix **d6bd72c531f785f4** verified; applied in a separate copy; built with
`-DFORGE_MATE_ALPHA_GUARD=1`. Honesty 8/8 under none / S14 / PC20 (`HONESTY_PC.md`).
**Every number below is Threads 1** (swarm rule, seat 04's multi-thread instability).

## The headline: one find repaired, one NOT, and file 3 conflates them

File 3 says the drawn-root defect I reported is "REPAIRED since 15 November" on the PC, and that "only a root with
insufficient material is still answered at once". **That repair is real and I confirm all three parts of it.** But it
is a different mechanism from my fifty-move findings, and testing the two separately shows my finding survives.

| | mechanism | on the PC r15 build |
|---|---|---|
| **A. root-draw shortcut** (file 3's repair) | at a root the engine *decides* is drawn it searched 0 nodes and played its first legal move, even with a mate on the board | **REPAIRED.** K+Q vs K with mate available scores `mate 1` / 280 nodes at halfmoves 0, **99, 100, 101, 150**. Threefold third-occurrence is searched (3,855 nodes). K vs K alone is still answered at once (`cp 0`, 0 nodes), exactly as file 3 says. |
| **B. fifty-move score floor** (my S-F3/S-F11/S-F14) | *during the search*, the drawn score is returned once the horizon crosses the counter, so a **won** position scores `cp 0` at a high counter | **STILL PRESENT.** K+R vs K: `cp 458` at 0, `cp 352` at 88, `cp 289` at 90, then **`cp 0` at 91** (13.99 M nodes), `cp 0` at 95/99/100/150. Unchanged by PC20. |

Evidence: `out/fifty_vs_repair.txt`, `out/repair_claim_test.txt`, `out/fifty_pc_detail.txt`.

So "the PC has repaired the drawn root" is true, and does **not** cover S-F3: a root that is genuinely won is still
scored as a draw once the search's own horizon reaches the counter. Under `date -u` this run is 2026-11-16T22:20Z.

## S-F1 / S-F9 — the mate-PV truncation is REPAIRED under PC20 but NOT under S14

This is the most useful result of the re-run, because it is not a simple "gone or not":

| setting on the PC build | score | plies needed | pv plies | consistent (2N-1 rule)? |
|---|---|---|---|---|
| no options | mate -7 | 14 | 14 | **yes** |
| Threads 1 + Hash 16 | mate -7 | 14 | 14 | **yes** |
| **S14** | mate -9 | 18 | 14 | **NO — short by 4** |
| **PC20** (all six) | mate -4 | 8 | 8 | **yes** |
| PC20 minus CuckooRep | mate -4 | 8 | 8 | yes |
| PC20 minus HistRework | mate -4 | 8 | 8 | yes |
| PC20 minus TtPruneV2 | mate -5 | 10 | 10 | yes |
| PC20 minus CorrHistV2 | mate -4 | 8 | 8 | yes |
| PC20 minus MateAlphaGuard | mate -7 | 14 | 14 | yes |
| PC20 minus OwnBook | mate -4 | 8 | 8 | yes |

G/192 (my S-F1 board) on the base tree under S14 was `mate -12` with an 18-ply pv needing 24 — inconsistent.
On the PC build the truncation **reappears under S14** (`mate -9`, 14 of 18 plies) and **vanishes under PC20**.
Removing any single PC20 option keeps it consistent, so no one option is responsible, and the score moves
(-7 / -9 / -4 / -5) between settings while the 2N-1 rule is met in every PC20 variant.

**G/306 and R/120:** G/306 gives `mate 2` with a 3-ply pv — consistent. **R/120 (my S-F9 instance) no longer
produces a mate score at all**: under PC20 at depth 12 it scores `cp -2713` with a 19-ply pv, so the truncation
I reported there cannot be reproduced on the PC build. I do not call it "repaired", because a different score is
not the same measurement — I call it **not reproducible on the PC build under PC20**.

## Draw scores unchanged (S-F6, S-F12)

| set | PC20 depth 10 | base tree |
|---|---|---|
| K v K | `cp 0`, 0 nodes | `cp 0`, 0 nodes |
| KN v K | `cp 0`, 0 nodes | `cp 0`, 0 nodes |
| KB v K | `cp 0`, 0 nodes | `cp 0`, 0 nodes |
| KNN v K | `cp 285`, 39,248 nodes | `cp 159..354` |

Same shape as the base tree: the three dead draws are zeroed with no search, KNN v K is evaluated as a win.
(Whether KNN v K *should* be a win is S-F12's question and `DeadMaterial true` still zeroes it — not re-tested here.)

## Terminal root (S-F7)

Checkmate root, `go depth 5`: `mate 0`, 0 nodes — same as the base tree.

## What I have NOT done yet
- S-F11/F13/F14/F15's boundary-vs-depth table on the PC build is in `out/rerun_pc20.txt` (boundary 95/93/91/90 for
  depths 6/8/10/12, still summing to ~101) but I have not repeated it under PC20 *and* S14 side by side, nor on a
  second material.
- No planted-case control yet for the "0 nodes at KNN v K" observation on the PC build (rule 1 of file 2).
- Everything here is Threads 1; nothing was measured above Threads 1 on the PC build.
