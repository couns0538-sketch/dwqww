#!/usr/bin/env python3
"""Original offline Forge FPOS/FHCE filter. Inputs are always opened read-only.

Identity is SHA256(board32 || STM1); POS does not contain castling/EP/clocks.
No engine/trainer code or parameter values are changed. See --help and report.
"""
from __future__ import annotations
import argparse,hashlib,json,mmap,os,shutil,sqlite3,struct,tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable,Iterator
HEADER=struct.Struct('<4sIQ')
DATE='20261025'
@dataclass(frozen=True)
class Record:
    board:bytes
    score:int
    meta:int
    hce:int|None
class Reader:
    def __init__(self,pos:Path,hce:Path|None=None):
        self.pos=Path(pos);self.hce=Path(hce) if hce is not None else None;self.files=[];self.maps=[]
        try:
            self.b=self._open(self.pos,b'FPOS',35);self.n=self._count
            self.h=self._open(self.hce,b'FHCE',2) if self.hce else None
            if self.h is not None and self._count!=self.n:raise ValueError('paired HCE count mismatch')
        except BaseException:self.close();raise
    def _open(self,path,magic,width):
        f=open(path,'rb');self.files.append(f);head=f.read(16)
        if len(head)!=16:raise ValueError('truncated header: '+str(path))
        m,version,n=HEADER.unpack(head)
        if m!=magic or version!=1 or os.fstat(f.fileno()).st_size!=16+width*n:raise ValueError('format/version/size mismatch: '+str(path))
        self._count=n;mm=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);self.maps.append(mm);return mm
    def row(self,i:int)->Record:
        if not 0<=i<self.n:raise IndexError(i)
        return Record(self.b[16+i*32:16+(i+1)*32],struct.unpack_from('<h',self.b,16+32*self.n+2*i)[0],self.b[16+34*self.n+i],struct.unpack_from('<h',self.h,16+2*i)[0] if self.h is not None else None)
    def close(self):
        for m in getattr(self,'maps',[]):m.close()
        for f in getattr(self,'files',[]):f.close()
        self.maps=[];self.files=[]
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
def read_records(pos:Path,hce:Path|None=None)->Iterator[Record]:
    with Reader(pos,hce) as r:
        for i in range(r.n):yield r.row(i)
def write_records(pos:Path,hce:Path,records:Iterable[Record])->int:
    """Original columnar writer; rebuild headers, retain each selected field exactly."""
    pos,hce=Path(pos),Path(hce)
    if pos.resolve()==hce.resolve():raise ValueError('POS and HCE outputs must differ')
    if pos.exists() or hce.exists():raise FileExistsError('output pair already exists')
    if pos.parent.resolve()!=hce.parent.resolve():raise ValueError('output pair must share own folder')
    n=0
    with tempfile.TemporaryFile(dir=pos.parent) as boards,tempfile.TemporaryFile(dir=pos.parent) as scores,tempfile.TemporaryFile(dir=pos.parent) as metas,tempfile.TemporaryFile(dir=pos.parent) as hces:
        for r in records:
            if len(r.board)!=32 or r.hce is None:raise ValueError('writer needs board32 and paired HCE')
            boards.write(r.board);scores.write(struct.pack('<h',r.score));metas.write(struct.pack('B',r.meta));hces.write(struct.pack('<h',r.hce));n+=1
        with open(pos,'xb') as p,open(hce,'xb') as h:
            p.write(HEADER.pack(b'FPOS',1,n));h.write(HEADER.pack(b'FHCE',1,n))
            for source in [boards,scores,metas]:source.seek(0);shutil.copyfileobj(source,p)
            hces.seek(0);shutil.copyfileobj(hces,h)
    return n
def md5(path):
    h=hashlib.md5()
    with open(path,'rb') as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()
def invalid_reason(r:Record):
    if r.meta not in range(6):return 'invalid_meta'
    if any((v&15)>12 or (v>>4)>12 for v in r.board):return 'invalid_piece_code'
    if r.hce==-32768:return 'invalid_hce'
    return None
def identity(r:Record):
    key=r.board+bytes([r.meta&1]);return hashlib.sha256(key).digest(),key
def insert_key(db,table,digest,key):
    existing=db.execute('SELECT key FROM '+table+' WHERE hash=?',(digest,)).fetchone()
    if existing:
        if existing[0]!=key:raise ValueError('position hash collision; refusing false dedupe')
        return False
    db.execute('INSERT INTO '+table+'(hash,key) VALUES(?,?)',(digest,key));return True
