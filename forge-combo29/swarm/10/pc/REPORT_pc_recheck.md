# REPORT — seat 10 (area 10): every find of mine re-run on the PC build under PC20

What was asked: file 5 says "your own finds on the base tree: run the reproduction on the PC build under
PC20. A find that is gone there is repaired on the PC; a find that is still there is worth much more now."

The answer, in one line: **all of my surviving finds are still present on the PC build under PC20**, and one
of them (10-F14) comes back with its sign **reversed**. One find of mine (10-F8) was **wrong** and is
retracted; its true form is different and also present on both builds.

How sure: certain for every row below — each number is the pasted output of a committed script, and every
search was driven by the EOF-safe driver (`audit/drv.py`) one `go` at a time.

## Honesty numbers for both builds

| build | settings | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|---|
| base 6b98f217 | none | 312866 | 862329 | 3024920 | 4865609 |
| base 6b98f217 | S14 | 242796 | 656517 | – | 4865609 |
| **PC r15** | **none** | **312866** | **862329** | **3024920** | **4865609** |
| **PC r15** | **S14** | **242796** | **656517** | – | – |
| **PC r15** | **PC20** | **278024** | **587276** | – | – |

All three PC rows match file 5's table to the digit (`pc/raw/pc_pins.json`); all 42 S14+PC20 option names
exist in the exe's own `uci` list (92 listed), 0 `unknown option` / `invalid value` / `ERROR` lines.
Build provenance and the patch sha256 (`d6bd72c531f785f4…`, matching the file): `pc/PC_BUILD.txt`.

**Thread rule (seat 04):** every score in this report is **Threads 1**, Hash 16. Nothing here is provisional.

## The table

| find | base (S14) | PC r15 (PC20) | state on the PC |
|---|---|---|---|
| **10-F11** `ucinewgame` AFTER `position` resets the board | eval total −351 → +38; perft 1 38 → 20 | eval total −351 → +38; perft 1 **37** → 20 | **STILL PRESENT** |
| **10-F21** two identical searches in one process are not reproducible | 56,720 → 4,951 | **21,600 → 5,161** | **STILL PRESENT** |
| **10-F22** `ucinewgame` restores cold; `Clear Hash` does not | cold 56,720; ucinewgame 56,720; ClearHash 40,569 | cold **21,600**; ucinewgame **21,600**; ClearHash **24,708** | **STILL PRESENT** (and Clear Hash is now *higher* than cold, not lower) |
| **K1** illegal move keeps the legal prefix | perft 1 = 29 | perft 1 = **29** | holds |
| **K2** `setoption name Hash value 0` message | `info string invalid value for option Hash` | identical string | holds |
| **K12** `bestmove 0000` on checkmate / stalemate | 0000 / 0000 | 0000 / 0000 (0 nodes each) | holds |
| **10-F14** `searchmoves` to ALL 20 moves changes the score | cp 30 / e2e4 vs cp **23** / d2d4 | cp 25 / d2d4 vs cp **29** / d2d4 | **STILL PRESENT, SIGN REVERSED** |
| **10-F19** that gap survives with IIR off | gap survives | gap survives (IirDepth 20: 44,271 nodes side) | **STILL PRESENT** |
| **10-F8** `go banana` "answers bestmove a2a3" | — | — | **RETRACTED, see 10-R4** |

Raw: `pc/raw2/pc_recheck.json`; reproduce with
`python3 forge-combo29/swarm/10/pc/pc_recheck.py <outdir>`.

## The things worth reading twice

**1. The warm-state defect is on the PC build too, and it is not a base-tree quirk (10-F21).** Two identical
unrestricted searches at depth 12 in one process go **21,600 → 5,161** nodes under PC20. So the rule I sent
out earlier — cold baseline is a fresh process or `ucinewgame`, never `Clear Hash` — applies to the engine the
owner actually plays. This is the find with the widest blast radius: it is about how everyone measures, not
about a feature.

**2. `Clear Hash` now makes the search *slower*, not faster (10-F22 on PC20).** On the base tree `Clear Hash`
gave 40,569 against a cold 56,720 (a "third value"). On PC20 it gives **24,708 against a cold 21,600**, i.e.
*above* cold. The direction is not even stable across builds, which is another reason `Clear Hash` must never
be used as a cold-start control.

**3. 10-F14's sign is reversed on the PC build.** Base: unrestricted is *better* (cp 30 vs cp 23).
PC20: unrestricted is *worse* (cp 25 vs cp 29) while playing the same move d2d4. A difference that changes
sign between the two builds is not "the restricted search is weaker" — it is that the two searches are
different searches, which is exactly the framing seat 27's mechanism supports (extra reduced ply + skipped
root store), and it makes seat 27's S-F8b "third cause" still open on the PC build too.

**4. 10-F8 was wrong, and the way it was wrong is the lesson (10-R4).** I recorded `go banana` as "runs a
real search and answers `bestmove a2a3`". With stdin held open it starts an **unlimited** search and answers
*nothing* until a `stop` is sent (24 `info depth` lines on base+S14, 22 on PC20, 22 on base+none). My
`bestmove a2a3` was the EOF-abort artefact of 10-C5 — the same trap I had broadcast to the swarm, in my own
measurement. **What survives and is worth keeping:** garbage `go` lines are **not** ignored; they start an
unbounded search, so a fuzzer that expects silence on junk `go` commands will hang. That is true on both
builds. Raw: `pc/raw3/go_banana.json`, probe: `pc/go_banana_probe.py`.

## Suspicions, not proven

- K12 returned `nodes 0` on both the checkmate and the stalemate root on the PC build. On the base tree the
  same rows also answered `0000`. File 3 says a **drawn** root is searched normally on the PC (only
  insufficient material is answered at once), and a checkmate/stalemate root has no legal move at all, so
  0 nodes is expected there. I did not test a *third-occurrence* repetition root on the PC build to see the
  FORGE_FIX_ROOT_DRAWN repair directly; that is the natural next check and I have not done it.
- 10-F19 on PC20 with `IirDepth 20` changed the node counts a lot (44,271 on one side). I recorded the scores
  but did not chase the node side; it is not needed for the claim as stated.

## What I did NOT do

- I did not re-run job2's deepseek6 recount on the PC build (it is about another helper's harness, not the
  engine, so the build is irrelevant to it).
- I did not test the PC build's FORGE_FIX_ROOT_DRAWN, FORGE_FIX_GO_PARSE or the bare-king switches directly;
  that is a separate job and is the next thing I would do.
- No sanitizer run was made on the PC build.

## What I am NOT sure about

- Whether 10-F14's sign reversal is a property of PC20's four new search switches (CuckooRep, HistRework,
  TtPruneV2, CorrHistV2) or of one of them. I did not isolate them; that needs one job per switch.

## times: see `pc/stamps.txt`

## The last command's output

```
$ git status --short
 (clean)
$ ls forge-combo29/swarm/10/pc/
go_banana_probe.py  PC_BUILD.txt  PATCH_SHA.txt  pc_pins.py  pc_recheck.py  raw  raw2  raw3  REPORT_pc_recheck.md  stamps.txt
```
