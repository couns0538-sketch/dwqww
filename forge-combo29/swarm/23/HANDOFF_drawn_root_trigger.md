# HANDOFF — the 0-node drawn-root trigger, for a source-reading seat

> ## STOP — THE TRIGGER IS NOW EXPLAINED. READ 23-F122 FIRST.
>
> **There is no engine anomaly to investigate. The "positions that bail" and "positions that search" split in this
> document was an artefact of MY fixture-validation key, which omitted the castling field.** Every fixture here was
> asserted to have its root occurring three times under a key of placement + side + EP; under FIDE identity
> (placement + side + castling) the two boards that SEARCHED had only ONE occurrence, because their cycles moved a
> rook or king and destroyed a castling right.
>
> Re-counted correctly, 9 of 9 correspond exactly: castling-neutral fixture → 3 occurrences → **bails**;
> castling-disturbing cycle → 1 occurrence → **searches**.
>
> So the drawn-root behaviour is exactly what the family originally claimed, and the mechanisms A–F below were
> answers to a question that did not exist. **23-F112's scope limit is withdrawn. 23-F114's "castling conditioner" is
> position identity working correctly.** The family core (F93/F96/F98/F100/F101/F103/F105/F108/F110/F113) stands.
>
> What remains genuinely open for a source reader is much smaller: **why the bail publishes the generator's FIRST
> move rather than searching** (23-F98/F100), and whether the guard that admits the bail sits before or after root
> ordering. The two-code-path observation (a bailing cell returns the list head; a searching cell returns index 5 of
> its divide) is still the sharpest clue, and it is now about ONE path, not two behaviours.
>
> The sections below are retained unedited because the measurements in them are correct — it is the QUESTION they
> were assembled to answer that was wrong. Reading them without this note would repeat my error.

Seat 23 (area 3, move generation), branch `for-fable-and-opus/swarm-23`, folder `forge-combo29/swarm/23/`.
Everything below is from the BASE build (`~/build/forge`, sha256 `e06310ec…`), Threads 1, Hash 16, OwnBook false,
`go depth 10`, fresh process per line, stdout drained to `bestmove`.

**What this document was ORIGINALLY asking you to explain, and what is actually left** (the STOP notice above supersedes
this paragraph; it is kept so the original framing is visible):

ORIGINAL: on some positions whose root had occurred three times in the move list, the engine returns `bestmove` with
**0 nodes**, scoring **cp 0** at every depth, and the move is the first of its own generated list (23-F98); on
other positions with "the same threefold root" it searched normally, and the state was recorded as *reproducible effect,
four explanations ruled out, no clean characterisation*.

ACTUAL: there was no such split. The trigger is fully characterised (23-F125/F140 — 0 nodes iff the SEARCHED position has
occurred at least three times in the sent move list), and the boards that searched were never threefolds because my
validator's key omitted castling (23-F122). The only question left for a source reader is why the bail publishes the
generator's first move rather than searching — §5 below states it in that form.

---

## 1. Master table — every drawn-root cell measured

Move lists are sent as `position fen <FEN> moves <list>`. "root occ" = how many times the ROOT position occurs in that
list (counted in python-chess on placement + side to move + castling; **not** on the halfmove field).
`cycle` is the 4-ply shuttle that is repeated; the full list is the cycle twice.

