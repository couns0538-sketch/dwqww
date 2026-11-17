# The 19-F59 numeric disagreement: raw output sent, counters explain one ply, and one thing does not add up

seat 19 · area 9 · answering the coordinator's request for verbatim raw output against seat 27's measurement.

## 1. The three things asked for, verbatim

**(1) My exact command line and FEN.** The FEN came from the sample file `loneking/mirror40.fens` line 12:

```
6k1/8/5K2/8/6r1/8/8/8 w - - 12 182
```

The invocation was, per search (one fresh process each):

```
forge                       # ~/pcbuild/build/forge, sha256 in checks/f59/raw.txt
uci
setoption name LmrQuietBase value 93          # ... the 13 other S14 settings ...
setoption name NonPawnCorrection value true
setoption name CuckooRep value true
setoption name HistRework value 2
setoption name TtPruneV2 value true
setoption name CorrHistV2 value true
setoption name MateAlphaGuard value true
setoption name OwnBook value false            # YES, OwnBook false
setoption name Hash value 16
ucinewgame
position fen 6k1/8/5K2/8/6r1/8/8/8 w - - 12 182
isready
go depth 24
```

`isready` after every `setoption`, every answer line read to `readyok`, `Threads` **never set** (default 1).
**The position was sent as `position fen`, not built from moves.**

**(2) The raw `info depth 24` line from my run:**

```
info depth 24 seldepth 39 score mate -15 nodes 15311437 nps 4059235 hashfull 259 time 3772 pv f6f5 g4a4 f5e5 g8f7 e5f5 f7e7 f5e5 a4h4 e5f5 e7d6 f5g5 h4c4 g5f5 c4a4 f5f6 a4a5 f6f7 a5f5 f7g7 d6e7 g7g6 f5c5 g6g7 c5c6 g7g8
```

and the depth 16 and 20 lines, for completeness:

```
info depth 16 seldepth 17 score cp -490 nodes 108536 ... pv f6e7 g8h7 e7d7 g4d4 ...
info depth 20 seldepth 23 score cp -490 nodes 232803 ... pv f6e7 g8h7 e7d7 g4d4 ...
```

**(3) `position fen`, and OwnBook false.** Yes to both.

## 2. The counters DO matter — for one ply

I re-ran **both** FENs on the same binary, same settings, and got:

| FEN | depth 24 score | depth 24 nodes | move |
|---|---|---|---|
| mine: `... w - - 12 182` | **`mate -15`** | 15,311,437 | `f6f5` |
| seat 27's: `... w - - 0 1` | **`mate -16`** | 7,608,471 | `f6f5` |

**So the halfmove counter explains a one-ply difference (−15 vs −16) — and nothing else.** The move is identical,
and both are far from seat 27's `mate -25`. Depths 16 and 20 are **identical between the two FENs** (`cp -490`,
`f6e7`, 108,536 and 232,803 nodes), so the counters cannot explain the depth-16/20 discrepancy either.

## 3. I could not reproduce seat 27's numbers under any PC20 variation

I tried each PC20 option off, and S14 alone, at depth 20 on seat 27's FEN:

| settings | move | score | nodes |
|---|---|---|---|
| PC20 (mine) | `f6e7` | cp −490 | 232,803 |
| without MateAlphaGuard | `f6e7` | cp −490 | 232,803 |
| without CorrHistV2 | `f6f5` | mate −27 | 1,148,766 |
| without TtPruneV2 | `f6e6` | cp −467 | 204,162 |
| without CuckooRep/HistRework | `f6e6` | cp −549 | 940,245 |
| S14 only | `f6f5` | cp −475 | 225,829 |
| Hash 32 | `f6e7` | cp −490 | 232,803 |
| **seat 27 reported** | **`f6e5`** | **cp −509** | **1,915,526** |

**No combination produces `f6e5`, `cp −509` or 1,915,526 nodes.** `CorrHistV2 off` gets a different move again
(`f6f5`, mate −27) and the closest node count is still 40 % short.

## 4. What I think is happening — stated as a possibility, not a conclusion

The two builds may simply not be the same binary. My `~/pcbuild/build/forge` was built from the file-5 patch with
`-DFORGE_MATE_ALPHA_GUARD=1` on **g++ 13.3.0**. Seat 27's build provenance is not in what I was given, and this
engine's node counts are extremely sensitive to the option set (the table above shows five distinct answers from
one option each) and to compile flags. **A different compiler or a differently-applied patch would show exactly
this pattern: same board, different move, different score, different node count.**

**A checksum comparison would settle it in one command**: `sha256sum` of both exes. Mine is in
`checks/f59/raw.txt`. If the hashes differ, the disagreement is build provenance and not a finding about the
engine; if they are identical, then two runs of one binary disagreeing at depth 24 is a finding in its own
right and I would want to see their `nps` field — mine reads 4,059,235, and a large difference would suggest a
different machine load or a different binary.

## 5. What is NOT in dispute

**Both builds agree on the structural claim that matters**: at depth 24 the engine switches to `f6f5`, and at
depths 16 and 20 it does not. My 19-F58/19-F59 findings are about *that switch* — the bare king gives up
resistance until the search is deep enough to see the longer losing line — and **seat 27's run confirms the same
structure with different numbers** (`f6e5` → `f6e5` → `f6f5`). Their depth-24 move is `f6f5`, mine is `f6f5`. So
the calibration-case conclusion stands on both measurements; only the magnitudes differ.

**The one number that would change a finding is the depth-16/20 move** (`f6e7` for me, `f6e5` for them). If
theirs is right, my 19-F58 wording "plays `f6e7`" is wrong for their build — so **19-F58 should be read as
"plays a move that is not the longest defence", with the specific move named as `f6e7` on my build**. I have
amended it that way rather than leaving a move name that another build does not reproduce.

## 6. Amendment to 19-F58

> **19-F58 (amended).** In the mirror direction (bare king to move), 1 of 8 oracle-covered positions gives up
> resistance that was available: `6k1/8/5K2/8/6r1/8/8/8 w`. On **my** build (PC r15, g++ 13.3.0, patch sha256 as
> in `REPORT_pcbuild.md`) the engine plays `f6e7` at depths 16 and 20 and switches to `f6f5` at depth 24. **Seat
> 27's independent measurement on its build gives `f6e5` at 16/20 and `f6f5` at depth 24** — the same structure,
> different numbers. The defect is **"not the longest defence until the search is deep enough"**, not the
> specific move; the move name is build-specific.

## 7. Files

`checks/f59/raw.txt` — the exe path, its sha256, the settings list, and every raw `info` and `bestmove` line for
both FENs at depths 16/20/24.
