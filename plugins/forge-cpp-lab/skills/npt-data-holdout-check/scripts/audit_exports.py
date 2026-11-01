#!/usr/bin/env python3
"""Independent streaming audit of authoritative normalized exports, not an NPT decoder.
IDEA_SOURCE: Forge full-FEN provenance, real holdout identities and crew game-split requirements.
Writes only a new owned evidence/index directory; never edits input or trainer files.
"""
import argparse,hashlib,json,os,re,shutil,sqlite3
from pathlib import Path

def identity(stat):
 value=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)
 return value+(stat.st_ctime_ns,) if os.name=='posix' else value

def fingerprint(path):
 path=Path(path);link=identity(path.lstat());opened=identity(path.stat());h=hashlib.sha256()
 with path.open('rb') as f:
  if identity(os.fstat(f.fileno()))!=opened:raise ValueError('input identity changed before hash')
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
  if identity(os.fstat(f.fileno()))!=opened or identity(path.stat())!=opened or identity(path.lstat())!=link:raise ValueError('input identity changed during hash')
 return {'sha256':h.hexdigest(),'identity':opened,'link_identity':link}

def sha(path):return fingerprint(path)['sha256']

def fen_state(value):
 if not isinstance(value,str):raise ValueError('FEN must be text')
 fields=value.split()
 if len(fields)!=6 or fields[1] not in ('w','b'):raise ValueError('full six-field FEN required')
 ranks=fields[0].split('/')
 if len(ranks)!=8:raise ValueError('invalid FEN board')
 expanded=[]
 for rank in ranks:
  row=[]
  for char in rank:
   if char in '12345678':row.extend('.'*int(char))
   elif char in 'PNBRQKpnbrqk':row.append(char)
   else:raise ValueError('invalid FEN piece')
  if len(row)!=8:raise ValueError('invalid FEN rank width')
  expanded.extend(row)
 rights=fields[2]
 if rights!='-' and (not re.fullmatch('[KQkqA-Ha-h]+',rights) or len(set(rights))!=len(rights)):raise ValueError('invalid castling field')
 if fields[3]!='-' and not re.fullmatch('[a-h][36]',fields[3]):raise ValueError('invalid en-passant field')
 if not fields[4].isdigit() or not fields[5].isdigit() or int(fields[5])<1:raise ValueError('invalid FEN clocks')
 # Deliberately conservative: same board+STM leaks even if rights/clocks differ.
 return ' '.join(fields),''.join(expanded)+' '+fields[1]

def unique(pairs):
 out={}
 for key,value in pairs:
  if key in out:raise ValueError('duplicate JSON field '+key)
  out[key]=value
 return out

def records(path,guard,expected):
 if identity(path.stat())!=expected['identity'] or identity(path.lstat())!=expected['link_identity']:raise ValueError('input identity changed before scan')
 consumed=hashlib.sha256()
 with path.open('rb') as f:
  if identity(os.fstat(f.fileno()))!=expected['identity']:raise ValueError('descriptor identity changed before scan')
  for number,line in enumerate(f,1):
   consumed.update(line)
   if number%1024==1:guard()
   row=json.loads(line.decode('utf-8-sig' if number==1 else 'utf-8'),object_pairs_hook=unique)
   if not isinstance(row,dict) or not isinstance(row.get('row_id'),str) or not row['row_id']:raise ValueError('authoritative row_id required')
   fen,key=fen_state(row.get('fen'));game=row.get('game_id')
   if game is not None and (not isinstance(game,str) or not game.strip()):raise ValueError('game_id must be nonempty text or null')
   yield row['row_id'],fen,key,game
  if identity(os.fstat(f.fileno()))!=expected['identity'] or identity(path.stat())!=expected['identity'] or identity(path.lstat())!=expected['link_identity'] or consumed.hexdigest()!=expected['sha256']:raise ValueError('input identity or consumed bytes changed during scan')