| # | FEN | full move list | root occ | nodes | score | bestmove | verdict |
|---|---|---|---|---|---|---|---|
| E1 | `1k6/3q1p1p/rp5p/4P3/pQ3P2/7P/3R2PK/8 b - - 0 1` | `b8c8 b4e7 c8b8 e7b4 b8c8 b4e7 c8b8 e7b4` | 3 | **0** | cp 0 | a4a3 | **BAIL** |
| E2 | `1K6/8/8/3R4/8/8/8/k7 w - - 0 1` | `b8c8 a1b2 c8b8 b2a1 b8c8 a1b2 c8b8 b2a1` | 3 | **0** | cp 0 | d5d1 | **BAIL** |
| E3 | `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1` | `g1h1 g8h8 h1g1 h8g8 g1h1 g8h8 h1g1 h8g8` | 3 | **0** | cp 0 | f2f3 | **BAIL** |
| E4 | `7k/8/8/8/8/8/6PP/7K b - - 0 1` | `h8g8 h1g1 g8h8 g1h1 h8g8 h1g1 g8h8 g1h1` | 3 | **0** | cp 0 | h8g7 | **BAIL** |
| M1 | `rnbqkbnr/pppp3p/6p1/4pp2/7P/1P1BP3/P1PP1PP1/RNBQK1NR b KQkq - 0 4` | `g8e7 d3a6 e7g8 a6d3 g8e7 d3a6 e7g8 a6d3` | 3 | **0** | cp 0 | **e5e4** | **BAIL** |
| M1s | same, castling field → `-` | same | 3 | **0** | cp 0 | e5e4 | **BAIL** |
| M4 | `r1bqkbnr/R2pp2p/5p2/1Ppn2p1/5P2/1P1P1N2/2P1P1PP/1NBQKB1R w Kkq - 0 8` | `a7c7 g8h6 c7a7 h6g8 a7c7 g8h6 c7a7 h6g8` | 3 | **0** | cp 0 | **c2c3** | **BAIL** |
| M4s | same, castling field → `-` | same | 3 | **0** | cp 0 | c2c3 | **BAIL** |
| M7 | `rn1qkb1r/p2p1p2/1p2p3/2pP2pp/Q1N3P1/P1P1BP2/1P2P1K1/R4BNR w kq - 1 15` | `c4e5 h8g8 e5c4 g8h8 c4e5 h8g8 e5c4 g8h8` | 1 | **11,390** | cp 965 | **d5e6** (index 5; divide head b2b3) | searched |
| M7s | same, castling field → `-` | same | 3 | **0** | cp 0 | (not recorded) | **BAIL** |
| C1 | `r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1` | `a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8` | 1 | **17,601** | cp 809 | h1h8 | searched |
| C1s | same, castling field → `-` | same | 3 | **0** | cp 0 | — | **BAIL** |
| C1h | `… w KQkq - 13 7` (halfmove 13) | same | 1 | **17,601** | cp 809 | h1h8 | searched |

**Same-position controls (bare FEN, no move list — these SEARCH, as they must, since no history is present):**

| # | FEN | nodes | move |
|---|---|---|---|
| E1 bare | `1k6/3q1p1p/rp5p/4P3/pQ3P2/7P/3R2PK/8 b - - 0 1` | 44,888 | d7c8 (cp -106) |
| E2 bare | `1K6/8/8/3R4/8/8/8/k7 w - - 0 1` | 7,581 | d5b5 (cp 381) |
| E3 bare | `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1` | 210 | — |
| E4 bare | `7k/8/8/8/8/8/6PP/7K b - - 0 1` | 8,522 | — |
| C1 bare | `r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1` | 11,970 | h1h8 (cp 799) |

**Halfmove sweep on the three middlegame boards (only that field varied):**

| # | halfmove 0 | 1 | 2 | original |
|---|---|---|---|---|
| M1 | 0 nodes | 0 | 0 | 0 (was 0) |
| M4 | 0 nodes | 0 | 0 | 0 (was 0) |
| M7 | **11,390** | **11,390** | **11,390** | 11,390 (was 1) |

---

## 2. The ladder — added material does not stop the bail (23-F115)

Each rung is a minimal edit of E2's board; each rung's cycle was found by search over legal non-capturing
non-checking moves, and the root's occurrence count was asserted `== 3` and asserted to end at the root before the
engine was called. A rung failing either assertion would have been excluded and printed as excluded.

| rung | FEN | cycle (sent twice) | nodes | verdict |
|---|---|---|---|---|
| L0 base | `1K6/8/8/3R4/8/8/8/k7 w - - 0 1` | `b8c8 a1b2 c8b8 b2a1` | **0** | BAIL |
| L2 +black rook h8 | `1K6/8/8/3R4/8/8/8/k6r w - - 0 1` | `b8c8 h1h7 c8b8 h7h1` | **0** | BAIL |
| L3 +black pawn h7 | `1K6/8/8/3R4/8/8/7p/k7 w - - 0 1` | `b8c8 a1b2 c8b8 b2a1` | **0** | BAIL |
| L4 black king to b2 | `1K6/8/8/3R4/8/8/1k6/8 w - - 0 1` | `b8c8 b2c3 c8b8 c3b2` | **0** | BAIL |
| L5 mirrored, black to move | `1k6/8/8/3r4/8/8/8/K7 b - - 0 1` | `b8c8 a1b2 c8b8 b2a1` | **0** | BAIL |
| L6 +black knight g1 | `1K6/8/8/3R4/8/8/8/k5n1 w - - 0 1` | `b8c8 g1h3 c8b8 h3g1` | **0** | BAIL |
| L7 +pawns both sides | `1K6/8/8/3R4/8/5P2/6p1/k7 w - - 0 1` | `b8c8 a1b2 c8b8 b2a1` | **0** | BAIL |

---

## 3. What these cells show — measured facts, NOT engine explanations ruled out

