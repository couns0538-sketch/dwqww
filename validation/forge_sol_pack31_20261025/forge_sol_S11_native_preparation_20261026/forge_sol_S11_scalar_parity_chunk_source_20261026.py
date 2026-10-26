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
        value={'schema':'forge.S11.original_stream_chunks.v1','positions':self.positions,'child_limit':self.child_limit,'records_per_chunk':self.chunk_records,'header_bytes':36,'record_bytes':RECORD_BYTES,'expected_raw_bytes':36+self.positions*RECORD_BYTES,'raw_bytes':self.offset,'raw_sha256':self.global_hash.hexdigest(),'complete_length':self.offset==36+self.positions*RECORD_BYTES,'gzip_level':1,'gzip_mtime':0,'chunks':self.rows}
        with self.index_path.open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    def __exit__(self,*unused):self.close()


def validate_chunk_index(path,positions,child_limit):
    path=Path(path);value=json.loads(path.read_text());records=value.get('records_per_chunk')
    if (value.get('schema')!='forge.S11.original_stream_chunks.v1' or type(records) is not int or not 1<=records<=10000
        or value.get('positions')!=positions or value.get('child_limit')!=child_limit or value.get('header_bytes')!=36 or value.get('record_bytes')!=RECORD_BYTES
        or value.get('complete_length') is not True or value.get('raw_bytes')!=36+positions*RECORD_BYTES or value.get('expected_raw_bytes')!=36+positions*RECORD_BYTES
        or value.get('gzip_level')!=1 or value.get('gzip_mtime')!=0):raise ValueError('chunk manifest source/format/completeness differs')
    rows=value.get('chunks',[])
    if len(rows)!=(positions+records-1)//records:raise ValueError('missing/excess original-stream chunk')
    offset=0;names=set()
    for index,row in enumerate(rows):
        count=min(records,positions-index*records);header=36 if index==0 else 0;name=row.get('path','')
        if (not name or Path(name).name!=name or name in names or row.get('index')!=index or row.get('raw_offset')!=offset
            or row.get('first_record')!=index*records or row.get('record_count')!=count or row.get('header_bytes')!=header or row.get('trailing_bytes')!=0 or row.get('raw_bytes')!=header+count*RECORD_BYTES):raise ValueError('chunk gap/reorder/overlap/partial-record metadata')
        names.add(name);target=path.parent/name
        if target.stat().st_size!=row.get('gzip_bytes') or sha(target)!=row.get('gzip_sha256'):raise ValueError('original compressed chunk changed')
        if not re.fullmatch('[0-9a-f]{64}',row.get('raw_sha256','')):raise ValueError('chunk raw hash malformed')
        offset+=row['raw_bytes']
    if offset!=value['raw_bytes'] or not re.fullmatch('[0-9a-f]{64}',value.get('raw_sha256','')):raise ValueError('chunk global offset/hash differs')
    return value


def compare_chunked(left,right,positions,child_limit,stop=None):
    left=Path(left);right=Path(right);aindex=validate_chunk_index(left,positions,child_limit);bindex=validate_chunk_index(right,positions,child_limit)
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
