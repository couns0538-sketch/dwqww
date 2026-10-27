from pathlib import Path
import gzip,tarfile,hashlib,json,subprocess,time,datetime
src=Path('/tmp/forge_sol_S18_none_smoke_failed_checkpoint_20261027')
out=Path('/tmp/forge_sol_S18_none_failed_publication_v2_20261027');out.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
files=sorted(p for p in src.rglob('*') if p.is_file())
assert len(files)==39
rows=[]
for p in files:
 assert not p.is_symlink() and p.open('rb').read(4)!=b'\x7fELF'
 rows.append({'path':p.relative_to(src).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'mode':p.stat().st_mode&0o777})
arc=out/'forge_sol_S18_none_failed_original_evidence_20261027.tar.gz'
with arc.open('xb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=1) as gz,tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
 for p in files:tf.add(p,arcname=p.relative_to(src).as_posix(),recursive=False)
with tarfile.open(arc,'r:gz') as tf:
 members=tf.getmembers();assert len(members)==len(rows)
 for m,row in zip(members,rows):
  assert m.isfile() and m.name==row['path'] and m.size==row['bytes'] and m.mode&0o777==row['mode']
  data=tf.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==row['sha256']
rest=Path('/tmp/forge_sol_S18_none_failed_GNU_roundtrip_v2_20261027');rest.mkdir(exist_ok=False)
argv=['tar','-xzf',str(arc),'-C',str(rest),'--no-same-owner','--same-permissions'];start=time.monotonic();p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
(out/'forge_sol_S18_none_failed_GNU_20261027.stdout').write_bytes(p.stdout);(out/'forge_sol_S18_none_failed_GNU_20261027.stderr').write_bytes(p.stderr)
assert p.returncode==0 and not p.stderr
assert sorted(x.relative_to(rest).as_posix() for x in rest.rglob('*') if x.is_file())==[r['path'] for r in rows]
for row in rows:
 q=rest/row['path'];assert sha(q)==row['sha256'] and q.stat().st_size==row['bytes'] and q.stat().st_mode&0o777==row['mode']
for row,p in zip(rows,files):assert sha(p)==row['sha256']
receipt={'status':'PASS_LOSSLESS_ORIGINAL_FAILURE_CHECKPOINT','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(src),'original_run_outcome':'FAIL_S18_TRAINING; never relabeled','included_files':len(rows),'logical_bytes':sum(x['bytes'] for x in rows),'compiled_payloads':0,'archive':arc.name,'archive_bytes':arc.stat().st_size,'archive_sha256':sha(arc),'Python_reader':'39/39 original SHA256/mode/size equal','GNU_reader':{'argv':argv,'returncode':p.returncode,'elapsed_s':time.monotonic()-start,'original_SHA256_mode_size':'39/39 equal'},'originals_unchanged':True}
(out/'forge_sol_S18_none_failed_archive_receipt_20261027.json').write_text(json.dumps(receipt,indent=2)+'\n')
(out/'forge_sol_S18_none_failed_archive_mapping_20261027.json').write_text(json.dumps({'files':rows},indent=2)+'\n')
(out/'forge_sol_S18_none_failed_archive_checkpoint_20261027.md').write_text('Original failed none-only smoke, complete39-file checkpoint preserved. Child training/postscore completed but controller resource observer rejected RSS_UNAVAILABLE. No qualified smoke, training gain or Elo claim. Archive includes the original model/checkpoint/export and copied data; none is an accepted engine/network. All originals remain in /tmp. Two independent decoders matched39/39 bytes, modes and sizes. Next: source-only RSS transition reproducer and separately reviewed successor; other arms held.\n')
print(json.dumps(receipt,sort_keys=True))
