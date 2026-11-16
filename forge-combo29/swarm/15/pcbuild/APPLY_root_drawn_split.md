# APPLY SHEET — the `root_drawn` conflation in the PC build (`FORGE_FIX_ROOT_DRAWN`)

**One page, act on this.** Seat 15, area 5. Every number below is a pasted engine output from a
committed script, **Threads 1**, Hash 16, one fresh process per case, `-DFORGE_MATE_ALPHA_GUARD=1`.
Honesty pins in the default option regime. No match was run (see §6).

---

## 1. The problem: one flag controls two unrelated repairs

The PC build's shipped state is `FORGE_FIX_ROOT_DRAWN=1`, which reduces the root-draw test to:

```cpp
const bool root_drawn = !legal.empty() && board.is_insufficient_material();
```

That single line does two jobs at once — it removes the `halfmove_clock() >= 100` clause (which is
what repairs a missed mate at counter 100) **and** it removes `board.is_repetition()` (which is what
adjudicates a thrice-repeated position as drawn). The two are independent, but the flag ties them.

Measured, both flag states, Threads 1, PC20 (`fix0_test.txt`, `thread_PC20.txt`, `repcount2_all.txt`):

| | **flag ON** (shipped) | **flag OFF** |
|---|---|---|
| thrice-repeated root | `cp 23`, **13,424 nodes**, `d2d4` — **searched** | `cp 0`, **0 nodes**, `a2a3` — drawn |
| twice-repeated root | searched | searched |
| mate in 1, halfmove 99 | `mate 1`, 144 nodes | `mate 1`, 144 nodes |
| **mate in 1, halfmove 100** | `mate 1`, 144 nodes ✓ | `cp 0`, **0 nodes**, `a1b1` ✗ **mate lost** |
| **pawn-move mate, halfmove 100** | `mate 1`, 265 nodes ✓ | `cp 0`, **0 nodes** ✗ **mate lost** |
| checkmated / stalemated root | `mate 0` / `cp 0`, `0000` | same |

**Neither setting is right.** ON loses the repetition adjudication; OFF loses the halfmove-100 mate.

## 2. The change (one line, `src/search.cpp`)

```diff
-    const bool root_drawn = !legal.empty() && board.is_insufficient_material();
+    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.is_insufficient_material());
```

Patch file: **`instr/root_rep_split_fix.patch.txt`** — unified diff, relative `a/` `b/` paths, one
hunk, `src/search.cpp` only. Applies to a clean PC tree with

```
cd <pc tree> && patch -p1 < root_rep_split_fix.patch.txt        # verified: --fuzz=0 dry run clean
```

Build as usual plus the PC's flag:
`cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`

Note `halfmove_clock() >= 100` stays **out** of the condition — that clause was the cause of the
missed mate, and it must remain out.

## 3. The five case outputs with the split applied

`split_fix_test.txt`, build `~/builds/split/forge`, Threads 1, PC20:

| case | result |
|---|---|
| thrice-repeated root | `cp 0`, **0 nodes**, `a2a3` — **declared drawn** |
| twice-repeated root (control) | `cp 26`-class, searched — correct, 2 is not a draw |
| mate in 1 at halfmove 99 (control) | `mate 1`, 144 nodes, `a1a8` |
| **mate in 1 at halfmove 100** | `mate 1`, **144 nodes**, `a1a8` — **found** |
| **pawn-move mate at halfmove 100** | `mate 1`, **265 nodes**, `a7a8q` — **found** |
| same board as plain FEN (control) | searched — the draw really was the repetition |

Every row correct, and no row that was correct before became wrong.

## 4. The four honesty pins — unchanged

Default option regime, no `setoption` sent (`honesty_instrumented.txt`, `honesty.meta` style):

| bench 11 | bench 13 | bench 16 | go perft 5 |
|---|---|---|---|
| **312866** | **862329** | **3024920** | **4865609** |

All four exact with the split applied. (Pins are default-regime numbers; applying S14 first moves
three of them — that is a separate known fact, see 15-C3 / 10-F6.)

## 5. What a GUI gets: a real move, not `0000`

`draw_bestmove_all.txt`, all three builds, Threads 1, six cases each — **18 of 18 cells correct**:

| case | legal moves | bestmove | correct? |
|---|---|---|---|
| thrice-repeated root (**split**) | 20 | **`a2a3`** (a real move) | yes |
| twice-repeated root | 20 | `d2d4` | yes |
| plain startpos | 20 | `d2d4` | yes |
| **checkmated root** | 0 | **`0000`** | yes — no move to give |
| **stalemated root** | 0 | **`0000`** | yes — no move to give |
| insufficient material | 8 | `e3d2` (a real move) | yes |

So the split does **not** break the GUI contract: a position adjudicated drawn still returns a real
move, so the game can continue if the opponent does not claim the draw. `0000` appears only where
there is genuinely no legal move. The same is true on the base tree and on the shipped PC build, so
this was never at risk — but it is now measured rather than assumed.

## 6. What this sheet does NOT claim

- **No match was run.** I did not play games with the split build, so I cannot say it costs nothing in
  strength. The change is a root-only condition and the plausible cost is nil, but nil-by-plausibility
  is not a measurement. **Anyone applying this should run their own match before trusting it in play.**
- **The drawn-root policy is the owner's choice.** Whether a thrice-repeated root *should* be
  adjudicated drawn by the engine — rather than played on for a GUI or arbiter to settle — is a
  decision about how he wants the engine to behave, not a defect. The split exists so that decision is
  his: it makes the two behaviours independent, and either can be taken by editing this one line.
- I did not test repetition counts above four, or a root that is simultaneously halfmove-100 and
  thrice-repeated.
- The instrumentation that established all this is a separate, experiment-only patch
  (`instr/root_rep_instrument.patch.txt`) and should **not** be applied to anything that plays.

## 7. Evidence index

| file | what it is |
|---|---|
| `repcount2_all.txt` | occurrence counts 1-4, both builds, with nodes |
| `fix0_test.txt` | the `FORGE_FIX_ROOT_DRAWN=0` build on repetition and the fifty-move cases |
| `split_fix_test.txt` | the split build on the same cases |
| `draw_bestmove_all.txt` | the six GUI cases on three builds |
| `honesty_instrumented.txt` | pins with instrumentation and with the split |
| `root_instr_pc.txt`, `root_instr_base.txt` | the instrumented root lines that found the conflation |
| `RESULT_root_repetition_instrumented.md` | the full write-up behind this sheet |
