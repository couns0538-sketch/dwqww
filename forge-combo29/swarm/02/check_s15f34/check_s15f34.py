import subprocess,threading,time,os,re,json,statistics
PC20=["setoption name Threads value 1","setoption name Hash value 16","setoption name LmrQuietBase value 93",
"setoption name LmrQuietDivisor value 205","setoption name LmrNoisyBase value 13","setoption name LmrNoisyDivisor value 333",
"setoption name LmrHistoryDivisor value 5643","setoption name NullMoveBase value 5","setoption name LmpBase value 8",
"setoption name HistoryPruneMultiplier value 2220","setoption name HistoryBonusQuadratic value 24",
"setoption name HistoryBonusLinear value 54","setoption name HistoryBonusMax value 2212",
"setoption name SingularDepth value 6","setoption name IirDepth value 2","setoption name NonPawnCorrection value true",
"setoption name CuckooRep value true","setoption name HistRework value 2","setoption name TtPruneV2 value true",
"setoption name CorrHistV2 value true","setoption name MateAlphaGuard value true","setoption name OwnBook value false"]
def run(fen,go):
    env={k:v for k,v in os.environ.items() if k not in ('ASAN_OPTIONS','UBSAN_OPTIONS')}
    p=subprocess.Popen(['/agent/repos/pc/forge-combo29/build-pc/forge'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,env=env)
    L=[];threading.Thread(target=lambda:[L.append(l.rstrip()) for l in p.stdout],daemon=True).start()
    def s(x):
        try: p.stdin.write(x+'\n'); p.stdin.flush()
        except: pass
    def wait(pref,n0=0,to=120):
        dl=time.time()+to
        while time.time()<dl:
            if any(l.startswith(pref) for l in L[n0:]): return True
            time.sleep(0.0005)
        return False
    s('uci');wait('uciok')
    for o in PC20: s(o)
    s('isready');wait('readyok')
    s('position fen '+fen);s('isready');n=len(L);wait('readyok',n)
    n=len(L);t0=time.monotonic();s(go);wait('bestmove',n,300);el=(time.monotonic()-t0)*1000
    seg=list(L[n:]); s('quit')
    try:p.wait(timeout=10)
    except:p.kill()
    nodes=None;depth=None
    for l in seg:
        if l.startswith('info depth'):
            m=re.search(r' nodes (\d+)',l)
            if m: nodes=int(m.group(1))
            md=re.match(r'info depth (\d+)',l)
            if md: depth=int(md.group(1))
    return {"wall_ms":round(el,0),"nodes":nodes,"depth":depth}
# a middlegame with real search work, and a trivially-finished endgame to reproduce their depth-64 case
BOARDS={
 "mid_sharp":"r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
 "mid_quiet":"r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
 "end_trivial":"6k1/8/6K1/8/8/8/8/5R2 w - - 0 1",
}
print("| board | movetime | wall ms | % of slice | nodes | depth |")
print("|---|---|---|---|---|---|")
rows=[]
for name,fen in BOARDS.items():
    for mt in (1000,3000):
        rs=[run(fen,'go movetime %d'%mt) for _ in range(2)]
        r=rs[0]
        rows.append({"board":name,"mt":mt,**r,"reps":rs})
        print("| %s | %d | %s | %s | %s | %s |" % (name,mt,[x['wall_ms'] for x in rs],
          ["%.1f%%"%(100*x['wall_ms']/mt) for x in rs],[x['nodes'] for x in rs],[x['depth'] for x in rs]))
json.dump(rows,open('/tmp/s15.json','w'),indent=1)
print()
print("Key checks:")
print(" 1. do the WORKING boards honour ~99-100% of both slices?")
for name in ("mid_sharp","mid_quiet"):
    for mt in (1000,3000):
        r=[x for x in rows if x['board']==name and x['mt']==mt][0]
        pct=100*r['wall_ms']/mt
        print("    %-10s %d ms -> %5.1f%%  %s" % (name,mt,pct,"honoured" if 95<=pct<=110 else "NOT honoured"))
print(" 2. does the trivial endgame hit depth 64 with IDENTICAL nodes at both slices?")
e=[x for x in rows if x['board']=='end_trivial']
for x in e: print("    %d ms -> nodes %s depth %s" % (x['mt'],x['nodes'],x['depth']))
print("    identical nodes: %s ; both depth 64: %s" % (
  len({x['nodes'] for x in e})==1, all(x['depth']==64 for x in e)))
