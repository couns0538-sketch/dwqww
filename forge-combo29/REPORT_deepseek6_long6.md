# REPORT — deepseek6, long 6 (the root of internal iterative reduction)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** write `IirNoRoot.patch.txt` adding `!root_node &&` to the IIR reduction at `src/search.cpp:1784` behind an option `IirRootExclude`, predict, then measure (a) rows on O under S14 with 0 and 1, (b) `go depth 12 searchmoves <first two legal moves>` on the first 50 of O, both values, and (c) the same with MultiPV 2 and no searchmoves.

**Answer:** the patch is written and applies with zero fuzz (option `IirRootExclude`, 0/1, default 0 = today). **(a) is 200 of 200 equal, exactly as the brief expects — no finding.** **(b) and (c) are the opposite of inert: 48 of 50 rows differ in each, and the root restriction raises the node sum by 55.0 % (b) and 25.8 % (c).** The reason is visible in the code and is the same mechanism in both: with a restricted root the engine refuses to store a root TT entry at all, so `tt_move` stays none for every iteration and the IIR reduction fires at the root on EVERY iteration, not just the first.
**How sure:** certain of every number and every row count. The mechanism is a two-line code reading (`search.cpp:2093`, `search.cpp:2496-2497`) that I quote; it explains (a) and (b)/(c) with one cause, and I have marked the parts of it I did not measure.

## 2. The honesty numbers (build with the option at its default 0)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |

exe `/agent/repos/work/build-l6/forge`, sha256 `5baa14998255d3c322eb1586536dc367549da4542d68246a9dac43d4942269a7`
(`exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate`, and the binary itself advertises
`option name IirRootExclude type spin default 0 min 0 max 1` (`uci.txt`). Clean copy `/agent/repos/p9` at
6b98f2170a3210e71beed04bbd2553972c253ed7; patch applied with `patch -p1 --fuzz=0` (`patch_apply.txt`).

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| write the patch | done | `IirNoRoot.patch.txt` | 3 hunks, one file, `diff -u` against the clean source, headers `a/forge-combo29/src/search.cpp` / `b/...` |
| applies to a clean copy without fuzz | done | `patch_apply.txt` | `checking file forge-combo29/src/search.cpp` then a clean apply, exit 0 |
| build | done | `exe.sha256` | Release g++ 13.3.0, 0 errors, 0 warnings |
| honesty at the default | done | `honesty_*.txt` | all four met |
| option 0 is the base (identity) | done | `O_S14_iir0.rows` | **200 of 200 equal** to long 1's `O_S14.rows`, sum 9,500,069 |
| (a) rows on O/S14, 0 vs 1 | done | `O_S14_iir0.rows`, `O_S14_iir1.rows` | **200 of 200 equal**, both sums 9,500,069 — the brief's expectation met, no finding |
| (b) searchmoves, first 50 of O, 0 vs 1 | done | `O50_sm_iir0.rows`, `O50_sm_iir1.rows` | **48 of 50 rows differ**; sums 1,214,081 vs 1,882,221 (+55.0 %) |
| (b) last info-line depth, 0 vs 1 | done | `O50_sm_depth_iir0.rows`, `O50_sm_depth_iir1.rows` | **12 in all 100 rows**, identical row by row |
| (c) MultiPV 2, no searchmoves, 0 vs 1 | done | `O50_mpv2_iir0.rows`, `O50_mpv2_iir1.rows` | **48 of 50 rows differ**; sums 3,893,160 vs 4,896,958 (+25.8 %) |
| which positions differ in (b) | done | `(b)_diff_rows.txt` in this folder's report tables | all 50 listed with fen, both node counts, both bestmoves |

## 4. Findings

### 4.1 The patch is an identity at 0 and applies exactly as long 6 asks

```
cd /agent/repos/p9 && patch -p1 --fuzz=0 --dry-run < IirNoRoot.patch.txt
checking file forge-combo29/src/search.cpp          (exit 0)
python3 cmprows.py O_S14_iir0.rows ../../../tests_deepseek6_long1/O_S14.rows   -> 200 of 200 equal
```
The diff adds `int IirRootExclude = 0;`, its parameter row `{..., 0, 1}`, and makes line 1784
`... && !(tune::IirRootExclude && root_node)) --depth;`. At 0 the extra conjunct is false, so the
condition is the original text.

### 4.2 (a) is EQUAL — the root has a hash move from the second iteration on, as the brief predicts

```
python3 cmprows.py O_S14_iir0.rows O_S14_iir1.rows
200 of 200 equal        (both sums 9500069)
```
This is the predicted outcome and I record it as a met expectation, not as a null result. It is also the
evidence that the option really is a no-op when the root behaves normally: at a normal root the search
stores its own TT entry at the end of each iteration (`search.cpp:2095`), so iteration n+1 sees
`tt_move != none` and the reduction is skipped by the `tt_move.is_none()` term regardless of the new
conjunct. My filed prediction was "200 of 200 equal" and that is what came back.

### 4.3 (b) and (c) are NOT inert, and one mechanism explains both

```
python3 sumrows.py O50_sm_iir0.rows      -> rows 50 sum 1214081
python3 sumrows.py O50_sm_iir1.rows      -> rows 50 sum 1882221   (+55.0 %)
python3 rowdiff.py O50_sm_iir0.rows O50_sm_iir1.rows --show 5
row 1: A 26204/a2a3  B 27925/b2b3
row 2: A 20758/a7a6  B 40095/a7a6
row 3: A 17205/a2a3  B 18627/a2a3
row 4: A 39909/a7a6  B 54720/a7a6
row 5: A 20140/a2a3  B 52450/b2b3
48 of 50 rows differ (48 nodes, 5 bestmove, 5 both)

python3 sumrows.py O50_mpv2_iir0.rows    -> rows 50 sum 3893160
python3 sumrows.py O50_mpv2_iir1.rows    -> rows 50 sum 4896958   (+25.8 %)
48 of 50 rows differ (48 nodes, 13 bestmove, 13 both)
```

**The mechanism, read from the code, not guessed:**

1. At `search.cpp:2093` the root **does not store a TT entry at all** when the root is restricted:
   `if (excluded.is_none() && !(root_node && root_restricted_)) { store_tt(...); }`
2. With `searchmoves`, `root_restricted_` is true (`search.cpp:2160`:
   `root_restricted_ = limits.search_moves_specified;`), so the root's `tt_move` is none on **every**
   iteration, not only the first. The `tt_move.is_none()` half of the IIR condition is therefore true
   at the root on all 12 iterations, and `IirRootExclude=1` removes a one-ply reduction from every one of
   them. That is why the tree grows by half.
3. MultiPV reaches the same state by a different road: the 2nd and later PV lines run as nested searches
   with `narrowed.search_moves_specified = true` (`search.cpp:2496-2497`), i.e. they are restricted roots
   too. So (c) inherits exactly the same "root never stores an entry, root always reduced" state.

**This is the finding long 6 was written to look for.** The brief's hypothesis was that the reduction at
the root is mostly harmless because the root has a hash move from the second iteration on. That is TRUE for
an unrestricted root (4.2, 200 of 200 equal) and FALSE for exactly the two configurations where the engine
suppresses the root's TT store: `searchmoves` and MultiPV above 1. In those two, every position I measured
changes and the tree grows by a quarter to a half.

### 4.4 The last info-line depth is 12 in every row of (b), both values

```
depth histogram, iir0: {12: 50}      iir0 vs iir1 on (index, depth): identical, diff exit 0
depth histogram, iir1: {12: 50}
```
So the effect in (b) is entirely inside the tree at a fixed depth: the iteration count and the final depth
do not change, only how much work each iteration does. That matches a root that is reduced on every
iteration in one run and on none in the other.

### 4.5 Which positions differ in (b) — all of them but two

Full table with fens and both node counts is the block below; the two unchanged positions are #0 and #31.
The complete list is in this report because the brief says to name each differing position rather than
count them.

| row | iir0 nodes/best | iir1 nodes/best | fen |
|---|---|---|---|
| 1 | 26204 a2a3 | 27925 b2b3 | `rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4` |
| 2 | 20758 a7a6 | 40095 a7a6 | `rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3` |
| 3 | 17205 a2a3 | 18627 a2a3 | `r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8` |
| 4 | 39909 a7a6 | 54720 a7a6 | `rnbqkbnr/ppp2ppp/4P3/8/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 3` |
| 5 | 20140 a2a3 | 52450 b2b3 | `rn1qkbnr/ppp2ppp/4b3/8/8/8/PPPP1PPP/RNBQKBNR w KQkq - 0 4` |
| 6 | 16718 b2b3 | 28103 b2b3 | `rn1qkb1r/ppp2ppp/4bn2/8/8/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 5` |
| 7 | 29520 a2a3 | 56454 a2a3 | `r1bqkbnr/ppp1pppp/3p4/3Pn3/4P3/8/PPP2PPP/RNBQKBNR w KQkq - 1 4` |
| 8 | 31510 a2a3 | 24584 a2a3 | `rnbqkbnr/p1pp1ppp/1p2p3/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3` |
| 9 | 14051 a7a6 | 21607 a7a6 | `r1bqk1nr/pppp1pp1/2n4p/2b5/2BPP3/5N2/PP3PPP/RNBQK2R b KQkq - 0 6` |
| 10 | 28344 a2a3 | 59707 a2a3 | `rnbqkbnr/ppp2ppp/8/3Pp3/8/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 3` |
| 11 | 27462 a2a3 | 40978 a2a3 | `rn2kbnr/ppp1pppp/8/q7/6b1/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 5` |
| 12 | 19974 a2a3 | 29378 a2a3 | `r1b1kbnr/ppppqppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4` |
| 13 | 20370 a2a3 | 25849 a2a3 | `rn1qkb1r/pbpppppp/1p3n2/8/3PP3/3B4/PPP2PPP/RNBQK1NR w KQkq - 3 4` |
| 14 | 13879 a2a3 | 31541 a2a3 | `rnbqkbnr/p1pppppp/8/1p6/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2` |
| 15 | 31504 a7a6 | 62829 a7a6 | `rnbqkbnr/p2p1ppp/4p3/2pP4/2B1P3/8/PP3PPP/RNBQK1NR b KQkq - 0 5` |
| 16 | 27729 b7b6 | 42930 a7a6 | `r1bqkb1r/pppp1ppp/2n2n2/4P3/4P3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 4` |
| 17 | 18172 a2a3 | 26140 a2a3 | `rnbqk1nr/p1ppppbp/1p4p1/8/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 4` |
| 18 | 13156 a7a6 | 23071 a7a6 | `rnbqkbnr/pp3ppp/3p4/2pPp3/2P5/2N5/PP2PPPP/R1BQKBNR b KQkq - 1 4` |
| 19 | 13632 a2a3 | 24379 a2a3 | `rnbqkbnr/ppp3pp/4p3/3p1p2/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 4` |
| 20 | 55356 a2a3 | 70527 a2a3 | `r1bqk2r/ppppbppp/5n2/6B1/3QP3/8/PPP2PPP/RN2KB1R w KQkq - 3 7` |
| 21 | 31445 a7a6 | 40703 a7a6 | `rnbqkb1r/ppp2ppp/4Pn2/8/8/2N5/PPPP1PPP/R1BQKBNR b KQkq - 0 4` |
| 22 | 20786 a2a3 | 47883 a2a3 | `r2qkbnr/ppp3pp/2p5/4Nb2/4p3/8/PPPP1PPP/RNBQK2R w KQkq - 0 7` |
| 23 | 30591 b2b3 | 30107 b2b3 | `rn1qk1nr/pbppppbp/1p4p1/8/3PP3/2NB4/PPP2PPP/R1BQK1NR w KQkq - 2 5` |
| 24 | 27461 b2b3 | 33761 b2b3 | `r1bqkb1r/pp1p1ppp/2n1pn2/2p3N1/2B1P3/8/PPPP1PPP/RNBQK2R w KQkq - 0 5` |
| 25 | 30765 d6d5 | 51834 d6d5 | `r1bqkbnr/p4ppp/2ppp3/2p5/4PP2/3P1N2/PPP3PP/RNBQK2R b KQkq - 0 6` |
| 26 | 25526 b6b5 | 32584 b6b5 | `rn1qk1nr/pbppppbp/1p4p1/8/2PPP3/2N2N2/PP3PPP/R1BQKB1R b KQkq - 4 5` |
| 27 | 29227 a2a3 | 33610 a2a3 | `rnb1kb1r/pppqpppp/5n2/8/3P4/2N5/PPP2PPP/R1BQKBNR w KQkq - 1 5` |
| 28 | 7054 a7a6 | 31725 a7a6 | `rnbqkbnr/ppp1pppp/8/3p4/8/4PQ2/PPPP1PPP/RNB1KBNR b KQkq - 1 2` |
| 29 | 12626 a7a6 | 19646 a7a6 | `r1bqkbnr/ppp1nppp/3p4/3Pp3/2P1P3/5N2/PP3PPP/RNBQKB1R b KQkq - 0 5` |
| 30 | 21658 a2a3 | 41063 b2b3 | `rn1qkb1r/ppp1pppp/5n2/3P4/6b1/2N5/PPPP1PPP/R1BQKBNR w KQkq - 3 4` |
| 32 | 16493 a7a6 | 33863 a7a6 | `r1bqkbnr/ppppn1pp/5p2/3Pp3/4P3/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 2 5` |
| 33 | 28128 c3c2 | 29710 c3c2 | `rnbqkbnr/pp1p1ppp/4p3/8/2B1P3/2p2N2/PP3PPP/RNBQK2R b KQkq - 1 5` |
| 34 | 15207 a7a6 | 46195 a7a6 | `rn1qkbnr/ppp2ppp/4b3/8/8/2N5/PPPP1PPP/R1BQKBNR b KQkq - 1 4` |
| 35 | 15970 a2a3 | 22580 a2a3 | `rnbqkb1r/1p3ppp/p3pn2/3p4/2PP4/2N2N2/PP3PPP/R1BQKB1R w KQkq - 0 7` |
| 36 | 15760 a7a6 | 28787 a7a6 | `r1bqkbnr/ppp1pppp/2n5/1B6/3P4/2N5/PPP2PPP/R1BQK1NR b KQkq - 4 5` |
| 37 | 24818 a2a3 | 41430 a2a3 | `r1bqkbnr/pp1ppp1p/2n3p1/8/3pP3/2P2N2/PP3PPP/RNBQKB1R w KQkq - 0 5` |
| 38 | 26536 a2a3 | 34656 a2a3 | `rnbqk2r/pp1p1ppp/4pn2/8/1b1PP3/2N5/PP3PPP/R1BQKBNR w KQkq - 3 6` |
| 39 | 41898 a7a6 | 49415 a7a6 | `rnbqk2r/pp1p1ppp/4pn2/8/1b1PP3/2NB4/PP3PPP/R1BQK1NR b KQkq - 4 6` |
| 40 | 24451 b6b5 | 40631 b6b5 | `rn1qk1nr/pbp2pbp/1p1pp1p1/8/2PPP3/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 1 7` |
| 41 | 30392 a2a3 | 36669 a2a3 | `r1bqkbnr/pppp2pp/2n2p2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4` |
| 42 | 39939 b2b3 | 28742 a2a3 | `rnbqk1nr/pppp1ppp/1b2p3/8/3PP3/5N2/PPP2PPP/RNBQKB1R w KQkq - 1 4` |
| 43 | 17800 a2a3 | 27074 a2a3 | `rnbqk2r/ppp1npbp/3pp1p1/8/2PPP3/2N2N2/PP3PPP/R1BQKB1R w KQkq - 2 6` |
| 44 | 17225 a7a6 | 40113 a7a6 | `rnbqkb1r/pppppppp/5n2/8/3P4/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 0 4` |
| 45 | 15613 a6a5 | 34135 a6a5 | `r1bqk2r/1pp2ppp/p1p2n2/4N3/1b2P3/2NP4/PPP2PPP/R1BQK2R b KQkq - 0 7` |
| 46 | 20629 a7a6 | 47488 a7a6 | `r1bqkbnr/ppp2ppp/2n5/3pP3/5B2/4P3/PPP2PPP/RN1QKBNR b KQkq - 0 4` |
| 47 | 16185 a2a3 | 39510 a2a3 | `rnbqkbnr/ppp1ppp1/3p3p/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3` |
| 48 | 38062 a2a3 | 63328 a2a3 | `rn1qkbnr/pp2pppp/6b1/3p4/3P2P1/5N1P/PPP2P2/RNBQKB1R w KQkq - 1 7` |
| 49 | 26980 a2a3 | 53822 a2a3 | `r1bqkbnr/ppp1pppp/8/3Pn3/2p5/2N5/PP2PPPP/R1BQKBNR w KQkq - 1 5` |

Unchanged: row 0 (`rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4`, 29154 both) and row 31
(`rnbqk1nr/pp3ppp/4p3/3pP3/1b1P4/8/PP3PPP/RNBQKBNR w KQkq - 1 6`, 30109 both). Five positions also change
their chosen move, not just their node count (rows 1, 5, 16, 30, 42), which says the extra depth at the
root is changing the best move in 1 position in 10 under a restricted root.

### 4.6 My predictions, scored

| I predicted | what happened | verdict |
|---|---|---|
| (a) 200 of 200 equal | 200 of 200 equal | **hit** |
| (b) at least one position differs | 48 of 50 differ | **hit** |
| (b) option-1 sum larger | larger by 55.0 % | **hit** |
| (b) final depth 12 in every finished row | 12 in all 100 rows | **hit** |
| (c) at least one position differs | 48 of 50 differ | **hit** |
| (c) sums differ | +25.8 % | **hit** |

Six for six. I say so because the previous reports had misses; this one did not, and the reason is that the
numbers I predicted were structural (equal / differs) rather than sizes.

### Suspicions, not proven

- **That the root is reduced on all 12 iterations** in (b) and (c). I infer it from `tt_move.is_none()`
  being true on every iteration (no root TT store at 2093) but I did not instrument the reduction count.
  The consistent +25…55 % growth is what that inference predicts; a counter would settle it.
- Whether the same happens with an EMPTY `root_candidates` or a one-move restriction. Not tested.
- Whether `IirRootExclude=1` is better or worse for strength under `searchmoves`/MultiPV. This report is a
  tree measurement only. A node sum under a restricted root is not a strength verdict.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): no entry on IIR or on the root; its job-9 note is about NodeLiterals.
  Nothing here came from it.
