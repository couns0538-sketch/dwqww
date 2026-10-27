"""S12 bounded alias-stream transport, adapted from own-project qualified S11.
Only payload protocol changed. Ownership, sealed input, gzip chunk retention,
EOF bounds and byte-for-byte comparison retain the original S11 transport.
No compiler/engine invocation at import; caller requires a new native grant.
"""
from pathlib import Path
import gzip,hashlib,importlib.util,json,os,re,selectors,shutil,struct,subprocess,time
OWNED=Path('/workspace/forge-pack24-20261026/S08/forge_sol_S08_build_window_subreaper_20261026.py')
OWNED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
HEADER=struct.Struct('<IIIIQQI')
RECORD_BYTES=2068
ORACLE_SHA='704dadabbe5a7320312e2760b6ed0729217b195951a3693dd9ae7aa40d5c15f3'

def parse_header(raw,positions,child_limit):
    if len(raw)!=HEADER.size:raise ValueError('truncated or excessive binary header')
    magic,version,hidden,width,count,children,mxcsr=HEADER.unpack(raw)
    if (magic,version,hidden,width,count,children)!=(0x4b323146,1,256,RECORD_BYTES,positions,child_limit):raise ValueError('S12 alias binary source/count/format header differs')
    if mxcsr==0xffffffff or mxcsr&~0x0000ffc0:raise ValueError('normally compiled driver FP header missing/invalid')
    return dict(magic=magic,version=version,hidden=hidden,record_bytes=width,positions=count,child_limit=children,MXCSR_masked=mxcsr)


def parse_summary(raw,positions,child_limit,expected_mode):
    try:value=json.loads(raw.decode('ascii'))
    except Exception as e:raise ValueError('missing/malformed actual alias summary') from e
    counters={'refreshes','updates','zero_dirty_edges','copies_avoided','alias_hits','evaluations'}
    keys={'positions','record_bytes','header_bytes','mode','implementation_present','worker_constructions',
          'history_clears_after_construction','transition_roots','oracle_root_refreshes','selected_nulls',
          'legal_children','nulls','verified_evaluations','fresh_mismatches','state_mismatches'}|counters
    if type(value) is not dict or set(value)!=keys or any(type(x) is not int or not 0<=x<2**64 for x in value.values()):
        raise ValueError('alias summary schema/counters invalid')
    wanted={'positions':positions,'record_bytes':RECORD_BYTES,'header_bytes':36,'mode':expected_mode,
            'implementation_present':int(expected_mode!=0),'worker_constructions':1,'history_clears_after_construction':0,
            'transition_roots':child_limit,'oracle_root_refreshes':positions,'fresh_mismatches':0,'state_mismatches':0}
    if any(value[k]!=v for k,v in wanted.items()):raise ValueError('actual alias binding/state/coverage differs')
    if not (0<value['selected_nulls']<=positions and value['nulls']>=value['selected_nulls'] and value['legal_children']>0
            and value['verified_evaluations']>=positions*2):raise ValueError('actual transition/evaluation coverage missing')
    if expected_mode==0:
        if any(value[k] for k in counters):raise ValueError('pristine baseline invents unavailable counters')
    else:
        if value['evaluations']!=value['verified_evaluations']:raise ValueError('actual Worker evaluation count differs')
        if expected_mode==1 and (value['copies_avoided'] or value['alias_hits']):raise ValueError('OFF claims alias work')
        if expected_mode==2 and not (value['copies_avoided']>0 and value['alias_hits']>0
                                    and value['copies_avoided']==value['zero_dirty_edges']):raise ValueError('ON alias path not exercised')
    return value


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()



def verify_sealed_input(fd,expected_size,expected_sha):
    import fcntl
    # Same Linux UAPI fallback as the preserved S09 sealer; Python may omit names.
    seals=fcntl.fcntl(fd,getattr(fcntl,'F_GET_SEALS',1034))
    required=0x000f  # F_SEAL_SEAL|SHRINK|GROW|WRITE, bits pinned by Linux UAPI.
    if seals&required!=required or os.fstat(fd).st_size!=expected_size:raise ValueError('immutable sealed corpus fd required')
    h=hashlib.sha256();offset=0
    while offset<expected_size:
        chunk=os.pread(fd,min(1048576,expected_size-offset),offset)
        if not chunk:raise ValueError('truncated sealed corpus')
        h.update(chunk);offset+=len(chunk)
    if h.hexdigest()!=expected_sha:raise ValueError('sealed corpus bytes differ from original manifest')
    return {'bytes':offset,'sha256':expected_sha,'seals':seals}



