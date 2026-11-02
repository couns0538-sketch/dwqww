"""Independent pack-only census and game-overlap proof; no builder imports.

The pack is the complete data boundary. Historical authenticity is supplied by
the reviewed code registry, never by an arbitrary assertion inside the pack.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from pack_io import (POPULATION_ROLES, ResourceBudget, decode, encoded, estimate_budget, hashes, lines,
                     need, pack_path, raw_record, safe_path, state,
                     pulse, tree_files, validate_request, write_json)


def verify_manifests(root):
    actual={p.relative_to(root).as_posix() for p in tree_files(root)
            if p.relative_to(root).as_posix() not in ('MD5SUMS','SHA256SUMS')}
    for algorithm,name,length in [('md5','MD5SUMS',32),('sha256','SHA256SUMS',64)]:
        listed={}
        for raw in (root/name).read_text(encoding='ascii').splitlines():
            fields=raw.split('  ',1)
            need(len(fields)==2 and len(fields[0])==length,'invalid checksum row')
            digest,relative=fields
            need(relative not in listed,'duplicate checksum entry')
            p=pack_path(root,relative)
            need(p.is_file() and hashes(p)[algorithm]==digest,'checksum mismatch: '+relative)
            listed[relative]=digest
        need(set(listed)==actual,'checksum coverage mismatch')


def consume(root,spec):
    digest=hashlib.sha256();count=0;size=0
    for raw in lines(pack_path(root,spec['path']),compressed=True):
        count+=1;size+=len(raw);digest.update(raw)
        if count%4096==1:pulse()
        yield count,raw
    need(digest.hexdigest()==spec['sha256'],'bundled original input SHA256 mismatch')
    need(count==spec['rows'] and size==spec['bytes'],'bundled input count/bytes mismatch')


def _verify_pack(pack, output, *, fixture_trust=None):
    root=safe_path(pack);out=safe_path(output,write=True)
    need(root.is_dir(),'pack directory required')
    out.mkdir(parents=True,exist_ok=False)
    verify_manifests(root)
    manifest=decode((root/'PACK.json').read_bytes())
    validate_request(manifest,fixture_trust)
    need(set(manifest.get('tool_hashes',{}))=={'pack_io.py','verify_game_provenance.py'},'complete bound verifier code required')
    for name,digest in manifest['tool_hashes'].items():
        need(hashes(pack_path(root,'tools/'+name))['sha256']==digest and
             hashes(Path(__file__).with_name(name))['sha256']==digest,'verifier code identity mismatch')
    paths=[s['path'] for kind in ('inputs','origins','bindings') for s in manifest[kind]]+manifest['row_chunks']
    need(len(paths)==len(set(paths)),'duplicate artifact reference')
    for p in paths:pack_path(root,p)
    con=sqlite3.connect(out/'audit.sqlite')
    con.execute('PRAGMA temp_store=MEMORY');con.execute('PRAGMA cache_size=-32768')
    con.executescript('''
      CREATE TABLE evidence(origin TEXT,gidx INTEGER,ply INTEGER,fen TEXT,
                            PRIMARY KEY(origin,gidx,ply)) WITHOUT ROWID;
      CREATE TABLE links(input TEXT,physical INTEGER,origin TEXT,gidx INTEGER,ply INTEGER,
                         used INTEGER DEFAULT 0,PRIMARY KEY(input,physical)) WITHOUT ROWID;
      CREATE TABLE emitted(input TEXT,physical INTEGER,payload TEXT,used INTEGER DEFAULT 0,
                           PRIMARY KEY(input,physical)) WITHOUT ROWID;
      CREATE TABLE games(id TEXT PRIMARY KEY,train INTEGER,holdout INTEGER) WITHOUT ROWID;
      CREATE TABLE original_hold_games(id TEXT PRIMARY KEY) WITHOUT ROWID;
      CREATE TABLE originals(source TEXT,physical INTEGER,payload TEXT,matched INTEGER DEFAULT 0,
                             selected INTEGER DEFAULT 0,PRIMARY KEY(source,physical)) WITHOUT ROWID;
    ''')
    counts={'population':0,'traced':0,'untraceable':0,'train':0,'holdout':0,'moved_to_holdout':0}
    by_role={r:{'rows':0,'traced':0,'untraceable':0} for r in ('train','holdout013','holdout014')}
    specs={s['id']:s for s in manifest['inputs']}
    try:
        for origin in manifest['origins']:
            for _,raw in consume(root,origin):
                item=decode(raw)
                need(set(item)=={'game_index','ply','fen'},'invalid origin fields')
                need(type(item['game_index']) is int and item['game_index']>=0 and
                     type(item['ply']) is int and item['ply']>=0,'invalid archived game index/ply')
                state(item['fen'])
                try:con.execute('INSERT INTO evidence VALUES (?,?,?,?)',
                                (origin['sha256'],item['game_index'],item['ply'],item['fen']))
                except sqlite3.IntegrityError as e:raise ValueError('ambiguous original game/ply') from e
        for binding in manifest['bindings']:
            for _,raw in consume(root,binding):
                item=decode(raw)
                need(set(item)=={'input_id','physical_row','origin_sha256','game_index','ply'},'invalid binding fields')
                inp=specs.get(item['input_id'])
                need(inp is not None and inp['role'] in POPULATION_ROLES,'binding not in original population')
                need(type(item['physical_row']) is int and 1<=item['physical_row']<=inp['rows'],'binding outside population')
                need(type(item['game_index']) is int and item['game_index']>=0 and
                     type(item['ply']) is int and item['ply']>=0,'invalid binding game/ply')
                expected=con.execute('SELECT fen FROM evidence WHERE origin=? AND gidx=? AND ply=?',
                        (item['origin_sha256'],item['game_index'],item['ply'])).fetchone()
                need(expected is not None,'unbound original game evidence')
                try:con.execute('INSERT INTO links(input,physical,origin,gidx,ply) VALUES (?,?,?,?,?)',
                      (item['input_id'],item['physical_row'],item['origin_sha256'],item['game_index'],item['ply']))
                except sqlite3.IntegrityError as e:raise ValueError('duplicate/ambiguous row binding') from e
                if inp['role'].startswith('holdout'):
                    key=hashlib.sha256(('astra-gameprov-v1\0'+item['origin_sha256']+'\0'+str(item['game_index'])).encode('ascii')).hexdigest()
                    con.execute('INSERT OR IGNORE INTO original_hold_games VALUES (?)',(key,))
        for name in manifest['row_chunks']:
            n=0
            for raw in lines(pack_path(root,name),compressed=True):
                n+=1
                if n%4096==1:pulse()
                item=decode(raw)
                need(set(item)=={'input_id','physical_row','row_id','original','fen','ply','game_id','origin_sha256','game_index','outcome'},
                     'invalid retained row fields')
                inp=specs.get(item['input_id'])
                need(inp is not None and inp['role'] in POPULATION_ROLES,'retained row outside population')
                need(type(item['physical_row']) is int and 1<=item['physical_row']<=inp['rows'],'retained physical row outside population')
                need(type(item['game_index']) is int and item['game_index']>=0 and type(item['ply']) is int and item['ply']>=0,
                     'retained game index/ply must be exact nonnegative integers')
                link=con.execute('SELECT origin,gidx,ply FROM links WHERE input=? AND physical=?',
                                 (item['input_id'],item['physical_row'])).fetchone()
                need(link is not None,'retained row lacks authenticated binding')
                need((item['origin_sha256'],item['game_index'],item['ply'])==link,'retained row provenance changed')
                key=hashlib.sha256(('astra-gameprov-v1\0'+link[0]+'\0'+str(link[1])).encode('ascii')).hexdigest()
                need(item['game_id']==key,'game_id does not recompute from canonical origin')
                archived=con.execute('SELECT fen FROM evidence WHERE origin=? AND gidx=? AND ply=?',link).fetchone()
                need(archived is not None and archived[0]==item['fen'],'retained FEN differs from archived game')
                need(item['outcome'] in ('train','holdout','moved_holdout'),'invalid split outcome')
                try:con.execute('INSERT INTO emitted(input,physical,payload) VALUES (?,?,?)',
                                (item['input_id'],item['physical_row'],encoded(item).decode()))
                except sqlite3.IntegrityError as e:raise ValueError('duplicate population accounting') from e
                train=int(item['outcome']=='train');hold=1-train
                con.execute('INSERT INTO games VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET train=MAX(train,excluded.train),holdout=MAX(holdout,excluded.holdout)',(key,train,hold))
            need(0<n<=50000,'invalid retained chunk size')
        con.commit()
        # Check actual emitted game sets BEFORE expected-split checks, so the
        # rechecksummed same-game/different-position negative hits this guard.
        overlap=con.execute('SELECT COUNT(*) FROM games WHERE train=1 AND holdout=1').fetchone()[0]
        need(overlap==0,'game overlap detected between retained train and holdout')
        excluded=decode((root/'UNTRACEABLE.json').read_bytes())
        need(excluded.get('schema')==1 and isinstance(excluded.get('ranges'),list),'invalid exclusion ledger')
        need(len(excluded['ranges'])<=100000,'exclusion range reservation exceeded')
        ranges={s['id']:[] for s in manifest['inputs'] if s['role'] in POPULATION_ROLES}
        for r in excluded['ranges']:
            need(set(r)=={'input_id','first','last','outcome','game_id','reason'},'invalid exclusion fields')
            need(r['input_id'] in ranges and type(r['first']) is int and type(r['last']) is int and
                 1<=r['first']<=r['last']<=specs[r['input_id']]['rows'],'exclusion outside population')
            need(r['game_id'] is None and r['outcome']=='UNTRACEABLE' and r['reason']=='NO_AUTHENTIC_GAME_EVIDENCE','invented exclusion identity/reason')
            ranges[r['input_id']].append((r['first'],r['last']))
        for value in ranges.values():
            value.sort()
            need(all(a[1]<b[0] for a,b in zip(value,value[1:])),'overlapping exclusion ranges')
        cohort=next(s for s in manifest['inputs'] if s['role']=='cohort')
        for _,raw in consume(root,cohort):
            item=decode(raw);state(item.get('fen'))
            source=manifest['source_labels'].get(item.get('source'));number=item.get('source_row')
            need(source is not None and type(number) is int and number>0,'cohort source row identity missing')
            try:con.execute('INSERT INTO originals(source,physical,payload) VALUES (?,?,?)',(source,number,encoded(item).decode()))
            except sqlite3.IntegrityError as e:raise ValueError('duplicate cohort row') from e
        con.commit()
        for spec in (s for s in manifest['inputs'] if s['role']=='source'):
            for number,raw in consume(root,spec):
                record=raw_record(raw)
                desired=con.execute('SELECT payload FROM originals WHERE source=? AND physical=?',(spec['id'],number)).fetchone()
                if desired:
                    item=decode(desired[0])
                    need(item['fen']==record['fen'] and item.get('ply')==record['ply'] and
                         item.get('raw_score')==record['raw_score'] and item.get('result_white')==record['result_white'],
                         'original source full state/label mismatch')
                    con.execute('UPDATE originals SET matched=1 WHERE source=? AND physical=?',(spec['id'],number))
            con.commit()
        need(con.execute('SELECT COUNT(*) FROM originals WHERE matched=0').fetchone()[0]==0,'cohort source coverage incomplete')
        for spec in (s for s in manifest['inputs'] if s['role'] in POPULATION_ROLES):
            idx=0;unknown=ranges[spec['id']]
            has_rows=con.execute('SELECT 1 FROM emitted WHERE input=? LIMIT 1',(spec['id'],)).fetchone() is not None
            has_links=con.execute('SELECT 1 FROM links WHERE input=? LIMIT 1',(spec['id'],)).fetchone() is not None
            for number,raw in consume(root,spec):
                counts['population']+=1;by_role[spec['role']]['rows']+=1
                if spec['format']=='jsonl':
                    item=decode(raw);state(item.get('fen'))
                    source=manifest['source_labels'].get(item.get('source'));physical=item.get('source_row')
                    need(source is not None and type(physical) is int and physical>0,'missing source row')
                    cohort_row=con.execute('SELECT payload,selected FROM originals WHERE source=? AND physical=?',(source,physical)).fetchone()
                    need(cohort_row is not None and decode(cohort_row[0])==item,'retained training source differs from frozen cohort')
                    need(cohort_row[1]==0,'duplicate filtered source row')
                    con.execute('UPDATE originals SET selected=1 WHERE source=? AND physical=?',(source,physical))
                    original=item;fen=item['fen'];ply=item['ply'];row_id=specs[source]['sha256']+':'+str(physical)
                else:
                    item=raw_record(raw);original=item['original_line'];fen=item['fen'];ply=item['ply'];row_id=spec['sha256']+':'+str(number)
                while idx<len(unknown) and unknown[idx][1]<number:idx+=1
                in_unknown=idx<len(unknown) and unknown[idx][0]<=number<=unknown[idx][1]
                emitted=con.execute('SELECT payload FROM emitted WHERE input=? AND physical=?',(spec['id'],number)).fetchone() if has_rows else None
                need(int(in_unknown)+int(emitted is not None)==1,'population coverage missing or duplicated')
                if in_unknown:
                    link=con.execute('SELECT 1 FROM links WHERE input=? AND physical=?',(spec['id'],number)).fetchone() if has_links else None
                    need(link is None,'authenticated row hidden as untraceable')
                    counts['untraceable']+=1;by_role[spec['role']]['untraceable']+=1
                    continue
                retained=decode(emitted[0])
                need(retained['original']==original and retained['fen']==fen and retained['ply']==ply and retained['row_id']==row_id,
                     'retained original fields/FEN/ply/identity changed')
                held=con.execute('SELECT 1 FROM original_hold_games WHERE id=?',(retained['game_id'],)).fetchone() is not None
                wanted='holdout' if spec['role'].startswith('holdout') else ('moved_holdout' if held else 'train')
                need(retained['outcome']==wanted,'game split violates holdout precedence')
                counts['traced']+=1;by_role[spec['role']]['traced']+=1
                counts['train' if wanted=='train' else 'holdout']+=1
                if wanted=='moved_holdout':counts['moved_to_holdout']+=1
                con.execute('UPDATE emitted SET used=1 WHERE input=? AND physical=?',(spec['id'],number))
                con.execute('UPDATE links SET used=1 WHERE input=? AND physical=?',(spec['id'],number))
            con.commit()
        need(con.execute('SELECT COUNT(*) FROM emitted WHERE used=0').fetchone()[0]==0 and
             con.execute('SELECT COUNT(*) FROM links WHERE used=0').fetchone()[0]==0,'unaccounted population rows/bindings')
        need(counts==manifest['producer_counts'],'producer count disagreement')
        games={'train':con.execute('SELECT COUNT(*) FROM games WHERE train=1').fetchone()[0],
               'holdout':con.execute('SELECT COUNT(*) FROM games WHERE holdout=1').fetchone()[0]}
        missing_holds=sum(by_role[r]['untraceable'] for r in ('holdout013','holdout014'))
        reasons=[]
        if missing_holds:reasons.append('UNTRACEABLE_ORIGINAL_HOLDOUT_ROWS')
        if not games['train']:reasons.append('NO_RETAINED_TRAINING_GAMES')
        if not games['holdout']:reasons.append('NO_RETAINED_HOLDOUT_GAMES')
        status='BLOCKED' if reasons else ('FIXTURE_PASS' if manifest['scope']=='fixture' else 'PROVENANCE_PASS')
        result={'schema':1,'status':status,'classification':'UNPROVEN','scope':manifest['scope'],
                'counts':counts,'by_role':by_role,'games':games,'game_overlap':None if reasons else overlap,
                'blockers':reasons,'training_authorized':False,
                'pack_md5sums_md5':hashes(root/'MD5SUMS')['md5'],
                'historical_authenticity':'Bound to reviewed origin registry; no claim beyond its evidence.'}
        write_json(out/'RESULT.json',result)
        return result
    finally:con.close()


def verify_pack(pack, output, *, fixture_trust=None):
    root=safe_path(pack);out=safe_path(output,write=True)
    req=decode((root/'PACK.json').read_bytes());validate_request(req,fixture_trust)
    for spec in req['inputs']+req['origins']+req['bindings']:
        need(type(spec.get('bytes')) is int and spec['bytes']>0,'bounded input byte metadata required')
    with ResourceBudget(estimate_budget(req,verification=True),[out]) as budget:
        result=_verify_pack(root,out,fixture_trust=fixture_trust)
        budget.check()
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--threads',type=int,choices=[1],required=True)
    args=parser.parse_args()
    result=verify_pack(args.pack,args.out)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(2 if result['status']=='BLOCKED' else 0)


if __name__=='__main__':main()
