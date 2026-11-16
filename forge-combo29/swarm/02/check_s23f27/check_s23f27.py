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
    def wait(pref,n0=0,to=180):
        dl=time.time()+to
        while time.time()<dl:
            if any(l.startswith(pref) for l in L[n0:]): return True
            time.sleep(0.001)
        return False
    s('uci');wait('uciok')
    for o in PC20: s(o)
    s('isready');wait('readyok')
    s('position fen '+fen);s('isready');n=len(L);wait('readyok',n)
    n=len(L);s(go);wait('bestmove',n,180)
    seg=list(L[n:]); bm=[l for l in seg if l.startswith('bestmove')]
    nodes=None
    for l in seg:
        if l.startswith('info depth'):
            m=re.search(r' nodes (\d+)',l)
            if m: nodes=int(m.group(1))
    s('quit')
    try:p.wait(timeout=10)
    except:p.kill()
    return (bm[-1].split()[1] if bm else None), nodes
# my six FOUND-MATE tie boards (gap 0, all mate 1) and three QUIET tie boards (gap 0, no mate)
MATE_TIES=[
 "4k3/8/4K3/8/8/8/8/R6R w - - 0 1",
 "k7/8/1K6/8/8/8/8/3R3R w - - 0 1",
 "k7/8/1K6/8/8/8/8/3Q3R w - - 0 1",
 "k7/8/1K6/8/8/8/7Q/7R w - - 0 1",
 "1k6/8/2K5/8/8/8/Q7/Q7 w - - 0 1",
 "1k6/8/3K4/8/8/8/8/R6Q w - - 0 1",
]
QUIET_TIES=[
 "4k3/8/8/3p4/3P4/8/8/4K3 w - - 0 1",
 "4k3/8/8/2p1p3/2P1P3/8/8/4K3 w - - 0 1",
 "4k3/8/3n4/8/8/3N4/8/4K3 w - - 0 1",
]
BUDGETS=[5000,20000,50000,200000]
print("SEAT 23's FRAME: does a gap-0 position change its move across BUDGETS?")
print("Their rule says a small margin is unstable. If found mates never change at gap 0, that is an exception.")
print()
print("| kind | position | moves across N=%s | stable? |" % BUDGETS)
print("|---|---|---|---|")
rows={}
for kind,boards in (("mate-tie(0cp)",MATE_TIES),("quiet-tie(0cp)",QUIET_TIES)):
    for fen in boards:
        ms=[]
        for n in BUDGETS:
            b,_=run(fen,'go nodes %d'%n)
            ms.append(b)
        stable=len(set(ms))==1
        rows.setdefault(kind,[]).append({"fen":fen,"moves":ms,"stable":stable})
        print("| %s | `%s` | %s | %s |" % (kind,fen,ms,"STABLE" if stable else "**CHANGED**"))
json.dump(rows,open('/tmp/s23.json','w'),indent=1)
print()
for kind,r in rows.items():
    print("%-14s stable %d of %d" % (kind,sum(1 for x in r if x['stable']),len(r)))
