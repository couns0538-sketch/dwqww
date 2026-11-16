#!/usr/bin/env python3
"""Job 3, P4 test: what share of Board::make_move's self cost is the checkers recomputation?
Reads a callgrind_annotate --auto=yes text file; exact instruction counts, immune to machine load."""
import re, sys
txt = open(sys.argv[1]).read()
pat = re.compile(r'^\s*([0-9][0-9,]*)\s+\(\s*([0-9.]+)%\)\s{2,}(.*)$')
start = txt.find('make_move(const Move& move, Undo& undo) {')
end = txt.find('void Board::unmake_move', start)
if start < 0 or end < 0:
    raise SystemExit("ABORT: make_move region not found in the annotation file -- refusing to report a share")
region = txt[start:end]
CK = ('checkers_ =', 'attacks::pawn(them, their_king)', 'attacks::knight(their_king)',
      'attacks::king(their_king)', 'their_king = king_square', 'occ_now = occupied()',
      'our_queens = pieces', 'attacks::bishop(their_king', 'attacks::rook(their_king')
tot = ck = 0
found = 0
for line in region.splitlines():
    m = pat.match(line)
    if not m:
        continue
    src = m.group(3).strip()
    if src.startswith('=>'):
        continue
    v = int(m.group(1).replace(',', ''))
    tot += v
    if any(k in src for k in CK):
        ck += v
        found += 1
if found == 0:
    raise SystemExit("ABORT: no checkers line matched -- the keyword list is wrong, share would be a fake 0")
MAKE_MOVE_SELF = 147453413   # from callgrind's own top-self table for this symbol
print(f"make_move region self instructions: {tot:,}")
print(f"checkers block:                     {ck:,}  ({found} lines matched)")
print(f"share of make_move's self cost:     {100*ck/MAKE_MOVE_SELF:.1f}%")
print("P4 predicted >= 40 %, killed under 20 %  ->", "P4 SURVIVES" if ck/MAKE_MOVE_SELF >= 0.40 else "P4 KILLED")
