# The engine cannot reliably win won endings — and the cause is the fifty-move counter, not the bare-minor inversion

**Short version.** Asked whether the engine can convert won endings, the answer is **no, not
reliably, and the failure is in the simplest endings of all**: **KRK converts 10 of 20**
positions at `go depth 12`, **KQK 18 of 20**, **KBNK 3 of 20**, and **KPK 167 of 192 won
cells** at `go nodes 12000`. Every failure I could attribute has the **same** mechanism: a
draw score at the root once the half-move clock passes ~90, with **zero** drawn-root bails.
The bare-minor inversion (§9b) is real but is **not** what loses these games — it is what
makes the engine shuffle a bare minor for 100 plies at ~100 bails per game.

The harness is validated by a control that must convert and does: **an exact-table oracle
playing the winning side converts 20/20 in KQK, 20/20 in KRK and 192/192 won KPK cells.**

Build `6b98f217`, `-DFORGE_MARCH=x86-64-v4`, g++ 13.3.0, four pins matched (below). One net:
the **built-in** net. Item 5 could not be done — see §8.

---

## 1. Results, with denominators

All rows: build `6b98f217`, Threads 1, Hash 16, `OwnBook false`, `MultiPV 1`, built-in net,
winning side to move. `oracle` = exact-table attacker, engine defends (**control: must be
100%**). `engine` = both sides engine.

| family | arm | budget | converted | moves to mate min / med / max | bails | ended by fifty-move |
|---|---|---|---|---|---|---|
| KQK | engine | depth 12 | **18 / 20** | 1 / 6 / 50 | 0 | 2 |
| KQK | engine | nodes 12000 | **19 / 20** | 1 / 17 / 41 | 0 | 1 |
| KQK | oracle | depth 12 | 20 / 20 | 1 / 5 / 9 | 0 | 0 |
| KQK | oracle | nodes 12000 | 20 / 20 | 1 / 5 / 9 | 0 | 0 |
| KRK | engine | depth 12 | **10 / 20** | 1 / 8 / 19 | 0 | 10 |
| KRK | engine | nodes 12000 | **8 / 20** | 1 / 7 / 37 | 100 | 12 |
| KRK | oracle | depth 12 | 20 / 20 | 1 / 9 / 13 | 0 | 0 |
| KRK | oracle | nodes 12000 | 20 / 20 | 1 / 9 / 11 | 0 | 0 |
| KBNK | engine | depth 12 | **3 / 20** | 16 / 19 / 41 | 100 | 17 |
| KBNK | engine | nodes 12000 | **3 / 20** | 14 / 18 / 40 | 0 | 17 |
| KBNK | oracle | — | **not run** (no table) | — | — | — |
| KBK | engine | depth 12 | 0 / 20 (draw is correct) | — | **2,152** | 20 |
| KNK | engine | depth 12 | 0 / 20 (draw is correct) | — | **2,064** | 20 |

KPK, over a **stratified sample of 384 of the 81,664 canonical cells** (192 won / 192 drawn;
stratified on pawn file × pawn half × exact-table verdict). The 192 won cells are the item-2
denominator:

| KPK arm | budget | won cells converted | drawn cells held | failures |
|---|---|---|---|---|
| engine | `go nodes 12000` | **167 / 192 (87.0%)** | 172 / 192 (89.6%) | 25 won-cell, 20 drawn-cell |
| engine | `go depth 12` | **142 / 192 (74.0%)** | 168 / 192 (87.5%) | 50 won-cell, 24 drawn-cell |
| oracle | `go nodes 12000` | 192 / 192 | 189 / 192 | 0 won-cell |
| oracle | `go depth 12` | 192 / 192 | 185 / 192 | 0 won-cell |

**Every one of the 25 KPK won-cell failures at `go nodes 12000` ended in
`fifty_move_claim` with 0 bails.** Same for both KQK failures and all 10 KRK failures at
depth 12. **Zero** of the failures I attribute were caused by the drawn-root bail.

The oracle's drawn-cell failures (7 and 3) run the other way and are **the engine losing
draws while defending**: the oracle attacks, the engine defends, and the engine walks into a
mate. Those are real, and are counted separately from the conversion rate.

