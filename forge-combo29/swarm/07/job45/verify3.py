import sys, json, queue, re, subprocess, threading
sys.path.insert(0,'.')
from midbudget import PC20
class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=900):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None
def run(exe,fen,go):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    r=R(p.stdout)
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def drain():
        while True:
            l=r.get()
            if l is None: raise RuntimeError("x")
            if l.strip()=="readyok": return
    send("uci")
    while True:
        l=r.get(60)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(go)
    best=None;score=None
    while True:
        l=r.get(900)
        if l is None: break
        if l.startswith("info depth") and " score " in l:
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: score=f"{m.group(1)} {m.group(2)}"
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=60)
    except subprocess.TimeoutExpired: p.kill()
    return best,score
rows=json.load(open('raw/midbudget.json'))
exe="/agent/repos/pcbase/forge-combo29/build-pc/forge"
for i in (15,94,118):
    r=[x for x in rows if x['i']==i][0]
    print(f"position #{i}  {r['fen']}")
    print(f"  moves: n20={r['n20']} n50={r['n50']} n100={r['n100']} n250={r['n250']}")
    # score BOTH the n100 move and the n250 move at the large budget
    for mv in {r['n100'], r['n250']}:
        b,s=run(exe,r['fen'],f"go nodes 250000 searchmoves {mv}")
        print(f"    scored at 250000: {mv} -> {s}")
    print()
