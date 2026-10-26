"""Lossless data-only transport of one closed S10 feature's original evidence.

No experiment is rerun. No original is changed. Main/test ELFs, objects,
archives, private source trees, licenses and agent instructions stay local.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
from types import ModuleType

CONTROLLER=Path('/workspace/forge-pack24-20261026/S10/forge_sol_S10_native_controller_20261026.py')
CONTROLLER_SHA='d6b8b9909373903e2ac3d2aca10e731acffeaff8352db8619d0577945f55b08b'
ROOT=Path('/tmp/forge_sol_S10_native_20261026')
FEATURES=('quiet_check_survival','improving_razor','singular_siblings','capture_history_lmp')

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()

def selected(relative):
 """Keep raw runtime output and explicit generated build/test recipes only."""
 if any(part in ('source','.git','__pycache__') for part in relative.parts):return False
 if any(part.lower() in ('agents.md','.agents') or part.lower().startswith(('license','licence')) for part in relative.parts):return False
 if 'build' not in relative.parts:
  return relative.suffix in ('.json','.jsonl','.xml','.stdout','.stderr','.stdin','.log','.txt')
 name=relative.name
 if name in ('CMakeCache.txt','compile_commands.json','CTestTestfile.cmake','flags.make','link.txt','CMakeCXXCompiler.cmake','CMakeSystem.cmake'):
  return True
 if 'Testing' in relative.parts:return relative.suffix in ('.log','.txt','.xml')
 return name in ('uci-regression.log','ownbook-regression.json')

def roots(feature):
 result=[]
 for base in ('Lprime','B'):
  job=ROOT/(feature+'_'+base+'_once');record=job/'forge_sol_S10_native_result_20261026.json'
  if not record.is_file():
   if base=='B' and result and result[0]['document'].get('status')=='REJECTED_ACTIVATION':continue
   raise ValueError('missing completed source-base result: '+str(record))
  document=json.loads(record.read_text())
  if document.get('status') in (None,'RUNNING'):raise ValueError('job is not closed: '+str(job))
  if document.get('controller_sha256')!=CONTROLLER_SHA or document.get('feature',{}).get('key')!=feature or document.get('base')!=base:
   raise ValueError('wrong producer/feature/base binding')
  result.append({'kind':base+'/qualification','root':job,'document':document})
  extra=ROOT/(feature+'_'+base+'_T2_ON_once')
  if extra.is_dir():
   proof=extra/'forge_sol_S10_ON_T2_asan_v2_result_20261026.json'
   if not proof.is_file() or json.loads(proof.read_text()).get('status') not in ('PASS','FAIL'):raise ValueError('T2 supplement is not closed')
   result.append({'kind':base+'/ON_T2','root':extra,'document':json.loads(proof.read_text())})
 return result

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--feature',choices=FEATURES,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args(argv)
 output=a.out.absolute()
 if not output.is_relative_to('/tmp') or '..' in output.parts or any(x.is_symlink() for x in (output,*output.parents)):p.error('NEW nonsymlink /tmp output required')
 if digest(CONTROLLER)!=CONTROLLER_SHA:raise ValueError('frozen process helper changed')
 m=ModuleType('s10_archive_owned_commands');m.__file__=str(CONTROLLER);exec(compile(CONTROLLER.read_bytes(),str(CONTROLLER),'exec'),m.__dict__)
 deps=json.loads(m.DEPENDENCIES.read_text());net=m.load_checked(deps['ctest'],'ctest');shared=m.load_checked(deps['subreaper'],'subreaper')
 inputs=roots(a.feature);rows=[]
 for source in inputs:
  for path in sorted(source['root'].rglob('*')):
   if path.is_symlink():raise ValueError('unexpected evidence symlink: '+str(path))
   rel=path.relative_to(source['root'])
   if path.is_file() and selected(rel):
    member=source['kind']+'/'+rel.as_posix()
    if '..' in Path(member).parts or Path(member).is_absolute():raise ValueError('unsafe member path')
    rows.append({'original':str(path),'member':member,'sha256':digest(path),'bytes':path.stat().st_size})
 if not rows or len({r['member'] for r in rows})!=len(rows):raise ValueError('empty/duplicate evidence map')
 output.mkdir(exist_ok=False)
 prefix='forge_sol_S10_'+a.feature
 mapping={'schema':'forge-s10-data-only-evidence-v1','feature':a.feature,'originals_unchanged':True,
          'source_patch_sha256':inputs[0]['document']['feature']['patch_sha256'],
          'closed_jobs':[{'kind':r['kind'],'root':str(r['root']),'status':r['document']['status']} for r in inputs],
          'excluded':'All build ELFs/.o/.a and private source trees; originals remain untouched. CPP .stdout is original preprocessor evidence, not replacement engine source.',
          'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'files':rows}
 map_path=output/(prefix+'_mapping_20261026.json');m.save(map_path,mapping);map_bytes=map_path.read_bytes()
 archive=output/(prefix+'_evidence_20261026.tar.gz')
 expected={r['member']:{'sha256':r['sha256'],'bytes':r['bytes']} for r in rows}
 expected[map_path.name]={'sha256':digest(map_path),'bytes':len(map_bytes)}
 with archive.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=6) as gz,tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as tar:
  for name,stream,size in [(map_path.name,io.BytesIO(map_bytes),len(map_bytes))]:
   info=tarfile.TarInfo(name);info.size=size;info.mode=0o444;info.mtime=0;tar.addfile(info,stream)
  for row in rows:
   path=Path(row['original'])
   if digest(path)!=row['sha256'] or path.stat().st_size!=row['bytes']:raise ValueError('closed evidence changed before archive')
   info=tarfile.TarInfo(row['member']);info.size=row['bytes'];info.mode=0o444;info.mtime=0
   with path.open('rb') as stream:tar.addfile(info,stream)
 archive_sha=digest(archive)
 python_rows={}
 with tarfile.open(archive,'r:gz') as tar:
  for item in tar.getmembers():
   if not item.isreg() or item.name not in expected or item.name in python_rows:raise ValueError('unexpected archive member')
   h=hashlib.sha256();size=0
   with tar.extractfile(item) as stream:
    for data in iter(lambda:stream.read(1<<20),b''):h.update(data);size+=len(data)
   python_rows[item.name]={'sha256':h.hexdigest(),'bytes':size}
 if python_rows!=expected:raise ValueError('Python archive roundtrip differs')
 restore=output/(prefix+'_GNU_roundtrip_20261026');restore.mkdir()
 commands=m.guarded_commands(net,shared,output,net.ResourceGuard(),180)
 commands.run(['/usr/bin/tar','--no-same-owner','--no-same-permissions','-xzf',str(archive),'-C',str(restore)],'GNU_tar_decode')
 gnu_rows={str(path.relative_to(restore)):{'sha256':digest(path),'bytes':path.stat().st_size} for path in sorted(restore.rglob('*')) if path.is_file()}
 if any(path.is_symlink() for path in restore.rglob('*')) or gnu_rows!=expected:raise ValueError('GNU archive roundtrip differs')
 if digest(archive)!=archive_sha or any(digest(r['original'])!=r['sha256'] or Path(r['original']).stat().st_size!=r['bytes'] for r in rows):raise ValueError('archive/original evidence changed')
 receipt={'status':'PASS_LOSSLESS_ENCODING_ONLY','feature':a.feature,'archiver_sha256':digest(__file__),
          'archive':{'path':str(archive),'sha256':archive_sha,'bytes':archive.stat().st_size},
          'mapping':{'path':str(map_path),'sha256':digest(map_path),'bytes':map_path.stat().st_size},
          'payload_files':len(rows),'payload_bytes':mapping['payload_bytes'],'archive_members':len(expected),
          'python_decoder':'PASS_ALL_MEMBER_BYTES','GNU_decoder':'PASS_ALL_MEMBER_BYTES','GNU_commands':commands.records,
          'originals_unchanged':True,'binaries_or_caches_deleted':False,'new_experiments_run':0}
 m.save(output/(prefix+'_archive_receipt_20261026.json'),receipt)
 print(json.dumps(receipt),flush=True);return 0

if __name__=='__main__':raise SystemExit(main())
