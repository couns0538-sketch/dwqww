# Drawn-root bail — measured exposure on the population that reaches it

Audit of the drawn-root bail in `forge-combo29` at base commit `6b98f217`.

**The report's exposure figure is a null from a corpus that cannot reach the condition. The
real rate is not zero and not rare: it fires once per ~114 plies of engine self-play, in
47% of games.** The report's own rule — *a null from a corpus that cannot reach the code is
vacuous* — applies to it, and this seat applies it.

---

## 0. The claim under audit, and what replaces it

`docs/forge-findings.md` §2 says:

> **0 threefolds in 600 random games of 60/120/200 plies, and 0 in 4,000 further 160-ply
> seeds.** So **a harness sampling random positions is essentially never affected. A harness
> REPLAYING REAL GAMES to a threefold is affected** ... The FEN-vs-move-list trap is not a
> general hazard; it is specific to game replay, and it is silent when it hits.

Measured replacement:

| question | report | this audit |
|---|---|---|
| how often does the guard fire | 0 in 4,600 random games → "essentially never" | **8.78 per 1,000 plies; 47.1% of games** reach ≥ 1 firing |
| who is exposed | game replay only | **any consumer of engine-played games**, including self-play harnesses and tools that analyse engine games |
| cost of the bad move | median 600–1,000 cp on 12 constructed fixtures | **41 of 2,251 roots (1.8%) hand the opponent a forced mate**; threefold-root cp median 3, p90 680 |
| who fixes it | repair the move (ship both patches) | **the shipped repair changes the move in 0 of 2,457 roots** — see §5 |

The mechanism the report established survives: **2,457 of 2,457** measured roots return the
engine's own generated head as `bestmove`, verified against `go perft 1` on the identical
position. That part was right and is now measured on real roots rather than six fixtures.

---

## 1. Why the original null is vacuous — measured, not asserted

The report counted drawn roots in random-play games. Random play cannot reach the guard, and
that is a measurement rather than an inference. Reproduced with the same three predicates as
the rest of this audit, 4,600 random games, 200-ply cap (`scripts/random_null.py`,
`evidence/random_null.json`):

| measurement | value |
|---|---|
| games played | 4,600 |
| plies played | 878,532 |
| **games that ever reached halfmove ≥ 100** | **0** |
| **max halfmove reached, over all 4,600 games** | **73** |
| median max halfmove per game | 18 |
| games that ever contained a threefold position | 3 |
| games that ever contained engine-insufficient material | 6 |
| firings | 9 |
| how games ended | 499 checkmate, 37 stalemate, 4,064 hit the ply cap |

