import io

p = 'FINDINGS.md'
s = io.open(p, encoding='utf-8').read()

# Each edit inserts the correction pointer IMMEDIATELY BEFORE the row's evidence cell, i.e. at the end of its prose.
# This is the adjacency discipline applied to the findings table itself: a superseded row must say so in its own row.
EDITS = [
    ("LIMIT: one rich-board cell, one build, `go depth 10`. | `cd forge-combo29/swarm/23/job55",
     "**SUPERSEDED IN SCOPE BY 23-F122, IN ITS OWN WORDS HERE SO A READER OF THIS ROW IS NOT MISLED: the bail is NOT narrower "
     "than threefold. The F112 board turned out never to have been a threefold \u2014 my occurrence key omitted the castling "
     "field, and its cycle moved a rook off a1, destroying a right. Every castling-neutral fixture with three true "
     "occurrences bails (23-F122, validated 9 of 9).** LIMIT: one rich-board cell, one build, `go depth 10`. | `cd forge-combo29/swarm/23/job55"),

    ("build only. | `cd forge-combo29/swarm/23/job56 && python3 ladder.py`",
     "**SUPERSEDED BY 23-F122 IN ITS INTERPRETATION: castling rights are not a \"conditioner\" inside the engine \u2014 the field is part of "
     "POSITION IDENTITY, and a cycle that disturbs it is simply not a repetition. The one-board contrast measured here is real and is "
     "explained by 23-F122, not by a quirk.** LIMIT: one board for the clean contrast plus three middlegame boards. | `cd forge-combo29/swarm/23/job56 && python3 ladder.py`"),

    ("strongest-looking result. | `cd forge-combo29/swarm/23/job68`",
     "**PARTLY CLOSED BY 23-F177: a second round found two more fixtures and one is a DIFFERENT mate type (a direct queen mate "
     "`e1e8`), taking the forfeit to 6 of 6 across two types \u2014 so the \"one structure\" limit in this row is now narrower than "
     "written, though breadth beyond two types remains untested.** strongest-looking result. | `cd forge-combo29/swarm/23/job68`"),

    ("match this move is never played \u2014 the cost lands on analysis, other GUIs and human play. | `cd forge-combo29/swarm/23/job23`",
     "**RE-VERIFIED UNDER THE CORRECTED VALIDATOR BY 23-F129 (fixture rebuilt with a castling-neutral cycle, `counted=3 "
     "python-chess=3`): the base still plays `e6e5` at 0 nodes and it loses 6 pawns of material by static exchange, so this "
     "row's finding stands on the corrected gate rather than on luck.** | `cd forge-combo29/swarm/23/job23`"),

    ("terial count backs them independently: black holds only a king). | `cd forge-combo29/swarm/23/job46`",
     "**QUALIFIED BY 23-F130: \"the base's unsearched move throws away the mate\" is a ONE-FIXTURE result \u2014 on 23-F60's second "
     "board the repair is material-NEUTRAL, so the general sentence was withdrawn in place (see also 23-F177's six-of-six on "
     "BACK-RANK and direct-queen mates, which is a different and narrower claim).** | `cd forge-combo29/swarm/23/job46`"),
]

for old, new in EDITS:
    assert old in s, "insertion point not found: %r" % old[:70]
    s = s.replace(old, new, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print("five superseded rows now carry their correction inline")
