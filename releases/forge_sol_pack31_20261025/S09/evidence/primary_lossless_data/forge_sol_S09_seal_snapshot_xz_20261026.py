from pathlib import Path
import lzma,hashlib,json,subprocess,time
root=Path(__file__).resolve().parent;base=Path('/tmp/forge_sol_S09_native_20261026')
originals=[base/'original_bit_snapshot_pair_once_20261026/reference.stdout',base/'original_bit_snapshot_pair_once_20261026/Lprime.stdout',base/'converted8_original_bit_snapshot_once_20261026/stored8_snapshot.stdout']
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1<<20):h.update(b)
 return h.hexdigest()
pins=[{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in originals];assert len({(p['sha256'],p['bytes']) for p in pins})==1
assert pins[0]['bytes']==41903752
out=root/'forge_sol_S09_exact_snapshot_raw_20261026.bin.xz';start=time.monotonic()
with originals[0].open('rb') as inp,lzma.open(out,'xb',preset=1,check=lzma.CHECK_SHA256) as encoded:
 while b:=inp.read(1<<20):encoded.write(b)
py=hashlib.sha256();size=0
with lzma.open(out,'rb') as f:
 while b:=f.read(1<<20):py.update(b);size+=len(b)
assert (py.hexdigest(),size)==(pins[0]['sha256'],41903752)
p=subprocess.Popen(['xz','-dc','--',str(out)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);gnu=hashlib.sha256();n=0
try:
 while b:=p.stdout.read(1<<20):gnu.update(b);n+=len(b)
 se=p.stderr.read();rc=p.wait(timeout=15)
finally:p.stdout.close();p.stderr.close()
assert rc==0 and not se and (gnu.hexdigest(),n)==(pins[0]['sha256'],41903752)
assert all(digest(Path(row['path']))==row['sha256'] for row in pins)
result={'status':'PASS','originals':pins,'raw_bytes':size,'raw_sha256':py.hexdigest(),'xz_bytes':out.stat().st_size,'xz_sha256':digest(out),'original_bytes_unchanged':True,'python_and_gnu_decoders_pass':True,'elapsed_seconds':time.monotonic()-start,'scope':'lossless one payload mapping three byte-identical ORIGINAL native stdout streams; no synthetic reconstruction'}
(root/'forge_sol_S09_snapshot_storage_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
