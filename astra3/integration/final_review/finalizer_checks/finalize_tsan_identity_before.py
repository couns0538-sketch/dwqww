#!/usr/bin/env python3
"""Seal completed TSan OFF identity plus kiwipete/FMA, preserving raw bytes.
IDEA_SOURCE: user exact-node and original-evidence qualification requirements.
Run only after identity_bench.py has completed successfully.
"""
import argparse,datetime,hashlib,json,os,pathlib,re,shutil,subprocess
from zoneinfo import ZoneInfo
from qualify_option_matrix import parse_bench_result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('engine',type=pathlib.Path);p.add_argument('tsan_dir',type=pathlib.Path);a=p.parse_args()
 engine=a.engine.resolve();r=a.tsan_dir.resolve();out=r/'final_identity';out.mkdir(exist_ok=False)
 sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
 digest=sha(engine);env={'TSAN_OPTIONS':os.environ.get('TSAN_OPTIONS')}
 command=['objdump','-d',str(engine)]
 receipt={'status':'RUNNING','source_commit':'926c55f33227bc4a030d7ce5b1140528aeba75af','binary_sha256':digest,'runtime_environment':env,'started_pt':datetime.datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),'ctest_coverage':'nine selected targets pass across original run plus unchanged longer-deadline replay; original timeout retained','performance_elo':'NOT_CLAIMED'}
 def save(): (out/'qualification.json').write_text(json.dumps(receipt,indent=2)+'\n')
 save()
 try:
  assert env=={'TSAN_OPTIONS':'halt_on_error=1'},env
  pins=json.loads((r/'pins/results.json').read_text());assert pins['sha256']==digest and len(pins['records'])==5
  for row,(depth,nodes) in zip(pins['records'],[(11,312866),(13,862329),(16,3024920),(20,12389307),(22,34048354)]):
   assert row['mode']=='OFF' and row['depth']==depth
   stem=r/'pins'/f'OFF_d{depth}'
   parsed=parse_bench_result(stem.with_suffix('.stdout').read_bytes(),stem.with_suffix('.stderr').read_bytes(),row['returncode'],depth,nodes)
   assert parsed['pass'],parsed
  assert re.findall(rb'^nodes (\d+)$',(r/'pins/perft.stdout').read_bytes(),re.M)==[b'4865609']
  tail=json.loads((r/'pins_driver.stdout').read_text().splitlines()[-1]);assert tail=={'perft5':True,'returncode':0},tail
  receipt['off_records']=pins['records'];receipt['perft5']=4865609;save()
  dis=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
  fmas=[line.decode() for line in dis.stdout.splitlines() if re.search(rb'\bvfn?m(?:add|sub)\w*\b',line,re.I)]
  (out/'whole_binary_fma.json').write_text(json.dumps({'command':command,'returncode':dis.returncode,'disassembly_sha256':hashlib.sha256(dis.stdout).hexdigest(),'count':len(fmas),'instructions':fmas},indent=2)+'\n')
  (out/'objdump.stderr').write_bytes(dis.stderr);assert not fmas
  data=b'position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1\ngo perft 5\nquit\n'
  (out/'kiwipete.stdin').write_bytes(data)
  (out/'kiwipete_command.json').write_text(json.dumps({'argv':[str(engine)],'timeout_seconds':300,'runtime_environment':env},indent=2)+'\n')
  try:run=subprocess.run([str(engine)],input=data,capture_output=True,timeout=300)
  except subprocess.TimeoutExpired as e:
   (out/'kiwipete.stdout').write_bytes(e.stdout or b'');(out/'kiwipete.stderr').write_bytes(e.stderr or b'');raise
  (out/'kiwipete.stdout').write_bytes(run.stdout);(out/'kiwipete.stderr').write_bytes(run.stderr)
  (out/'kiwipete_exit.txt').write_text(str(run.returncode)+'\n')
  assert run.returncode==0 and re.findall(rb'^nodes (\d+)$',run.stdout,re.M)==[b'193690690']
  assert not re.search(rb'WARNING: ThreadSanitizer|SUMMARY: ThreadSanitizer|runtime error:',run.stdout+run.stderr)
  assert sha(engine)==digest,'binary changed during qualification'
  shutil.copy2(engine,out/'forge_tsan_linux')
  shutil.copy2(engine.parent/'CMakeFiles/forge_core.dir/flags.make',out/'forge_core_compile_flags.make')
  receipt.update(status='PASS',kiwipete5=193690690,whole_binary_fma=0,finished_pt=datetime.datetime.now(ZoneInfo('America/Los_Angeles')).isoformat());save()
 except BaseException as e:
  receipt.update(status='FAIL_OR_INCOMPLETE',error_type=type(e).__name__,error=str(e));save();raise
 finally:
  (out/'SHA256SUMS.txt').write_text(''.join(sha(f)+'  '+f.name+'\n' for f in sorted(out.iterdir()) if f.is_file() and f.name!='SHA256SUMS.txt'))
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
