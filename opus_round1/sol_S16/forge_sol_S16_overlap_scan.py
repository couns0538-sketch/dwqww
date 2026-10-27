#!/usr/bin/env python3
"""S16 real 013/014 overlap scan: read-only, streaming, memory-bounded (Opus 5.5, 2026-10-27).

For every training shard, count the rows whose position also occurs in the holdout shards. The identity is Sol's
Job D identity (board32 + side to move; FPOS stores no castling, e.p. or clocks). Matching is exact: a 64-bit key
finds candidates and every candidate is confirmed byte for byte on all 33 key bytes. The scan also reports:
  - holdout-side overlap per inferred game group (Sol's conservative ordered-text rule: a new game starts when the
    fullmove number decreases, the piece count increases or the WHITE result changes), plus the interleaving tripwire
    (more than 20 boundaries in a rolling 100-row window fails the game analysis closed);
  - games that straddle a holdout/training shard boundary in chronological order;
  - label conflicts (same position, different score or result), whole-file duplicates (md5);
  - an advisory removal list (training stem, row, reason).
It removes nothing and writes no training data. All inputs are opened read-only; the NEW output directory may not lie
inside any input directory ("no writes next to the data"). On Windows the process enters background mode (lowest
CPU, I/O and memory priority). Needs numpy (on the PC: the read-only torch venv, numpy 1.26.4).
"""
from __future__ import annotations
import argparse,datetime,gzip,hashlib,io,json,os,platform,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np

DATE='20261027'
HEADER_BYTES=16
POS_WIDTH=35
CODES=' PNBRQKpnbrqk'
RESULTS={'0.0':0,'0.5':1,'1.0':2,'0':0,'1':2}
TRIPWIRE_WINDOW,TRIPWIRE_LIMIT=100,20  # Sol's interleaving tripwire: more than 20 boundaries in a rolling 100-row window
U64=np.uint64

# ------------------------------------------------------------------ FPOS reading (same layout as Sol's Reader)
def pos_count(path):
    """Validate the FPOS v1 header and size; return the row count."""
    with open(path,'rb') as f:head=f.read(HEADER_BYTES)
    if len(head)!=HEADER_BYTES:raise ValueError('truncated header: '+str(path))
    magic=head[:4];version=int.from_bytes(head[4:8],'little');n=int.from_bytes(head[8:16],'little')
    if magic!=b'FPOS' or version!=1 or os.path.getsize(path)!=HEADER_BYTES+POS_WIDTH*n:raise ValueError('format/version/size mismatch: '+str(path))
    return n

class Shard:
    """One FPOS file, read-only. Columnar layout: boards (n,32) u8, scores (n,) <i2, metas (n,) u8.
    Sequential passes use explicit chunked reads (the pages go to the OS file cache, which counts as available RAM);
    the memory map is opened lazily and only for sparse random gathers (matched rows, sampled rows)."""
    def __init__(self,path):
        self.path=Path(path).resolve(strict=True);self.stem=self.path.stem;self.n=pos_count(self.path);self._mm=None
    def read(self,a,b):
        """Rows [a, b): (boards (m,32), scores (m,), metas (m,)) as fresh arrays."""
        n=self.n;m=b-a
        with open(self.path,'rb') as f:
            f.seek(HEADER_BYTES+32*a);boards=np.frombuffer(f.read(32*m),np.uint8).reshape(m,32)
            f.seek(HEADER_BYTES+32*n+2*a);scores=np.frombuffer(f.read(2*m),'<i2')
            f.seek(HEADER_BYTES+34*n+a);metas=np.frombuffer(f.read(m),np.uint8)
        if len(metas)!=m:raise ValueError('short read: '+str(self.path))
        return boards,scores,metas
    def column(self,name):
        """A whole small column ('scores' or 'metas') read sequentially."""
        n=self.n;off,width,dt={'scores':(HEADER_BYTES+32*n,2,'<i2'),'metas':(HEADER_BYTES+34*n,1,np.uint8)}[name]
        with open(self.path,'rb') as f:f.seek(off);return np.frombuffer(f.read(width*n),dt)
    def _map(self):
        if self._mm is None:
            n=self.n;mm=np.memmap(self.path,dtype=np.uint8,mode='r')
            self._mm=(mm[HEADER_BYTES:HEADER_BYTES+32*n].reshape(n,32),mm[HEADER_BYTES+32*n:HEADER_BYTES+34*n].view('<i2'),mm[HEADER_BYTES+34*n:HEADER_BYTES+35*n])
        return self._mm
    @property
    def boards(self):return self._map()[0]
    @property
    def scores(self):return self._map()[1]
    @property
    def metas(self):return self._map()[2]
    def md5(self):
        h=hashlib.md5()
        with open(self.path,'rb') as f:
            for block in iter(lambda:f.read(16*1024*1024),b''):h.update(block)
        return h.hexdigest()