- **glmflash5** (`NOTES_glmflash5.md`): its job-16 note reports that S14 shrinks its base tree 12573318 ->
  9500069 (−24 %) — the same two numbers as my O/none and O/S14 rows, so its tree and mine agree at that
  layer. It says nothing about IIR.
- **deepseek5** (`NOTES_deepseek5.md`): its job-30 note is the counters lesson ("read the state variable at
  the moment the event happens"). That is exactly the discipline 4.3's mechanism needs and the reason I
  quote the store condition at 2093 rather than assuming a root TT entry exists.
- No note is an order and no number above came from a note.

## 6. What I did NOT do

- I did not instrument the IIR reduction counter, so 4.5's "reduced on every iteration" is a code reading,
  not a count.
- I did not run (b)/(c) on G, or at another depth.
- I did not test `searchmoves` with a single move, or MultiPV 3 or more.
- I did not measure strength and I make no claim about which setting is better.
- I did not commit engine source; the patch is committed as text.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether the brief's "(a) expectation is EQUAL" was meant to be the only expected outcome, with (b)/(c)
  as probes for a difference. If so, my (b)/(c) results are the intended finding and I have the first
  report of it.
- The exact share of the +55 % in (b) that comes from the extra root ply versus from the changed move
  ordering the deeper root produces. The five bestmove changes say ordering matters, but I have not
  separated the two.

## 8. A better way

The whole of long 6 turns on one line of the base engine that neither the brief nor kimi5's notes mention:
**a restricted root does not store a TT entry** (`search.cpp:2093`). Any future "does X matter at the root"
test should read that line FIRST and split its runs into "unrestricted root" and "restricted root" from the
start, because the two are different experiments — (a) and (b) are, in effect, two different engines at the
root. My harness now takes `--searchmoves-from` per row, so this split costs nothing to repeat.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`ls` + `git status --short` before this commit: `precommit_evidence.txt`. Harnesses in this folder:
`rows.py` (now with `--searchmoves-from`), `lastdepth.py`, `firstmoves.py`, `sumrows.py`, `cmprows.py`,
`rowdiff.py`.