**No game in that corpus ever got within 27 plies of the fifty-move threshold**, and only 3 of
4,600 ever produced a threefold position at all. A null from that corpus says nothing about a
guard that needs halfmove ≥ 100 or three occurrences — the corpus is not a sample of the
condition, it is a sample of positions where the condition is unreachable. This is exactly the
rule §6 of the report states (*"A control must search for a case that differs, and a run that
cannot demonstrate a difference must invalidate itself"*) applied to its own headline figure.

**One discrepancy, stated rather than smoothed over.** This corpus found **3** threefold
positions where the report found 0. The likely reason is the cap, not a disagreement: the report
used 200 plies for 600 games and 160 plies for 4,000, this uses 200 for all 4,600, and the three
occur at plies **56, 188 and 198** — two of them in the last 12 plies of a capped game. That
difference runs **in the report's favour on its own count** and does not help mine — 3 in 4,600 is
still a corpus that essentially cannot reach the guard. It is recorded so the reproduction can be
seen to differ rather than to agree by construction.

**The mechanism, measured rather than assumed.** The report's explanation is that "random play
mates long before the counter fills". That is not what happens in this corpus — 4,064 of 4,600
games hit the ply cap instead of ending in mate. The reason the counter never fills is that
**random play resets it constantly**: over 300 random games (mean 194 plies), a capture or pawn
move occurs a mean of **50.5 times per game**, so the **longest quiet run in a game averages 19.3
plies and never exceeded 49** — while reaching halfmove 100 needs one unbroken run of 100. The
fifty-move arm is unreachable to random play for a structural reason.

The 9 firings that did occur are 6 `insufficient` and 3 `threefold`, at halfmove 0 or ≤ 26: the
guard is reachable by random play only through the material arm, or by a threefold that happens
to land in a capped game.

**Depth-independent.** Depth 6 (500 games) gives 8.53 per 1,000 plies; depth 10 (1,500 games)
gives 8.78. The condition is a property of how engine games unfold, not of search depth.

---

## 2. The real base rate

Engine self-play, **fixed depth 10**, `Threads 1`, `Hash 16`, no book, no tablebase. Games
start from a seeded random legal opening prefix of 3–8 plies, so every game is a genuinely
different game (see §7 for why that matters). Games run to real game-over or a 300-ply cap,
and **every** firing is recorded rather than stopping at the first one — otherwise "firings per
1,000 plies" collapses into the game rate and measures nothing.

Depth is fixed rather than clocked because the engine is deterministic at a fixed depth
(verified: two identical 60-ply games, move-for-move), which makes every number below
reproducible from a seed. Depth 10 was chosen after timing: ~0.009 s per position, so a
1,500-game sample is affordable, while remaining deep enough that the engine plays coherent
chess rather than random moves.

### Rates

| corpus | games | distinct | plies | firings | games with ≥1 |
|---|---|---|---|---|---|
| **depth 10, production** | 1,500 | 1,496 | 279,737 | **2,457** | **706 (47.1%)** |
| depth 10, independent replication | 1,000 | 1,000 | 188,714 | 1,773 | 485 (48.5%) |
| depth 6 | 500 | 500 | 79,763 | 680 | 144 (28.8%) |

**Games containing at least one drawn root:**

- depth 10 production: **47.1%**, 95% Wilson **[44.6%, 49.6%]**
- depth 10 replication: **48.5%**, 95% Wilson **[45.4%, 51.6%]** — agrees with the above
- depth 6: **28.8%**, 95% Wilson **[25.0%, 32.9%]** (shallower play decides games sooner)

**Firings per 1,000 plies:**

- depth 10 production: **8.78** per 1,000 plies, i.e. **1 firing per 114 plies**
  - exact Poisson 95% CI **[8.44, 9.14]**
  - **cluster bootstrap 95% CI [7.80, 9.82]** (resampling whole games; design effect 2.9)
- depth 10 replication: **9.40** per 1,000 plies (1 per 106), Poisson [8.96, 9.84]
- depth 6: **8.53** per 1,000 plies (1 per 117), Poisson [7.90, 9.19]

**The cluster interval is the one to quote.** Consecutive plies in one game are not independent
— a threefold that persists fires on every ply until something changes — so the naive Poisson
interval over plies treats a run of dependent firings as independent evidence. Resampling whole
games gives a design effect near 3, which is the honest width. Even the wide end, 9.82 per 1,000
plies, is three orders of magnitude away from "never".

**Both rates are reported because they answer different questions.** "Is a consumer exposed" is
the game rate (47%). "How often does play walk into it" is the ply rate (8.78 per 1,000). The
report quoted neither; it quoted a zero.

### Which predicate fires

2,457 firings: **1,032 threefold only**, **961 halfmove only**, **258 both**, **206
insufficient material**. So the repetition arm — the one the report tested with random games
and found zero — is the single largest contributor, and random play reached it 3 times in
4,600 games because random play almost never repeats a position on purpose.

---

## 3. Did the bail change the move, and what did it cost?

Three arms on the **identical** position, same move list, same depth (`scripts/cost.py`):

- **base** — the shipped build; bails.
- **patched** — seat 12 + seat 27 composed; the repair the owner is asked to ship.
- **nobail** — **instrument only, not a shipped configuration**: the bail compiled out so the
  position is searched normally. This is the only thing that can answer "what would the search
  have played", because the base searches nothing.

Every row is gated on the replayed board reproducing the recorded FEN exactly; **2,457 of
2,457 rows passed, 0 errors**, and **2,457 of 2,457 confirmed bailing** (0 nodes, empty `pv`)
in the real binary.

### The headline result

| | count |
|---|---|
| roots measured | 2,457 |
| base bails (0 nodes + empty pv) | **2,457 / 2,457** |
| **patched (shipped repair) changes the move** | **0 / 2,457** |
| base move is the engine's generated head | **2,457 / 2,457** |
| searched arm would have played something else | 1,425 / 2,457 |
| roots with a mate-in-1 available to the mover | **0 / 2,457** |

**The shipped repair does not change the move on any real drawn root.** It changes only the
reported `depth` (8 → 1) and the number of `info` lines. That is because seat 12's patch
cancels the adjudication *only* when the side to move has a move that mates immediately — and
on 2,457 real roots that never happens (0 mate-in-1). The report's mate-in-1 fixtures are real,
but they are not what real drawn roots look like: they are constructed positions where a
repetition coexists with a mate on the board.

This does not contradict the earlier seats' measurements; it bounds them. "The repair removes
the zero-node path *when a mate exists*" is what the evidence supports. "The repair fixes the
move" is not, and the report's ship verdict rests on the stronger reading.

### Cost of the move the bail plays

Centipawns are measured from the **opponent's best reply**, scored from the root side's point
of view — an objective loss of the move, not a comparison of two scores belonging to different
sides. Rows where either arm's reply score is a mate sentinel (|cp| ≥ 90,000) are separated.

**Threefold roots** (n = 1,251 after removing mate sentinels):

| | value |
|---|---|
| median | **3 cp** |
| mean | 204 cp |
| p75 / p90 / max | 166 / 680 / 2,957 |
| unchanged (0 cp) | 538 |
| > 0 | 638 |
| ≥ 100 cp | 401 |
| ≥ 300 cp | 229 |
| < 0 (bail did *better*) | 75 |

**Halfmove-only roots** (n = 950):

| | value |
|---|---|
| median | 0 cp |
| p75 / p90 / max | 0 / 44 / 3,112 |
| ≥ 100 cp | 78 |

**The median cost is small and the tail is not.** Half the threefold firings cost nothing
because the position is genuinely drawn and any move draws. That is the report's own
"the score is largely sound" point, and it survives. What the median hides is the tail, and the
tail is where the damage is.

### The sharp end: the bail hands over forced mates

Comparing the two arms' moves on the same root, with the opponent's reply scored:

| case | count |
|---|---|
| bail's move allows a forced mate, **searched move does not** | **41** |
| both arms' moves allow a forced mate (not the bail's fault) | 6 |
| searched move allows a mate the bail's does not | 2 |