def mix64(x):
    """splitmix64 finalizer on a u64 array (wrapping arithmetic)."""
    x=(x^(x>>U64(30)))*U64(0xbf58476d1ce4e5b9);x=(x^(x>>U64(27)))*U64(0x94d049bb133111eb);return x^(x>>U64(31))

def keys64(boards,metas):
    """64-bit candidate key of (board32, side to move). Equal positions give equal keys; candidates are confirmed exactly."""
    with np.errstate(over='ignore'):
        w=np.ascontiguousarray(boards).view('<u8').reshape(-1,4)
        h=mix64(w[:,0]^U64(0x9e3779b97f4a7c15))
        for j in (1,2,3):h=mix64(h^w[:,j])
        return mix64(h^((metas&1).astype(U64)+U64(0x632be59bd9b4e019)))

def exact_keys(boards,metas):
    """The 33 identity bytes per row: board32 || (meta & 1)."""
    return np.concatenate([np.asarray(boards),(np.asarray(metas)&1).reshape(-1,1)],axis=1)

def piece_counts(boards):
    b=np.asarray(boards);return ((b&15)!=0).sum(axis=1,dtype=np.int16)+((b>>4)!=0).sum(axis=1,dtype=np.int16)

# ------------------------------------------------------------------ text (FEN | STM score | WHITE result)
def pack_placement(placement):
    ranks=placement.split('/')
    if len(ranks)!=8:raise ValueError('text FEN ranks')
    packed=bytearray(32)
    for rank,text in enumerate(reversed(ranks)):
        f=0
        for ch in text:
            if ch in '12345678':f+=int(ch)
            else:
                code=CODES.index(ch) if ch in CODES[1:] else -1
                if code<0 or f>7:raise ValueError('text FEN piece/rank')
                sq=rank*8+f;packed[sq//2]|=code<<(4*(sq%2));f+=1
        if f!=8:raise ValueError('text rank width')
    return bytes(packed)

def parse_text(path,n,metas,scores,board_sample_every=997):
    """Parse a whole text shard. Every row's side to move, score and result must equal the POS row (checked per batch);
    returns the fullmove numbers (int16) and the packed boards of every `board_sample_every`-th row."""
    fm=np.empty(n,np.int16);samples={};i=0
    with open(path,'r',encoding='utf-8',newline=None) as stream:
        while True:
            lines=stream.readlines(1<<24)
            if not lines:break
            if i+len(lines)>n:raise ValueError('text has more lines than POS records: '+str(path))
            f_fm=[];f_stm=[];f_sc=[];f_res=[]
            for k,line in enumerate(lines):
                parts=line.split('|')
                if len(parts)!=3:raise ValueError(f'text line {i+k} is not FEN | score | result: {path}')
                fen=parts[0].split()
                if len(fen)!=6 or fen[1] not in ('w','b'):raise ValueError(f'text FEN fields at line {i+k}: {path}')
                f_fm.append(int(fen[5]));f_stm.append(fen[1]=='b');f_sc.append(int(parts[1]));r=RESULTS.get(parts[2].strip())
                if r is None:raise ValueError(f'text result at line {i+k}: {path}')
                f_res.append(r)
                if (i+k)%board_sample_every==0:samples[i+k]=pack_placement(fen[0])
            m=len(lines);mt=metas[i:i+m]
            if max(f_fm)>32767 or not (np.array_equal(np.array(f_stm,np.uint8),mt&1) and np.array_equal(np.array(f_sc,np.int32),scores[i:i+m].astype(np.int32)) and np.array_equal(np.array(f_res,np.uint8),mt>>1)):
                raise ValueError(f'text/POS field mismatch (stm/score/result) in rows {i}..{i+m-1}: {path}')
            fm[i:i+m]=f_fm;i+=m
    if i!=n:raise ValueError(f'text/POS row count mismatch ({i} vs {n}): {path}')
    return fm,samples

def edge_lines(path,count,tail):
    """The first or last `count` lines of a text file (tail read from the end, no full scan)."""
    if not tail:
        out=[]
        with open(path,'r',encoding='utf-8') as s:
            for line in s:
                out.append(line)
                if len(out)>=count:break
        return out
    with open(path,'rb') as f:
        size=f.seek(0,2);chunk=min(size,max(4096,count*120));data=b''
        while True:
            f.seek(size-chunk);data=f.read(chunk);lines=data.splitlines()
            if len(lines)>count or chunk==size:break
            chunk=min(size,chunk*2)
    lines=data.decode('utf-8').splitlines()
    return [l+'\n' for l in (lines[-count:] if chunk<size else lines)][-count:]

def line_context(line,board_pieces=None):
    parts=line.split('|');fen=parts[0].split()
    pieces=sum(ch.isalpha() for ch in fen[0]) if board_pieces is None else board_pieces
    return int(fen[5]),pieces,RESULTS[parts[2].strip()]

def boundaries(fm,pc,res):
    """Sol's conservative rule between consecutive rows: new game if fullmove decreases, pieces increase or result changes."""
    return (fm[1:]<fm[:-1])|(pc[1:]>pc[:-1])|(res[1:]!=res[:-1])

def tripwire(flags,window=100,limit=20):
    """Largest number of boundaries among any 99 consecutive transitions (= a rolling 100-row window)."""
    if len(flags)<window-1:return int(flags.sum())
    c=np.concatenate([[0],np.cumsum(flags,dtype=np.int64)]);return int((c[window-1:]-c[:-(window-1)]).max())

# ------------------------------------------------------------------ environment guards
def lower_priority(mode='idle'):
    """'idle' (default): make sure this process runs in the Idle priority class (Windows; = nice -n 19) or at nice 19
    (POSIX); it never raises priority. 'background': Windows PROCESS_MODE_BACKGROUND_BEGIN (CPU, I/O and memory priority
    very low). On the loaded PC, background mode starved the scan (31k rows/s, about 100x slower), so it is opt-in."""
    if os.name=='nt':
        import ctypes
        k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
        k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.GetPriorityClass.argtypes=[ctypes.c_void_p]
        me=k.GetCurrentProcess()
        if mode=='background':
            ok=k.SetPriorityClass(me,0x00100000)
            return 'windows_background_mode' if ok or ctypes.get_last_error()==402 else 'windows_background_mode_FAILED'  # 402: already in background mode
        if k.GetPriorityClass(me)!=0x40 and not k.SetPriorityClass(me,0x40):return 'windows_idle_class_FAILED'
        return 'windows_idle_priority_class' if k.GetPriorityClass(me)==0x40 else 'windows_idle_class_FAILED'
    try:
        if os.getpriority(os.PRIO_PROCESS,0)<19:os.setpriority(os.PRIO_PROCESS,0,19)
        return 'posix_nice_19'
    except OSError:return 'posix_nice_unchanged'

def free_ram_bytes():
    if os.name=='nt':
        import ctypes
        class S(ctypes.Structure):
            _fields_=[('l',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(f,ctypes.c_ulonglong) for f in ('tp','ap','tpf','apf','tv','av','ae')]
        s=S();s.l=ctypes.sizeof(S)
        return int(s.ap) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)) else None
    try:
        for line in open('/proc/meminfo'):
            if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
    except OSError:pass
    return None

