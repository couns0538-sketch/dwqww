#!/usr/bin/env python3
"""ttprune_alone.py -- does TtPruneV2 ALONE reproduce the depth-14 quality signal PC20 showed?

Seat 29's 29-F50 / 29-N34: on 30 positions from R_2911 at depth 14, 27/30 agree and of the 3
disagreements, judged under the NEUTRAL S14 regime at depth 17, ALL THREE favour S14 (one by a full
move of mate distance). They mark it a SIGNAL, not a result, and flag that depth 14 is where the PC
actually plays.

My check: same design, on 40 R_2911 positions at depth 14 (bigger n than their 30), and judge each
disagreement by scoring BOTH moves under S14 at a deeper fixed depth. Report the tally and, for mate
cases, the mate distance -- never converting mate to centipawns (07-C44).

Neutral regime = S14 for the judging search, per their recipe, so PC20 is not judging itself.
"""
import json, os, queue, re, subprocess, sys, threading
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["TtPruneV2 value true","OwnBook value false"]   # TtPruneV2 ALONE (plus OwnBook off, which no analysis search uses)

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=1200):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def search(exe,fen,go,opts):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    r=R(p.stdout)
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def drain():
        while True:
            l=r.get(30)
            if l is None: raise RuntimeError("no readyok")
            if l.strip()=="readyok": return
    send("uci")
    while True:
        l=r.get(30)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1","OwnBook value false"]+opts:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(go)
    score=None;best=None
    while True:
        l=r.get(1200)
        if l is None: break
        if l.startswith("info depth"):
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: score=(m.group(1),int(m.group(2)))
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"score":score,"best":best}

def better(a,b):
    """Which of two scores is better for the side to move? Mate beats cp; more mate wins; higher cp wins."""
    if a is None or b is None: return "?"
    ka,va=a; kb,vb=b
    if ka=="mate" and kb=="mate":
        # mate N > 0: side to move mates in N -> smaller N better. mate N < 0: being mated -> larger N better.
        if va>0 and vb>0: return "A" if va<vb else ("B" if vb<va else "tie")
        if va<0 and vb<0: return "A" if va>vb else ("B" if vb>va else "tie")
        return "A" if va>0 else "B"
    if ka=="mate": return "A" if va>0 else "B"
    if kb=="mate": return "B" if vb>0 else "A"
    return "A" if va>vb else ("B" if vb>va else "tie")

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    n=int(sys.argv[3]) if len(sys.argv)>3 else 40
    os.makedirs(outdir,exist_ok=True)
    fens=[]
    for line in open('/tmp/R_2911.fens',encoding='utf-8'):
        p=line.split()
        if len(p)>=4:
            f=" ".join(p[:6]) if len(p)>=6 else " ".join(p[:4])+" 0 1"
            try: chess.Board(f)
            except ValueError: continue
            fens.append(f)
    sample=fens[:n]
    print(f"R_2911: {len(fens)} positions; using the first {len(sample)}",flush=True)
    agree=0; rows=[]
    for i,fen in enumerate(sample):
        a=search(exe,fen,"go depth 14",S14)
        b=search(exe,fen,"go depth 14",PC20)
        same = a["best"]==b["best"]
        if same:
            agree+=1
            rows.append({"i":i,"fen":fen,"agree":True,"s14":a,"ttprune":b})
        else:
            # neutral judgement: score BOTH moves under S14 at depth 17
            sa=search(exe,fen,f"go depth 17 searchmoves {a['best']}",S14)
            sb=search(exe,fen,f"go depth 17 searchmoves {b['best']}",S14)
            who=better(sa["score"],sb["score"])
            rows.append({"i":i,"fen":fen,"agree":False,"s14":a,"ttprune":b,
                         "judge_s14move":sa,"judge_ttprunemove":sb,"favours":who})
            print(f"  DISAGREE #{i}: S14 {a['best']} -> {sa['score']}; PC20 {b['best']} -> {sb['score']}"
                  f"  favours {who}",flush=True)
        if (i+1)%10==0: print(f"  ...{i+1}/{len(sample)} agree {agree}",flush=True)
    json.dump(rows,open(os.path.join(outdir,"ttprune_alone.json"),"w"),indent=1)
    d=[r for r in rows if not r["agree"]]
    tally={"A":0,"B":0,"tie":0,"?":0}
    for r in d: tally[r["favours"]]+=1
    print()
    print(f"agreement: {agree}/{len(rows)} = {100.0*agree/len(rows):.1f} %")
    print(f"disagreements: {len(d)}")
    print(f"  favouring S14 (A): {tally['A']}")
    print(f"  favouring TtPruneV2 (B): {tally['B']}")
    print(f"  ties: {tally['tie']}   unreadable: {tally['?']}")
    print(f"DIFFERENCE from 07-C61: PC20 replaced by S14+TtPruneV2 alone, which carries 85% of the node reduction.")

if __name__=="__main__": main()
