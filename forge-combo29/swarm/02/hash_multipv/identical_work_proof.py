import subprocess,threading,time,os,re
EXE='/agent/repos/base/forge-combo29/build/forge'
def run(hv,mp):
    env={k:v for k,v in os.environ.items() if k not in ('ASAN_OPTIONS','UBSAN_OPTIONS')}
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,env=env)
    L=[];threading.Thread(target=lambda:[L.append(l.rstrip()) for l in p.stdout],daemon=True).start()
    def s(x):
        try: p.stdin.write(x+'\n'); p.stdin.flush()
        except: pass
    def wait(pref,n0=0,to=400):
        dl=time.time()+to
        while time.time()<dl:
            if any(l.startswith(pref) for l in L[n0:]): return True
            time.sleep(0.001)
        return False
    s('uci');wait('uciok');s('setoption name Hash value %d'%hv)
    s('setoption name MultiPV value %d'%mp);s('isready');wait('readyok')
    s('position startpos');s('isready');n=len(L);wait('readyok',n)
    n=len(L);s('go depth 4');wait('bestmove',n,400)
    seg=list(L[n:])
    s('quit')
    try:p.wait(timeout=5)
    except:p.kill()
    d4=[l for l in seg if l.startswith('info depth 4 ')]
    return d4
for hv in (16,2048):
    d4=run(hv,5)
    print("Hash %d, MultiPV 5, depth 4 -> %d info lines at depth 4" % (hv,len(d4)))
    mult=[l for l in d4 if ' multipv ' in l]
    print("   lines carrying 'multipv':",len(mult))
    for l in d4[:6]: print("   ",l[:110])
    print()
