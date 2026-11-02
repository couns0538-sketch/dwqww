"""Create a new evidence pack; missing historical provenance remains BLOCKED.

archived-game-rows-v1 is a normalized historical evidence adapter, NOT a PGN or
binpack decoder. Production history needs a separately reviewed digest registry.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from pack_io import (CHUNK_ROWS, POPULATION_ROLES, ResourceBudget, decode, encoded, estimate_budget, hashes,
                     lines, need, pack_path, raw_record, safe_path, state,
                     pulse, tree_files, validate_request, write_json)


def canonical_game_id(origin_sha256, game_index):
    need(isinstance(origin_sha256,str) and len(origin_sha256)==64 and
         all(c in '0123456789abcdef' for c in origin_sha256),'canonical source SHA256 required')
    need(type(game_index) is int and game_index>=0,'authentic nonnegative game index required')
    return hashlib.sha256(b'astra-gameprov-v1\0'+origin_sha256.encode('ascii')+b'\0'+str(game_index).encode('ascii')).hexdigest()


def seal_hashes(out, *, replace=False):
    out=safe_path(out,write=True)
    rows=[]
    for p in sorted(tree_files(out)):
        relative=p.relative_to(out).as_posix()
        if relative not in ('MD5SUMS','SHA256SUMS'):
            rows.append((relative,hashes(p)))
    for alg,name in [('md5','MD5SUMS'),('sha256','SHA256SUMS')]:
        with (out/name).open('w' if replace else 'x',encoding='ascii',newline='\n') as f:
            for path,digests in rows:f.write(digests[alg]+'  '+path+'\n')


def freeze(spec, output, relative, *, resumed=False):
    source=safe_path(spec['path']); target=pack_path(output,relative)
    before=source.stat()
    digest=hashlib.sha256(); count=size=0
    if resumed:
        need(target.is_file(),'resume missing committed input')
        stream=lines(target,compressed=True)
        for raw in stream:digest.update(raw);count+=1;size+=len(raw)
        need(digest.hexdigest()==spec['sha256'] and count==spec.get('rows',count),'resume input hash/count mismatch')
        need(hashes(source)['sha256']==spec['sha256'],'resume original source changed')
        return dict(sha256=digest.hexdigest(),rows=count,bytes=size,path=relative)
    target.parent.mkdir(parents=True,exist_ok=True)
    pending=target.with_name(target.name+'.pending')
    need(not target.exists() and not pending.exists(),'existing/orphan input output refused')
    with pending.open('xb') as raw_out:
        with gzip.GzipFile(filename='',fileobj=raw_out,mode='wb',compresslevel=1,mtime=0) as compressed:
            for raw in lines(source):
                if count%4096==0:pulse()
                digest.update(raw);count+=1;size+=len(raw);compressed.write(raw)
        raw_out.flush();os.fsync(raw_out.fileno())
    after=source.stat()
    need((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'source identity changed during copy')
    need(digest.hexdigest()==spec['sha256'],'consumed input SHA256 mismatch')
    need(count==spec.get('rows',count),'input row count mismatch')
    if 'bytes' in spec:need(size==spec['bytes'],'input byte count mismatch')
    os.rename(pending,target)  # Windows rename refuses replacement.
    return dict(sha256=digest.hexdigest(),rows=count,bytes=size,path=relative)


def database(path):
    con=sqlite3.connect(path)
    con.execute('PRAGMA temp_store=MEMORY')
    con.execute('PRAGMA cache_size=-32768')
    con.executescript('''
      CREATE TABLE cohort(source TEXT,row INTEGER,payload TEXT,matched INTEGER DEFAULT 0,trained INTEGER DEFAULT 0,
                          PRIMARY KEY(source,row)) WITHOUT ROWID;
      CREATE TABLE origins(origin TEXT,game INTEGER,ply INTEGER,fen TEXT,PRIMARY KEY(origin,game,ply)) WITHOUT ROWID;
      CREATE TABLE bindings(input TEXT,row INTEGER,origin TEXT,game INTEGER,ply INTEGER,used INTEGER DEFAULT 0,
                            PRIMARY KEY(input,row)) WITHOUT ROWID;
      CREATE TABLE held_games(game_id TEXT PRIMARY KEY) WITHOUT ROWID;
    ''')
    return con


def populate_evidence(con, manifest, out):
    for spec in manifest['origins']:
        for raw in lines(pack_path(out,spec['path']),compressed=True):
            row=decode(raw)
            need(set(row)=={'game_index','ply','fen'},'archived game row fields')
            need(type(row['game_index']) is int and row['game_index']>=0 and type(row['ply']) is int and row['ply']>=0,'invalid archived game/ply')
            state(row['fen'])
            try:con.execute('INSERT INTO origins VALUES (?,?,?,?)',(spec['sha256'],row['game_index'],row['ply'],row['fen']))
            except sqlite3.IntegrityError as e:raise ValueError('ambiguous duplicate origin game/ply') from e
    specs={s['id']:s for s in manifest['inputs']}
    for spec in manifest['bindings']:
        for raw in lines(pack_path(out,spec['path']),compressed=True):
            row=decode(raw)
            need(set(row)=={'input_id','physical_row','origin_sha256','game_index','ply'},'binding fields')
            src=specs.get(row['input_id'])
            need(src is not None and src['role'] in POPULATION_ROLES,'binding outside original population')
            need(type(row['physical_row']) is int and 1<=row['physical_row']<=src['rows'],'binding row outside population')
            canonical_game_id(row['origin_sha256'],row['game_index'])
            need(type(row['ply']) is int and row['ply']>=0,'invalid binding ply')
            found=con.execute('SELECT 1 FROM origins WHERE origin=? AND game=? AND ply=?',
                              (row['origin_sha256'],row['game_index'],row['ply'])).fetchone()
            need(found is not None,'binding has no archived original game position')
            try:con.execute('INSERT INTO bindings(input,row,origin,game,ply) VALUES (?,?,?,?,?)',
                 (row['input_id'],row['physical_row'],row['origin_sha256'],row['game_index'],row['ply']))
            except sqlite3.IntegrityError as e:raise ValueError('ambiguous duplicate row binding') from e
            if src['role'].startswith('holdout'):
                con.execute('INSERT OR IGNORE INTO held_games VALUES (?)',(canonical_game_id(row['origin_sha256'],row['game_index']),))
    con.commit()


def validate_original_state(con, manifest, out):
    inputs=manifest['inputs'];labels=manifest['source_labels']
    cohort=next(s for s in inputs if s['role']=='cohort')
    for number,raw in enumerate(lines(pack_path(out,cohort['path']),compressed=True),1):
        if number%4096==1:pulse()
        r=decode(raw);state(r.get('fen'))
        need(r.get('source') in labels and type(r.get('source_row')) is int and r['source_row']>0,'cohort exact source identity required')
        try:con.execute('INSERT INTO cohort(source,row,payload) VALUES (?,?,?)',
                        (labels[r['source']],r['source_row'],encoded(r).decode()))
        except sqlite3.IntegrityError as e:raise ValueError('duplicate cohort source row') from e
    con.commit()
    for source in (s for s in inputs if s['role']=='source'):
        for number,raw in enumerate(lines(pack_path(out,source['path']),compressed=True),1):
            if number%4096==1:pulse()
            record=raw_record(raw)
            wanted=con.execute('SELECT payload FROM cohort WHERE source=? AND row=?',(source['id'],number)).fetchone()
            if wanted is not None:
                r=decode(wanted[0])
                need(r['fen']==record['fen'] and r.get('raw_score')==record['raw_score'] and
                     r.get('result_white')==record['result_white'] and r.get('ply')==record['ply'],
                     'cohort original source FEN/score/result/ply mismatch')
                con.execute('UPDATE cohort SET matched=1 WHERE source=? AND row=?',(source['id'],number))
        con.commit()
    need(con.execute('SELECT COUNT(*) FROM cohort WHERE matched=0').fetchone()[0]==0,'cohort missing original source rows')


class ChunkWriter:
    def __init__(self, output):self.output=output;self.names=[];self.stream=None;self.raw=None;self.count=0
    def append(self,row):
        if self.count%CHUNK_ROWS==0:
            pulse()
            self.close()
            name=f'rows/{len(self.names):06d}.jsonl.gz';self.names.append(name)
            p=pack_path(self.output,name);p.parent.mkdir(exist_ok=True)
            self.raw=p.open('xb');self.stream=gzip.GzipFile(filename='',fileobj=self.raw,mode='wb',mtime=0,compresslevel=1)
        self.stream.write(encoded(row));self.count+=1
    def close(self):
        if self.stream is not None:
            self.stream.close();self.raw.flush();os.fsync(self.raw.fileno());self.raw.close();self.stream=self.raw=None


def produce_rows(con, manifest, out):
    writer=ChunkWriter(out);ranges=[];counts={'population':0,'traced':0,'untraceable':0,'train':0,'holdout':0,'moved_to_holdout':0}
    specs={s['id']:s for s in manifest['inputs']}
    try:
        for spec in manifest['inputs']:
            if spec['role'] not in POPULATION_ROLES:continue
            start=None;last=0
            has_bindings=con.execute('SELECT 1 FROM bindings WHERE input=? LIMIT 1',(spec['id'],)).fetchone() is not None
            for number,raw in enumerate(lines(pack_path(out,spec['path']),compressed=True),1):
                if number%4096==1:pulse()
                counts['population']+=1;last=number
                if spec['format']=='jsonl':
                    record=decode(raw);state(record.get('fen'))
                    source_id=manifest['source_labels'].get(record.get('source'))
                    source_row=record.get('source_row')
                    need(source_id is not None and type(source_row) is int,'exact original row identity required')
                    existing=con.execute('SELECT payload,trained FROM cohort WHERE source=? AND row=?',(source_id,source_row)).fetchone()
                    need(existing is not None and decode(existing[0])==record,'training record not exact frozen cohort source row')
                    need(existing[1]==0,'duplicate training source row')
                    con.execute('UPDATE cohort SET trained=1 WHERE source=? AND row=?',(source_id,source_row))
                    original=record;fen=record['fen'];ply=record['ply']
                    identity=specs[source_id]['sha256']+':'+str(source_row)
                else:
                    record=raw_record(raw);original=record['original_line'];fen=record['fen'];ply=record['ply']
                    identity=spec['sha256']+':'+str(number)
                binding=con.execute('SELECT origin,game,ply FROM bindings WHERE input=? AND row=?',(spec['id'],number)).fetchone() if has_bindings else None
                if binding is None:
                    counts['untraceable']+=1
                    if start is None:start=number
                    continue
                if start is not None:
                    need(len(ranges)<100000,'exclusion range reservation exceeded; use a reviewed streaming-ledger extension')
                    ranges.append(dict(input_id=spec['id'],first=start,last=number-1,outcome='UNTRACEABLE',game_id=None,reason='NO_AUTHENTIC_GAME_EVIDENCE'));start=None
                origin,game,original_ply=binding
                position=con.execute('SELECT fen FROM origins WHERE origin=? AND game=? AND ply=?',binding).fetchone()
                need(position is not None and position[0]==fen and original_ply==ply,'source game FEN/ply mismatch')
                game_id=canonical_game_id(origin,game)
                held=con.execute('SELECT 1 FROM held_games WHERE game_id=?',(game_id,)).fetchone() is not None
                outcome='holdout' if spec['role'].startswith('holdout') else ('moved_holdout' if held else 'train')
                counts['traced']+=1
                counts['train' if outcome=='train' else 'holdout']+=1
                if outcome=='moved_holdout':counts['moved_to_holdout']+=1
                writer.append(dict(input_id=spec['id'],physical_row=number,row_id=identity,original=original,fen=fen,
                                   ply=ply,game_id=game_id,origin_sha256=origin,game_index=game,outcome=outcome))
                con.execute('UPDATE bindings SET used=1 WHERE input=? AND row=?',(spec['id'],number))
            if start is not None:
                need(len(ranges)<100000,'exclusion range reservation exceeded')
                ranges.append(dict(input_id=spec['id'],first=start,last=last,outcome='UNTRACEABLE',game_id=None,reason='NO_AUTHENTIC_GAME_EVIDENCE'))
            con.commit()
    finally:writer.close()
    need(con.execute('SELECT COUNT(*) FROM bindings WHERE used=0').fetchone()[0]==0,'unaccounted bindings')
    write_json(out/'UNTRACEABLE.json',{'schema':1,'ranges':ranges})
    return writer.names,counts


def _build_pack(request_path, output, *, fixture_trust=None, resume=False, interrupt_after=None):
    request_path=safe_path(request_path);out=safe_path(output,write=True)
    raw=request_path.read_bytes();req=decode(raw);validate_request(req,fixture_trust)
    request_hash=hashlib.sha256(raw).hexdigest()
    if resume:
        need(out.is_dir() and not (out/'PACK.json').exists(),'resume requires unfinished owned pack')
        checkpoint=decode((out/'CHECKPOINT.json').read_bytes())
        need(checkpoint['request_sha256']==request_hash,'resume request changed')
    else:
        out.mkdir(parents=True,exist_ok=False)
        checkpoint={'schema':1,'request_sha256':request_hash,'completed':[]}
        write_json(out/'CHECKPOINT.json',checkpoint)
    manifest={'schema':1,'scope':req['scope'],'request_sha256':request_hash,'inputs':[],
              'source_labels':req['source_labels'],'origins':[],'bindings':[],
              'authenticity':'Production origins require independently reviewed registry; hashes alone do not authenticate history.'}
    done=set(checkpoint['completed']);step=0
    for category in ('inputs','origins','bindings'):
        for i,spec in enumerate(req[category]):
            relative=f'{category}/{i:03d}.gz';step+=1
            frozen=freeze(spec,out,relative,resumed=relative in done)
            copied={k:v for k,v in spec.items() if k!='path'};copied.update(frozen)
            manifest[category].append(copied)
            if relative not in done:
                done.add(relative);checkpoint['completed']=sorted(done)
                write_json(out/'CHECKPOINT.json',checkpoint,replace=True)
            if interrupt_after==step:raise RuntimeError('cooperative interruption after committed input')
    # Resumption is deliberately restricted to completed input-copy boundaries.
    # A partial processing state is preserved and requires a fresh attempt.
    work=out.parent/(out.name+'.build.sqlite')
    need(not work.exists(),'existing processing state requires new output attempt')
    con=database(work)
    try:
        populate_evidence(con,manifest,out)
        validate_original_state(con,manifest,out)
        chunks,counts=produce_rows(con,manifest,out)
    finally:con.close()
    manifest['row_chunks']=chunks;manifest['producer_counts']=counts
    manifest['status']='PENDING_INDEPENDENT_VERIFICATION'
    manifest['tool_hashes']={}
    tools_dir=out/'tools';tools_dir.mkdir()
    for name in ('pack_io.py','verify_game_provenance.py'):
        source=Path(__file__).with_name(name);content=source.read_bytes()
        with (tools_dir/name).open('xb') as stream:stream.write(content)
        manifest['tool_hashes'][name]=hashlib.sha256(content).hexdigest()
    write_json(out/'PACK.json',manifest)
    seal_hashes(out)
    return manifest


def build_pack(request_path, output, *, fixture_trust=None, resume=False, interrupt_after=None):
    request_path=safe_path(request_path);out=safe_path(output,write=True)
    req=decode(request_path.read_bytes());validate_request(req,fixture_trust)
    for category in ('inputs','origins','bindings'):
        for spec in req[category]:
            size=os.lstat(safe_path(spec['path'])).st_size
            need('bytes' not in spec or spec['bytes']==size,'input declared byte reservation differs from actual file')
            spec['bytes']=size
    work=out.parent/(out.name+'.build.sqlite')
    tracked=[out,work,Path(str(work)+'-journal'),Path(str(work)+'-wal'),Path(str(work)+'-shm')]
    with ResourceBudget(estimate_budget(req),tracked) as budget:
        result=_build_pack(request_path,out,fixture_trust=fixture_trust,resume=resume,interrupt_after=interrupt_after)
        budget.check()
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    build_pack(args.request,args.out,resume=args.resume)


if __name__=='__main__':main()