**41 of 2,251 non-dead roots (1.8%) are cases where the bail plays into a forced mate that the
search avoids.** Eight were re-verified independently at depth 16:

| halfmove | base plays | searched move | after the base move |
|---|---|---|---|
| 13 | `h5h4` | `f2e2` | `mate 1` for the opponent (python-chess agrees: `a7a8`) |
| 13 | `g6g5` | `h3g4` | `mate 1` (`f6h8`) |
| 8 | `f7f2` | `g1h1` | `mate 2` |
| 9 | `e7f6` | `e7e8` | `mate 2` |
| 10 | `h4h3` | `e1d1` | `mate 2` |
| 11 | `g5g7` | `f7e8` | `mate 2` |
| 11 | `f5f4` | `f3g4` | `mate 1` (`e7e8`) |
| 24 | `b6b7` | `e7g5` | `mate 1` (`d2h2`) |

All eight are at **halfmove 8–24**, far from the fifty-move boundary, so this is not the
documented leaf-rule defect one ply down. `8/8` confirmed at depth 16.

This is a different and worse failure than the report's "median 600–1,000 cp material loss":
it is not a lost pawn, it is a lost game, on 1.8% of firings.

### Games decided

Per-position cost does not answer "how many games were decided by it". Paired comparison on
identical openings (`scripts/pairs.py`): the same 250 prefixes played by base and by the
bail-disarmed instrument, both deterministic at depth 10.

- **111 of 250 games** reached at least one firing.
- **66 of those 111 (59%) had a different result** with the bail disarmed.
- Direction: **48 decisive games became draws, 0 draws became decisive**, 18 involved the ply
  cap.
- **97 of 111 games diverged at exactly the first firing ply** — so the divergence is caused by
  the bail and not by downstream noise.

Read this carefully, because the direction is not uniform and an earlier draft of this report
over-read it. The 48 "decisive → draw" cases split by **who was to move at the first firing**:

| the side to move at the firing, in the base game | count |
|---|---|
| **lost** the base game (disarming made it a draw) | **34** |
| **won** the base game (disarming made it a draw) | **14** |

In the 34, the bail's unsearched move hurt the side that played it, which is what "the bail
concedes" predicts. In the 14 it is the reverse — the side that bailed went on to win, and
disarming turned that win into a draw — so those 14 are **not** cases of the bail losing the
game, and a first draft that described all 48 as the bail conceding was wrong. What survives is
the weaker, still-important statement: **66 of 111 games that reach a firing change result when
the bail is disarmed (59%), the direction is overwhelmingly towards draws (48 to 0), and 97 of
111 diverged at exactly the first firing ply.** The per-game mechanism inside that association
is not traced, and the split above is the reason it cannot be assumed in either direction.

---

## 4. Where the exposure is — it is endgames, not openings

### Not openings

Across 20 opening families (≥ 50 games each, by first move), the game-with-firing rate ranges
only **38.9% (1.d4) to 52.9% (1.g3)**, around the 47% mean. **No opening family is materially
more exposed.** Whatever an owner does about this, an opening-specific fix would be misdirected.

