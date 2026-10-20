#!/usr/bin/env python3
"""Archive frozen Forge6.4.14 evidence; no engine execution or input mutations."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, importlib.util, json, os, shutil, subprocess, tarfile
R=Path('/workspace/dwqww'); C=Path('/workspace/.cloud-setup')
REV='21538ec5416c909fc98a08688242a0b3b9710b25'
V=R/'validation/double-extension-path-20261020'; O=V/'archive6414-complete'
S=C/'extension-21538-complete-evidence-stage'; STATE=C/'extension-21538-archive-staging-state.json'
READY=C/'extension-21538-root-ready'
HELPER=R/'.github/hosted-tt-strength/archive_results.py'
EXPECTED='952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def write(path,data): path.write_text(json.dumps(data,indent=2)+'\n')
def check_helper():
 assert digest(HELPER)==EXPECTED
 assert EXPECTED+'  .github/hosted-tt-strength/archive_results.py' in (R/'.github/hosted-tt-strength/PACKAGE-SHA256SUMS').read_text().splitlines()
origins=[]
def copy_file(source,relative):
 source=Path(source)
 if source.is_symlink() or not source.is_file(): raise RuntimeError('Not regular input: '+str(source))
 target=S/relative; target.parent.mkdir(parents=True,exist_ok=True)
 before=source.stat(); expected=digest(source)
 if target.exists(): raise RuntimeError('Refusing staged overwrite: '+str(target))
 shutil.copy2(source,target); after=source.stat()
 if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns) or digest(source)!=expected or digest(target)!=expected: raise RuntimeError('Changed input: '+str(source))
 origins.append({'original':str(source),'archive_path':relative,'size':after.st_size,'sha256':expected})
def copy_tree(source,relative,excluded=()):
 source=Path(source)
 if not source.is_dir() or source.is_symlink(): raise RuntimeError('Not regular directory: '+str(source))
 excluded=set(map(Path,excluded))
 for parent,dirs,files in os.walk(source,followlinks=False):
  dirs.sort(); dirs[:]=[n for n in dirs if Path(parent)/n not in excluded]
  if any((Path(parent)/n).is_symlink() for n in dirs): raise RuntimeError('Symlinked directory')
  for name in sorted(files):
   q=Path(parent)/name
   copy_file(q,str(PurePosixPath(relative)/q.relative_to(source).as_posix()))
def phase_prepare():
 check_helper(); S.mkdir(exist_ok=False)
 release=json.loads((V/'native6414/frozen-release-attempt1/summary.json').read_text())
 assert release['status']=='PASS' and release['source_commit']==REV
 copy_tree(C/'forge-extension-path-release','builds/forge-extension-path-release')
 copy_tree(C/'forge-extension-path-source','frozen-source-export-21538ec')
 export=S/'git-source-exports/extension-path-21538ec.tar'; export.parent.mkdir()
 command=['git','archive',REV,'CMakeLists.txt','LICENSE','bench','include','src','tests','tools']
 with export.open('xb') as stream: subprocess.run(command,cwd=R,stdout=stream,check=True)
 dest=S/'git-source-exports/extension-path-21538ec'; dest.mkdir()
 with tarfile.open(export) as a: a.extractall(dest,filter='data')
 origins.append({'generated_by':command,'archive_path':export.relative_to(S).as_posix(),'size':export.stat().st_size,'sha256':digest(export),'source_commit':REV})
 # Compare every frozen exported source file with the trusted Git TAR bytes.
 with tarfile.open(export) as a:
  expected={m.name:hashlib.sha256(a.extractfile(m).read()).hexdigest() for m in a.getmembers() if m.isfile()}
 observed={q.relative_to(C/'forge-extension-path-source').as_posix():digest(q) for q in sorted((C/'forge-extension-path-source').rglob('*')) if q.is_file()}
 assert expected==observed
 write(STATE,{'status':'immutable_source_release_staged','source_commit':REV,'origins':origins,'waiting_for':str(READY)})
 print(json.dumps({'status':'immutable_source_release_staged','files':len(origins),'waiting_for':str(READY)}),flush=True)
def phase_finalize():
 global origins
 check_helper(); assert READY.is_file(),'Root final evidence marker missing'
 state=json.loads(STATE.read_text()); assert state['status']=='immutable_source_release_staged' and state['source_commit']==REV
 origins=state['origins']
 for profile in ['release','asan','tsan']:
  x=json.loads((V/('native6414/frozen-'+profile+'-attempt1/summary.json')).read_text())
  assert x['status']=='PASS' and x['source_commit']==REV
 for profile in ['asan','tsan']: copy_tree(C/('forge-extension-path-'+profile),'builds/forge-extension-path-'+profile)
 if (C/'forge-extension-path-diagnostics').is_dir(): copy_tree(C/'forge-extension-path-diagnostics','actual-native-diagnostic-binaries')
 copy_tree(C/'forge-windows-extension-path','builds/forge-windows-extension-path')
 copy_tree(C/'forge-windows-extension-path-source','frozen-windows-source-export-21538ec')
 copy_tree(V,'repository/validation/double-extension-path-20261020',excluded={O})
 for name in ['CURRENT_BASELINE.md','EXPERIMENT_LEDGER.md','NEXT_EXPERIMENTS.md']: copy_file(R/'docs'/name,'repository/docs/'+name)
 copy_file(R/'validation/EXPERIMENTS.json','repository/validation/EXPERIMENTS.json')
 copy_file(R/'releases/forge-6.4.14-candidate-windows-zen5.zip','repository/releases/forge-6.4.14-candidate-windows-zen5.zip')
 copy_tree(R/'releases/forge-6.4.14-candidate-windows-zen5','repository/releases/forge-6.4.14-candidate-windows-zen5')
 copy_file(HELPER,'archive-helper/archive_results.py')
 copy_file(Path(__file__),'archive-helper/archive-command.py')
 copy_file(READY,'root-ready-marker')
 write(S/'STAGING-ORIGINS.json',{'schema_version':1,'source_commit':REV,'original_file_copies':origins,'note':'Every original checked by stat and SHA before/after copying. Failed benchmark/diagnostic attempts are retained without changing outcomes. No engine or downloaded code executed by archival; no speed/Elo claim.'})
 spec=importlib.util.spec_from_file_location('trusted_archive',HELPER); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 manifest=m.archive_results(S,O,'extension-path-complete-21538ec'); verified=m.verify_archive(manifest)
 for row in origins:
  if 'original' in row:
   q=Path(row['original']); assert q.is_file() and q.stat().st_size==row['size'] and digest(q)==row['sha256'],'Live original changed: '+str(q)
 receipt={'status':'PASS','source_commit':REV,'manifest':manifest.name,'manifest_sha256':digest(manifest),'helper_sha256':digest(HELPER),'input_file_count':len(verified['files']),'input_bytes':sum(r['size'] for r in verified['files']),'archive':verified['archive'],'parts':verified['parts'],'all_copied_live_originals_rehashed_after_archive':True,'original_file_count':sum('original' in r for r in origins),'no_originals_deleted_or_mutated':True,'scope':['complete three native build trees, source, binaries/core/test executables/objects/CMake/CTest','actual native diagnostics, active UCI and original benchmark timeout plus later syscall diagnostics','normal and synthetic boundary trace proof with failed harness attempts retained','complete Windows source/build/raw evidence and user candidate ZIP/expanded bundle','frozen source Git export and root experiment/recovery records']}
 write(O/'VERIFY-RECEIPT.json',receipt)
 (O/'README.md').write_text('# Complete Forge6.4.14 evidence\n\n'+f'Verified {receipt["input_file_count"]} files ({receipt["input_bytes"]:,} original bytes) using the unchanged trusted archive helper. All copied originals were rehashed after verification. Concatenate parts in manifest order if split. The manifest records full archive, each part and every payload SHA256. No original files were deleted.\n\n'+'The original benchmark deadline remains preserved; later passing diagnostics do not rewrite its outcome or establish a cause. Synthetic inherited-counter boundary tests are not normal-root overflow or strength evidence. No speed, Elo, native Ryzen or Stockfish superiority claim follows. No engine was executed during archival; restore executable permissions explicitly only when intentionally using trusted archived programs.\n')
 write(STATE,{'status':'archived_and_verified','source_commit':REV,'manifest':str(manifest),'receipt':receipt,'all_archival_cpu_work_finished':True})
 print(json.dumps(receipt,indent=2),flush=True)
parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','finalize']);args=parser.parse_args()
(phase_prepare if args.phase=='prepare' else phase_finalize)()
