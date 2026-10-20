#!/usr/bin/env python3
"""Preserve exact Forge 6.4.13 source and complete evidence; no engine execution."""
import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, tarfile, time
R=pathlib.Path('/workspace/dwqww'); C=pathlib.Path('/workspace/.cloud-setup')
REV='cecf0b9e3af5602053bcaf5c5d16ffc09f58850d'
S=C/'clock-cecf-complete-evidence-stage'
V=R/'validation/upstream-clock-reconcile-20261020'
O=V/'archive-complete'
READY=C/'clock-cecf-root-ready'
HELPER=R/'.github/hosted-tt-strength/archive_results.py'
EXPECTED_HELPER='952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c'
def digest(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
assert digest(HELPER)==EXPECTED_HELPER
inventory=(R/'.github/hosted-tt-strength/PACKAGE-SHA256SUMS').read_text().splitlines()
assert EXPECTED_HELPER+'  .github/hosted-tt-strength/archive_results.py' in inventory
origins=[]
def copy_file(source, relative):
 source=pathlib.Path(source)
 if source.is_symlink() or not source.is_file():raise RuntimeError('Not regular input: '+str(source))
 target=S/relative;target.parent.mkdir(parents=True,exist_ok=True)
 before=source.stat();expected=digest(source);shutil.copy2(source,target);after=source.stat()
 if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns) or digest(source)!=expected or digest(target)!=expected:raise RuntimeError('Changed input: '+str(source))
 origins.append({'original':str(source),'archive_path':relative,'size':after.st_size,'sha256':expected})
def copy_tree(source,relative,excluded=None):
 source=pathlib.Path(source)
 if not source.is_dir() or source.is_symlink():raise RuntimeError('Not regular directory: '+str(source))
 for directory,dirs,files in os.walk(source,followlinks=False):
  dirs.sort()
  if excluded:dirs[:]=[d for d in dirs if pathlib.Path(directory)/d not in excluded]
  for d in dirs:
   if (pathlib.Path(directory)/d).is_symlink():raise RuntimeError('Symlinked directory')
  for name in sorted(files):
   p=pathlib.Path(directory)/name
   copy_file(p,str(pathlib.PurePosixPath(relative)/p.relative_to(source).as_posix()))
S.mkdir(exist_ok=False)
# Root has already completed these builds/tests. They will never be rebuilt.
for name in ['forge-clock-contract-release','forge-clock-contract-asan']:
 summary=json.loads((V/('frozen-'+name.rsplit('-',1)[1]+'-attempt1')/'summary.json').read_text())
 assert summary['status']=='PASS' and summary['source_commit']==REV
 copy_tree(C/name,'builds/'+name)
copy_tree(C/'forge-clock-contract-source','frozen-source-export-cecf0b9')
target=S/'git-source-exports/clock-contract-cecf0b9.tar';target.parent.mkdir()
command=['git','archive',REV,'CMakeLists.txt','LICENSE','bench','include','src','tests','tools']
with target.open('xb') as stream:subprocess.run(command,cwd=R,stdout=stream,check=True)
dest=S/'git-source-exports/clock-contract-cecf0b9';dest.mkdir()
with tarfile.open(target) as archive:archive.extractall(dest,filter='data')
origins.append({'generated_by':command,'archive_path':target.relative_to(S).as_posix(),'size':target.stat().st_size,'sha256':digest(target),'source_commit':REV})
(C/'clock-cecf-builds-staged.json').write_text(json.dumps({'status':'immutable_source_release_asan_staged','files':len(origins),'awaiting':str(READY)},indent=2)+'\n')
print('Immutable source/Release/ASan staged; waiting root final evidence freeze.',flush=True)
while not READY.exists():time.sleep(1)
# Only read mutable-until-finished proof directories after the root ready marker.
for profile in ['release','asan','tsan']:
 summary=json.loads((V/('frozen-'+profile+'-attempt1')/'summary.json').read_text())
 assert summary['status']=='PASS' and summary['source_commit']==REV
 witness='witnesses-release-attempt2' if profile=='release' else 'witnesses-'+profile+'-attempt1'
 summary=json.loads((V/witness/'summary.json').read_text())
 assert summary['status']=='PASS' and summary['source_commit']==REV
