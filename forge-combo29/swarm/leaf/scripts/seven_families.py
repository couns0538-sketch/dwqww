import sys, json
sys.path.insert(0,'.')
from family_lib import ask, board_after, OUT
import chess, re

exe = sys.argv[1]
outfile = sys.argv[2]

def record(fam, name, posline, expect_fn, expect_doc):
    r = ask(exe, posline)
    b = board_after(posline)
    m1 = []
    for m in list(b.legal_moves):
        b.push(m)
        if b.is_checkmate(): m1.append(m.uci())
        b.pop()
    bm_mates = None
    if r["bestmove"]:
        try:
            b.push_uci(r["bestmove"]); bm_mates = b.is_checkmate(); b.pop()
        except ValueError: bm_mates = "bad"
    ok = expect_fn(r, m1, bm_mates)
    OUT.append({"family": fam, "case": name, "expect": expect_doc, "posline": posline,
                "result": r, "oracle_mate_in_1": m1, "bestmove_mates": bm_mates, "pass": ok})
    print(f"{'PASS' if ok else 'FAIL':4} {fam:26} {name:20} bm={str(r['bestmove']):6} "
          f"score={str(r['score']):9} nodes={str(r['nodes']):>7} oracle_m1={m1}")
    return ok

# F1 halfmove limit, exactly one mate -> must find it
record("F1 fifty-move, one mate", "hm100_mate1",
       "position fen 6k1/5ppp/8/8/8/8/8/R5NK w - - 100 40",
       lambda r,m1,bm: bm is True and r["score"]=="mate 1",
       "mate 1 and the printed move mates")
# F2 two distinct mates -> must find one
record("F2 fifty-move, two mates", "hm100_mate2ways",
       "position fen 6k1/5ppp/8/8/8/8/8/1R4NK w - - 100 40",
       lambda r,m1,bm: bm is True and len(m1)>=1,
       "some mate")
# F3 NEAR MISS: stalemate available, not mate -> must NOT cancel
record("F3 near-miss stalemate", "hm100_stalemate",
       "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 100 60",
       lambda r,m1,bm: r["score"]=="cp 0",
       "genuine draw (stalemate/claim), not a mate")
# F4 NEAR MISS: non-mating check only
record("F4 near-miss check", "hm99_check_not_mate",
       "position fen 6k1/8/5PPP/8/8/8/8/R6K b - - 99 40",
       lambda r,m1,bm: r["score"]=="mate -1" and bm is False,
       "the true mate -1 (mating move at ply 2, so not the printed move)")
# F5 NEAR MISS: mate in two at hm100 -> still adjudicated (stated limit)
record("F5 near-miss mate-in-2", "hm100_mate_in_2",
       "position fen 6k1/8/6K1/8/8/8/8/R7 b - - 100 40",
       lambda r,m1,bm: r["score"]=="cp 0" and r["nodes"]==0,
       "still adjudicated at the root guard")
# F6 insufficient material -> must stay 0
record("F6 insufficient material", "kbk",
       "position fen 4k3/8/8/8/8/8/8/2B1K3 w - - 0 1",
       lambda r,m1,bm: r["score"]=="cp 0",
       "cp 0")
# F7 threefold root that ALSO has a mate-in-1
record("F7 threefold + mate", "rep3_mate",
       "position fen 6k1/5ppp/8/8/8/8/8/R5NK w - - 0 1 moves g1f3 g8h8 f3g1 h8g8 g1f3 g8h8 f3g1 h8g8",
       lambda r,m1,bm: bm is True,
       "the mate is played")

json.dump(OUT, open(outfile,"w"), indent=1)
bad = [o for o in OUT if not o["pass"]]
print(f"\n{len(OUT)-len(bad)}/{len(OUT)} pass")
sys.exit(1 if bad else 0)