## 2. The failure with the full move list

**KQK, mate in 8 by the exact table, drawn after 100 plies.** Cleanest case: a three-piece
board, no capture available, and the whole ending inside the search.

`8/8/8/8/8/8/6k1/KQ6 w - - 0 1` — exact DTM 15 plies (8 moves). Engine: draw by fifty-move
rule, **0 bails**, 100 plies.

```
Qb8 Kh3 Qh8+ Kg2 Ka2 Kg3 Qh1 Kf4 Qh2+ Kg4 Kb2 Kf5 Qh4 Ke6 Ka3 Kf7 Qd8 Kg6
Qd6+ Kg5 Qh2 Kf6 Qh4+ Ke6 Qd8 Kf5 Qh8 Kg5 Qg8+ Kf5 Qg3 Kf6 Qf4+ Kg7 Qb8 Kg6
Qf8 Kg5 Qf2 Kg6 Qh4 Kf5 Qh3+ Kf6 Qc3+ Kg5 Qg3+ Kf6 Qf4+ Kg7 Qd4+ Kg6 Qd3+ Kf6
Qd8+ Kg6 Qh4 Kf5 Qh8 Kg6 Qg8+ Kf5 Qg1 Kf6 Qd4+ Ke6 Qd8 Kf5 Qh4 Kg6 Qh3 Kg5
Qe3+ Kg6 Qd3+ Kf6 Qc3+ Kg5 Qc1+ Kg6 Qg1+ Kf5 Qf2+ Kg4 Kb3 Kg5 Qg3+ Kf6 Qe1 Kg6
Qe6+ Kg7 Qe7+ Kg8 Qd8+ Kf7 Qh4 Ke6 Ka3 Kd7
```

**The oracle on the identical FEN mates in 13 plies:**
`Kb2 Kh2 Qg6 Kh1 Kc1 Kh2 Kd1 Kh1 Ke1 Kh2 Kf2 Kh3 Qg3#`.

**The score was not wrong on the way — it was right and then *damped*.** First-ply score
`cp 1078`, correct; it holds near `cp 1100` through ply 84, then:

| ply | halfmove | score | nodes |
|---|---|---|---|
| 80 | 80 | cp 1071 | 18,250,904 |
| 84 | 84 | cp 1052 | 38,169,094 |
| 86 | 86 | cp 1048 | **324,177,920** |
| 94 | 94 | cp 1016 | 1,759 |
| 95 | 95 | **cp 0** | 3,158 |
| 96 | 96 | **cp 0** | 23,419 |

From a correct +1052 to a hard `cp 0` in eleven plies, with the node count exploding to
3.2×10⁸ on the way. The engine did not "fail to see" the win; it **decided the position was
drawn** and then shuffled correctly — for a drawn position.

## 3. The mechanism, isolated

Same board, same build, same depth, **only the half-move clock differs**. KQK
`8/8/8/8/8/2k5/8/KQ6 w - - {hm} 1`, `go depth 12`:

| hm | 0 | 20 | 40 | 60 | 70 | **80** | **85** | **90** | **95** | **99** |
|---|---|---|---|---|---|---|---|---|---|---|
| score | cp 1220 | mate 10 | mate 10 | mate 10 | mate 10 | mate 6 | mate 6 | **cp 0** | cp 0 | cp 0 |
| nodes | 93,585 | 5,253 | 695 | 601 | 612 | 520,100 | 110,412 | **116,428,190** | 144,371 | 264 |

**The band is [90, 100] and the score there is exactly `cp 0`** — not "small", the same value
a real draw returns, which is why the engine cannot tell a won position from a drawn one at
that clock. Node counts grow ~10³ approaching the band: a three-piece board needs 116 million
nodes to answer a question it answered in 612.

This is the **leaf draw rule** the brief names (`H > 100 − p`): from ply `p`, a line reaching
halfmove 100 scores 0, and at depth 12 from clock 90 the best line reaches it. The behaviour
fits that rule exactly and the band is where the rule predicts, but I did **not** instrument
the leaf, so this is "consistent with the documented rule", not "proved".

