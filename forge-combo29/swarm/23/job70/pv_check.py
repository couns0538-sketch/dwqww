#!/usr/bin/env python3
"""pv_check.py : the decisive test of 'hangs a piece'. Play the base's 0-node move, then ask
the PC build what WHITE does about it. If the PV is a capture of a piece that the base's move
left in place, the loss is a FAILURE TO ANSWER, not a newly created hang."""
import re, subprocess, json, chess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*? pv (.+)$")
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
def search(fen,depth=16):
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush();names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in OPTS:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: raise RuntimeError("STOP "+nm)
        p.stdin.write(line+"\n");p.stdin.flush();p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go depth %d\n"%depth);p.stdin.flush()
    last=None
    while True:
        l=p.stdout.readline()
        if not l: break
        m=INFO.match(l.strip())
        if m: last=(m.group(2),int(m.group(3)),m.group(4).split())
        if l.strip().startswith("bestmove"): break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except Exception: p.kill()
    return last
BASE={"1":"e6e5","2":"a5a4","3":"c4c5","5":"g3g4","6":"c6c5"}
TABLE={"1":0,"2":1,"3":2,"5":4,"6":5}
games=json.load(open('../job30/games.json'))
print("After the base's 0-node move, the PC build's PV as the OPPONENT (depth 16).")
print("A first move that CAPTURES a piece left in place = failure to answer an existing threat.\n")
for g,bmv in BASE.items():
    gd=games[TABLE[g]]; moves=gd[1]; fen=gd[2][2]
    b=chess.Board(); [b.push_uci(m) for m in moves]
    assert b.fen()==fen, (g,b.fen(),fen)
    c=b.copy(); c.push_uci(bmv)
    sc=search(c.fen())
    pv=sc[2]; first=pv[0]
    m=chess.Move.from_uci(first)
    cap=c.piece_at(m.to_square)
    # was that piece attacked already at the ROOT (before the base's move)?
    was_attacked = b.is_attacked_by(b.turn, m.to_square) if cap else None
    print("g%s base %-5s -> opponent PV: %-8s score=%s%-4d captures %s   [same piece attacked at root? %s]"
          %(g,bmv,first,sc[0],sc[1], cap.symbol().upper() if cap else "nothing", was_attacked))
    print("     pv: %s"%(" ".join(pv[:8])))