**Reframed (23-F122).** The rows below were originally headed "what is ruled out", which implied they eliminated candidate
causes inside the engine. They do not: each is a fact about MY fixtures, and the reason none of them explains anything is
that the boards in question were not all threefolds. Kept because the measurements are correct and a reader may want them.

| observation | how it was established |
|---|---|
| **Material count / sparse endgame** | M1 (32 pieces), M4 (30) and the ladder's 7 of 7 — pieces added, still bails |
| **Castling rights alone** | M1 and M4 bail **with** rights present (M1 `KQkq`, M4 `Kkq`), while M7 and C1 search with rights |
| **Halfmove clock** | M7 searches at halfmove **0, 1 and 2**; M1/M4 bail at **0, 1 and 2** — the field was varied alone, board and cycle fixed (`halfmove_probe.out`) |
| **"No history" vs "history"** | every bare-FEN control searches; every threefold-in-the-list cell bails or searches as tabled |

## 4. The asymmetry a source reader should explain — REWRITTEN (it was never an engine asymmetry)

The original text here described castling rights as a "conditioner": rights present sometimes prevented the bail, sometimes
not. **That framing was wrong and is replaced.** What was actually happening is ordinary correctness:

- a cycle that destroys a castling right does not produce a repetition at all, because the castling field is part of
  position identity (FIDE), and the engine correctly sees ONE occurrence rather than three (23-F122);
- a cycle that preserves the field produces a genuine threefold and the engine bails (23-F125).

So there is no asymmetry in the engine to explain, and **the only thing a source reader needs from this section is the
confirmation that the engine's repetition key includes the castling field** — which is correct behaviour and needs no
investigation (23-F122, job 59).

## 5. SUPERSEDED — the six candidate mechanisms below answered a question that does not exist

**Read this instead of §5's original content, which is retained further down only so the error is visible.**

Mechanisms A–F were written to explain why SOME threefold roots bail and others search. 23-F122 showed there was no such
split: the boards that searched were miscounted by my own validator, because its position key omitted the castling field.
Every one of A–F was a hypothesis about a non-existent distinction.

What is actually open is ONE question, and it is much smaller:

> **On a genuine threefold root — where the FIDE identity has truly occurred three times — why does the engine publish
> its generator's first move with 0 nodes, instead of searching?**

The two facts that constrain the answer:
- the bail's move is `go perft 1`'s first move on every bailing cell tested (23-F98), and on a searching cell the move is
  an ordinary search result (M7: `d5e6`, index 5 of a divide headed by `b2b3`, `job56/m7_index.out`);
- the bail is conditional on HISTORY only: the same position as a bare FEN searches (23-F109/F110).

So the shapes still worth looking for, and I do NOT claim this list is exhaustive:

1. **A draw test that returns before any root ordering runs**, publishing the generated head. This is the shape most
   consistent with everything measured, and mechanism A/B in the original text is a version of it.
2. **A draw test after generation whose failure path never applies ordering** — behaviourally identical from outside,
   distinguishable only in source.
3. **Anything else** — and this caveat is not decoration: mechanism C's premise (that the castling field is part of the
   repetition key) turned out to be TRUE (23-F122 via job 59), even though C as written was answering the wrong
   question. A list of eliminated mechanisms is only as good as the questions they were asked, and these were asked the
   wrong one.

The discriminating observation from outside, if a reader gets one cheap cell: a drawn root whose returned move is NOT
the generator's first generated move would rule out shape 1 as a complete account. None of the nine bailing cells
measured does that, which is why shape 1 survives.

### Original §5, retained unedited as the record of what was tried and why it was wrong

## 5b. ORIGINAL candidate mechanisms — retained as the record of what was tried

I have not read the source. These are listed so you can look for the one that matches, not because I can rank them. For
each: what it predicts, and what in my table (or one cheap extra cell) would refute it.

