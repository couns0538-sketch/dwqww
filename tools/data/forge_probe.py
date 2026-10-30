"""Bounded, logged IPC to the unchanged Forge offline data probe.
IDEA_SOURCE: this project's native probe protocol and explicit evidence preservation.
"""
from __future__ import annotations
import concurrent.futures, gzip, hashlib, json, os, queue, re, subprocess, threading, time
from pathlib import Path

class ProbeError(RuntimeError): pass

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

class ProbeClient:
    def __init__(self, exe, nodes, hash_mb=1, workdir=None, timeout=60):
        if nodes<1 or hash_mb<1 or timeout<=0:raise ValueError('positive budget/hash/timeout required')
        self.exe=Path(exe).resolve(strict=True);self.timeout=timeout;self.count=0;self.cpu_ns=0
        self.lock=threading.Lock();self.done=threading.Event();self.queue=queue.Queue(maxsize=2);self.files=[]
        self.directory=Path(workdir) if workdir is not None else None
        self.requests=None;self.responses=None;self.stderr=None
        if self.directory is not None:
            self.directory.mkdir(parents=True,exist_ok=False)
            self.requests=gzip.GzipFile(filename=str(self.directory/'requests.tsv.gz'),mode='xb',mtime=0,compresslevel=1)
            self.responses=gzip.GzipFile(filename=str(self.directory/'responses.jsonl.gz'),mode='xb',mtime=0,compresslevel=1)
            self.stderr=open(self.directory/'stderr.bin','xb');self.files=[self.requests,self.responses,self.stderr]
        self.command=[str(self.exe),'--nodes',str(nodes),'--hash-mb',str(hash_mb)]
        self.binary_sha256=sha256(self.exe)
        flags=(subprocess.IDLE_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) if os.name=='nt' else 0
        try:self.process=subprocess.Popen(self.command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr or subprocess.DEVNULL,creationflags=flags)
        except BaseException:
            for f in self.files:f.close()
            raise
        self.reader=threading.Thread(target=self._read,daemon=True);self.reader.start()
    def _enqueue(self,item):
        while not self.done.is_set():
            try:self.queue.put(item,timeout=.1);return
            except queue.Full:pass
    def _read(self):
        try:
            while not self.done.is_set():
                raw=self.process.stdout.readline(131073)
                if not raw:break
                if self.responses:self.responses.write(raw)
                if len(raw)>131072 or not raw.endswith(b'\n'):
                    self._enqueue(ProbeError('overlong or incomplete native response'));break
                self._enqueue(raw)
        except BaseException as e:self._enqueue(ProbeError('native stdout read: '+repr(e)))
        finally:self._enqueue(None)
    def query(self,fen,op='analyze',request_id=None):
        if op not in ('inspect','analyze','filter'):raise ValueError('unknown operation')
        if not isinstance(fen,str) or '\t' in fen or '\n' in fen or '\r' in fen or len(fen)>512:raise ValueError('invalid request FEN framing')
        with self.lock:
            ident=str(self.count if request_id is None else request_id)
            if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}',ident):raise ValueError('invalid request id')
            raw=(ident+'\t'+op+'\t'+fen+'\n').encode('ascii')
            if self.requests:self.requests.write(raw)
            try:self.process.stdin.write(raw);self.process.stdin.flush()
            except (BrokenPipeError,OSError) as e:raise ProbeError('native input closed') from e
            try:line=self.queue.get(timeout=self.timeout)
            except queue.Empty as e:
                self.process.terminate();raise ProbeError('native request timeout; only owned child terminated') from e
            if line is None:raise ProbeError('native EOF before response')
            if isinstance(line,BaseException):raise line
            try:result=json.loads(line)
            except (ValueError,UnicodeError) as e:raise ProbeError('invalid native JSON') from e
            if not isinstance(result,dict) or str(result.get('id'))!=ident:raise ProbeError('native response id/type mismatch')
            if result.get('ok') is not True:raise ProbeError('native rejected '+ident+': '+str(result.get('error')))
            self.count+=1;self.cpu_ns+=int(result.get('cpu_ns',0))
            return result
    def close(self):
        if getattr(self,'closed',False):return
        self.closed=True
        try:
            if self.process.stdin:self.process.stdin.close()
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:self.process.terminate();self.process.wait(timeout=5)
        finally:
            self.done.set();self.reader.join(timeout=2)
            if self.process.stdout:self.process.stdout.close()
            for f in self.files:f.close()
            if self.directory:
                record={'argv':self.command,'binary_sha256':self.binary_sha256,'returncode':self.process.poll(),'successful_requests':self.count,'reported_query_cpu_ns':self.cpu_ns,'binary_unchanged':sha256(self.exe)==self.binary_sha256}
                (self.directory/'process.json').write_text(json.dumps(record,indent=2)+'\n')
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

class ProbePool:
    def __init__(self,exe,nodes,workers=1,workdir=None,hash_mb=1,timeout=60):
        if not 1<=workers<=32:raise ValueError('workers must be1..32')
        self.clients=[];self.executor=None
        try:
            for i in range(workers):self.clients.append(ProbeClient(exe,nodes,hash_mb,None if workdir is None else Path(workdir)/f'worker-{i}',timeout))
            self.executor=concurrent.futures.ThreadPoolExecutor(max_workers=workers)
        except BaseException:
            for c in self.clients:c.close()
            raise
    def map(self,items,op='filter'):
        items=list(items);n=len(self.clients)
        def run(k):return [(i,self.clients[k].query(fen,op,ident)) for i,(ident,fen) in enumerate(items) if i%n==k]
        futures=[self.executor.submit(run,k) for k in range(n)];answer=[None]*len(items)
        for f in futures:
            for i,value in f.result():answer[i]=value
        return answer
    def close(self):
        if self.executor:self.executor.shutdown(wait=True);self.executor=None
        for c in self.clients:c.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