def check_out_dir(out,inputs):
    out=Path(out).resolve()
    if out.exists():raise FileExistsError('output directory must be new: '+str(out))
    if not out.parent.is_dir():raise ValueError('output parent must exist: '+str(out.parent))
    for p in inputs:
        d=Path(p).resolve();d=d if d.is_dir() else d.parent
        if out==d or d in out.parents:raise ValueError(f'refusing to write next to input data: {out} is inside {d}')
    return out

# ------------------------------------------------------------------ the scan
class Holdout:
    """Sorted 64-bit keys over all holdout rows (global row = shard offset + local row), exact-verified duplicate runs."""
    def __init__(self,shards,chunk):
        self.shards=shards;self.off=np.cumsum([0]+[s.n for s in shards]);self.n=int(self.off[-1])
        if self.n==0:raise ValueError('empty holdout')
        keys=np.empty(self.n,U64)
        for s,o in zip(shards,self.off):
            for a in range(0,s.n,chunk):
                b=min(s.n,a+chunk);bd,_,mt=s.read(a,b);keys[o+a:o+b]=keys64(bd,mt)
        idx=np.int32 if self.n<2**31 else np.int64
        self.order=np.argsort(keys,kind='stable').astype(idx);self.sorted=keys[self.order];del keys  # peak about 33 B/row
        new=np.empty(self.n,bool);new[0]=True;np.not_equal(self.sorted[1:],self.sorted[:-1],out=new[1:])
        self.run_id=np.cumsum(new,dtype=idx);self.run_id-=1;self.runs=int(self.run_id[-1])+1
        dup=np.flatnonzero(~new)  # sorted positions whose key equals the previous one: confirm the 33 bytes agree
        self.verified_duplicate_pairs=0
        for a in range(0,len(dup),chunk):
            d=dup[a:a+chunk]
            if not np.array_equal(self.exact(self.order[d]),self.exact(self.order[d-1])):raise ValueError('64-bit key collision inside the holdout; refusing an inexact count')
            self.verified_duplicate_pairs+=len(d)
        del new,dup
    def release(self):
        """Drop the index arrays (the game analysis needs only the per-row hit flags)."""
        self.sorted=self.order=self.run_id=None
    def locate(self,g):
        """(shard index, local row) for global rows g."""
        s=np.searchsorted(self.off,g,side='right')-1;return s,g-self.off[s]
    def exact(self,g):
        g=np.asarray(g,np.int64);s,r=self.locate(g);out=np.empty((len(g),33),np.uint8)
        for k,sh in enumerate(self.shards):
            m=s==k
            if m.any():rows=r[m];out[m]=exact_keys(sh.boards[rows],sh.metas[rows])
        return out
    def labels(self,g):
        g=np.asarray(g,np.int64);s,r=self.locate(g);sc=np.empty(len(g),np.int32);res=np.empty(len(g),np.uint8)
        for k,sh in enumerate(self.shards):
            m=s==k
            if m.any():rows=r[m];sc[m]=sh.scores[rows];res[m]=sh.metas[rows]>>1
        return sc,res

