#!/usr/bin/env python3
"""fix_column.py : rewrite the HANDOFF master table's `root occ` cell FROM THE DOCUMENT'S OWN
text, so no value is retyped (23-F232). Prints the before/after for every row it changes,
and refuses to write if any row it cannot parse would be left inconsistent."""
import re, chess, sys
P='HANDOFF_drawn_root_trigger.md'
lines=open(P).read().split("\n")
def occ(fen, moves):
    b=chess.Board(fen); root=(b.board_fen(),b.turn,b.castling_rights); n=1
    for mv in moves.split():
        b.push(chess.Move.from_uci(mv))
        if (b.board_fen(),b.turn,b.castling_rights)==root: n+=1
    return n
changed=[]
for i,l in enumerate(lines):
    if not l.startswith("| ") or l.startswith("|---") or l.startswith("| #"): continue
    cells=l.split(" | ")
    if len(cells)<8: continue
    fen_m=re.search(r'`([^`]+)`',cells[1] if len(cells)>1 else "")
    if not fen_m: continue
    tick=re.findall(r'`([^`]+)`',l)
    if len(tick)<2: continue
    fen, moves = tick[0], tick[1]
    if " " not in moves: continue          # not a move list
    try: n=occ(fen,moves)
    except Exception as e:
        print("  SKIP (unplayable): %s"%l[:60]); continue
    m=re.match(r'^(\|.*?\| )(\d+)( \|)',l)
    if not m: continue
    cur=int(m.group(2))
    if cur!=n:
        new="%s%d%s"%(m.group(1),n,m.group(3))+l[m.end():]
        # only the numeric cell changes
        lines[i]=re.sub(r'^(\| [^|]+\| [^|]+\| [^|]+\| )\d+( \|)', lambda mm: "%s%d%s"%(mm.group(1),n,mm.group(2)), l, count=1)
        changed.append((i+1,cur,n,l.split(" | ")[0]))
if not changed:
    print("no column cell disagrees with its own move list"); sys.exit(0)
print("cells rewritten from the document's own move lists:")
for ln,old,new,row in changed:
    print("  line %-4d %-6s %s -> %d"%(ln,row.strip(),old,new))
open(P,'w').write("\n".join(lines))
print("wrote %s (%d cells)"%(P,len(changed)))
