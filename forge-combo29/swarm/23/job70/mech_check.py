#!/usr/bin/env python3
"""mech_check.py : checks the MECHANISM sentence, not just the verb.

verb_check.py (23-F221) would have PASSED my incorrect "walks the queen away" story, because
it only tested that the queen was attacked before the move. The mechanism claim is a
different predicate: what the RECAPTURE takes back. This checks that, and would fail the
wrong story.

Exits nonzero if the recapture balance differs from the report's claim, or if the
known-answer control does not come out the opposite way."""
import sys, chess
V={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
def adv(bd): return sum(V[p.piece_type]*(1 if p.color==chess.WHITE else -1) for p in bd.piece_map().values())
fails=[]
def check(name,got,want):
    ok=got==want
    print("  %-64s got=%-14s want=%-10s %s"%(name,got,want,"OK" if ok else "**FAIL**"))
    if not ok: fails.append(name)

def recapture_balance(b, mv):
    """net White advantage after: black plays mv, white captures the queen, black recaptures."""
    c=b.copy(); c.push_uci(mv)
    cap=None
    for m in c.legal_moves:
        if c.is_capture(m) and c.piece_at(m.to_square).piece_type==chess.QUEEN:
            cap=m; break
    if cap is None: return None,None,None
    d=c.copy(); d.push(cap)
    recs=[x for x in d.legal_moves if x.to_square==cap.to_square]
    if not recs: return adv(d),cap.uci(),None
    best=None
    for r in recs:
        e=d.copy(); e.push(r); a=adv(e)
        if best is None or a<best[0]: best=(a,r.uci(),e.piece_at(cap.to_square).piece_type)
    return best[0],cap.uci(),best[2]

FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
b=chess.Board(FEN)
print("A. THE MECHANISM CLAIM (23-F223): recapture balance, base vs repair, on 23-F60's board")
net_cap,cap,recap = recapture_balance(b,"e6e5")
check("bail e6e5: White nets +6 (queen 9 - knight 3)", net_cap, 6)
check("bail e6e5: White captures with the KNIGHT a4b6", cap, "a4b6")
check("bail e6e5: Black recaptures with a PAWN", recap, chess.PAWN)
net_pc,capp,recapp = recapture_balance(b,"b6b4")
check("repair b6b4: White nets 0 (queen 9 - queen 9, a TRADE)", net_pc, 0)
check("repair b6b4: Black recaptures with a BISHOP", recapp, chess.BISHOP)

print("\nB. THIS CHECK WOULD FAIL THE WRONG STORY. If the repair 'walked the queen away', it")
print("   would not be capturable at all. Assert the opposite of my earlier claim:")
c=b.copy(); c.push_uci("b6b4")
check("after repair b6b4 the queen IS still capturable (so 'walked away' is FALSE)",
      any(c.is_capture(m) and c.piece_at(m.to_square).piece_type==chess.QUEEN for m in c.legal_moves), True)
check("...and it is on b4, still attacked by Qd2", c.piece_at(chess.B4).piece_type==chess.QUEEN, True)

print("\nC. KNOWN-ANSWER CONTROL: a board where a queen really IS walked away.")
# Qd8 in check? no: simple - black queen a8, and a move to a safe square exists
ctl=chess.Board("q3k3/8/8/8/8/8/8/4K2Q b - - 0 1")
before=ctl.is_attacked_by(chess.WHITE,chess.A8)
check("control: black queen a8 IS attacked by White before it moves", before, True)
g=ctl.copy(); g.push_uci("a8a1")
check("control: after Qa8-a1 the queen is NOT capturable (a genuine walk-away)",
      any(g.is_capture(m) and g.piece_at(m.to_square) and g.piece_at(m.to_square).piece_type==chess.QUEEN
          for m in g.legal_moves), False)

print("\nVERDICT:", "PASS" if not fails else "FAIL (%d)"%len(fails))
sys.exit(0 if not fails else 1)
