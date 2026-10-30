"""Original streaming real-sample roundtrip; all evidence retained."""
import argparse,hashlib,json,pathlib,resource,subprocess,time
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True,type=pathlib.Path);ap.add_argument('--adapter',required=True,type=pathlib.Path);ap.add_argument('--out',required=True,type=pathlib.Path);ap.add_argument('--adapter-source',required=True,type=pathlib.Path);a=ap.parse_args()
r=a.out;r.mkdir(parents=True,exist_ok=False);(r/'evidence').mkdir();src=a.input;out=r/'sample_first_1000000.binpack';exe=a.adapter
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
start=time.perf_counter();before=resource.getrusage(resource.RUSAGE_CHILDREN)
with (r/'evidence/encode_1m.stderr').open('wb') as err:
 p=subprocess.Popen([str(exe),'encode','-',str(out),'--allow-transport-move'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err)
 h=hashlib.sha256();rights=ep=0;sent=0
 with src.open('rb') as f:
  for i in range(1000000):
   line=f.readline()
   if not line:raise RuntimeError('source short')
   h.update(line);fields=line.split(b'|')[0].split();rights+=fields[2]!=b'-';ep+=fields[3]!=b'-';p.stdin.write(line);sent+=1
 p.stdin.close();stdout=p.stdout.read();code=p.wait()
 (r/'evidence/encode_1m.stdout').write_bytes(stdout)
 if code:raise RuntimeError('encode failed:'+str(code))
with (r/'evidence/decode_1m.stderr').open('wb') as err:
 p=subprocess.Popen([str(exe),'decode',str(out)],stdout=subprocess.PIPE,stderr=err)
 dh=hashlib.sha256();count=0
 with src.open('rb') as f:
  for observed in p.stdout:
   expected=f.readline()
   if observed!=expected:raise RuntimeError('roundtrip mismatch row'+str(count))
   dh.update(observed);count+=1
 code=p.wait()
 if code or count!=1000000:raise RuntimeError('decode failed/rowcount')
after=resource.getrusage(resource.RUSAGE_CHILDREN)
report={'status':'PASS','input':str(src),'rows':count,'exact_byte_lines':True,'mismatches':0,'castling_rows':rights,'ep_rows':ep,'source_slice_sha256':h.hexdigest(),'decoded_slice_sha256':dh.hexdigest(),'binpack_sha256':sha(out),'binpack_bytes':out.stat().st_size,'adapter_sha256':sha(exe),'adapter_source_sha256':sha(a.adapter_source),'wall_seconds':time.perf_counter()-start,'children_cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'transport_move_fallback_rows':sent,'scope':'First1Moriginal003rows; standard independent-record binpack; original fullFEN/STMscore/White result exact. Fallback move is legal transport metadata, never claimed searched bestmove. No filtering/training/strength claim.'}
(r/'evidence/roundtrip_1m.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