def audit(source,train,holdouts,expected,out,min_free_mib=32768):
 source,train,out=Path(source),Path(train),Path(out);holdouts=[Path(p) for p in holdouts]
 if len(holdouts)!=2 or len({p.resolve() for p in holdouts})!=2 or len({p.name for p in holdouts})!=2:raise ValueError('distinct complete 013 and 014 exports required')
 if type(min_free_mib) is not int or min_free_mib<0:raise ValueError('invalid disk reserve')
 inputs=[source,train,*holdouts]
 if any(not p.is_file() for p in inputs):raise ValueError('all exports must be existing files')
 if any(out.resolve()==p.resolve() or out.resolve() in p.resolve().parents for p in inputs):raise ValueError('output must not contain or alias an input')
 before={str(p.absolute()):fingerprint(p) for p in inputs}
 for p in holdouts:
  e=expected.get(p.name,{})
  if type(e.get('rows')) is not int or e['rows']<=0:raise ValueError('trusted positive holdout row count required')
  if not isinstance(e.get('sha256'),str) or not re.fullmatch('[a-fA-F0-9]{64}',e['sha256']):raise ValueError('trusted complete holdout SHA-256 required')
  if before[str(p.absolute())]['sha256']!=e['sha256'].lower():raise ValueError('trusted holdout hash mismatch')
 # Four input-byte equivalents cover this simple SQLite projection conservatively;
 # periodic guards remain necessary and are not a hard filesystem quota.
 if shutil.disk_usage(out.parent).free < min_free_mib*1024**2+4*sum(p.stat().st_size for p in inputs)+16*1024**2:raise ValueError('preflight disk budget insufficient')
 out.mkdir(exist_ok=False)
 def guard():
  if shutil.disk_usage(out).free<min_free_mib*1024**2:raise ValueError('disk floor reached; incomplete evidence retained')
 result={'status':'UNVERIFIED','scope':'Normalized exports only; authoritative format-reader/roundtrip and original-shard identity require separate evidence.', 'source_rows':0,'training_rows':0,'holdout_rows':{},'position_overlap_rows':0,'game_overlap_rows':0,'state_mismatch_rows':0,'unknown_game_id_rows':0,'source_hashes':{name:value['sha256'] for name,value in before.items()},'source_identities':before,'position_key':'expanded board + side to move; rights and clocks deliberately ignored for conservative exclusion','index_retention':'keep; no prune or delete performed'}
 conn=sqlite3.connect(out/'audit.sqlite')
 try:
  conn.executescript('CREATE TABLE source(id TEXT PRIMARY KEY, fen TEXT NOT NULL, game TEXT); CREATE TABLE train(id TEXT PRIMARY KEY); CREATE TABLE positions(key TEXT PRIMARY KEY); CREATE TABLE games(id TEXT PRIMARY KEY);')
  for ident,fen,key,game in records(source,guard,before[str(source.absolute())]):
   try:conn.execute('INSERT INTO source VALUES(?,?,?)',(ident,fen,game))
   except sqlite3.IntegrityError:raise ValueError('duplicate source row_id') from None
   result['source_rows']+=1
  conn.commit()
  for ident,fen,key,game in records(train,guard,before[str(train.absolute())]):
   row=conn.execute('SELECT fen,game FROM source WHERE id=?',(ident,)).fetchone()
   if row is None or tuple(row)!=(fen,game):result['state_mismatch_rows']+=1
   try:conn.execute('INSERT INTO train VALUES(?)',(ident,))
   except sqlite3.IntegrityError:raise ValueError('duplicate retained row_id') from None
   conn.execute('INSERT OR IGNORE INTO positions VALUES(?)',(key,))
   if game is None:result['unknown_game_id_rows']+=1
   else:conn.execute('INSERT OR IGNORE INTO games VALUES(?)',(game,))
   result['training_rows']+=1
  conn.commit()
  if not result['source_rows'] or not result['training_rows']:raise ValueError('empty source/training set cannot pass')
  for path in holdouts:
   count=0
   for ident,fen,key,game in records(path,guard,before[str(path.absolute())]):
    count+=1
    result['position_overlap_rows']+=int(conn.execute('SELECT 1 FROM positions WHERE key=?',(key,)).fetchone() is not None)
    if game is None:result['unknown_game_id_rows']+=1
    else:result['game_overlap_rows']+=int(conn.execute('SELECT 1 FROM games WHERE id=?',(game,)).fetchone() is not None)
   result['holdout_rows'][path.name]=count
   if count!=expected[path.name]['rows']:raise ValueError('trusted holdout row count mismatch')
  for path in inputs:
   if fingerprint(path)!=before[str(path.absolute())]:raise ValueError('input identity changed during audit')
  failed=any(result[k] for k in ('position_overlap_rows','game_overlap_rows','state_mismatch_rows'))
  result['status']='FAIL' if failed else 'UNVERIFIED' if result['unknown_game_id_rows'] else 'PASS'
 finally:conn.close()
 result['index_bytes']=(out/'audit.sqlite').stat().st_size
 result['index_sha256']=sha(out/'audit.sqlite')
 with (out/'audit.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source',required=True,type=Path);p.add_argument('--train',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
 p.add_argument('--min-free-mib',type=int,default=32768)
 for shard in ('013','014'):
  p.add_argument('--holdout-'+shard,required=True,type=Path);p.add_argument('--sha256-'+shard,required=True);p.add_argument('--rows-'+shard,required=True,type=int)
 a=p.parse_args();hs=[a.holdout_013,a.holdout_014];expected={hs[0].name:dict(sha256=a.sha256_013,rows=a.rows_013),hs[1].name:dict(sha256=a.sha256_014,rows=a.rows_014)}
 try:r=audit(a.source,a.train,hs,expected,a.out,a.min_free_mib)
 except (OSError,ValueError,sqlite3.Error) as e:r={'status':'BLOCKED','error':str(e),'scope':'No completed clearance; retain any partial output.'}
 print(json.dumps(r,sort_keys=True,indent=2));return 0 if r['status']=='PASS' else 1 if r['status']=='FAIL' else 2
if __name__=='__main__':raise SystemExit(main())