KRK behaves identically (same family at clock 90 → `cp 0`, 9.6M nodes against ~900 at clock
70). KPK's 25 failures are all fifty-move claims at 0 bails — the same signature.

## 4. The drawn-root bail is NOT what loses these games — measured, not argued

This contradicts the natural hypothesis and is the most useful negative here.

- **All 37 attributed conversion failures (2 KQK + 10 KRK + 25 KPK) have `n_bails = 0`.**
  The bail never fired in one of them.
- The bail *does* fire heavily, but in the **bare-minor** games: **2,152 bails across 20 KBK
  games**, **2,064 across 20 KNK games** (~100/game; reasons `repetition` 1757 + `material`
  395 in the KBK arm). There it is the *mechanism of the draw*, not the cause of a lost win:
  a KBK game has nothing to convert, so a 0-node bail playing the generator's first move is
  invisible.
- The one place the bail and a real loss coincide is **KRK at `go nodes 12000`, 100 bails**.
  That game ran **200 plies**: the engine held the win for 100 plies, the clock reached 99 at
  ply 100, its score collapsed to `cp 0` (320 nodes), it played `Kxh3` — **giving up the
  rook** — and the remainder is K vs K with the bail firing every ply. The §2 clock defect
  *created* the material bail, not the reverse.

**The fifty-move interaction is real and dominant, but it is a score defect, not a bail
defect.** A repair aimed only at the drawn-root bail would not fix one of these 37 failures.

## 5. The bare-minor inversion at game level: what it actually costs

The static finding is confirmed and the game-level cost is now measured — and it is
**smaller than the static number suggests**, because the defect cannot lose a game that was
already drawn.

- **As the defender (engine must hold KBK/KNK): 20/20 held, both families.** The −147/−144
  score never costs a draw, because `is_insufficient_material()` short-circuits the root and
  the engine plays the generator's first move. **This is a null, and it is a null for a reason
  that makes the static finding's severity smaller than it reads.**
- **As the side with the extra piece: it cannot win, correctly, and the cost is the bail
  storm** — 2,152 / 2,064 bails per 20 games, ~100/game, and 100+ plies of `Bb2`/`Ba1`.
- **KNN vs K I did not test.** §9b is right that the verdict is not a bug; I am recording
  that I left it out rather than reporting a number I did not take.

**KBNK is where the inversion plausibly bites, and it converts 3/20.** KBNK is a *generic*
win (33 moves maximum) with **zero** material-bail protection — the engine must actually find
the bishop+knight mate. 17 of 20 ended in a fifty-move claim. **But I cannot attribute KBNK's
failures to the inversion**: I did not build a KBNK table (4-piece retrograde was too
expensive in the window), so there is no exact DTM per position and no oracle arm. The KBNK
row is a **measurement without a mechanism**, flagged rather than explained by borrowing the
KQK story.

## 6. Is it a horizon effect? Yes for KQK — and the horizon needed is absurd

Depth ladder on the **exact KQK FENs that failed at depth 12** (same position, four depths):

| depth | `8/8/8/8/8/8/6k1/KQ6` (DTM 8 moves) | `8/8/8/8/8/8/7k/KQ6` |
|---|---|---|
| 8 | drawn, fifty-move | drawn, fifty-move |
| 12 | **drawn, fifty-move** | **drawn, fifty-move** |
| 16 | converted, 34 moves | converted, 11 moves |
| 20 | converted, 21 moves | converted, 10 moves |

So it **is** horizon-dependent — and at depth 16 a **mate in 8** converts in 34 moves. The
engine needs roughly **4× the depth of the mate itself** to convert a KQK win. That is not a
search one ply short; it is win-detection that has to outrun a draw-scoring rule firing 10
plies before the horizon.

## 7. Pins, controls, and what makes the numbers trustworthy

**Four honesty pins, all matched at `6b98f217`** (`bench N` sent on stdin; `bench` prints one
`info string bench depth ...` line and never a line starting `nodes`, so a reader waiting for
`nodes` hangs — it did, twice):

