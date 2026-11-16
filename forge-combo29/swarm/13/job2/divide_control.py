#!/usr/bin/env python3
"""Control for my own divide check: prove it catches a COMPENSATING error.

This is the lesson of seat 06's S-F22 applied to my area: a total can be exactly right while the
per-root-move counts are wrong, if one move is over-counted and another under-counted by the same
amount. A checker that only compares totals passes such an error; mine must not.

Method: take real engine divide output, find a position with >= 2 root moves, add +1 to one root
move's count and -1 to another's (so the TOTAL is unchanged), then run the same comparison logic.
My checker must report a difference at that position.
"""
import chess, re, subprocess, sys

EXE=sys.argv[1]; TSV=sys.argv[2]
rows=[l.rstrip("\n").split("\t") for l in open(TSV) if not l.startswith("#") and l.strip()]
fens=[r[1] for r in rows]

def engine_divide(fen_list):
    proc=subprocess.run([EXE],input="".join("position fen %s\ngo perft 2\n"%f for f in fen_list)+"quit\n",
                        text=True,capture_output=True,timeout=600)
    blocks=[];cur=None
    for ln in proc.stdout.splitlines():
        m=re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$",ln)
        if m:
            if cur is None: cur={}
            cur[m.group(1)]=int(m.group(2)); continue
        if ln.startswith("nodes "):
            blocks.append(cur if cur is not None else {}); cur=None
    return blocks

# pick a position with at least 2 root moves and a real divide
idx=None
for i,f in enumerate(fens[:60]):
    b=chess.Board(f)
    if b.legal_moves.count()>=2: idx=i; break
sub=[fens[idx]]
eng=engine_divide(sub)[0]
moves=sorted(eng)
print("control position",idx,fens[idx])
print("real divide:",{m:eng[m] for m in moves})

# python-chess reference divide equals the engine's (already established in VERDICT.md)
ref={}
b=chess.Board(fens[idx])
def perft(bd,d):
    if d==0: return 1
    n=0
    for m in bd.legal_moves:
        bd.push(m); n+=perft(bd,d-1); bd.pop()
    return n
for m in b.legal_moves:
    b.push(m); ref[m.uci()]=perft(b,1); b.pop()

def compare(engd,refd):
    miss=set(refd)-set(engd); extra=set(engd)-set(refd)
    wrong=[m for m in set(refd)&set(engd) if refd[m]!=engd[m]]
    return miss,extra,wrong

print()
print("A) real engine output vs python-chess:")
miss,extra,wrong=compare(eng,ref)
print("   missing",miss,"extra",extra,"wrong",wrong,
      "-> totals equal:",sum(eng.values())==sum(ref.values()))
print("   RESULT:", "PASS (no difference)" if not(miss or extra or wrong) else "DIFFERENCE")

# plant a compensating error: +1 on one move, -1 on another (skip any that would go negative)
a,c=moves[0],moves[1]
mut=dict(eng)
if eng[c]>0:
    mut[a]=eng[a]+1; mut[c]=eng[c]-1
    print()
    print("B) COMPENSATING error planted: %s +1, %s -1"%(a,c))
    print("   mutated:",{m:mut[m] for m in moves})
    print("   total unchanged?",sum(mut.values())==sum(eng.values()),
          "(%d vs %d)"%(sum(mut.values()),sum(eng.values())))
    miss,extra,wrong=compare(mut,ref)
    print("   divide check sees: wrong moves =",wrong)
    print("   RESULT:", "CAUGHT by the divide check" if wrong else "MISSED - checker would pass a wrong engine")
