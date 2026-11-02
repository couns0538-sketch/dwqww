"""Bounded native UCI correctness checks; only touches subprocesses it creates."""
import argparse, hashlib, json, os, pathlib, queue, re, subprocess, sys, threading, time
sys.path.insert(0,'D:/a10/pydeps')
import chess, psutil

PINS={11:312866,13:862329,16:3024920,20:12389307,22:34048354}
KIWI='r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
class Engine:
    def __init__(self,exe,log,threads=1,on=False,core=2):
        self.log=open(log,'w'); self.q=queue.Queue(); self.p=None; self.reader=None
        def pump():
            for s in self.p.stdout:
                self.log.write(s); self.log.flush(); self.q.put(s.strip())
            self.q.put(None)
        try:
            self.p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                    text=True,creationflags=subprocess.IDLE_PRIORITY_CLASS)
            psutil.Process(self.p.pid).cpu_affinity([core] if threads==1 else [2,3])
            self.reader=threading.Thread(target=pump,daemon=True); self.reader.start()
            self.send('uci'); lines=self.wait(r'^uciok$')
            self.options='\n'.join(lines)
            for n,v in [('Threads',str(threads)),('Hash','16'),('OwnBook','false')]: self.send(f'setoption name {n} value {v}')
            if on:
                if 'option name NNUEWideOutput type check default false' not in self.options: raise RuntimeError('missing option')
                self.send('setoption name NNUEWideOutput value true')
            self.send('isready'); self.wait('^readyok$')
        except BaseException:
            self.abort(); raise
    def send(self,s):
        self.log.write('> '+s+'\n'); self.log.flush()
        self.p.stdin.write(s+'\n'); self.p.stdin.flush()
    def wait(self,rx,timeout=300):
        end=time.monotonic()+timeout; lines=[]
        while True:
            remaining=end-time.monotonic()
            if remaining<=0: raise TimeoutError('absolute UCI deadline waiting for '+rx)
            s=self.q.get(timeout=remaining)
            if s is None: raise RuntimeError('engine exited: '+str(self.p.poll()))
            if 'ERROR: AddressSanitizer' in s or 'runtime error:' in s or 'SUMMARY: UndefinedBehaviorSanitizer' in s:
                raise RuntimeError('sanitizer report: '+s)
            lines.append(s)
            if re.search(rx,s): return lines
    def close(self):
        if self.p.poll() is None:
            self.send('quit')
            try: self.p.wait(timeout=15)
            except subprocess.TimeoutExpired: self.p.kill(); self.p.wait(); raise
        self.reader.join(timeout=5)
        if self.reader.is_alive(): raise RuntimeError('engine output drain did not complete')
        self.log.close()
        if self.p.returncode != 0: raise RuntimeError('engine exit '+str(self.p.returncode))
        transcript=pathlib.Path(self.log.name).read_text()
        if re.search(r'ERROR: AddressSanitizer|runtime error:|SUMMARY: (?:UndefinedBehaviorSanitizer|AddressSanitizer)',transcript):
            raise RuntimeError('sanitizer report in complete transcript')
    def abort(self):
        if self.p is not None and self.p.poll() is None: self.p.kill(); self.p.wait()
        if self.reader is not None: self.reader.join(timeout=5)
        self.log.close()
    def move(self,b,command):
        self.send('position fen '+b.fen()); started=time.perf_counter(); self.send(command)
        lines=self.wait('^bestmove ')
        self.last_move_seconds=time.perf_counter()-started
        token=lines[-1].split()[1]
        move=chess.Move.from_uci(token)
        if move not in b.legal_moves: raise RuntimeError('illegal bestmove '+token+' '+b.fen())
        return move

def validate_start(board):
    if not board.is_valid() or board.is_game_over():
        raise RuntimeError('invalid or terminal selfplay start: '+board.fen())

def smoke_move(engine, board):
    move=engine.move(board,'go movetime 100')
    # Preregistered smoke allowance:100ms requested,500ms observed maximum.
    if engine.last_move_seconds > .5:
        raise RuntimeError('smoke time allowance exceeded: '+str(engine.last_move_seconds))
    return move
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['pins','smoke','selfplay'])
    ap.add_argument('--threads',type=int,choices=[1],required=True); ap.add_argument('exe'); ap.add_argument('out'); ap.add_argument('--on',action='store_true')
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False)
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS); psutil.Process().cpu_affinity([3])
    result={'exe':str(pathlib.Path(args.exe).resolve()),'sha256':hashlib.sha256(pathlib.Path(args.exe).read_bytes()).hexdigest(),
            'mode':args.mode,'on':args.on,'checks':[],'status':'RUNNING'}
    e=None
    try:
        if args.mode=='pins':
            e=Engine(args.exe,out/'uci.log',on=args.on)
            for d,n in PINS.items():
                e.send(f'bench {d}'); s=e.wait(rf'bench depth {d} nodes ')[-1]
                actual=int(re.search(r'nodes (\d+)',s)[1])
                if actual!=n: raise RuntimeError(('bench pin',d,actual,n))
                result['checks'].append({'depth':d,'nodes':actual}); print(s,flush=True)
            for name,fen,n in [('startpos',chess.STARTING_FEN,4865609),('kiwipete',KIWI,193690690)]:
                e.send('position fen '+fen); e.send('go perft 5'); s=e.wait(r'^nodes \d+')[-1]
                actual=int(s.split()[1])
                if actual!=n: raise RuntimeError(('perft pin',name,actual,n))
                result['checks'].append({'perft':name,'nodes':actual}); print(name,s,flush=True)
            e.close(); e=None
        elif args.mode=='smoke':
            fens=[chess.STARTING_FEN,KIWI,'8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1']
            for threads in [1]:
                e=Engine(args.exe,out/f't{threads}.log',threads=threads,on=args.on)
                for fen in fens:
                    b=chess.Board(fen)
                    for _ in range(4):
                        if b.is_game_over(): break
                        move=smoke_move(e,b); result['checks'].append({'threads':threads,'fen':b.fen(),'bestmove':move.uci(),'elapsed_seconds':e.last_move_seconds,'maximum_seconds':.5}); b.push(move)
                e.close(); e=None
        else:
            fens=pathlib.Path('D:/a10/inputs/fens_12k.txt').read_text().splitlines()
            e=Engine(args.exe,out/'selfplay.log',on=args.on)
            for game in range(8):
                e.send('ucinewgame'); e.send('isready'); e.wait('^readyok$')
                b=chess.Board(fens[game*1499]); validate_start(b); record={'game':game,'start':b.fen(),'moves':[]}
                for ply in range(80):
                    if b.is_game_over(): break
                    move=e.move(b,'go nodes 1000'); record['moves'].append(move.uci()); b.push(move)
                if not record['moves']: raise RuntimeError('no searched legal plies')
                result['checks'].append(record); print('game',game,'legal plies',len(record['moves']),flush=True)
            e.close(); e=None
        result['status']='PASS'
    except BaseException as error:
        result['status']='FAIL'; result['error']=repr(error)
        if e: e.abort()
        raise
    finally: (out/'result.json').write_text(json.dumps(result,indent=2))
    print('PASS',args.mode,'on',args.on,flush=True)
if __name__=='__main__': main()