| pin | want | got |
|---|---|---|
| `bench 11` | 312,866 | **312,866** |
| `bench 13` | 862,329 | **862,329** |
| `bench 16` | 3,024,920 | **3,024,920** |
| `go perft 5` | 4,865,609 | **4,865,609** |

**The oracle arm is the control that makes "the engine failed" mean something.** Without it,
"this ending did not convert" and "this ending was not winnable against this defence" are one
observation. It converts **20/20 KQK, 20/20 KRK, 192/192 won KPK cells** — so every start
position is genuinely won and every engine failure is the attacking side's.

**The oracle control was itself broken, and only the 192/192 requirement caught it.** The
first version scored a promotion — which leaves the KPK table — as an "unknown" child, ranked
unknown as bad, and so **refused to promote**, shuffling a pawn on a7 for 100 plies. It
"failed" 178 of 192 won cells. A plausible-looking number that was a harness bug, found only
because the control had a value it had to hit.

**The KBK/KNK arms were vacuous and are now not.** The first fixture set decanonicalised
whatever key it reached, so half the positions had the *bare king* to move; python-chess
adjudicates those as over at once, and **all 40 games ended at ply 0** while looking like a
clean 20/20 draw. `board.is_game_over()` also returns True for every KBK/KNK position even
with a move available, so it cannot be the loop's stop condition. The condition is now "no
legal move", and the arms run 100+ plies.

**The bail predicate is validated against the binary, and the validator can fail**
(`scripts/oracle.py`, 8 cases × 3 arms):
- real predicate: **PASS** on all 8 (clock 98/99 search, 100 bails; KBK/KNK bail on material;
  KQK searches; twofold searches, threefold bails).
- planted fault `halfmove >= 99`: **detected** (disagrees on clock 99).
- planted fault `is_repetition(2)`: **detected** (disagrees on a twofold history).

**Fixture provenance.** KQK/KRK start positions come from the **exact retrograde tables**
(stratified across DTM buckets), not a hand-written list. The tables are checked against four
independent classical values: KQK max DTM **10 moves**, KRK **16**, KPK **28**, and KBK/KNK
**zero wins anywhere**. All four match.

**Protocol.** No `quit` into a live search. Every search is read to `bestmove`; a runaway
search gets UCI `stop` from a watchdog, never `quit`, and is counted as a timeout.

## 8. What I could not test, and why

- **The v3 test net (item 5).** The built-in net was used on **every** row above. The v3 path
  is compiled out of this build (`FORGE_NNUE_V3` defaults to 0 and the CMake recipe does not
  set it), and no `FORGENN3` net file exists anywhere in the repository — the only writer
  named in the format doc (`tools/nnue/fable_nnue_v3.py`) is not in the tree. **Item 5 is not
  done, and no row here is a second-net row.** I did not synthesise a net to test a net.
- **KBNK mechanism.** 3/20 measured, but with no exact table and no oracle arm. It is the
  family where the bare-minor inversion would most plausibly matter and the one I can least
  explain.
- **The full KPK boundary.** 384 of 81,664 canonical cells (0.47%), stratified. The
  denominator is stated everywhere rather than implied.
- **Attribution of the clock collapse to the leaf draw rule.** The behaviour is what
  `H > 100 − p` predicts and the band is [90,100] as predicted, but I did not instrument the
  leaf. "Consistent with" is the strongest claim I make.
- **KNN vs K.** Not tested; §9b's FIDE-agreement result is not contradicted here.
- Four parallel workers on 4 cores: node counts come from each row's own `info nodes` and are
  unaffected by co-scheduling; wall-clock seconds are not comparable across cells.

## 9. The one-line answer for the owner

**If a won ending must be converted reliably, do not ship this build.** KRK — the ending every
engine converts — converts **half the time** at depth 12, and the cause is a root score of
exactly `cp 0` once the half-move clock passes 90: not the drawn-root bail (0 bails in all 37
attributed failures) and not the bare-minor inversion (20/20 draws held when defending). The
cheapest high-value repair is the clock band [90,100], where a three-piece won position costs
10⁸ nodes to misjudge. The drawn-root bail is a real defect but is **not** on the critical
path for conversion.
