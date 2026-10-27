# v2 (Opus 5.5, 2026-10-27) = Sol's forge_sol_S17_gamesplit_20261026.py (sha256 a0331979...5894) with 5 Windows fixes found on the
# PC, marked "v2": the per-source segments cursor is materialized (Python < 3.12 keeps a live statement and the SQLite file
# open after close: scratch cleanup failed with WinError 32), the three write_text calls use UTF-8 and LF, and the config is
# read as UTF-8 (BOM allowed). Logic, DATE, output names and the pinned S16 v2 dependency are unchanged.
"""New-file-only game-group split and sealed-shard dedupe audit.

Ideas: supplied S17 contract and group-splitting reference. Encoding and game
provenance are reused from the unchanged, hash-pinned S16/Job D dependency.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
from types import ModuleType

DATE='20261026'
DEPENDENCY_SHA='5dd0c009566bc5a8c8e06300a8541c5d130d458ca75266a432d1477d1d156332'
DEPENDENCY=Path(__file__).with_name('forge_sol_datafilter_v2_20261026.py')
source=DEPENDENCY.read_bytes()
if hashlib.sha256(source).hexdigest()!=DEPENDENCY_SHA:raise ValueError('S16 dependency SHA256 mismatch')
codec=ModuleType('forge_sol_S17_pinned_S16');codec.__file__=str(DEPENDENCY)
exec(compile(source,str(DEPENDENCY),'exec'),codec.__dict__)

def fingerprint(path):
    sha=hashlib.sha256();md5=hashlib.md5();size=0
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):
            sha.update(chunk);md5.update(chunk);size+=len(chunk)
    return {'sha256':sha.hexdigest(),'md5':md5.hexdigest(),'bytes':size}

def output_line(line):
    # Preserve CRLF/LF; an EOF-terminated source row needs a separator when merged.
    return line if line.endswith(b'\n') else line+b'\n'

def new_output(path,work,sealed_dirs):
    path=Path(path).absolute();work=Path(work).resolve(strict=True)
    if path.exists():raise FileExistsError('output directory must be new')
    if not path.parent.is_dir() or not work.is_dir():raise ValueError('output parent/work directory must exist')
    if '..' in path.parts or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('output must not traverse symlinks or parents')
    if codec._protected(path) or codec._protected(work):raise ValueError('protected output/work directory')
    if any(path.is_relative_to(root) or work.is_relative_to(root) for root in sealed_dirs):
        raise ValueError('output/work must be outside sealed input directories')
    return path,work

def inputs(sources,sealed_dirs,production,provenance):
    if not sources:raise ValueError('at least one ordered source required')
    normalized=[];names=set();files={};labels={};shards={}
    def record(path,label):
        path=Path(path).resolve(strict=True)
        if not path.is_file():raise ValueError('input is not a file')
        files.setdefault(path,fingerprint(path));labels[label]=files[path]
        return path
    def shard(path,label):
        path=record(path,label);hce=path.with_suffix('.hce')
        if hce.exists():hce=record(hce,label[:-4]+'.hce')
        else:hce=None
        if production and (path.stat().st_mode&0o222 or hce is None or hce.stat().st_mode&0o222):
            raise ValueError('production requires sealed POS and provided sealed HCE')
        with codec.Reader(path,hce) as reader:count=reader.n
        if path in shards:shards[path]['aliases'].append(label)
        else:shards[path]={'path':path,'hce':hce,'label':label,'aliases':[],'records':count}
        return path,hce
    for item in sources:
        name=item.get('name')
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',name) or name in names:
            raise ValueError('unique portable source names required')
        names.add(name)
        pos,hce=shard(item['pos'],'ordered/'+name+'.pos')
        row={'name':name,'pos':pos,'hce':hce,'text':record(item['text'],'ordered/'+name+'.txt')}
        if item.get('game_ids') is not None:row['game_ids']=record(item['game_ids'],'ordered/'+name+'.ids')
        normalized.append(row)
    if production and (not isinstance(provenance,str) or not provenance.strip() or any('game_ids' not in s for s in normalized)):
        raise ValueError('production requires authoritative game-ID files and provenance')
    if any('game_ids' in s for s in normalized) and not all('game_ids' in s for s in normalized):
        raise ValueError('game-ID maps must cover every ordered source')
    if all('game_ids' in s for s in normalized) and (not isinstance(provenance,str) or not provenance.strip()):
        raise ValueError('authoritative game-ID provenance required')
    for index,root in enumerate(sealed_dirs):
        found=sorted(root.rglob('*.pos'))
        if not found:raise ValueError('declared sealed directory is empty')
        for path in found:shard(path,'sealed'+str(index)+'/'+path.relative_to(root).as_posix())
    return normalized,files,labels,list(shards.values())

def shard_manifest(db,shards,path,duplicates_path,production):
    db.execute('CREATE TABLE shard_keys(hash BLOB PRIMARY KEY,key BLOB,label TEXT,row INTEGER,score INTEGER,meta INTEGER,hce INTEGER)')
    db.execute('CREATE TABLE shard_md5(md5 TEXT PRIMARY KEY,label TEXT)')
    total=unique=duplicates=conflicts=whole=0
    with path.open('x',encoding='utf-8',newline='\n') as report,duplicates_path.open('x',encoding='utf-8',newline='\n') as ledger:
        for item in shards:
            label=item['label'];meta=fingerprint(item['path']);previous=db.execute('SELECT label FROM shard_md5 WHERE md5=?',(meta['md5'],)).fetchone()
            if previous:whole+=1
            else:db.execute('INSERT INTO shard_md5 VALUES(?,?)',(meta['md5'],label))
            kept=dropped=badlabels=unknown_hce=0
            with codec.Reader(item['path'],item['hce']) as reader:
                for i in range(reader.n):
                    row=reader.row(i)
                    if codec.invalid_reason(row):raise ValueError('invalid record in dedupe manifest input')
                    digest,key=codec.identity(row);old=db.execute('SELECT key,label,row,score,meta,hce FROM shard_keys WHERE hash=?',(digest,)).fetchone()
                    if old:
                        if old[0]!=key:raise ValueError('position hash collision')
                        unknown_hce+=old[5] is None or row.hce is None
                        conflict=(old[3],old[4])!=(row.score,row.meta) or (old[5] is not None and row.hce is not None and old[5]!=row.hce)
                        badlabels+=conflict;dropped+=1
                        ledger.write(json.dumps({'source':label,'row':i,'position_sha256':digest.hex(),'canonical_source':old[1],
                            'canonical_row':old[2],'conflicting_label':bool(conflict),'hce_comparison_known':old[5] is not None and row.hce is not None},sort_keys=True)+'\n')
                    else:
                        db.execute('INSERT INTO shard_keys VALUES(?,?,?,?,?,?,?)',(digest,key,label,i,row.score,row.meta,row.hce));kept+=1
                    if i%10000==0:db.commit()
            entry={'source':label,'aliases':item['aliases'],'records':reader.n,'unique_first_positions':kept,'duplicate_positions':dropped,
                   'conflicting_label_duplicates':badlabels,'duplicates_with_unknown_HCE':unknown_hce,'whole_POS_duplicate_of':previous[0] if previous else None,
                   'pos':meta,'hce':fingerprint(item['hce']) if item['hce'] else 'UNVERIFIED_MISSING_HCE',
                   'POS_is_readonly':not bool(item['path'].stat().st_mode&0o222)}
            report.write(json.dumps(entry,sort_keys=True)+'\n');total+=reader.n;unique+=kept;duplicates+=dropped;conflicts+=badlabels
        db.commit()
    return {'files':len(shards),'records':total,'unique_positions':unique,'duplicate_positions':duplicates,
            'conflicting_label_duplicates':conflicts,'whole_shard_duplicates':whole}

def split_sources(sources,out,work,*,seed,validation_basis_points,production=True,game_id_provenance=None,sealed_dirs=()):
    if type(seed) is not int or not 0<=seed<2**64:raise ValueError('seed must be an unsigned64 integer')
    if type(validation_basis_points) is not int or not 0<validation_basis_points<10000:
        raise ValueError('validation basis points must be 1..9999')
    roots=[Path(p).resolve(strict=True) for p in sealed_dirs]
    if any(not p.is_dir() for p in roots):raise ValueError('sealed input root is not a directory')
    out,work=new_output(out,work,roots)
    sources,files,labels,shards=inputs(sources,roots,production,game_id_provenance)
    rows=sum(s['records'] for s in shards);text_bytes=sum(files[s['text']]['bytes'] for s in sources)
    required=512*rows+4*text_bytes+8*1048576
    if os.stat(out.parent).st_dev==os.stat(work).st_dev:
        if shutil.disk_usage(work).free<2*required:raise ValueError('insufficient free disk for scratch/output')
    elif min(shutil.disk_usage(work).free,shutil.disk_usage(out.parent).free)<required:
        raise ValueError('insufficient free disk for scratch/output')
    out.mkdir(mode=0o700);scratch=None;db=None
    try:
        scratch=Path(tempfile.mkdtemp(prefix='forge_sol_S17_sqlite_',dir=work))
        db=sqlite3.connect(scratch/'split.sqlite');db.row_factory=sqlite3.Row
        db.executescript('PRAGMA journal_mode=WAL; PRAGMA synchronous=OFF; CREATE TABLE segments(stem TEXT,start INTEGER,end INTEGER,gid TEXT); CREATE INDEX segment_order ON segments(stem,start); CREATE TABLE held_groups(gid TEXT PRIMARY KEY); CREATE TABLE assigned(gid TEXT PRIMARY KEY,rank BLOB,split TEXT); CREATE TABLE rows(rid INTEGER PRIMARY KEY,stem TEXT,row INTEGER,gid TEXT,hash BLOB,key BLOB,board BLOB,score INTEGER,meta INTEGER,hce INTEGER,line BLOB,keep INTEGER DEFAULT 0,reason TEXT); CREATE TABLE validation_keys(hash BLOB PRIMARY KEY,key BLOB); CREATE TABLE train_keys(hash BLOB PRIMARY KEY,key BLOB);')
        paths={s['name']:s['pos'] for s in sources};texts={s['name']:s['text'] for s in sources};order=list(paths)
        ids={s['name']:s['game_ids'] for s in sources} if all('game_ids' in s for s in sources) else None
        policy=codec._groups(db,paths,set(),texts,order,ids,game_id_provenance)
        for (gid,) in db.execute('SELECT DISTINCT gid FROM segments'):
            rank=hashlib.sha256(b'S17-group-split\0'+str(seed).encode()+b'\0'+gid.encode()).digest()
            db.execute('INSERT INTO assigned VALUES(?,?,?)',(gid,rank,'train'))
        groups=db.execute('SELECT count(*) FROM assigned').fetchone()[0]
        if groups<2:raise ValueError('at least two defined groups required for validation split')
        nval=max(1,min(groups-1,(groups*validation_basis_points+9999)//10000))
        db.execute('UPDATE assigned SET split="validation" WHERE gid IN (SELECT gid FROM assigned ORDER BY rank,gid LIMIT ?)',(nval,))
        for item in sources:
            segments=iter(db.execute('SELECT start,end,gid FROM segments WHERE stem=? ORDER BY start',(item['name'],)).fetchall());segment=next(segments,None)  # v2: no live statement at close (WinError 32)
            with codec.Reader(item['pos'],item['hce']) as reader,item['text'].open('rb') as text:
                for i in range(reader.n):
                    line=text.readline();record,context=codec.text_record(line.decode('utf-8'))
                    original=reader.row(i)
                    if (record.board,record.score,record.meta)!=(original.board,original.score,original.meta):raise ValueError('text/POS mismatch during split')
                    while segment is not None and i>=segment[1]:segment=next(segments,None)
                    if segment is None or not segment[0]<=i<segment[1]:raise ValueError('incomplete group index')
                    digest,key=codec.identity(original)
                    db.execute('INSERT INTO rows(stem,row,gid,hash,key,board,score,meta,hce,line) VALUES(?,?,?,?,?,?,?,?,?,?)',
                               (item['name'],i,segment[2],digest,key,original.board,original.score,original.meta,original.hce,line))
                if text.read(1):raise ValueError('extra text after POS count')
        db.commit()
        for row in db.execute('SELECT rows.* FROM rows JOIN assigned USING(gid) WHERE split="validation" ORDER BY rid'):
            keep=codec.insert_key(db,'validation_keys',row['hash'],row['key'])
            db.execute('UPDATE rows SET keep=?,reason=? WHERE rid=?',(int(keep),None if keep else 'duplicate_validation',row['rid']))
        for row in db.execute('SELECT rows.* FROM rows JOIN assigned USING(gid) WHERE split="train" ORDER BY rid'):
            old=db.execute('SELECT key FROM validation_keys WHERE hash=?',(row['hash'],)).fetchone()
            if old and old[0]!=row['key']:raise ValueError('position hash collision across split')
            keep=not old and codec.insert_key(db,'train_keys',row['hash'],row['key'])
            db.execute('UPDATE rows SET keep=?,reason=? WHERE rid=?',(int(keep),None if keep else ('validation_position_overlap' if old else 'duplicate_train'),row['rid']))
        db.commit();output_counts={}
        db.executescript('CREATE TABLE train_audit(hash BLOB PRIMARY KEY,key BLOB); CREATE TABLE validation_audit(hash BLOB PRIMARY KEY,key BLOB); CREATE TABLE output_groups(part TEXT,gid TEXT,PRIMARY KEY(part,gid));')
        ledger=out/('forge_sol_S17_row_selection_'+DATE+'.jsonl')
        with ledger.open('x',encoding='utf-8',newline='\n') as stream:
            for row in db.execute('SELECT rows.*,assigned.split FROM rows JOIN assigned USING(gid) ORDER BY rid'):
                group=row['gid'] if policy['authentic_ids'] else 'inferred:'+row['gid']
                stream.write(json.dumps({'source':row['stem'],'row':row['row'],'group':group,'assigned_split':row['split'],
                    'status':'kept' if row['keep'] else 'dropped','reason':row['reason'],'position_sha256':row['hash'].hex()},sort_keys=True)+'\n')
        for part in ('train','validation'):
            path=out/('forge_sol_S17_'+part+'_'+DATE+'.txt')
            with path.open('xb') as stream:
                for row in db.execute('SELECT line,gid FROM rows JOIN assigned USING(gid) WHERE keep=1 AND split=? ORDER BY rid',(part,)):
                    stream.write(output_line(row[0]));db.execute('INSERT OR IGNORE INTO output_groups VALUES(?,?)',(part,row[1]))
            count=0
            with path.open('rb') as stream:
                for selected in db.execute('SELECT line FROM rows JOIN assigned USING(gid) WHERE keep=1 AND split=? ORDER BY rid',(part,)):
                    line=stream.readline()
                    if line!=output_line(selected[0]):raise ValueError('output differs from selected original record')
                    record,_=codec.text_record(line.decode('utf-8'));digest,key=codec.identity(record)
                    if not codec.insert_key(db,part+'_audit',digest,key):raise ValueError('duplicate position in output reread')
                    count+=1
                if stream.read(1):raise ValueError('extra output record after original selection')
            output_counts[part]=count
        cross_groups=db.execute('SELECT count(*) FROM (SELECT gid FROM output_groups GROUP BY gid HAVING count(DISTINCT part)>1)').fetchone()[0]
        cross_positions=db.execute('SELECT count(*) FROM train_audit JOIN validation_audit USING(hash)').fetchone()[0]
        if cross_groups or cross_positions:raise ValueError('cross-split group/position overlap')
        if production and not all(output_counts.values()):raise ValueError('production split must retain both nonempty parts')
        available=db.execute('SELECT count(*) FROM rows WHERE keep=1 AND hce IS NULL').fetchone()[0]==0
        if available:
            for part in ('train','validation'):
                def records():
                    for r in db.execute('SELECT board,score,meta,hce FROM rows JOIN assigned USING(gid) WHERE keep=1 AND split=? ORDER BY rid',(part,)):yield codec.Record(*r)
                codec.write_records(out/('forge_sol_S17_'+part+'_'+DATE+'.pos'),out/('forge_sol_S17_'+part+'_'+DATE+'.hce'),records())
        audit=shard_manifest(db,shards,out/('forge_sol_S17_shard_dedupe_'+DATE+'.jsonl'),out/('forge_sol_S17_duplicate_rows_'+DATE+'.jsonl'),production)
        total=db.execute('SELECT count(*) FROM rows').fetchone()[0];kept=sum(output_counts.values())
        reasons={r[0]:r[1] for r in db.execute('SELECT reason,count(*) FROM rows WHERE keep=0 GROUP BY reason')}
        if any(fingerprint(path)!=value for path,value in files.items()):raise ValueError('input changed during read')
        summary={'mode':'OWNER_AUTHORITATIVE_GAME_IDS' if production else 'DIAGNOSTIC_ONLY','seed':seed,'validation_basis_points':validation_basis_points,
                 'group_assignment':'ceil(group_count*basis_points/10000), bounded to 1..n-1; first SHA256(domain,seed,gid) ranks',
                 'text_output_policy':'Preserve each original record; preserve LF/CRLF; append LF only to EOF-unterminated source rows when exporting',
                 'groups':groups,'assigned_validation_groups':nval,'group_policy':policy,'input_rows':total,'retained_rows':kept,'dropped_rows':total-kept,
                 'dropped_reasons':reasons,'output_rows':output_counts,'cross_split_defined_groups':cross_groups,'cross_split_position_overlap':cross_positions,
                 'game_overlap_verified':policy['authentic_ids'],'authentic_game_overlap':0 if policy['authentic_ids'] else 'UNVERIFIED_NO_AUTHORITATIVE_GAME_IDS',
                 'external_013_014_overlap':'UNVERIFIED_NOT_SUPPLIED','training_approved':False,'HCE_values_invented':False,
                 'binary_output_status':'WRITTEN_WITH_PROVIDED_HCE' if available else 'UNVERIFIED_MISSING_HCE',
                 'position_identity':'S16 SHA256(board32||STM); unavailable castling/EP/clocks excluded','sealed_manifest':audit,'input_inventory':labels,
                 'S16_dependency_sha256':DEPENDENCY_SHA,'base_codec_sha256':codec.BASE_SHA256,'source_inputs_unchanged':True}
        db.close();db=None;shutil.rmtree(scratch)
        (out/('forge_sol_S17_summary_'+DATE+'.json')).write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n', encoding='utf-8', newline='\n')  # v2
        manifest=out/('forge_sol_S17_output_manifest_'+DATE+'.md5')
        manifest.write_text(''.join(codec.md5(p)+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file()), encoding='utf-8', newline='\n')  # v2
        for path in out.iterdir():
            if path.is_file():path.chmod(0o444)
        return summary
    except BaseException as error:
        if db is not None:db.close()
        (out/('forge_sol_S17_FAILED_UNSEALED_'+DATE+'.json')).write_text(json.dumps({'status':'FAILED_UNSEALED','error':str(error)},indent=2)+'\n', encoding='utf-8', newline='\n')  # v2
        raise

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--diagnostic-mode',action='store_true');args=parser.parse_args(argv)
    try:
        path=args.config.resolve(strict=True);config=json.loads(path.read_text(encoding='utf-8-sig'));base=path.parent  # v2: explicit encoding (Windows cp1252)
        if set(config)-{'sources','sealed_pos_dirs','out','work_dir','seed','validation_basis_points','game_id_provenance'}:
            raise ValueError('unknown config key')
        def resolve(value):return (base/Path(value)).resolve(strict=True)
        sources=[]
        for raw in config['sources']:
            if set(raw)-{'name','text','pos','game_ids'}:raise ValueError('unknown source key')
            sources.append({k:(resolve(v) if k!='name' else v) for k,v in raw.items()})
        out=(base/Path(config['out'])).absolute()
        result=split_sources(sources,out,resolve(config['work_dir']),seed=config['seed'],validation_basis_points=config['validation_basis_points'],
            production=not args.diagnostic_mode,game_id_provenance=config.get('game_id_provenance'),sealed_dirs=[resolve(p) for p in config.get('sealed_pos_dirs',[])])
        print(json.dumps({'status':'PASS_DEFINED_GROUP_SPLIT','mode':result['mode'],'groups':result['groups'],'rows':result['output_rows'],'authentic_game_overlap':result['authentic_game_overlap']},sort_keys=True))
        return 0
    except (ValueError,OSError,KeyError,TypeError) as error:parser.exit(1,str(error)+'\n')

if __name__=='__main__':raise SystemExit(main())