class ChunkedGzip:
    """Retain one original stdout stream at fixed record boundaries, never rerun it."""
    def __init__(self,out,label,positions,child_limit,chunk_records=10000):
        if not 1<=chunk_records<=10000:raise ValueError('chunk record bound must be1..10000')
        self.out=Path(out);self.label=label;self.positions=positions;self.child_limit=child_limit;self.chunk_records=chunk_records
        self.rows=[];self.file=None;self.gz=None;self.current=0;self.offset=0;self.current_hash=None;self.global_hash=hashlib.sha256();self.closed=False
        self.index_path=self.out/(label+'.stdout.chunks.json');self.ledger=self.out/(label+'.stdout.chunkledger.jsonl')
        if self.index_path.exists() or self.ledger.exists() or list(self.out.glob(label+'.stdout.part*.gz')):raise FileExistsError('chunk output must be new')
    def __enter__(self):return self
    def _open(self):
        self.path=self.out/(self.label+'.stdout.part'+str(len(self.rows)).zfill(4)+'.gz');self.file=self.path.open('xb')
        self.gz=gzip.GzipFile(filename='',mode='wb',fileobj=self.file,mtime=0,compresslevel=1);self.current=0;self.current_hash=hashlib.sha256()
    def _finish(self):
        if self.file is None:return
        self.gz.close();self.file.flush();os.fsync(self.file.fileno());self.file.close()
        head=min(36,self.current) if not self.rows else 0;body=max(0,self.current-head)
        row={'index':len(self.rows),'path':self.path.name,'raw_offset':self.offset,'raw_bytes':self.current,'raw_sha256':self.current_hash.hexdigest(),'gzip_bytes':self.path.stat().st_size,'gzip_sha256':sha(self.path),'first_record':len(self.rows)*self.chunk_records,'record_count':body//RECORD_BYTES,'header_bytes':head,'trailing_bytes':body%RECORD_BYTES}
        self.rows.append(row);self.offset+=self.current;self.file=None;self.gz=None
        with self.ledger.open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
    def write(self,data):
        if self.closed:raise ValueError('closed original stream writer')
        self.global_hash.update(data);view=memoryview(data)
        while view:
            if self.file is None:self._open()
            bound=self.chunk_records*RECORD_BYTES+(36 if not self.rows else 0);take=min(len(view),bound-self.current)
            piece=view[:take];self.gz.write(piece);self.current_hash.update(piece);self.current+=take;view=view[take:]
            if self.current==bound:self._finish()
    def close(self):
        if self.closed:return
        self._finish();self.closed=True
        value={'schema':'forge.S12.original_alias_stream_chunks.v1','positions':self.positions,'child_limit':self.child_limit,'records_per_chunk':self.chunk_records,'header_bytes':36,'record_bytes':RECORD_BYTES,'expected_raw_bytes':36+self.positions*RECORD_BYTES,'raw_bytes':self.offset,'raw_sha256':self.global_hash.hexdigest(),'complete_length':self.offset==36+self.positions*RECORD_BYTES,'gzip_level':1,'gzip_mtime':0,'chunks':self.rows}
        with self.index_path.open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    def __exit__(self,*unused):self.close()



def validate_chunk_index(path,positions,child_limit,stop=None,capture=None):
    reason=stop() if stop else None
    if reason:raise RuntimeError('root chunk-index stop: '+str(reason))
    path=Path(path);manifest_raw=path.read_bytes();value=json.loads(manifest_raw);records=value.get('records_per_chunk')
    if capture is not None:
        stored=capture.get('captures',{}).get('chunks',{})
        if (capture.get('status')!='PASS_CAPTURE' or stored.get('path')!=str(path) or stored.get('bytes')!=len(manifest_raw)
            or stored.get('sha256')!=hashlib.sha256(manifest_raw).hexdigest() or capture.get('raw_stdout_bytes')!=36+positions*RECORD_BYTES
            or capture.get('raw_stdout_sha256')!=value.get('raw_sha256')):raise ValueError('manifest or original bytes differ from captured arm identity')
    if (value.get('schema')!='forge.S12.original_alias_stream_chunks.v1' or type(records) is not int or not 1<=records<=10000
        or value.get('positions')!=positions or value.get('child_limit')!=child_limit or value.get('header_bytes')!=36 or value.get('record_bytes')!=RECORD_BYTES
        or value.get('complete_length') is not True or value.get('raw_bytes')!=36+positions*RECORD_BYTES or value.get('expected_raw_bytes')!=36+positions*RECORD_BYTES
        or value.get('gzip_level')!=1 or value.get('gzip_mtime')!=0):raise ValueError('chunk manifest source/format/completeness differs')
    rows=value.get('chunks',[])
    if len(rows)!=(positions+records-1)//records:raise ValueError('missing/excess original-stream chunk')
    offset=0;names=set()
    for index,row in enumerate(rows):
        reason=stop() if stop else None
        if reason:raise RuntimeError('root chunk-index stop: '+str(reason))
        count=min(records,positions-index*records);header=36 if index==0 else 0;name=row.get('path','')
        if (not name or Path(name).name!=name or name in names or row.get('index')!=index or row.get('raw_offset')!=offset
            or row.get('first_record')!=index*records or row.get('record_count')!=count or row.get('header_bytes')!=header or row.get('trailing_bytes')!=0 or row.get('raw_bytes')!=header+count*RECORD_BYTES):raise ValueError('chunk gap/reorder/overlap/partial-record metadata')
        names.add(name);target=path.parent/name
        if target.stat().st_size!=row.get('gzip_bytes') or sha(target)!=row.get('gzip_sha256'):raise ValueError('original compressed chunk changed')
        if not re.fullmatch('[0-9a-f]{64}',row.get('raw_sha256','')):raise ValueError('chunk raw hash malformed')
        offset+=row['raw_bytes']
    if offset!=value['raw_bytes'] or not re.fullmatch('[0-9a-f]{64}',value.get('raw_sha256','')):raise ValueError('chunk global offset/hash differs')
    return value



def compare_chunked(left,right,positions,child_limit,stop=None,left_capture=None,right_capture=None):
    left=Path(left);right=Path(right);aindex=validate_chunk_index(left,positions,child_limit,stop=stop,capture=left_capture);bindex=validate_chunk_index(right,positions,child_limit,stop=stop,capture=right_capture)
    if aindex['records_per_chunk']!=bindex['records_per_chunk']:raise ValueError('chunk boundary protocols differ')
    global_offset=0;global_a=hashlib.sha256();global_b=hashlib.sha256();header=None
    for arow,brow in zip(aindex['chunks'],bindex['chunks']):
        local=0;ah=hashlib.sha256();bh=hashlib.sha256()
        with gzip.open(left.parent/arow['path'],'rb') as a,gzip.open(right.parent/brow['path'],'rb') as b:
            while True:
                reason=stop() if stop else None
                if reason:raise RuntimeError('root comparison stop: '+str(reason))
                x,y=a.read(1048576),b.read(1048576)
                if x!=y:
                    first=next((i for i,(u,v) in enumerate(zip(x,y)) if u!=v),min(len(x),len(y)))
                    raise ValueError('exact original stream differs at byte '+str(global_offset+local+first))
                if not x:break
                if header is None:header=parse_header(x[:36],positions,child_limit)
                ah.update(x);bh.update(y);global_a.update(x);global_b.update(y);local+=len(x)
                if local>arow['raw_bytes'] or local>brow['raw_bytes']:raise ValueError('chunk has excess decoded bytes')
        if local!=arow['raw_bytes'] or local!=brow['raw_bytes'] or ah.hexdigest()!=arow['raw_sha256'] or bh.hexdigest()!=brow['raw_sha256']:raise ValueError('truncated/changed decoded chunk')
        global_offset+=local
    if global_offset!=36+positions*RECORD_BYTES or global_a.hexdigest()!=aindex['raw_sha256'] or global_b.hexdigest()!=bindex['raw_sha256']:raise ValueError('global original stream coverage/hash differs')
    return {'status':'PASS_EXACT_BYTES','positions':positions,'bytes_compared':global_offset,'chunks_compared':len(aindex['chunks']),'header':header,'comparison':'every original decompressed byte with exact contiguous chunk/record coverage; not hash-only'}



def load_owned_module():
    spec=importlib.util.spec_from_file_location('s11_original_owned',OWNED);owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned);return owned



