from pathlib import Path
import json,shutil,hashlib,zipfile,stat
R=Path('/workspace/dwqww');H=Path('/workspace/forge-nnue-handoff-20261023');V=R/'validation/nnue-pipeline-20261023'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['full-selected-original-report-attempt1','full-selected-original-report-controller-attempt1','legacy-loader-final-net-roundtrip-attempt1','independent-audit-evaluation-controller-attempt1','independent-audit-frozen-zeroep3-report-attempt1','independent-audit-shipped-baseline-attempt1','final-net-native-parity-attempt1','windows-final-net-artifact-review-attempt1','windows-trial-root-package-verification-attempt1','rebuild-default-tests-after-f4a1ed6']:
 source=H/name
 if not source.exists():raise ValueError('Unexpected source path '+str(source))
 dest=V/name
 if dest.exists():
  for f in source.rglob('*'):
   if f.is_file():assert (dest/f.relative_to(source)).is_file() and sha(dest/f.relative_to(source))==sha(f)
 else:shutil.copytree(source,dest)
for n in ['run_original_full_report.py','run_final_loader_roundtrip.py','verify_windows_trial_package_root.py','INDEPENDENT-AUDIT-EVALUATION-TOOL-CLOSED.json']:
 shutil.copy2(H/n,V/n)
name='full-warm20-recovery-attempt1';d=V/name;d.mkdir(exist_ok=False)
for p in (H/name).iterdir():
 if p.is_file() and (p.suffix in ('.json','.md') or '.zip.00' in p.name or p.name.startswith('archive.')):shutil.copy2(p,d/p.name)
a=json.loads((d/'ARCHIVE-MANIFEST.json').read_text())
for rec in a['parts']:
 p=d/rec['name'];assert p.stat().st_size==rec['bytes'] and sha(p)==rec['sha256']
name='publication-frozen-net-before-audit-attempt1';(V/name).mkdir(exist_ok=False);shutil.copy2(H/name/'VERIFIED.json',V/name/'VERIFIED.json')
package=H/'forge-6.4.24-nnue-a52efa5f7864-trial-windows-zen5.zip';dest=R/'releases'/package.name;assert not dest.exists();shutil.copy2(package,dest)
assert sha(dest)=='276598f6ea45eae76cea7016052e00c37e54ccf5c709c48448c1e3aadbf5c3ca'
outer=H/'windows-final-net-trial-attempt1';d=V/'windows-final-net-trial-recovery-index';d.mkdir(exist_ok=False)
with zipfile.ZipFile(package) as z:
 names=z.namelist();prefix=names[0].split('/')[0]+'/'
 contents={}
 for n in names:
  b=z.read(n);contents.setdefault((hashlib.sha256(b).hexdigest(),len(b)),[]).append(n)
 original=json.loads((outer/'FILES-SHA256.json').read_text());records={}
 for p in sorted(outer.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(outer).as_posix();digest=sha(p);size=p.stat().st_size
  if rel in original:assert digest==original[rel]['sha256'] and size==original[rel]['bytes']
  matches=contents.get((digest,size),[])
  rec={'sha256':digest,'bytes':size,'mode':stat.S_IMODE(p.stat().st_mode),'in_original_producer_manifest':rel in original}
  if matches:rec['recover_from_zip_member']=matches[0]
  else:
   t=d/'additional-originals'/rel;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t);assert sha(t)==digest;rec['recover_from_repository']='additional-originals/'+rel
  records[rel]=rec
 assert set(original).issubset(records)
 index={'status':'ALL_ORIGINAL_WINDOWS_OUTER_BYTES_BOUND_FOR_RECOVERY','package_repository_path':'releases/'+package.name,'package_sha256':sha(dest),'original_producer_manifest_records':len(original),'all_closed_outer_files':len(records),'records':records,'scope':'Restore each original outer path into a new directory from the chosen ZIP member or additional-originals, verify bytes/SHA and restore mode; no execution needed.'}
 (d/'RECOVERY-INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
print('Staged completed reports, once-only audit, all warm checkpoints, native parity, exact Windows trial and recoverable raw outer evidence.')
