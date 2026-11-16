# REPORT_job13 — is the built-in book's play good by the engine's own judgement?

## What was asked
Nothing specific. This follows S-F15 (the book answers game searches with no search at all for the
opening). The owner's match uses the book, so the natural follow-up is: are the book's moves moves this
engine would stand behind? If the book walked into positions the engine rates badly, a book-on match
would be partly measuring someone else's opening file.

## The answer
**The book disagrees with the engine on most moves but never badly.** Of the 16 book plies walked:

| measure | value |
|---|---|
| book plies walked | 16 (then the book ends) |
| book move **equals** the engine's own choice | 4 of 16 |
| book move **differs** from the engine's choice | 12 of 16 |
| score gap at equal depth (book move − engine move) | median **0 cp**, range **−26 to +18 cp** |
| book moves the engine rates ≥50 cp worse | **0** |
| book moves the engine rates ≥100 cp worse | **0** |

So the book frequently plays a different move from the one the engine would pick, but the engine
considers those moves **essentially equivalent** — the worst is 26 centipawns, well inside normal
engine-to-engine noise on opening moves. There is no evidence here that the book walks into trouble.

## The gaps, in full (16 comparisons at equal depth 12)
```
-26 -26 -23 -18 -15 -11 -5 0 0 0 0 +1 +3 +8 +8 +18
```
Median 0. The distribution is centred on zero, which is what you expect if the book's choices are
reasonable moves that score the same as the engine's own favourites.

## How the comparison was made (equal depth, both moves scored the same way)
For each book position:
1. **A**: `go movetime 100` with `OwnBook true` -> the book's move (recognised from
   `info string book move`, since a book answer emits no `info depth` lines at all — S-F15).
2. **B**: `go movetime 100` with `OwnBook false` -> the engine's own preferred move.
3. **C**: to compare the two moves at **equal depth** rather than at whatever depths the two clock
   searches happened to reach, I played each candidate move and searched the resulting position at
   `go depth 12`, negating the score for the side-to-move flip. That is why the gap column is a
   controlled number and not an artefact of one search running longer than the other.

## How sure
Moderate-to-high on the numbers, **low on their generalisation**, and the distinction matters here:

- The walk is **one line** — the book's own first choice at every ply. A different first move enters a
  different book sub-tree, and I did not enumerate the book.
- Depth-12 evaluation of opening moves is shallow; a book move can look equivalent at depth 12 and be
  clearly better or worse at depth 20. **I cannot conclude the book is good, only that it is not
  obviously bad by a shallow measure.**
- `go movetime 100` with the book off reached depths around 12–14, so the two sides of the comparison
  are of similar quality; but on a slower machine the book-off search would be shallower and the gap
  could look different.

## Findings
- S-F16: the built-in book's moves **differ from the engine's own choice on 12 of 16 opening plies**,
  but score **within −26 to +18 cp of the engine's preference at equal depth 12 (median 0, none ≥50 cp
  worse)**, so the book is not visibly harmful by the engine's own measure. Only 4 of 16 book moves were
  also the engine's first choice. Scope: one book line, 16 plies, depth-12 comparison.
  Reproduce: `cd forge-combo29/swarm/13/job13 && python3 book_quality.py ~/b/pc/forge /tmp/bq 20 12`.

## Suspicions, not proven
- The frequent-but-cheap disagreement is what you would expect from a book built from human or
  third-party games: different but sound moves. I have not verified the book's provenance or quality
  against any external source, so this is a shape-of-the-data observation, not a provenance claim.

## What I did NOT do
- No match, no Elo, no claim about the book's strength.
- Did not enumerate the book's other lines, or test `Book Variety` / `Book Depth`.
- Did not compare at a deeper depth than 12, which is the main limitation.

## What I am NOT sure about
- Whether a book-on match would score better or worse than a book-off match. S-F15 shows the book makes
  matches measure something different; this job only shows the book's moves are not obviously bad, which
  is a much weaker statement than "the book is good for the owner".
- My own first pass at this report said "16 comparisons" and "12 disagreements" while mixing book and
  non-book plies (the 4 plies after the book ended have no comparison). Corrected here: the statistics
  are over the **16 book plies only**, and the four post-book plies are excluded rather than counted as
  disagreements.

## Files
`book_quality.py`, `out/book_quality.json` (per-ply rows with both moves and both scores), `stamps.txt`.

## Last command output

```
$ ls
book_quality.py
out
REPORT_job13.md
stamps.txt
```
