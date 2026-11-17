import io

p = 'FINDINGS.md'
lines = io.open(p, encoding='utf-8').read().split('\n')

# (row id, phrase that must appear in that row, the correction sentence to insert before its evidence cell)
INLINE = {
    '23-F112': ("LIMIT: one rich-board cell",
                "**SUPERSEDED IN SCOPE BY 23-F122 \u2014 the bail is NOT narrower than threefold; this board turned out never to have "
                "been a threefold, because my occurrence key omitted the castling field and its cycle moved a rook off a1.** "),
    '23-F114': ("LIMIT: one board for the clean contrast",
                "**SUPERSEDED IN INTERPRETATION BY 23-F122 \u2014 castling is not a \"conditioner\" in the engine; the field is part of "
                "position identity, so a cycle that disturbs it is simply not a repetition.** "),
    '23-F175': ("breadth beyond two types remains untested",
                ""),  # already carries F177 inline
    '23-F60': ("the cost lands on analysis, other GUIs and human play",
               "**RE-VERIFIED UNDER THE CORRECTED VALIDATOR BY 23-F129 (castling-neutral cycle, counted=3 python-chess=3): the base "
               "still plays `e6e5` at 0 nodes and loses 6 pawns by static exchange, so this stands on the corrected gate.** "),
    '23-F96': ("black holds only a king",
               "**QUALIFIED BY 23-F130 \u2014 \"the unsearched move throws away the mate\" is a ONE-FIXTURE result; on 23-F60's second "
               "board the repair is material-neutral, so the general sentence was withdrawn in place.** "),
}

changed = 0
for i, line in enumerate(lines):
    if not line.startswith('| 23-'):
        continue
    rid = line.split('|')[1].strip()
    if rid not in INLINE:
        continue
    marker, insert = INLINE[rid]
    if not insert:
        continue
    if marker not in line:
        print("SKIP %s: marker %r not in row" % (rid, marker[:40]))
        continue
    cells = line.split('|')
    # cells: ['', ' id ', ' area ', ' prose ', ' evidence ', ' status ', '']
    if len(cells) < 6:
        print("SKIP %s: only %d cells" % (rid, len(cells)))
        continue
    cells[3] = cells[3] + insert
    lines[i] = '|'.join(cells)
    changed += 1
    print("updated %s" % rid)

io.open(p, 'w', encoding='utf-8').write('\n'.join(lines))
print("rows changed: %d" % changed)
