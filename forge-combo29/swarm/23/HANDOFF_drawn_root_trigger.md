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

**What you are being asked to explain:** on some positions whose root has occurred three times in the move list, the
engine returns `bestmove` with **0 `info depth` lines and 0 nodes**, scoring **cp 0** — and the move it returns is the
first move of its own generated list (23-F98). On other positions with the same threefold root it searches normally.
The state is: **reproducible effect, four explanations ruled out, no clean characterisation.** The table below is the
input; the last section lists the mechanisms I would consider and the cell that would kill each.

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
| M7 | `rn1qkb1r/p2p1p2/1p2p3/2pP2pp/Q1N3P1/P1P1BP2/1P2P1K1/R4BNR w kq - 1 15` | `c4e5 h8g8 e5c4 g8h8 c4e5 h8g8 e5c4 g8h8` | 3 | **11,390** | cp 965 | **d5e6** (index 5; divide head b2b3) | searched |
| M7s | same, castling field → `-` | same | 3 | **0** | cp 0 | (not recorded) | **BAIL** |
| C1 | `r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1` | `a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8` | 3 | **17,601** | cp 809 | h1h8 | searched |
| C1s | same, castling field → `-` | same | 3 | **0** | cp 0 | — | **BAIL** |
| C1h | `… w KQkq - 13 7` (halfmove 13) | same | 3 | **17,601** | cp 809 | h1h8 | searched |

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

## 3. What is ruled out, and by which cells

| explanation | killed by |
|---|---|
| **Material count / sparse endgame** | M1 (32 pieces), M4 (30) and the ladder's 7 of 7 — pieces added, still bails |
| **Castling rights alone** | M1 and M4 bail **with** rights present (M1 `KQkq`, M4 `Kkq`), while M7 and C1 search with rights |
| **Halfmove clock** | M7 searches at halfmove **0, 1 and 2**; M1/M4 bail at **0, 1 and 2** — the field was varied alone, board and cycle fixed (`halfmove_probe.out`) |
| **"No history" vs "history"** | every bare-FEN control searches; every threefold-in-the-list cell bails or searches as tabled |

## 4. The one asymmetry a source reader should explain

- **Stripping castling rights never prevented a bail**: 3 of 3 stripped cells (M1s, M4s, M7s) plus C1s bail, and all
  seven ladder rungs have an empty castling field and bail.
- **Having castling rights sometimes prevents it and sometimes does not**: M7 and C1 search with rights; M1 and M4 bail
  with rights.

So castling rights are **necessary-but-not-sufficient for the searching behaviour**, which means the code contains at
least two conditions, one of them involving castling rights. That is the most useful single observation here.

**And the closest pair in the table is M1 vs M7** — both middlegame, both rights present, opposite verdicts — with one
further measured difference that cuts against the simplest remaining story: **M7 SEARCHED and its move `d5e6` is at
index 5 of its divide (head `b2b3`), so on a searching cell the move is an ordinary search result, not a list head.**
That is consistent with the bail path publishing the list head (23-F98) while the non-bail path orders and searches
normally — which is why the search is for the CONDITION that selects between the two paths, not for two different
move-selection rules.

---

## 5. Candidate mechanisms, and the cell that would kill each

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

## 6. What I would measure next, if measuring were the tool

1. **Distance axis (E):** root at plies 0/4/8 vs 0/8/16 vs 0/4/12 — the only axis every current cell holds constant.
   **ATTEMPTED AND COULD NOT BE CONSTRUCTED (job 57):** varying the spacing needs a FILLER shuttle that returns to a
   NON-root position, and search found none on either M1 or M7 — the same "few pieces, every shuttle returns where it
   started" obstruction that made 23-F113's T1 impossible. So this axis is **UNTESTED, not tested-and-negative**; it
   needs a board busy enough to admit a non-root 4-ply loop.
2. **Rights-history mismatch (C):** root sent with `-` inside a game whose history carried rights.
3. **A rights-present board that bails:** already have two (M1, M4) — a source reader should start by diffing
   **M1 vs M7**, which are the closest pair in the table (both middlegame, both rights present, opposite verdicts).

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
The trigger is now exactly characterised — the base returns 0 nodes iff the root's FIDE identity has occurred at least
three times (23-F125, tested at 2/3/4/5/6 and confirmed in both directions across nine boards, 23-F132/F133). Everything
in this document's sections 1–6 was assembled to explain that non-existent split and should be read as superseded; the
MEASUREMENTS in them are correct, the QUESTION was wrong. Current state: 23-F125, 23-F126, 23-F128, 23-F129/F130.
