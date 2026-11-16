import subprocess,threading,time,os,re,json
PC20=["setoption name Threads value 1","setoption name Hash value 16","setoption name LmrQuietBase value 93",
"setoption name LmrQuietDivisor value 205","setoption name LmrNoisyBase value 13","setoption name LmrNoisyDivisor value 333",
"setoption name LmrHistoryDivisor value 5643","setoption name NullMoveBase value 5","setoption name LmpBase value 8",
"setoption name HistoryPruneMultiplier value 2220","setoption name HistoryBonusQuadratic value 24",
"setoption name HistoryBonusLinear value 54","setoption name HistoryBonusMax value 2212",
"setoption name SingularDepth value 6","setoption name IirDepth value 2","setoption name NonPawnCorrection value true",
"setoption name CuckooRep value true","setoption name HistRework value 2","setoption name TtPruneV2 value true",
"setoption name CorrHistV2 value true","setoption name MateAlphaGuard value true","setoption name OwnBook value false"]
def run(fen,go,exe):
    env={k:v for k,v in os.environ.items() if k not in ('ASAN_OPTIONS','UBSAN_OPTIONS')}
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,env=env)
    L=[];threading.Thread(target=lambda:[L.append(l.rstrip()) for l in p.stdout],daemon=True).start()
    def s(x):
        try: p.stdin.write(x+'\n'); p.stdin.flush()
        except: pass
    def wait(pref,n0=0,to=120):
        dl=time.time()+to
        while time.time()<dl:
            if any(l.startswith(pref) for l in L[n0:]): return True
            time.sleep(0.001)
        return False
    s('uci');wait('uciok')
    for o in PC20 if 'pc' in exe else PC20[:16]: s(o)
    s('isready');wait('readyok')
    s('position fen '+fen);s('isready');n=len(L);wait('readyok',n)
    n=len(L);s(go);wait('bestmove',n,200)
    seg=list(L[n:]); bm=[l for l in seg if l.startswith('bestmove')]
    zero=len([l for l in seg if l.startswith('info depth') and ' nodes 0 ' in l])
    dl=len([l for l in seg if l.startswith('info depth')])
    s('quit')
    try:p.wait(timeout=10)
    except:p.kill()
    return {"bestmove":(bm[-1].split()[1] if bm else None),"depth_lines":dl,"zero_node_lines":zero}
SP="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
out={}
for label,exe in (("pc_r15_pc20","/agent/repos/pc/forge-combo29/build-pc/forge"),
                  ("base_s14","/agent/repos/base/forge-combo29/build/forge")):
    out[label]=[dict(mv=mv or "(none)", **run(SP,("go depth 5 searchmoves %s"%mv).strip(),exe))
                for mv in ("zzzz","e2e5","a1a8","","e2e4")]
json.dump(out,open('/tmp/s17.json','w'),indent=1)
print("| build | searchmoves | bestmove | depth lines | zero-node lines |")
print("|---|---|---|---|---|")
for lbl,rows in out.items():
    for r in rows:
        print("| %s | `%s` | %s | %d | %d |" % (lbl,r['mv'],r['bestmove'],r['depth_lines'],r['zero_node_lines']))
