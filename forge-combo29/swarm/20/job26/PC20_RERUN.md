> **READ THIS FIRST (seat 20, S-F38/S-F34a).** This file reports results obtained under **PC20**, which is a
> **bundle**. The mate-distance correction is NOT the bundle: **`MateAlphaGuard true` alone** (Threads 1,
> Hash 16, nothing else) turns the PC build's `mate -7` into the true `mate -4`, while the other five PC20
> extras *alone* lose the mate entirely (`cp -3122`). Do not quote "PC20 fixes X" from this file; quote the
> switch. Details: `job29/MATEALPHAGUARD.md`.

# seat 20 — job 26: my own finds re-run on the PC r15 build under PC20

File 5: "run the reproduction on the PC build under PC20. A find that is gone there is 'repaired on the PC'; a find
that is still there is worth much more now."

**Every row below is `Threads 1`** (the swarm rule effective 22:19Z; PC20 pins `Threads 1` explicitly and so does my
base S14 config). **Builds:** `base_s14` = base tree 6b98f217, S14, Threads 1, Hash 16, OwnBook false.
`pc20` = PC r15 (base + file 5 patch, sha256 d6bd72c531f785f4…, `-DFORGE_MATE_ALPHA_GUARD=1`), PC20 = Threads 1,
Hash 16, the 14 S14 settings, then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
MateAlphaGuard true, OwnBook false. Fresh process per search throughout (`AUDIT/hardened.py`).

Raw: `job26/pc20_rerun.json` (38 rows). Script: `job26/pc20_rerun.py`.

## The result, case by case

| # | my find | base_s14 | pc20 | verdict |
|---|---|---|---|---|
| F1 | repetition door: board reached a THIRD time, mate in 1 available | `f2f3` / **cp 0 / 0 nodes** | `d1d8` / **mate 1 / 162 nodes** | **REPAIRED on the PC build** |
| F1c | control: same board, no history | `d1d8` / mate 1 / 168 | `d1d8` / mate 1 / 168 | control passes on both |
| F2 | halfmove 100, mate in 1 | `f2f3` / **cp 0 / 0 nodes** | `d1d8` / **mate 1 / 168 nodes** | **REPAIRED** |
| F2c | control: halfmove 99 | `d1d8` / mate 1 / 168 | `d1d8` / mate 1 / 168 | control passes on both |
| **F3** | empty `searchmoves` on a 20-move board | `0000` / cp 0 / 0 nodes | `0000` / cp 0 / 0 nodes | **STILL LIVE on the PC build** |
| F3c | control: plain `go depth 2` | `d2d4` / cp 39 / 59 | `d2d4` / cp 39 / 59 | control passes on both |
| **F4** | `ucinewgame` resets the board | `c2c4` (a startpos move) | `c2c4` (a startpos move) | **STILL LIVE on the PC build** |
| **F5** | mate distance on the S-F19 board, depth 12 (true = 8 plies = mate −4) | `c2c3` / **mate −12** / 19,197 nodes / 18-ply pv | `c2b1` / **mate −4** / 34,365 nodes / 8-ply pv | **FIXED — the PC build reports the TRUE distance** |
| **F7** | `hashfull` samples only the first 1000 clusters | Hash 16: 32, Hash 1024: **0**; nodes 68,388 both | Hash 16: 14, Hash 1024: **0**; nodes 36,104 both | **STILL LIVE on the PC build** |
| **F8** | `go nodes 1` answers the first legal move, no search | `a2a3` / 0 nodes | `a2a3` / 0 nodes | **STILL LIVE on the PC build** |
| F9 | `go movetime 100` stops ~9 ms early | 91.75 ms default / 101.92 at overhead 0 | 91.20 / 101.72 | **STILL LIVE (by design, file 3)** |
| **F10** | fifty-move horizon reaches the root score ~10 plies early | first `cp 0` at **halfmove 91** | first `cp 0` at **halfmove 91** | **STILL LIVE, but see below** |

## The four things that matter

**1. The two drawn-root doors are genuinely closed on the PC build (F1, F2).** This independently confirms Opus's
file 3 claim — not by trusting the text, but by running the same third-occurrence and halfmove-100 cases on both
binaries. Base: 0 nodes, cp 0, first legal move. PC: the mate, searched. My S-C1/S-C4/S-F13 are therefore
**base-tree-only** across both builds, and S-F28's reading is now backed by measurement rather than by a quotation.

**2. The mate-distance problem is FIXED on the PC build (F5).** This is the strongest single result of the job.
Base at depth 12 claims 24 plies; the PC build at the same depth 12 returns `mate -4` — exactly the 8-ply distance
my job16 proved by exhaustive search. So S-F17/S-F18/S-F22 describe a base-tree behaviour that the owner's engine
does not have.

**3. Four of my findings survive on the PC build — these are the valuable ones now:** empty-`searchmoves` → `0000`
(F3), `ucinewgame` resetting the board (F4), the 1000-cluster `hashfull` window (F7), and `go nodes 1` returning an
unexamined first legal move (F8). Each has a passing control on the same harness, so none is an artefact.

**4. F10 needs a careful reading, not a headline.** The first `cp 0` is at halfmove 91 on BOTH builds, so that is
not changed by the PC patch. But two details differ and both matter:
- at halfmove 100 the PC build searches **200 nodes** where the base searches **0** — consistent with F1/F2 being
  repaired at the root;
- at halfmove 85 the PC build reports **`mate 8`** where the base reports `cp 349`. A K+R v K win that becomes a
  forced mate 8 is *better* information, not worse.
So "cp 0 from 91" is not a defect on either build: with 9 half-moves left a K+R-v-K win really is not reachable, and
scoring it a draw is correct chess. My S-F16 distinction (0-node root shortcut vs millions-of-nodes in-tree horizon)
still holds and is now shown to be *only* the in-tree kind on the PC build.

## Consequences for my FINDINGS labels
I will not rewrite the old lines (FINDINGS is add-only). Instead each old find gets a state line naming the build
and settings under which it was last checked, and the PC-build status above is recorded as its own finding.

## What this does NOT establish
- Only `Threads 1`. Seat 04's report (four distinct scores at Threads 4 on one position: +2576, mate 13, mate 18,
  mate 16, with nodes 5.0M–31.4M) means no score of mine may be quoted above Threads 1, and none is.
- PC20 uses the BUILT-IN net. The PC plays its own trained net (file 5: not shared), so evaluation-dependent
  results — my S-C6 `eval` symmetry, F10's `mate 8` — remain questions for the PC.
