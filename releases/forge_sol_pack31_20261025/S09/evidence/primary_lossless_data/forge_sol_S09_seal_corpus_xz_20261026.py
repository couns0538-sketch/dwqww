from pathlib import Path
import gzip,lzma,hashlib,json,subprocess,time,os
root=Path(__file__).resolve().parent
src=Path('/tmp/forge_sol_S09_native_20261026/million_unique_corpus_once_20261026/legal_fens.fen.gz')
expected='0d6594d3fb7dba38064eddc2a0f673d23c6551c052186cc5989047b86e762eb6'
source_expected='e06bf2de476f1819ab098b854d718ff1b528c49c60ee9edbfd82206b99798a42'
assert hashlib.sha256(src.read_bytes()).hexdigest()==source_expected
out=root/'forge_sol_S09_million_legal_fens_20261026.fen.xz';start=time.monotonic();raw=hashlib.sha256();size=0;lines=0
with gzip.open(src,'rb') as inp,lzma.open(out,'xb',preset=6,check=lzma.CHECK_SHA256) as sealed:
 while chunk:=inp.read(1<<20):
  raw.update(chunk);size+=len(chunk);lines+=chunk.count(b'\n');sealed.write(chunk)
assert (raw.hexdigest(),size,lines)==(expected,52261200,1000000)
py=hashlib.sha256();n=0
with lzma.open(out,'rb') as inp:
 while chunk:=inp.read(1<<20):py.update(chunk);n+=len(chunk)
assert (py.hexdigest(),n)==(expected,size)
p=subprocess.Popen(['xz','-dc','--',str(out)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
gnu=hashlib.sha256();n2=0
try:
 while chunk:=p.stdout.read(1<<20):gnu.update(chunk);n2+=len(chunk)
 stderr=p.stderr.read();rc=p.wait(timeout=15)
finally:
 p.stdout.close();p.stderr.close()
assert rc==0 and not stderr and (gnu.hexdigest(),n2)==(expected,size)
assert hashlib.sha256(src.read_bytes()).hexdigest()==source_expected
result={'status':'PASS','purpose':'lossless storage encoding only; native corpus unchanged','source_gzip':str(src),'source_gzip_sha256':source_expected,'raw_sha256':expected,'raw_bytes':size,'line_count':lines,'xz_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'xz_bytes':out.stat().st_size,'python_decoder':True,'gnu_xz_decoder':True,'source_gzip_unchanged':True,'elapsed_seconds':time.monotonic()-start,'affinity':sorted(os.sched_getaffinity(0))}
(root/'forge_sol_S09_corpus_storage_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