### Decisively endgames

Firings by total material, against the material distribution of all positions actually played
(sampled every 5th ply across the production corpus, 58,215 positions):

| pieces on board | share of played positions | share of firings | enrichment |
|---|---|---|---|
| 2 (bare kings) | 0.04% | 4.84% | **128×** |
| 3–5 | 18.2% | 50.5% | **2.8×** |
| 6–8 | 17.9% | 18.0% | 1.0× |
| 9–11 | 12.2% | 10.2% | 0.8× |
| 12–14 | 8.3% | 5.5% | 0.7× |
| 15–17 | 6.8% | 4.3% | 0.6× |
| 18+ | 36.6% | 6.6% | 0.2× |

**More than half of all firings — 55.4% — occur with 5 or fewer pieces on the board, a band that
is 18.2% of played positions.** The most common endgame types are `3-piece 1R` (338),
`3-piece 1Q` (150), `5-piece 1P2R` (124) and `bare kings` (119). Mobility at the firing is a
median of 13 legal moves (min 1, max 58).

So the exposure is where the draw rules decide games: rook and queen endings shuffling towards
fifty moves, and bare-minimal material. **That is the opposite of the report's §2 line "the
exposure is MIDDLEGAMES, not endgames"**, which was measured on one constructed 32-piece
position with an artificial repetition. Real exposure is endgame-concentrated by 2.8×, and 128×
at the extreme.

Caveat, stated because it bounds the claim: this corpus is engine self-play at depth 10, which
reaches simplified endings often. A corpus of human master games would have a different material
distribution, and the enrichment factors would move. The *ordering* (endgames over openings) is
robust to that; the exact multipliers are corpus-specific.

---

## 5. What this means for the ship verdict

The report's verdict is "SHIP BOTH PATCHES". Measured against real drawn roots:

- The **reporting** patch (seat 27) does exactly what it claims: it stops a drawn root claiming
  `depth 8`/`depth 64` on a search that visited no nodes, reporting `depth 1` honestly. That
  claim is verified here on 2,457 roots: base reports depth 8 with 0 nodes; patched reports
  depth 1.
- The **mate-guard** patch (seat 12) is correct for what it does — it stops the adjudication when
  a mating move exists — but on the population that actually reaches the guard it **never
  triggers**: 0 of 2,457 roots have a mate-in-1.

So shipping both patches is right for **honesty about the score and the depth**, and is
demonstrably **not** a fix for the move. The defect that remains after both patches is the one
§2 already names at the end — the rule is one ply too low and the leaf rule adjudicates at
search.cpp:1302 — and, per this audit, the larger remaining defect is that **the zero-node path
still plays the generated head**. What that is worth, measured: **41 of 2,251 non-dead roots
(1.8%) play into a forced mate the search avoids**, and disarming the bail changes the result of
**59% of games that reach one (66 of 111)**, overwhelmingly towards draws (48 to 0), with the
side that bailed losing the base game in 34 of those 48.

That is not the same sentence as "the bail loses games it would otherwise win". It is: the
unsearched move measurably changes outcomes on the population that reaches the guard, and on
1.8% of roots the change is a forced mate.

If the owner wants the move fixed, the minimal change consistent with this evidence is to make
the drawn-root path play a **searched** move rather than the generated head — which is what the
`nobail` instrument does, and which changes the move on 1,425 of 2,457 roots. That is a design
change with its own pin cost and was not attempted here; it is the recommendation, not a result.

---

## 6. How the numbers were validated

Everything load-bearing has a check that can fail.

**Honesty pins, both builds.** `scripts/pins.py`, run on base and on the composed patched
tree: bench 11 = **312,866**, bench 13 = **862,329**, bench 16 = **3,024,920**, perft 5 =
**4,865,609**. All four agree on both builds.

**Repair composition.** Seat 12 at `-p1` from the repo root, then seat 27 at `-p1` from inside
`forge-combo29/`; both `patch` runs exit 0 (the seat-27 hunk lands at 2275, offset 19), and the
resulting `src/search.cpp` is sha256
**`24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`** — the expected value.

**The predicate reimplementation, proven able to fail** (`scripts/oracle.py`). The whole audit
rests on `is_drawn_root()`. It is checked against the base binary's own caller-visible bail
signature (0 nodes AND empty `pv`) on 10 cases whose answer is known in both directions —
5 positives (threefold, halfmove 100, K+N v K, K+B v K, bare kings) and 5 negatives (halfmove
99, twofold only, K+2N v K, knight-and-pawn, ordinary middlegame). **ORACLE PASS, 10/10.**
Non-vacuity was proved by planting a fault: changing the threshold from `>= 100` to `>= 99`
makes the `halfmove_99` case flip and the oracle report **FAIL**. Restoring the file returns
PASS.

