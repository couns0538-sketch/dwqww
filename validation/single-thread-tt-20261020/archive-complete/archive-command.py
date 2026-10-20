#!/usr/bin/env python3
"""Preserve frozen TT experiments; no engine execution or repository mutation."""
import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys, tarfile, time
R=pathlib.Path('/workspace/dwqww'); C=pathlib.Path('/workspace/.cloud-setup')
S=C/'tt-single-worker-complete-evidence-stage'
O=R/'validation/single-thread-tt-20261020/archive-complete'
V=R/'validation/single-thread-tt-20261020'
HELPER=R/'.github/hosted-nnue-strength/archive_results.py'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024), b''):h.update(b)
 return h.hexdigest()
origins=[]
def copy_file(source, relative):
 if source.is_symlink() or not source.is_file():raise RuntimeError(f'Nonregular input: {source}')
 target=S/relative; target.parent.mkdir(parents=True,exist_ok=True)
 before=source.stat(); expected=digest(source); shutil.copy2(source,target); after=source.stat()
 if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns) or digest(target)!=expected or digest(source)!=expected:raise RuntimeError(f'Changed input: {source}')
 origins.append({'original':str(source),'archive_path':relative,'size':after.st_size,'sha256':expected})
def copy_tree(source, relative, excluded=None):
 for directory, dirs, files in os.walk(source,followlinks=False):
  dirs.sort()
  if excluded:dirs[:]=[d for d in dirs if pathlib.Path(directory)/d not in excluded]
  for d in dirs:
   if (pathlib.Path(directory)/d).is_symlink():raise RuntimeError('Symlink directory')
  for name in sorted(files):
   p=pathlib.Path(directory)/name
   copy_file(p,str(pathlib.PurePosixPath(relative)/p.relative_to(source).as_posix()))
S.mkdir(exist_ok=False)
# Full build trees retain original CMake/CTest provenance, actual core, engines,
# test executables and objects. These immutable build trees are never rebuilt.
for name in ['forge-nnue-capture-release','forge-tt-single-worker-release','forge-tt-single-worker-gated-release','forge-tt-single-worker-gated-asan','forge-tt-single-worker-gated-tsan']:
 copy_tree(C/name,'builds/'+name)
for name in ['tt-single-worker-baseline-counted','tt-single-worker-candidate-counted','tt-single-worker-gated-counted']:
 copy_file(C/name,'counted-binaries/'+name)
copy_tree(C/'forge-tt-single-worker-gated-source','frozen-source-export-8865666')
# Export every actual source/build/test/tool input at each commit. The source TAR
# itself is retained in addition to extracted files. No downloaded code runs.
for label,commit in [('baseline-c5cbf97','c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e'),('prototype-a5d2fcb','a5d2fcb5b3270c50b96bcc1b2ebd3bc42db5f2fc'),('gated-8865666','8865666cc0ab4961cd507bae40ff6ce44e9319df')]:
 target=S/'git-source-exports'/f'{label}.tar'; target.parent.mkdir(parents=True,exist_ok=True)
 command=['git','archive',commit,'CMakeLists.txt','LICENSE','bench','include','src','tests','tools']
 with target.open('xb') as out:subprocess.run(command,cwd=R,stdout=out,check=True)
 dest=S/'git-source-exports'/label; dest.mkdir()
 with tarfile.open(target) as archive:archive.extractall(dest,filter='data')
 origins.append({'generated_by':command,'archive_path':target.relative_to(S).as_posix(),'size':target.stat().st_size,'sha256':digest(target),'source_commit':commit})
# Signal parent that independent immutable build snapshots are complete. Parent
# updates the concise proof summaries before issuing this ready marker.
(C/'tt-complete-builds-staged.json').write_text(json.dumps({'status':'builds_and_git_sources_staged','files':len(origins),'awaiting':'tt-complete-root-evidence-ready'},indent=2)+'\n')
print('Build/source snapshots staged; waiting root proof-summary freeze.',flush=True)
while not (C/'tt-complete-root-evidence-ready').exists():time.sleep(1)
copy_tree(V,'repository/validation/single-thread-tt-20261020',excluded={O})
copy_file(R/'releases/forge-6.4.12-candidate-windows-zen5.zip','repository/releases/forge-6.4.12-candidate-windows-zen5.zip')
copy_tree(R/'releases/forge-6.4.12-candidate-windows-zen5','repository/releases/forge-6.4.12-candidate-windows-zen5')
copy_file(HELPER,'archive-helper/archive_results.py')
(S/'STAGING-ORIGINS.json').write_text(json.dumps({'schema_version':1,'original_file_copies':origins,'note':'All source copies compared before/after stat and SHA; source TAR generation does not execute code. Initial prototype-linked actual-api-concurrency binary is preserved as NOT_RUN/ABI-uncertain; see prototype-unexecuted-api-driver.json. No NPS/Elo or match assertion is implied.'},indent=2)+'\n')
spec=importlib.util.spec_from_file_location('trusted_archive',HELPER); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
manifest=module.archive_results(S,O,'tt-single-worker-complete-8865666')
verified=module.verify_archive(manifest)
# Recheck every live copied input after archive, to detect late modifications.
for row in origins:
 if 'original' in row:
  p=pathlib.Path(row['original'])
  if p.stat().st_size!=row['size'] or digest(p)!=row['sha256']:raise RuntimeError('Live original changed: '+str(p))
receipt={'status':'PASS','manifest':manifest.name,'manifest_sha256':digest(manifest),'helper_sha256':digest(HELPER),'input_file_count':len(verified['files']),'input_bytes':sum(x['size'] for x in verified['files']),'archive':verified['archive'],'parts':verified['parts'],'all_copied_live_originals_rehashed_after_archive':True,'original_file_count':len([x for x in origins if 'original' in x]),'source_commits':{'baseline':'c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e','prototype':'a5d2fcb5b3270c50b96bcc1b2ebd3bc42db5f2fc','gated':'8865666cc0ab4961cd507bae40ff6ce44e9319df'},'scope':['complete baseline/prototype/gated Release and gated ASan/TSan build trees','actual counted and API binaries including explicitly unused prototype helper','all TT validation originals before archive directory creation','original Windows evidence and candidate distributable','git archive original source TARs and extracted inputs at three source commits'],'no_originals_deleted_or_mutated':True}
(O/'VERIFY-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
(O/'README.md').write_text('# Complete Forge6.4.12 TT experiment evidence\n\n'+f'Verified {receipt["input_file_count"]} files ({receipt["input_bytes"]:,} original bytes) using the unchanged hosted NNUE archive helper. Every live source copy was rehashed after archival. Concatenate manifest-ordered parts, if multiple, to reconstruct the original ZIP. The adjacent manifest records complete archive and per-file SHA256. No original files were deleted.\n\n'+'The all-stripes prototype remains rejected/tool-blocked by the default TSan held-lock limit. Its first prototype-linked API binary was never executed and is retained only as a failed/unused artifact. Gated6.4.12 correctness evidence is separate; fewer mutex operations do not prove speed or Elo.\n')
print(json.dumps(receipt,indent=2),flush=True)