def disagreement(r:Record,threshold:int|None):
    if threshold is None:return None
    outcome=r.meta>>1
    if r.meta&1:outcome=2-outcome
    if outcome==0 and r.score>=threshold:return 'result_loss_score_positive'
    if outcome==2 and r.score<=-threshold:return 'result_win_score_negative'
    if outcome==1 and abs(r.score)>=threshold:return 'result_draw_score_large'
    return None
def text_record(line:str):
    fields=line.strip().split('|')
    if len(fields)!=3:raise ValueError('text must be FEN | STM score | WHITE result')
    fen=fields[0].split()
    if len(fen)!=6 or fen[1] not in ['w','b']:raise ValueError('text FEN fields')
    ranks=fen[0].split('/')
    if len(ranks)!=8:raise ValueError('text FEN ranks')
    codes=' PNBRQKpnbrqk';packed=bytearray(32);pieces=0
    for rank,text in enumerate(reversed(ranks)):
        file=0
        for char in text:
            if char in '12345678':file+=int(char)
            elif char in codes[1:] and file<8:
                square=rank*8+file;packed[square//2]|=codes.index(char)<<(4*(square%2));file+=1;pieces+=1
            else:raise ValueError('text FEN piece/rank')
            if file>8:raise ValueError('text rank overflow')
        if file!=8:raise ValueError('text rank width')
    numeric_result=float(fields[2].strip())
    if numeric_result not in [0.0,0.5,1.0]:raise ValueError('text result')
    result=int(numeric_result*2)
    score=int(fields[1].strip());fullmove=int(fen[5])
    if not -32767<=score<=32767 or fullmove<1:raise ValueError('text score/fullmove')
    return Record(bytes(packed),score,(fen[1]=='b')|(result<<1),None),(fullmove,pieces,result)
def build_groups(db,paths,holdout_set,text_map,ordered_stems):
    if not text_map and not ordered_stems:return {'mode':'UNVERIFIED_NO_ORDERED_TEXT'}
    if not text_map or not ordered_stems or set(text_map)!=set(paths) or set(ordered_stems)!=set(paths) or len(ordered_stems)!=len(paths):raise ValueError('complete text map and chronological stems required for ALL training/holdout sources')
    previous=None;gid=0;segments=0;text_hashes={}
    for stem in ordered_stems:
        path=paths[stem];tp=Path(text_map[stem]);text_hashes[stem]=md5(tp)
        with Reader(path) as reader,open(tp,'r',encoding='utf8') as text:
            start=0;segment_gid=None;count=0
            for i,line in enumerate(text):
                if i>=reader.n:raise ValueError('text has more records than POS: '+stem)
                tr,context=text_record(line);r=reader.row(i);count=i+1
                if (tr.board,tr.score,tr.meta)!=(r.board,r.score,r.meta):raise ValueError('text/POS record mismatch: '+stem+' row '+str(i))
                boundary=previous is not None and (context[0]<previous[0] or context[1]>previous[1] or context[2]!=previous[2])
                if boundary:gid+=1
                if segment_gid is None:segment_gid=gid;start=i
                elif segment_gid!=gid:
                    db.execute('INSERT INTO segments VALUES(?,?,?,?)',(stem,start,i,segment_gid));segments+=1;start=i;segment_gid=gid
                if stem in holdout_set:db.execute('INSERT OR IGNORE INTO held_groups VALUES(?)',(gid,))
                previous=context
            if count!=reader.n:raise ValueError('text/POS record count mismatch: '+stem)
            if reader.n:db.execute('INSERT INTO segments VALUES(?,?,?,?)',(stem,start,reader.n,segment_gid));segments+=1
    db.commit()
    return {'mode':'CONSERVATIVE_ORDERED_TEXT_GROUPS','groups':gid+1 if previous else 0,'segments':segments,'text_md5':text_hashes,'assumptions':['chronological legal chess trajectories','fullmove never decreases within a game','piece count never increases within a game','WHITE result constant within a game'],'limitation':'Missed boundaries merge games; groups are supersets, not authentic game IDs. No reset at shard boundaries.'}
def filter_data(train:list[Path],holdout:list[Path],hce_dir:Path,out:Path,seed:int=20261025,threshold:int|None=None,text_map:dict[str,Path]|None=None,ordered_stems:list[str]|None=None):
    if threshold is not None and (not isinstance(threshold,int) or threshold<=0):raise ValueError('disagreement threshold must be a positive integer; omit for OFF')
    out=Path(out).absolute();hce_dir=Path(hce_dir).resolve();train=[Path(p).resolve(strict=True) for p in train];holdout=[Path(p).resolve(strict=True) for p in holdout]
    if not holdout:raise ValueError('explicit authoritative holdout inputs required')
    if len(set(holdout))!=len(holdout):raise ValueError('duplicate holdout paths')
    # Exclude hardlinks/symlink aliases of complete holdout shards before training.
    excluded=[];kept_train=[]
    for p in dict.fromkeys(train):
        if any(os.path.samefile(p,h) for h in holdout):excluded.append(p.name)
        else:kept_train.append(p)
    train=kept_train;allpaths=train+holdout
    if len({p.stem for p in allpaths})!=len(allpaths):raise ValueError('unambiguous unique source stems required')
    paths={p.stem:p for p in allpaths};counts={};input_md5={}
    for p in allpaths:
        hp=hce_dir/(p.stem+'.hce') if p in train else None
        with Reader(p,hp) as rd:counts[p.stem]=rd.n
        input_md5[p.name]=md5(p)
        if hp:input_md5[hp.name]=md5(hp)
    if out.exists():raise FileExistsError('output directory must be new; no overwrite')
    out.mkdir(parents=False,mode=0o700);db=None
    try:
        db=sqlite3.connect(out/'forge_sol_filter_work_20261025.sqlite')
        db.executescript('PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL; CREATE TABLE holdout(hash BLOB PRIMARY KEY,key BLOB NOT NULL); CREATE TABLE seen(hash BLOB PRIMARY KEY,key BLOB NOT NULL); CREATE TABLE kept(stem TEXT,row INTEGER,gid INTEGER,hash BLOB,PRIMARY KEY(stem,row)); CREATE TABLE segments(stem TEXT,start INTEGER,end INTEGER,gid INTEGER); CREATE INDEX segments_order ON segments(stem,start); CREATE TABLE held_groups(gid INTEGER PRIMARY KEY); CREATE TABLE audit(hash BLOB PRIMARY KEY,key BLOB NOT NULL);')
        for p in sorted(holdout,key=lambda x:x.name):
            for i,r in enumerate(read_records(p)):
                if invalid_reason(r):raise ValueError('invalid authoritative holdout record')
                digest,key=identity(r);insert_key(db,'holdout',digest,key)
                if i%10000==0:db.commit()
        db.commit();games=build_groups(db,paths,{p.stem for p in holdout},text_map,ordered_stems)
        summary={'format':'FPOS/FHCE version1, original columnar layout','position_identity':'SHA256(board32 || STM1); excludes unavailable castling/EP/clocks','seed':seed,'disagreement_threshold':threshold,'input_md5':input_md5,'excluded_holdout_shards':sorted(excluded),'holdout_sources':[p.name for p in sorted(holdout,key=lambda x:x.name)],'holdout_unique_positions':db.execute('SELECT count(*) FROM holdout').fetchone()[0],'game_policy':games,'game_overlap':'UNVERIFIED_NO_ORDERED_TEXT','real_holdout_overlap':'UNVERIFIED','shards':[],'totals':{'input':0,'kept':0,'dropped':0},'supplied_holdout_overlap':None,'output_duplicate_positions':None}
        order=sorted(train,key=lambda p:(hashlib.sha256((str(seed)+'\0'+p.stem).encode()).digest(),p.name))
        for p in order:
            dropped={};kept=0;segments=db.execute('SELECT start,end,gid FROM segments WHERE stem=? ORDER BY start',(p.stem,)).fetchall();segment_index=0;held_gid=None;held_state=False
            with Reader(p,hce_dir/(p.stem+'.hce')) as rd:
                for i in range(rd.n):
                    r=rd.row(i);reason=invalid_reason(r);gid=None
                    if segments:
                        while i>=segments[segment_index][1]:segment_index+=1
                        begin,end,gid=segments[segment_index]
                        if not begin<=i<end:raise ValueError('incomplete group index')
                    digest,key=identity(r)
                    if gid is not None and gid!=held_gid:
                        held_gid=gid;held_state=bool(db.execute('SELECT 1 FROM held_groups WHERE gid=?',(gid,)).fetchone())
                    if reason is None and held_state:reason='holdout_game_group'
                    if reason is None:
                        held_key=db.execute('SELECT key FROM holdout WHERE hash=?',(digest,)).fetchone()
                        if held_key:
                            if held_key[0]!=key:raise ValueError('position hash collision with holdout')
                            reason='holdout_position'
                    if reason is None:
                        seen=db.execute('SELECT key FROM seen WHERE hash=?',(digest,)).fetchone()
                        if seen:
                            if seen[0]!=key:raise ValueError('position hash collision')
                            reason='duplicate_position'
                    if reason is None:reason=disagreement(r,threshold)
                    if reason:dropped[reason]=dropped.get(reason,0)+1
                    else:
                        insert_key(db,'seen',digest,key);db.execute('INSERT INTO kept VALUES(?,?,?,?)',(p.stem,i,gid,digest));kept+=1
                    if i%10000==0:db.commit()
                db.commit()
                if kept:
                    def selected():
                        for (i,) in db.execute('SELECT row FROM kept WHERE stem=? ORDER BY row',(p.stem,)):yield rd.row(i)
                    stem=p.stem+'_filtered_'+DATE;n=write_records(out/(stem+'.pos'),out/(stem+'.hce'),selected())
                    if n!=kept:raise ValueError('writer selection count mismatch')
                row={'stem':p.stem,'input':rd.n,'kept':kept,'dropped':dropped,'dropped_total':sum(dropped.values())}
                if row['input']!=kept+row['dropped_total']:raise ValueError('accounting mismatch')
                summary['shards'].append(row);summary['totals']['input']+=rd.n;summary['totals']['kept']+=kept;summary['totals']['dropped']+=row['dropped_total']
        # Independent OUTPUT reread audit: neither selection counters nor input keys stand in for this.
        overlaps=duplicates=written=0
        for p in sorted(out.glob('*.pos')):
            for r in read_records(p,p.with_suffix('.hce')):
                if invalid_reason(r):raise ValueError('invalid output record')
                digest,key=identity(r);overlaps+=bool(db.execute('SELECT 1 FROM holdout WHERE hash=?',(digest,)).fetchone());duplicates+=not insert_key(db,'audit',digest,key);written+=1
        if overlaps or duplicates or written!=summary['totals']['kept']:raise ValueError('independent output overlap/uniqueness/count audit failed')
        summary['supplied_holdout_overlap']=overlaps;summary['output_duplicate_positions']=duplicates
        if games['mode']=='CONSERVATIVE_ORDERED_TEXT_GROUPS':
            n=db.execute('SELECT count(*) FROM kept JOIN held_groups USING(gid)').fetchone()[0]
            if n:raise ValueError('retained holdout-touched game group')
            summary['game_overlap']=0
        # Prove text and source shards unchanged before sealing this new output.
        if text_map:
            for stem,digest in games['text_md5'].items():
                if md5(Path(text_map[stem]))!=digest:raise ValueError('text source changed during read')
        for p in allpaths:
            if md5(p)!=input_md5[p.name]:raise ValueError('input changed during read')
            if p in train and md5(hce_dir/(p.stem+'.hce'))!=input_md5[p.stem+'.hce']:raise ValueError('HCE input changed during read')
        db.close();db=None
        for name in ['forge_sol_filter_work_20261025.sqlite','forge_sol_filter_work_20261025.sqlite-journal']:
            q=out/name
            if q.exists():q.unlink()  # only temporary files created by THIS fresh run
        summary['outputs']={p.name:md5(p) for p in sorted(out.iterdir()) if p.is_file()}
        report=out/'forge_sol_datafilter_summary_20261025.json';report.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
        manifest=out/'forge_sol_datafilter_manifest_20261025.md5';manifest.write_text(''.join(md5(p)+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file() and p!=manifest))
        for p in out.iterdir():
            if p.is_file():p.chmod(0o444)
        return summary
    except BaseException as error:
        if db is not None:db.close()
        error_path=out/'forge_sol_datafilter_failed_20261025.json'
        if not error_path.exists():error_path.write_text(json.dumps({'status':'FAILED_UNSEALED_OUTPUT','error_type':type(error).__name__,'error':str(error)},indent=2)+'\n')
        raise

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--train',nargs='+',type=Path,required=True);ap.add_argument('--holdout-pos',nargs='+',type=Path,required=True);ap.add_argument('--hce-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seed',type=int,default=20261025);ap.add_argument('--disagreement-threshold',type=int);ap.add_argument('--text-map',type=Path,help='JSON source stem -> matching ordered text path');ap.add_argument('--ordered-stems',nargs='+',help='Complete chronological source order, including holdouts');a=ap.parse_args()
    tm=json.loads(a.text_map.read_text()) if a.text_map else None
    result=filter_data(a.train,a.holdout_pos,a.hce_dir,a.out,a.seed,a.disagreement_threshold,tm,a.ordered_stems);print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
