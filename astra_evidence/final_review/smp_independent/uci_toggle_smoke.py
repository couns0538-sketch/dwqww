# IDEA_SOURCE: Owner A2; verify UCI option changes safely stop active Forge search.
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,queue,re,subprocess,threading,time
root=Path('/tmp/astra-review-smp')
exe=Path('/tmp/forge-astra-build-j5fix-20261029/forge')
results={'start':datetime.now(timezone.utc).isoformat(),'binary':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'configurations':[],'claim':'UCI lifecycle smoke only; no real tablebase files or race detector'}
legal={'a2a3','a2a4','b2b3','b2b4','c2c3','c2c4','d2d3','d2d4','e2e3','e2e4','f2f3','f2f4','g2g3','g2g4','h2h3','h2h4','b1a3','b1c3','g1f3','g1h3'}
for threads in (2,3):
    q=queue.Queue();stdout=[];stderr=[];stdin=[]
    p=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    def read_stdout():
        for line in iter(p.stdout.readline,b''):
            stdout.append(line);q.put(line.decode('utf-8',errors='replace').strip())
        q.put(None)
    def read_stderr():
        for line in iter(p.stderr.readline,b''):stderr.append(line)
    readers=[threading.Thread(target=read_stdout,daemon=True),threading.Thread(target=read_stderr,daemon=True)]
    for r in readers:r.start()
    def send(line):
        data=(line+'\n').encode();stdin.append(data);p.stdin.write(data);p.stdin.flush()
    def until(predicate,timeout=10):
        stop=time.monotonic()+timeout
        while True:
            line=q.get(timeout=max(.01,stop-time.monotonic()))
            if line is None:raise AssertionError('unexpected EOF')
            if 'info string invalid' in line or 'info string unknown' in line:raise AssertionError(line)
            if predicate(line):return line
            if time.monotonic()>stop:raise TimeoutError('UCI deadline exceeded')
    def best():
        line=until(lambda s:s.startswith('bestmove '))
        assert line.split()[1] in legal,line
        return line
    row={'threads':threads,'moves':[]}
    try:
        send('uci');until(lambda s:s=='uciok')
        for name,value in [('OwnBook','false'),('Hash','16'),('Threads',str(threads)),('SmpBestThread','true'),('SmpProtectProvenScore','false')]:
            send(f'setoption name {name} value {value}')
        send('isready');until(lambda s:s=='readyok')
        send('position startpos');send('go infinite')
        until(lambda s:re.match(r'info depth ([3-9]|\d{2,}) ',s))
        send('setoption name SmpProtectProvenScore value true')
        row['moves'].append(best())
        send('isready');until(lambda s:s=='readyok')
        send('position startpos');send('go depth 5')
        row['moves'].append(best())
        send('position startpos');send('go infinite')
        until(lambda s:re.match(r'info depth ([3-9]|\d{2,}) ',s))
        send('setoption name SmpProtectProvenScore value false')
        row['moves'].append(best())
        send('isready');until(lambda s:s=='readyok')
        send('quit');row['returncode']=p.wait(timeout=10)
        assert row['returncode']==0
        row['verdict']='PASS'
    finally:
        if p.poll() is None:
            try:send('quit');p.wait(timeout=5)
            except Exception:p.terminate();p.wait(timeout=5)
        for r in readers:r.join(timeout=1)
        for kind,data in [('stdin',stdin),('stdout',stdout),('stderr',stderr)]:
            (root/f'uci_threads{threads}.{kind}').write_bytes(b''.join(data))
    assert not stderr,stderr
    results['configurations'].append(row)
assert hashlib.sha256(exe.read_bytes()).hexdigest()==results['sha256']
results['verdict']='PASS: two thread configurations; four active-search option toggles; six legal bestmove replies; ready/quit clean.'
(root/'uci_toggle_results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