**A. Early return before root ordering, publishing the head of the generated list.**
Predicts the bail on *every* drawn root. Refuted as a complete explanation by **M7 and C1** (searched, 11,390 / 17,601
nodes, and M7's searched move `d5e6` sits at index **5** of its divide whose head is `b2b3`, so M7 searched rather than publishing a list head — verified in `job56/m7_index.out`). Still the likely *shape* of the bail path —
it is the "why does it sometimes not fire" that needs a second condition.
*Discriminating cell:* any board where the root is drawn and the returned move is **not** the generator's first move
would rule this out even as a partial account; all bailing cells so far returned index 0, so it survives as the bail
path itself.

**B. A draw test placed after move generation but before the search, whose failure path leaves the list unordered.**
Behaviourally identical to A from outside; distinguishable only in source. *Discriminating evidence:* if the bail's
returned move ever differs from `go perft 1`'s first move, B is wrong about the list head — none does, so A and B stand
together and source is the only way to separate them.

**C. A repetition detector whose position key includes the castling field.**
Predicts that a root whose castling field differs from the field recorded in the engine's own history would not be seen
as a repetition. Refuted as a *complete* explanation by M1/M4 (rights present in both root and history, still bail).
*Discriminating cell:* send a move list where the root's castling field is `-` but the history was built under rights
(or the reverse) — if the engine's own bookkeeping disagrees with the sent FEN field, C becomes live. Not yet measured.

**D. The draw test being skipped or short-circuited when castling rights are present (a castling-specific code path).**
Predicts: rights present ⇒ search, always. Refuted by **M1 and M4**.
*Discriminating cell:* more rights-present boards; if any rights-present board ever bails, D is dead — two of four
already do, so D is very unlikely.

**E. Something size- or count-dependent in the history (e.g. a fixed-size history array, or a repetition search
window shorter than the cycle).**
Predicts dependence on how far back the repeated position sits, not on its content. *Discriminating cell:* two lists
where the root occurs 3 times but at DIFFERENT distances (e.g. plies 0/8/16 vs 0/4/8). If verdicts differ, E is live.
**This is the cheapest untested axis in the table** — every cell above has the root at plies 0, 4 and 8.

**F. The engine treating "draw" as a score adjustment (cp 0) rather than a hard return, with the search then finding
nothing to add.**
Predicts a nonzero node count with cp 0. **No cell shows that** — every bailing cell has exactly 0 nodes — so F is
unlikely, and its absence is one of the firmer facts here.


## 6. What is still worth measuring — rewritten, because the original three items are settled

**The original list asked a source reader to diff M1 vs M7 and to chase a rights-history mismatch. Both are answered.**

1. **What was measured instead, and settles the question:** the threshold at the END of a LONG list — 10-ply preamble plus
   repetitions, searched position never the start position — gives **2 → searches (17,399 nodes), 3/4/5 → bails**
   (23-F141). So list length and root position are irrelevant; only the searched position's own count matters.
2. **Distance axis: UNTESTED, and now known to be structurally hard rather than merely under-resourced (23-F142).** A
   board admitting a non-root loop is necessary but NOT sufficient: with one position anchoring both the count and the
   spacing, `A + B + A` always yields FOUR occurrences rather than three, for all ten neutral fillers enumerated on a dense
   middlegame board. Varying spacing while holding the count at three needs an anchor reachable by two paths of different
   length — a different fixture design, not a busier board. If anybody builds it, the prediction to kill is: "the spacing
   of the three occurrences changes nothing, because only the count matters" (23-F125/F140/F141).
3. **The only live question for a source reader:** *why does the bail publish the generator's first move rather than
   searching?* §5 states it, and the discriminating observation from outside remains: a bailing root whose returned move
   is NOT the generator's first move would rule out the "early return publishes the head" shape. None of the nine bailing
   cells measured does that.

## 7. Reproduce

```
cd forge-combo29/swarm/23/job54 && python3 history_gate.py        # E1-E4 + bare controls
cd forge-combo29/swarm/23/job56 && python3 ladder.py              # the 7-rung ladder
cd forge-combo29/swarm/23/job56 && python3 castling_probe.py      # C1 / C1s / C1h
cd forge-combo29/swarm/23/job56 && python3 middlegame_probe.py    # M1,M1s,M4,M4s,M7,M7s
cd forge-combo29/swarm/23/job56 && python3 halfmove_probe.py      # the halfmove sweep
```

Related rows: 23-F93, F96, F98, F100, F101, F103, F105, F108, F110, F112, F113, F114, F115. The mechanism as it stands
(index 0 played unsearched) is 23-F98/F100; the gate on history is 23-F109/F110.

**CORRECTION, added after 23-F122 — the rows named above as "the scope limits and this handoff" are WITHDRAWN.** F112's
scope limit, F114's castling conditioner and F115's material ladder were all responses to a defect in MY fixture
validation: the occurrence key omitted the castling field, so two boards that searched were miscounted as threefolds.
The trigger is now exactly characterised — the base returns 0 nodes iff the POSITION BEING SEARCHED (the end of the sent
move list) has occurred at least three times in that list (23-F125, tested at 2/3/4/5/6 and confirmed in both directions
across nine boards, 23-F132/F133; the wording "root's identity" became "searched position" in 23-F140, and the
measurements are unaffected because every fixture had the repeated position at the end of its list). Everything
in this document's sections 1–6 was assembled to explain that non-existent split and should be read as superseded; the
MEASUREMENTS in them are correct, the QUESTION was wrong. Current state: 23-F125, 23-F126, 23-F128, 23-F129/F130.