**A claim of mine that was false, and was removed.** An earlier version of `predicates.py`
asserted that python-chess calls K+N v K *sufficient* while the engine calls it insufficient.
Testing it showed **python-chess agrees with the engine** — zero disagreements across 4,000
random bare-minor positions and six hand cases. The claim is gone from the code and from this
report; the predicate is still reimplemented from the engine's source, but for drift-resistance,
not because the libraries disagree.

**The mechanism, verified on every row.** The report's claim "the bail returns the head of the
generated list" was tested on all 2,457 measured roots by comparing the bail's `bestmove` with
the head of `go perft 1` on the identical position: **2,457 / 2,457 is the head**, and
**2,457 / 2,457 is a legal move in the engine's own list**. (python-chess's move order differs
from the engine's — it sorts by square — so the check uses the engine's list, not python-chess's;
a first attempt using python-chess's order scored 0/130 and would have wrongly refuted a true
claim.)

**Position-identity gate on every adjudicated row.** Each firing records the exact move count at
which it occurred; the adjudication replays that prefix and refuses any row whose FEN differs
from the recorded one. This is not decorative: an earlier version passed the game's *full* move
list instead of the prefix, put the engine on a later position, and produced 35 of 40 bogus rows.
The gate caught it.

---

## 7. Harness defects found and fixed in this seat

Recorded because each one would have produced a confident wrong number, and two of them would
have reproduced the very error this audit is about.

1. **The first game loop could not see the condition.** It tested `board.is_game_over()` before
   the guard, so every game ending in a claim was recorded as "never reached a drawn root" — a
   structural zero from a loop that could not observe the thing it was counting. Fixed by testing
   the guard first, on the position before the move, which is the position the engine is asked
   about.

2. **python-chess's claim rule truncated the threefold arm.** `is_game_over(claim_draw=True)`
   ends a game when the side to move *could* claim by making a move — i.e. at a **twofold**, one
   ply before the engine's guard needs three occurrences. Measured effect: 17 of 31 games ended
   "claim" with the guard never having fired. Fixed by running on `claim_draw=False` and
   recording claim availability separately.

3. **A fake `n`.** The engine is fully deterministic at fixed depth, and the first version cycled
   a 35-entry opening list 200 times — producing **35 distinct games reported as 200**, i.e. every
   game counted 5.7 times. Four "different seeds" produced byte-identical output, which is what
   exposed it. Fixed by drawing a seeded random legal prefix per game; the harness now records
   `distinct_games` and every run reports it (1,496 of 1,500 on the largest run).

4. **A units error that was caught by absurdity.** The first Poisson interval multiplied by 1000
   twice, producing intervals of ±1,700 firings per 1,000 plies. The numbers were obviously wrong;
   the fix passes `plies/1000` as the exposure.

5. **A mislabelled endgame signature.** The material label built `(piece_type, count)` pairs and
   printed them reversed, so `3-piece 1124` meant "3 pieces, 1 rook" and read as nonsense. Caught
   by looking at the output rather than the code.

---

## 8. What is not established

- **Per-game mechanism.** The paired comparison shows the result changes in 66 of 111 games that
  reach a firing, and that 97 of 111 diverge exactly at the first firing ply. That is a
  deterministic paired association, not a per-game proof that the bail's specific move lost that
  specific game.
- **Human-game exposure.** All rates are from engine self-play at depth 6 and 10. Human games
  reach different material distributions and repeat positions differently. The endgame
  concentration should hold; the multipliers need re-measuring on a human corpus.
- **MultiPV and clock modes.** Everything here is MultiPV 1 at fixed depth with `Threads 1`.
  The report's clock-based observations are not re-tested.
- **Only the composed repair was compared.** The `nobail` instrument is not a shipping
  candidate; it exists to make "the search would have played" measurable. Whether a *searched*
  drawn-root path is safe to ship (pin cost, determinism, the leaf rule at
  `search.cpp:1302`) is untested here.
- **The 48 decisive→draw transitions are not individually explained.** The direction is
  unambiguous and causally anchored at the firing ply, but I did not trace each game's
  adjudication to separate "the bail lost it" from "the disarmed build found a defence the bail
  never looked for". Both are consistent with the data; both are the bail's fault; they are
  different sentences.
