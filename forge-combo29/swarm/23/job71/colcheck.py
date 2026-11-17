#!/usr/bin/env python3
"""colcheck.py : verify the HANDOFF master table's `root occ` column against the key that
column's own header declares (placement + side + castling, NOT halfmove).

Reads every value OUT of the document - no FEN or count is retyped here (23-F232: the
previous version hardcoded the table, so it reported the old values even after the file
was fixed). Rows that abbreviate with "same" are resolved against the row they refer to.
Exits nonzero if any cell disagrees."""
import re, sys, chess
P='/agent/repos/dwqww/forge-combo29/swarm/23/HANDOFF_drawn_root_trigger.md'
lines=open(P).read().split("\n")
def occ(fen,moves):
    b=chess.Board(fen); root=(b.board_fen(),b.turn,b.castling_rights); n=1
    for mv in moves.split():
        b.push(chess.Move.from_uci(mv))
        if (b.board_fen(),b.turn,b.castling_rights)==root: n+=1
    return n
start=next(i for i,l in enumerate(lines) if l.startswith("| # | FEN | full move list"))
end=next(i for i,l in enumerate(lines[start+2:],start+2) if not l.startswith("|"))
print("master table: lines %d-%d (%d rows)"%(start+3,end,end-start-2))
last_fen=None; last_moves=None; bad=[]; rows=0
for i,l in enumerate(lines[start:end],start):
    if not l.startswith("| ") or l.startswith("|---") or l.startswith("| #"): continue
    tick=re.findall(r'`([^`]+)`',l)
    m=re.match(r'^(\| [^|]+\| )([^|]+)\| ([^|]+)\| (\d+) \|',l)
    if not m: continue
    fen_cell, mv_cell, stated = m.group(2).strip(), m.group(3).strip(), int(m.group(4))
    # resolve the FEN
    if "castling field" in fen_cell and last_fen:
        # "same, castling field -> `-`": same placement, castling rights removed
        parts=last_fen.split(" ")
        parts[2]="-"
        fen=" ".join(parts)
    elif "same" in fen_cell and last_fen: fen=last_fen
    elif tick and re.match(r'^[rnbqkpRNBQKP1-8/]+ [bw] ',tick[0]): fen=tick[0]; last_fen=fen
    elif "…" in l and last_fen:
        # abbreviated: "… w KQkq - 13 7" - substitute the tail
        tail=re.search(r'`…\s*([^`]+)`',l)
        # "… w KQkq - 13 7" supplies side+castling+ep+counters, so take ONLY the placement
        fen=(last_fen.split(" ")[0]+" "+tail.group(1).strip()) if tail else last_fen
    else:
        fen=last_fen
    # resolve the move list
    if "same" in mv_cell and last_moves: moves=last_moves
    elif len(tick)>=2 and " " in tick[1] and not tick[1].startswith("go"): moves=tick[1]; last_moves=moves
    else: moves=last_moves
    if not fen or not moves: continue
    try: n=occ(fen,moves)
    except Exception as e:
        print("  line %-4d UNPLAYABLE (%s)  %s"%(i+1,type(e).__name__,l[:48])); bad.append(i+1); continue
    rows+=1
    ok = (n==stated)
    if not ok:
        print("  line %-4d stated %d, measured %d   %s"%(i+1,stated,n,l.split(" | ")[1].strip()))
        bad.append(i+1)
print()
print("rows checked: %d | cells disagreeing with their own move list: %d"%(rows,len(bad)))
if bad:
    print("VERDICT: FAIL - root occ column is stale in the rows above")
    sys.exit(1)
print("VERDICT: PASS - every root occ cell matches the key its header declares")
sys.exit(0)