copy_tree(C/'forge-clock-contract-tsan','builds/forge-clock-contract-tsan')
copy_tree(C/'forge-clock-contract-diagnostics','actual-diagnostic-binaries')
# Preserve the exact original accepted shim/fixture artifacts from the actual RED.
identity=json.loads((V/'red-attempt1/identity.json').read_text())
red_temp=pathlib.Path(identity['temp_directory'])
assert digest(red_temp/'libdelay.so')==identity['shim_sha256']
copy_tree(red_temp,'actual-red-shim-and-fixture-artifacts')
# Match old header and core ABI for the legacy counterfactual; do not mix versions.
old=C/'forge-tt-single-worker-gated-release'
for name in ['forge','libforge_core.a','CMakeCache.txt','compile_commands.json']:
 copy_file(old/name,'old886-counterfactual/'+name)
copy_tree(C/'forge-tt-single-worker-gated-source/include','old886-counterfactual/include')
# Preserve every original clock/Windows proof and immutable user bundle.
copy_tree(V,'repository/validation/upstream-clock-reconcile-20261020',excluded={O})
copy_file(R/'releases/forge-6.4.13-candidate-windows-zen5.zip','repository/releases/forge-6.4.13-candidate-windows-zen5.zip')
copy_tree(R/'releases/forge-6.4.13-candidate-windows-zen5','repository/releases/forge-6.4.13-candidate-windows-zen5')
copy_file(HELPER,'archive-helper/archive_results.py')
copy_file(pathlib.Path(__file__),'archive-helper/archive-command.py')
copy_file(READY,'root-ready-marker')
(S/'STAGING-ORIGINS.json').write_text(json.dumps({'schema_version':1,'source_commit':REV,'original_file_copies':origins,'note':'Every copied input compared by stat and SHA before/after; only trusted Git source is exported. Failed GNU-wrap and ZIP audit harness attempts retained. No source/binary/test evidence was rebuilt or executed by this archive task. No speed/Elo claim.'},indent=2)+'\n')
spec=importlib.util.spec_from_file_location('trusted_archive',HELPER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest=m.archive_results(S,O,'clock-contract-complete-cecf0b9')
verified=m.verify_archive(manifest)
for row in origins:
 if 'original' in row:
  p=pathlib.Path(row['original'])
  if p.stat().st_size!=row['size'] or digest(p)!=row['sha256']:raise RuntimeError('Live original changed: '+str(p))
receipt={'status':'PASS','source_commit':REV,'manifest':manifest.name,'manifest_sha256':digest(manifest),'helper_sha256':digest(HELPER),'input_file_count':len(verified['files']),'input_bytes':sum(x['size'] for x in verified['files']),'archive':verified['archive'],'parts':verified['parts'],'all_copied_live_originals_rehashed_after_archive':True,'original_file_count':sum('original' in x for x in origins),'scope':['complete frozen Release/ASan/TSan build trees, binaries/core/test executables/objects/CMake/CTest','actual origin and TT API diagnostic binaries, exact shim/fixtures and old886 counterfactual inputs','all clock validation originals including failed diagnostic attempts and independent review','complete Windows raw evidence and candidate ZIP/expanded bundle','exact Git source TAR and complete frozen source export at cecf0b9'],'no_originals_deleted_or_mutated':True}
(O/'VERIFY-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
(O/'README.md').write_text('# Complete Forge 6.4.13 clock evidence\n\n'+f'Verified {receipt["input_file_count"]} files ({receipt["input_bytes"]:,} original bytes) with the unchanged trusted split-ZIP helper. Every live copied original was rehashed after archival. Concatenate manifest-ordered parts to reconstruct the ZIP; the adjacent manifest records archive, part and per-file SHA256. No original file was deleted.\n\n'+'This preserves finite correctness evidence and failed diagnostic attempts. The original GNU-wrap probe did not observe shared-library helper calls; its zero-helper result was invalid, not an engine failure. The corrected exported-symbol diagnostic and matched header/core artifacts are separately preserved. No NPS, Elo, native Ryzen or separate hosted-forfeit remedy follows.\n\n'+'No engine or downloaded code was executed during archival. Archive extraction does not restore executable permissions automatically; restore permissions explicitly only for trusted programs if execution is intended.\n')
print(json.dumps(receipt,indent=2),flush=True)
