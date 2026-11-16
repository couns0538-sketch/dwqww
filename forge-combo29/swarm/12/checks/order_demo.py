import chess, subprocess, queue, threading, time, re
KIWI="r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
START="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
def engine_order(exe, fen):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    q=queue.Queue(); out=[]
    threading.Thread(target=lambda: ([q.put(l.rstrip()) for l in p.stdout], q.put(None)),daemon=True).start()
    p.stdin.write(f"uci\nsetoption name OwnBook value false\nposition fen {fen}\nisready\ngo perft 1\n"); p.stdin.flush()
    end=time.monotonic()+60
    while time.monotonic()<end:
        try:
            l=q.get(timeout=0.2)
            if l is None: break
            out.append(l)
            if l.startswith("nodes "): break
        except queue.Empty: continue
    p.stdin.write("quit\n"); p.stdin.flush()
    try: p.stdin.close()
    except Exception: pass
    try: p.wait(timeout=10)
    except Exception: p.kill()
    return [l.split(":")[0] for l in out if re.match(r"^[a-h][1-8][a-h][1-8][qrbn]?: \d+$", l)]
def fabricated_move(exe, fen):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    q=queue.Queue(); out=[]
    threading.Thread(target=lambda: ([q.put(l.rstrip()) for l in p.stdout], q.put(None)),daemon=True).start()
    p.stdin.write(f"uci\nsetoption name OwnBook value false\nposition fen {fen}\nisready\ngo depth 12\nquit\n"); p.stdin.flush()
    end=time.monotonic()+30
    while time.monotonic()<end:
        try:
            l=q.get(timeout=0.2)
            if l is None: break
            out.append(l)
            if l.startswith("bestmove"): break
        except queue.Empty: continue
    try: p.stdin.close()
    except Exception: pass
    try: p.wait(timeout=10)
    except Exception: p.kill()
    bm=[l for l in out if l.startswith("bestmove")]
    infos=[l for l in out if l.startswith("info depth")]
    return (bm[-1].split()[1] if bm else None), len(infos)
exe='/home/ubuntu/build/pc_r15/forge'
print(f"{'position':10} {'engine order[0]':16} {'python sorted[0]':17} {'agree':6} {'fabricated move':16} {'matches engine':14} {'matches python':13}")
for name,fen in (("startpos",START),("kiwipete",KIWI)):
    eo=engine_order(exe,fen); ps=sorted(m.uci() for m in chess.Board(fen).legal_moves)[0]
    fm,ni=fabricated_move(exe,fen)
    print(f"{name:10} {eo[0]:16} {ps:17} {str(eo[0]==ps):6} {str(fm):16} {str(fm==eo[0]):14} {str(fm==ps):13}")