def capture_arm(executable,corpus_fd,*,input_bytes,input_sha256,positions,child_limit,expected_mode,out,label,seconds,stop=None,minimum_free_bytes=64*1048576,chunk_records=10000):
    """Run one already-qualified oracle, preserving bounded gzip and original stderr.

    The caller first verifies source/build/link/ISA receipts and has the finite
    native grant. No corpus is generated here. The same sealed fd is rewound for
    each sequential arm. This is correctness work, not a timed speed comparison.
    """
    if positions!=8192 or child_limit!=1024 or expected_mode not in (0,1,2) or not 1<=seconds<=1800:raise ValueError('invalid finite native arm protocol')
    if not re.fullmatch('[a-zA-Z0-9_]+',label):raise ValueError('unsafe raw label')
    out=Path(out);exe=Path(executable)
    if not out.is_dir() or not exe.is_file():raise ValueError('existing output directory and executable required')
    paths={key:out/(label+suffix) for key,suffix in [('chunks','.stdout.chunks.json'),('stderr','.stderr'),('receipt','.receipt.json')]}
    if any(path.exists() for path in paths.values()):raise FileExistsError('new raw capture paths required')
    if sha(OWNED)!=OWNED_SHA:raise ValueError('owned-process helper changed')
    owned=load_owned_module()
    source=verify_sealed_input(corpus_fd,input_bytes,input_sha256);os.lseek(corpus_fd,0,os.SEEK_SET)
    argv=[str(exe),'--positions',str(positions),'--child-limit',str(child_limit)];start=time.monotonic();deadline=start+seconds
    result={'status':'FAIL_CAPTURE','argv':argv,'executable_sha256_before':sha(exe),'sealed_input':source,'positions':positions,'child_limit':child_limit,'expected_mode':expected_mode,'raw_stdout_bytes':0,'maximum_raw_stdout_bytes':36+positions*RECORD_BYTES,'source_oracle_sha256_required':ORACLE_SHA,'nps_used':False,'leader_reaped':False,'remaining_owned_group':[]}
    proc=None;sel=selectors.DefaultSelector();header=bytearray();digest=hashlib.sha256();stderr=bytearray();error=None;saved=None
    try:
        with owned.SubreaperScope():
            try:
                with paths['stderr'].open('xb') as saved_err:
                    with ChunkedGzip(out,label,positions,child_limit,chunk_records) as saved:
                        reason=stop() if stop else None
                        if reason or shutil.disk_usage(out).free<minimum_free_bytes:raise RuntimeError('prelaunch root stop/free-disk floor')
                        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
                        proc=subprocess.Popen(argv,stdin=corpus_fd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env=env)
                        result.update(pid=proc.pid,process_group=proc.pid)
                        with (out/'events.jsonl').open('a') as events:events.write(json.dumps({'event':'child_start','label':label,'pid':proc.pid,'utc':owned.utc()})+'\n')
                        sel.register(proc.stdout,selectors.EVENT_READ,'stdout');sel.register(proc.stderr,selectors.EVENT_READ,'stderr')
                        while sel.get_map():
                            reason=stop() if stop else None
                            if reason:raise RuntimeError('root stop: '+str(reason))
                            if time.monotonic()>=deadline-1:raise TimeoutError('owned oracle deadline')
                            if shutil.disk_usage(out).free<minimum_free_bytes:raise RuntimeError('raw evidence free-disk floor')
                            for key,_ in sel.select(.05):
                                chunk=os.read(key.fd,131072)
                                if not chunk:sel.unregister(key.fileobj);continue
                                if key.data=='stderr':
                                    saved_err.write(chunk);stderr.extend(chunk)
                                    if len(stderr)>16384:raise ValueError('oracle stderr exceeded fixed summary bound')
                                else:
                                    saved.write(chunk);digest.update(chunk);result['raw_stdout_bytes']+=len(chunk)
                                    if result['raw_stdout_bytes']>result['maximum_raw_stdout_bytes']:raise ValueError('oracle emitted excess snapshot bytes')
                                    if len(header)<36:
                                        header.extend(chunk[:36-len(header)])
                                        if len(header)==36:result['header']=parse_header(header,positions,child_limit)
                        proc.wait(timeout=max(.01,deadline-time.monotonic()));result['returncode']=proc.returncode;result['leader_reaped']=True
                        if proc.returncode!=0:raise ValueError('oracle did not exit normally with rc0')
                        if result['raw_stdout_bytes']!=result['maximum_raw_stdout_bytes']:raise ValueError('truncated/partial-record oracle stream')
                        result['summary']=parse_summary(bytes(stderr),positions,child_limit,expected_mode)
                reaped,remaining=owned._reap_group(proc.pid,timeout=.1);result['reaped_descendants']=reaped;result['remaining_owned_group']=remaining
                if remaining:raise ValueError('oracle owned group not empty after exit')
                result['status']='PASS_CAPTURE'
            finally:
                if proc is not None:
                    if proc.poll() is None or owned._all_members(proc.pid):
                        reaped,remaining=owned._close_group(proc);result['cleanup_reaped']=reaped;result['remaining_owned_group']=remaining
                    result['returncode']=proc.returncode;result['leader_reaped']=proc.poll() is not None
                    for stream in (proc.stdout,proc.stderr):
                        if stream:stream.close()
    except BaseException as exc:error=exc;result['status']='FAIL_CAPTURE';result['error']=type(exc).__name__+': '+str(exc)
    finally:
        sel.close();result['raw_stdout_sha256']=digest.hexdigest();result['elapsed_seconds']=time.monotonic()-start
        result['executable_sha256_after']=sha(exe);result['executable_unchanged']=result['executable_sha256_before']==result['executable_sha256_after']
        if not result['executable_unchanged'] or result['remaining_owned_group']:result['status']='FAIL_CAPTURE'
        if saved is not None:result['chunk_count']=len(saved.rows)
        result['captures']={name:{'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)} for name,path in paths.items() if name!='receipt' and path.exists()}
        with paths['receipt'].open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    if result['status']!='PASS_CAPTURE':raise RuntimeError('native arm failed; original receipt '+str(paths['receipt'])) from error
    return result

