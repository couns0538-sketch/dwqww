import subprocess,queue,threading,time,re,chess
def ask(exe, fenline, depth=10, extra=""):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    q=queue.Queue(); out=[]
    threading.Thread(target=lambda: ([q.put(l.rstrip()) for l in p.stdout], q.put(None)),daemon=True).start()
    p.stdin.write(f"uci\nsetoption name OwnBook value false\n{fenline}\nisready\ngo depth {depth}{extra}\n"); p.stdin.flush()
    end=time.monotonic()+120
    while time.monotonic()<end:
        try:
            l=q.get(timeout=0.3)
            if l is None: break
            out.append(l)
            if l.startswith("bestmove"): break
        except queue.Empty: continue
    p.stdin.write("quit\n"); p.stdin.flush()
    try: p.stdin.close()
    except Exception: pass
    try: p.wait(timeout=15)
    except Exception: p.kill()
    infos=[x for x in out if x.startswith("info depth")]
    score=nodes=None
    if infos:
        s=re.search(r"score (cp|mate) (-?\d+)",infos[-1]); score=(s.group(1),int(s.group(2))) if s else None
        n=re.search(r" nodes (\d+)",infos[-1]); nodes=int(n.group(1)) if n else None
    return score,nodes
W="4k3/8/8/8/8/8/4P3/R3K3 w - - 0 40"
seq7="a1a2 e8d8 a2a1 d8e8 a1a2 e8d8 a2a1"
for exe,label in [("/home/ubuntu/build/release/forge","base"),("/home/ubuntu/build/pc_r15/forge","PC r15")]:
    print(f"== {label}")
    # (a) the repeated child, WHITE (winning) to move - should be ~+1100, engine says?
    print(f"   a) d8e8 (creates 3-fold, WHITE to move, win for white): {ask(exe,f'position fen {W} moves {seq7}','10',' searchmoves d8e8')}")
    # (b) the SAME board at clock 8 with NO repetition history: truth
    print(f"   b) same board, no repetition history                 : {ask(exe,'position fen 4k3/8/8/8/8/8/4P3/R3K3 w - - 8 44')}")
    # (c) a DIFFERENT black move (d8c8) which does not create a repetition
    print(f"   c) d8c8 (no repetition)                              : {ask(exe,f'position fen {W} moves {seq7}','10',' searchmoves d8c8')}")
