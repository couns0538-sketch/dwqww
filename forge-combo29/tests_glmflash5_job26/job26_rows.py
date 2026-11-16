import subprocess, sys, threading, queue
DEF_STYLE=[("Threads","1"),("Hash","16")]
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
SETS=[("S14",S14),
("S14+fine-identity",S14+[("LmrFine","1"),("LmrFineHistory","0"),("LmrRoundF","0")]),
("T1",S14+[("LmrFine","1"),("LmrFineHistory","1")]),
("T2",S14+[("LmrFine","1"),("LmrFineHistory","1"),("LmrRoundF","0")])]
class Refusal(Exception): pass
def reader(proc,q):
    for line in proc.stdout: q.put(line.rstrip("\n"))
    q.put(None)
class Eng:
    def __init__(self,exe,opts=()):
        self.p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
        self.q=queue.Queue(); threading.Thread(target=reader,args=(self.p,self.q),daemon=True).start()
        self.refusals=[]
        for n,v in list(opts)+DEF_STYLE:
            self.send(f"setoption name {n} value {v}"); self.send("isready"); self.until("readyok")
        if self.refusals: raise Refusal(self.refusals)
        self.send("uci"); self.until("uciok")
    def send(self,s): self.p.stdin.write(s+"\n"); self.p.stdin.flush()
    def until(self,tok):
        while True:
            line=self.q.get(timeout=180)
            if line is None: raise RuntimeError("died")
            if "unknown option" in line or "invalid value" in line:
                self.refusals.append(line); raise Refusal(self.refusals)
            if line.startswith(tok): return line
            if line.startswith("info") and " nodes " in line: self.last_nodes=line
    def search(self,fen):
        self.send("ucinewgame"); self.send("isready"); self.until("readyok")
        self.send(f"position fen {fen}"); self.send("isready"); self.until("readyok")
        self.last_nodes=""; self.send("go depth 12"); self.until("bestmove")
        t=self.last_nodes.split(); return t[t.index("nodes")+1] if "nodes" in t else "?"
n=int(sys.argv[2]); fens=[l.strip() for l in open(sys.argv[1])][:n]
out=[];summary=[]
for tag,opts in SETS:
    try: e=Eng("/tmp/forgebuild_bfine/forge",opts)
    except Refusal as r: summary.append(f"{tag}: DRIVER STOPPED on refusal: {r.args[0]}"); continue
    nodes=[]
    for i,f in enumerate(fens,1):
        v=e.search(f); nodes.append(int(v)); out.append(f"{tag}|{i}|{v}")
    e.p.kill(); summary.append(f"{tag}: first3={nodes[:3]} sum_all{n}={sum(nodes)}")
print("\n".join(summary))
open(sys.argv[3],"w").write("\n".join(out)+"\n")
open(sys.argv[4],"w").write("\n".join(summary)+"\n")
