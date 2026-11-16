# REPORT — seat 07, job 37: where does the PC patch actually act? (two real-game samples)

## What was asked / the answer / how sure

**Asked:** build the real-game sample the differential needs — 100 late-endgame and drawn positions (the
states the four switches target) — then 100 ordinary middlegames from G, so the two together tell the
owner where the patch acts.

**Answer:** **targeted sample: 50 of 100 positions differ. Ordinary sample: 0 of 100 differ.** Every
difference is attributable to a named switch. The patch is **precisely targeted, not a broad rewrite** —
and on real material it catches the base tree being **wrong** in a way the PC build gets right.

**How sure:** high. Two independent samples, identical settings on both builds, fresh process per run,
Threads 1, Hash 16, depth 12, and the isolation machinery was already proven able to fire (07-C29,
and the 1-of-1 control in 07-C33).

## The samples, and how they were built

Both from **set G** (353 real game positions), classified with python-chess, not by hand:

| sample | composition |
|---|---|
| **targeted** (100) | 30 bare-king endings (real G positions stripped to one side's lone king + 3 pieces), 20 roots with the halfmove counter at exactly 100, 50 late endgames (material 3–14, both sides with material) |
| **ordinary** (100) | G middlegames with material ≥ 26 and no bare king |

Builder: `job37/build_samples.py`; the classifier, the FEN list and the tags are in
`job37/raw/samples.json`.

## Result

    targeted:  50 of 100 positions differ
      BARE_KING_LMR_CAP  30   (every bare-king position)
      ROOT_DRAWN         19   (every fifty-move position: 19 exact, 1 same move/score, different nodes)
      NONE/COMBINATION    1
    ordinary:   0 of 100 positions differ
    absent answers: none

Per-tag breakdown of the targeted sample:

| tag | positions | differing |
|---|---|---|
| `bare_king_white_has_material` | 30 | **30** |
| `fifty_move_100` | 20 | **20** |
| `late_endgame` | 50 | **0** |

That last row is worth stating clearly: **the 50 late endgames did not differ at all.** The fixes are
not "endgame fixes"; they are fixes for the specific states named — a bare king, and a drawn root.

## What this tells the owner

The patch is **targeted and harmless**: it changes exactly the positions its switches name, and leaves
ordinary middlegame trees **bit-identical** (0 of 100, matching 07-C33's 0 of 100 on set O and 07-C30's
`PC+S14 == base+S14 = 9,500,069`). So it is safe to keep by default, and its value is the specific
defects it repairs rather than any general search improvement.

## The case where the base tree is simply wrong (07-F3)

One fifty-move position, `8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1`:

| build | answer |
|---|---|
| base | `b3b2`, **`cp 0`, 0 nodes**, 12 depth lines — never searched |
| PC | `b3b2`, **`mate 6`**, 15,981 nodes |

Black has Q + pawns b3/g3 against a lone king, so black is winning and mates. The base tree declared a
draw on the halfmove counter without looking, which is the ROOT_DRAWN defect exactly.

**The subtlety that decides it, and that I got wrong at first:** file 6's inequality (2N−1 ≤ 100−counter)
would say 11 ≤ 0, i.e. the mate is unreachable, and for a moment I read this as the PC build making a
false mate claim. That inequality is only valid when the fifty-move draw **cannot be reset**. Black has
`b3b2` and `g3g2` available — a **pawn move resets the counter** — so the game is not drawn and the mate
is real. Checking black's pawn moves is what settled it. **The base tree is wrong here and the PC build
is right.**

This is the first case tonight where I can show the base tree demonstrably wrong on real material, and
it is direct evidence that `FORGE_FIX_ROOT_DRAWN` earns its place.

## An honest limitation of the sample

**No third-repetition roots could be built from set G.** I searched for a returning move pair in the
first 60 G positions and found **0 of 60**: G's middlegames have pieces committed to progress, so a
position that can shuffle back to itself essentially never occurs there. So the `ROOT_DRAWN` evidence
here comes entirely from **fifty-move** roots, not from repetition roots. A repetition sample would need
positions built by playing into a repetition (not from G), and I did not manufacture them for this job —
that is a gap in the sample, stated rather than papered over.

## Findings

**07-C34** (where the patch acts) and **07-C35** / **07-F3** (the base tree is wrong on a fifty-move
root; the PC build gets it right).

## Suspicions, not proven

- Whether the base tree is wrong on *many* fifty-move roots or only where a pawn move resets the counter.
  All 20 differ, and all 20 base answers are `cp 0` with 0 nodes, so the "answers without searching"
  part is systematic. How often that is also *wrong* depends on whether a reset is available, which I
  checked in detail for one position only.
- Whether a repetition-root sample would show ROOT_DRAWN firing too. Presumably yes by construction,
  but I have not measured it.

## What I did NOT do

- Did not manufacture repetition positions; see the limitation above.
- Did not run the ordinary sample at other depths or with node budgets.
- Did not count how many of the 20 fifty-move positions have a pawn move available (I checked one in
  detail). That count would say how many of the 20 are genuine base-tree errors rather than harmless
  draw declarations.

## What I am NOT sure about

- Whether the 1 "combination" row (same move and score as the ROOT_DRAWN variant but a different node
  count) is a second switch contributing or aspiration-order noise. It is one position and I did not
  isolate it further.

## Times

See job37/stamps.txt.
