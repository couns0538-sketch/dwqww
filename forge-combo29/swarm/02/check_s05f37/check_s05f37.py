import subprocess,threading,time,os,re,json,statistics
PC20=["setoption name Threads value 1","setoption name Hash value 16","setoption name LmrQuietBase value 93",
"setoption name LmrQuietDivisor value 205","setoption name LmrNoisyBase value 13","setoption name LmrNoisyDivisor value 333",
"setoption name LmrHistoryDivisor value 5643","setoption name NullMoveBase value 5","setoption name LmpBase value 8",
"setoption name HistoryPruneMultiplier value 2220","setoption name HistoryBonusQuadratic value 24",
"setoption name HistoryBonusLinear value 54","setoption name HistoryBonusMax value 2212",
"setoption name SingularDepth value 6","setoption name IirDepth value 2","setoption name NonPawnCorrection value true",
"setoption name CuckooRep value true","setoption name HistRework value 2","setoption name TtPruneV2 value true",
"setoption name CorrHistV2 value true","setoption name MateAlphaGuard value true","setoption name OwnBook value false"]
SP="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
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
    n=len(L);t0=time.monotonic();s(go);wait('bestmove',n,150);el=(time.monotonic()-t0)*1000
    seg=list(L[n:]); s('quit')
    try:p.wait(timeout=5)
    except:p.kill()
    d=[int(m.group(1)) for l in seg for m in [re.match(r'info depth (\d+)',l)] if m]
    nodes=[int(m.group(1)) for l in seg for m in [re.search(r' nodes (\d+)',l)] if m]
    return round(el,0),(max(d) if d else 0),(nodes[-1] if nodes else None)
res={}
print("| go command | wall ms | depth | nodes |")
print("|---|---|---|---|")
for go in ('go wtime 6000 btime 6000 winc 60 binc 60','go movetime 6000','go depth 19'):
    rs=[run(SP,go) for _ in range(2)]
    print("| `%s` | %s | %s | %s |" % (go,[r[0] for r in rs],[r[1] for r in rs],[r[2] for r in rs]))
    res[go]=rs
json.dump(res,open('/tmp/c37.json','w'),indent=1)