def scan(args):
    started=time.monotonic();mode=lower_priority(args.priority)
    holdout_paths=[Path(p).resolve(strict=True) for p in args.holdout];train_paths=[Path(p).resolve(strict=True) for p in args.train]
    stems=[p.stem for p in holdout_paths+train_paths]
    if len(set(stems))!=len(stems):raise ValueError('shard stems must be unique')
    for t in train_paths:
        if any(os.path.samefile(t,h) for h in holdout_paths):raise ValueError('a training input is a holdout file: '+str(t))
    text_dir=Path(args.text_dir).resolve(strict=True) if args.text_dir else None
    out=check_out_dir(args.out,holdout_paths+train_paths+([text_dir] if text_dir else []))
    order=args.order.split(',') if args.order else sorted(stems)
    if set(order)!=set(stems) or len(order)!=len(stems):raise ValueError('--order must list every holdout and training stem exactly once')
    out.mkdir();summary={'tool':Path(__file__).name,'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'RUNNING','priority':mode,'python':sys.version.split()[0],'numpy':np.__version__,'platform':platform.platform(),'identity':'board32 + side to move (Sol Job D identity; FPOS has no castling/e.p./clocks); 64-bit candidate key, every match confirmed on all 33 bytes','chronological_order':order,'min_free_ram_gib':args.min_free_ram_gib,'max_wall_seconds':args.max_wall_seconds,'production_eligible':False,'game_ids':'INFERRED with Sol\'s conservative ordered-text rule (supersets of games); not authoritative IDs','removal_list_is_advisory':True,'writes':'only the new --out directory','strength_claim':None}
    def guard(where,extra=0.0):
        """Stop (clean, partial results kept) if free RAM < floor (+ `extra`: the expected footprint, at start) or over budget."""
        free=free_ram_bytes();el=time.monotonic()-started
        if free is not None and free<(args.min_free_ram_gib+extra)*2**30:raise RuntimeError(f'STOPPED_LOW_RAM: {free/2**30:.2f} GiB free {where} (need {args.min_free_ram_gib+extra:g})')
        if el>args.max_wall_seconds:raise RuntimeError(f'STOPPED_WALL_BUDGET: {el:.0f} s used {where}')
        return None if free is None else round(free/2**30,2)
    raw=open(out/f'forge_sol_S16_removal_list_{DATE}.csv.gz','xb')  # gzip mtime 0: identical inputs give identical bytes
    removal=io.TextIOWrapper(gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6),encoding='utf-8',newline='\n')
    removal.write('stem,row,reason,holdout_stem,holdout_row,label_conflict\n')
    try:
        summary['free_ram_gib_start']=guard('at start',args.footprint_gib)
        hold=[Shard(p) for p in holdout_paths];t0=time.monotonic();H=Holdout(hold,args.chunk_rows)
        summary['holdout']={'shards':[{'stem':s.stem,'path':str(s.path),'rows':s.n,'bytes':s.path.stat().st_size} for s in hold],'rows':H.n,'unique_positions':H.runs,'duplicate_rows_within_holdout':H.n-H.runs,'verified_duplicate_pairs':H.verified_duplicate_pairs,'index_seconds':round(time.monotonic()-t0,2)}
        hit_run=np.zeros(H.runs,bool);per_shard=[];shard_md5={}
        for s in hold:shard_md5[s.stem]=s.md5()
        for p in train_paths:
            free=guard('before '+p.stem);t1=time.monotonic();s=Shard(p);rows_hit=0;conflicts=0;collisions=0;runs_this=[]
            summary['in_progress_partial_removal_rows_for']=p.stem  # removed again when the shard completes
            for a in range(0,s.n,args.chunk_rows):
                if a:guard(f'in {p.stem} at row {a}')
                b=min(s.n,a+args.chunk_rows);bd,sc,mt=s.read(a,b);k=keys64(bd,mt);pos=np.searchsorted(H.sorted,k);pos_c=np.minimum(pos,H.n-1)
                cand=np.flatnonzero((pos<H.n)&(H.sorted[pos_c]==k))
                if not len(cand):continue
                g=H.order[pos_c[cand]].astype(np.int64)
                same=(exact_keys(bd[cand],mt[cand])==H.exact(g)).all(axis=1)
                collisions+=int((~same).sum());g=g[same];cand=cand[same];rows=cand+a
                if not len(rows):continue
                runs=H.run_id[pos_c[cand]];hit_run[runs]=True;runs_this.append(runs)
                hs,hr=H.labels(g);conf=(sc[cand].astype(np.int32)!=hs)|((mt[cand]>>1)!=hr);conflicts+=int(conf.sum());rows_hit+=len(rows)
                gs,gl=H.locate(g)
                removal.write(''.join(f'{s.stem},{r},holdout_position,{hold[x].stem},{y},{int(c)}\n' for r,x,y,c in zip(rows.tolist(),gs.tolist(),gl.tolist(),conf.tolist())))
            unique=int(len(np.unique(np.concatenate(runs_this)))) if runs_this else 0
            shard_md5[s.stem]=s.md5()
            per_shard.append({'stem':s.stem,'rows':s.n,'overlap_rows':rows_hit,'overlap_fraction':round(rows_hit/s.n,6) if s.n else 0.0,'distinct_holdout_positions_hit':unique,'label_conflicts':conflicts,'key_collisions_rejected':collisions,'md5':shard_md5[s.stem],'seconds':round(time.monotonic()-t1,2),'free_ram_gib_before':free})
            summary['train']=per_shard;del s;summary.pop('in_progress_partial_removal_rows_for')
        summary['train_totals']={'shards':len(per_shard),'rows':sum(x['rows'] for x in per_shard),'overlap_rows':sum(x['overlap_rows'] for x in per_shard),'label_conflicts':sum(x['label_conflicts'] for x in per_shard),'key_collisions_rejected':sum(x['key_collisions_rejected'] for x in per_shard)}
        t=summary['train_totals'];t['overlap_fraction']=round(t['overlap_rows']/t['rows'],6) if t['rows'] else 0.0
        # holdout side: every holdout row whose position occurs in any training shard
        hit_rows=np.empty(H.n,bool);hit_rows[H.order]=hit_run[H.run_id];H.release()
        with open(out/f'forge_sol_S16_holdout_rows_in_training_bitmap_{DATE}.npy','xb') as f:np.save(f,np.packbits(hit_rows,bitorder='little'))  # bit i = holdout global row i (013 rows first)
        summary['holdout']['positions_also_in_training']=int(hit_run.sum());summary['holdout']['rows_whose_position_is_in_training']=int(hit_rows.sum())
        summary['holdout']['per_shard_rows_in_training']={s.stem:int(hit_rows[H.off[k]:H.off[k+1]].sum()) for k,s in enumerate(hold)}
        groups=md5_dupes=None
        md5s={};[md5s.setdefault(v,[]).append(k) for k,v in sorted(shard_md5.items())]
        summary['whole_file_md5']=shard_md5;summary['whole_file_duplicates']=[v for v in md5s.values() if len(v)>1]
        if text_dir:summary['games']=games(args,hold,H,hit_rows,text_dir,order,train_paths,removal,guard)
        else:summary['games']={'status':'UNVERIFIED_NO_TEXT'}
        summary['status']='COMPLETED'
    except RuntimeError as exc:
        summary['status']=str(exc).split(':')[0];summary['stop_reason']=str(exc)
    except Exception as exc:
        summary['status']='FAILED';summary['stop_reason']=type(exc).__name__+': '+str(exc);raise
    finally:
        removal.close();raw.close();summary['elapsed_seconds']=round(time.monotonic()-started,2)
        with open(out/f'forge_sol_S16_overlap_summary_{DATE}.json','xb') as f:f.write((json.dumps(summary,indent=2,sort_keys=True)+'\n').encode())
        rows=[hashlib.sha256((out/p.name).read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file()]
        with open(out/'SHA256SUMS','xb') as f:f.write(''.join(rows).encode())
    return summary

def games(args,hold,H,hit_rows,text_dir,order,train_paths,removal,guard):
    """Game groups over the holdout text (chronologically adjacent holdout shards continue a game), the tripwire,
    straddling games at every holdout/training junction, per-group overlap and overlap by fullmove bucket."""
    t0=time.monotonic();fm_all=[];res_all=[];pc_all=[];report={'board_sample_every':args.board_sample_every}
    for s in hold:
        guard('before text '+s.stem);metas=s.column('metas');scores=s.column('scores')
        fm,samples=parse_text(text_dir/(s.stem+'.txt'),s.n,metas,scores,args.board_sample_every);res=metas>>1
        rows=np.array(sorted(samples),np.int64);bad=[int(i) for i,b in zip(rows,s.boards[rows]) if bytes(b)!=samples[int(i)]] if len(rows) else []
        if bad:raise ValueError(f'text/POS board mismatch at sampled rows {bad[:5]}: {s.stem}')
        report.setdefault('text_checked',[]).append({'stem':s.stem,'rows':s.n,'fields_equal':'stm, score, result on every row','boards_equal_sampled_rows':len(samples)})
        pc=np.empty(s.n,np.int16)
        for a in range(0,s.n,args.chunk_rows):b=min(s.n,a+args.chunk_rows);pc[a:b]=piece_counts(s.read(a,b)[0])
        fm_all.append(fm);res_all.append(res);pc_all.append(pc);del metas,scores
    # holdout shards that are not chronologically adjacent never continue a game: force a boundary there
    idx={st:i for i,st in enumerate(order)};fm=np.concatenate(fm_all);res=np.concatenate(res_all);pc=np.concatenate(pc_all)
    flags=boundaries(fm,pc,res)
    for k in range(1,len(hold)):
        if idx[hold[k].stem]!=idx[hold[k-1].stem]+1:flags[H.off[k]-1]=True
    largest=tripwire(flags,TRIPWIRE_WINDOW,TRIPWIRE_LIMIT);failed=largest>TRIPWIRE_LIMIT
    report['tripwire']={'window_rows':TRIPWIRE_WINDOW,'limit':TRIPWIRE_LIMIT,'largest_boundaries_in_window':largest,'result':'FAIL_SUSPECTED_INTERLEAVING' if failed else 'PASS'}
    gid=np.concatenate([[0],np.cumsum(flags,dtype=np.int64)]);n_groups=int(gid[-1])+1
    if failed:report.update({'status':'FAILED_CLOSED_INTERLEAVED_TEXT','groups':None});return report
    size=np.bincount(gid,minlength=n_groups);hits=np.bincount(gid,weights=hit_rows,minlength=n_groups).astype(np.int64);frac=hits/size
    report['groups']=n_groups;report['rows_per_group_median']=float(np.median(size))
    report['groups_with_any_training_position']=int((hits>0).sum());report['groups_fully_in_training']=int((hits==size).sum())
    edges=[0,1e-12,.25,.5,.75,1-1e-12,1.0000001];names=['0','(0,0.25]','(0.25,0.5]','(0.5,0.75]','(0.75,1)','1']
    report['group_overlap_fraction_histogram']=dict(zip(names,np.histogram(frac,bins=edges)[0].tolist()))
    buckets=[(1,10),(11,20),(21,40),(41,80),(81,10**9)];report['holdout_rows_by_fullmove']=[]
    for lo,hi in buckets:
        m=(fm>=lo)&(fm<=hi);report['holdout_rows_by_fullmove'].append({'fullmove':f'{lo}-{hi if hi<10**9 else "max"}','rows':int(m.sum()),'rows_in_training':int(hit_rows[m].sum())})
    # straddling games at holdout/training junctions (chronological neighbours)
    hold_stems={s.stem for s in hold};train_by_stem={p.stem:p for p in train_paths};junctions=[]
    for a,b in zip(order,order[1:]):
        if (a in hold_stems)==(b in hold_stems):continue
        j={'before':a,'after':b}
        ta,tb=text_dir/(a+'.txt'),text_dir/(b+'.txt')
        if not ta.exists() or not tb.exists():j['result']='UNVERIFIED_NO_TEXT';junctions.append(j);continue
        sa=Shard(train_by_stem[a]) if a in train_by_stem else hold[[s.stem for s in hold].index(a)]
        sb=Shard(train_by_stem[b]) if b in train_by_stem else hold[[s.stem for s in hold].index(b)]
        last=line_context(edge_lines(ta,1,True)[-1],int(piece_counts(sa.read(sa.n-1,sa.n)[0])[0]));first=line_context(edge_lines(tb,1,False)[0],int(piece_counts(sb.read(0,1)[0])[0]))
        new_game=first[0]<last[0] or first[1]>last[1] or first[2]!=last[2]
        j.update({'last_row_context':last,'first_row_context':first,'new_game_at_junction':bool(new_game)})
        if new_game:j['straddling_training_rows']=0
        else:
            # the game continues into/out of the training shard: every training row of that game is a removal
            train_side=b if b in train_by_stem else a;ts=Shard(train_by_stem[train_side]);count=0
            lines=edge_lines(text_dir/(train_side+'.txt'),min(ts.n,args.edge_rows),train_side==a)
            ctx=[line_context(l) for l in lines]
            seq=ctx if train_side==b else ctx[::-1]
            for i in range(len(seq)):
                if i==0:count=1;continue
                x,y=(seq[i-1],seq[i]) if train_side==b else (seq[i],seq[i-1])
                if y[0]<x[0] or y[1]>x[1] or y[2]!=x[2]:break
                count+=1
            rows=range(count) if train_side==b else range(ts.n-count,ts.n)
            removal.write(''.join(f'{train_side},{r},holdout_game_group,,,0\n' for r in rows))
            j['straddling_training_rows']=count;j['note']='piece counts from FEN text for the edge rows'
            if count==len(seq) and len(seq)<ts.n:j['result']='UNVERIFIED_EDGE_ROWS_EXHAUSTED (raise --edge-rows)'
        junctions.append(j)
    report['junctions']=junctions;report['straddling_training_rows_total']=sum(j.get('straddling_training_rows',0) for j in junctions)
    report['status']='COMPLETED';report['seconds']=round(time.monotonic()-t0,2);return report

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--holdout',nargs='+',required=True);p.add_argument('--train',nargs='+',required=True);p.add_argument('--text-dir')
    p.add_argument('--order',help='comma-separated chronological stems (default: sorted stems)');p.add_argument('--out',required=True)
    p.add_argument('--chunk-rows',type=int,default=500_000);p.add_argument('--board-sample-every',type=int,default=997);p.add_argument('--edge-rows',type=int,default=5000)
    p.add_argument('--min-free-ram-gib',type=float,default=6.0,help='floor checked before every chunk');p.add_argument('--footprint-gib',type=float,default=0.6,help='extra free RAM required at start')
    p.add_argument('--max-wall-seconds',type=float,default=540.0);p.add_argument('--priority',choices=('idle','background'),default='idle')
    args=p.parse_args(argv)
    if args.chunk_rows<1 or args.board_sample_every<1 or args.edge_rows<1:p.error('invalid sizes')
    s=scan(args)
    print(json.dumps({'status':s['status'],'out':str(Path(args.out).resolve()),'train_totals':s.get('train_totals'),'holdout_rows':s.get('holdout',{}).get('rows'),'stop_reason':s.get('stop_reason')},sort_keys=True))
    return 0 if s['status']=='COMPLETED' else 3
if __name__=='__main__':raise SystemExit(main())
