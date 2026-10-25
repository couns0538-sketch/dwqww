from pathlib import Path
import json,hashlib,zipfile,difflib,shutil,subprocess,re,datetime
r=Path('/workspace/dwqww');h=Path('/workspace/forge-sol-20261025');d=h/'forge_sol_return_20261025';p=Path('/workspace/forge-sol-20261025-pgo');v=r/'validation/forge_sol_20261025'
# Additions-only PGO tooling patch. No engine source/test deletions or edits.
selected=[]
for line in (d/'forge_sol_pgo_sha256_20261025.txt').read_text().splitlines():
 digest,name=line.split(None,1);name=name.strip();assert hashlib.sha256((d/name).read_bytes()).hexdigest()==digest;
 if "/" not in name and Path(name).suffix in {".ps1",".py",".sh",".cs",".md"}:selected.append(name)
selected.append('forge_sol_pgo_idea_source_20261025.md')
patch=[]
for name in sorted(selected):
 text=(d/name).read_text();patch.append('diff --git a/'+name+' b/'+name+'\nnew file mode '+('100755' if name.endswith('.sh') else '100644')+'\n');patch.extend(difflib.unified_diff([],text.splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+name))
patchpath=d/'forge_sol_pgo_patch_20261025.patch';patchpath.write_text(''.join(patch))
# Reconstruct each delivered patch against the exact canonical lock export.
proofdir=h/'forge_sol_patch_checks_20261025';proofdir.mkdir(exist_ok=False);proofs=[]
for name,source in [('forge_sol_buffer_patch_20261025.patch','forge_sol_buffer_source_20261025'),('forge_sol_int16_patch_20261025.patch','forge_sol_int16_source_20261025'),('forge_sol_pgo_patch_20261025.patch',None)]:
 work=proofdir/name.removesuffix('.patch');shutil.copytree(d/'forge_sol_lock_source_20261025',work);data=(d/name).read_bytes();steps=[]
 for tag,extra in [('dryrun',['--dry-run']),('apply',[])]:
  argv=['patch','--batch','--forward','--fuzz=0','-p1',*extra];done=subprocess.run(argv,cwd=work,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE);(proofdir/(name+'.'+tag+'.stdout')).write_bytes(done.stdout);(proofdir/(name+'.'+tag+'.stderr')).write_bytes(done.stderr);assert done.returncode==0 and not re.search(rb'offset|fuzz|FAILED|reject|reversed',done.stdout+done.stderr,re.I);steps.append({'argv':argv,'actual_exit':done.returncode})
 if source:
  required=[q for folder in ['include','src','tests','bench'] for q in(d/source/folder).rglob('*') if q.is_file()]+[d/source/'CMakeLists.txt']
  for q in required:assert (work/q.relative_to(d/source)).read_bytes()==q.read_bytes(),str(q)
  scope='all compiled engine, original/new test, bench and CMake inputs equal delivered source'
 else:
  for folder in ['include','src','tests','bench']:
   for q in(d/'forge_sol_lock_source_20261025'/folder).rglob('*'):
    if q.is_file():assert(work/q.relative_to(d/'forge_sol_lock_source_20261025')).read_bytes()==q.read_bytes()
  for q in selected:assert(work/q).read_bytes()==(d/q).read_bytes()
  scope='tool additions match; every original engine/test/bench source remains unchanged'
 proofs.append({'patch':name,'sha256':hashlib.sha256(data).hexdigest(),'base':'f4911f2709bd5ae7e5fca7aea30aac5d87314a05','steps':steps,'status':'PASS','scope':scope})
# Keep compact proof; scratch reconstructions can be regenerated from sealed inputs.
(proofdir/'forge_sol_patch_results_20261025.json').write_text(json.dumps(proofs,indent=2)+'\n');shutil.copyfile(proofdir/'forge_sol_patch_results_20261025.json',d/'forge_sol_patch_results_20261025.json')
q=v/'forge_sol_patch_evidence_20261025';q.mkdir(exist_ok=True)
for f in proofdir.iterdir():
 if f.is_file():shutil.copyfile(f,q/f.name)
# Store next-week recovery metadata and source/report entries.
for name in ['forge_sol_report_20261025.md','forge_sol_continue_20261025.md','forge_sol_pgo_idea_source_20261025.md','forge_sol_int16_local_checks_20261025.txt','forge_sol_pgo_linux_results_20261025.txt']:
 if(d/name).exists():shutil.copyfile(d/name,v/name)
# Every payload file is hashed; manifest self exclusion is explicit.
def purpose(rel):
 if rel.startswith(('forge_sol_buffer_source_20261025/','forge_sol_int16_source_20261025/','forge_sol_lock_source_20261025/')):return 'Frozen original build source; canonical filename retained for exact recipe'
 if rel.startswith('forge_sol_pgo_evidence_20261025/'):return 'Original PGO software checks and preserved failed approaches'
 if rel.endswith('.patch'):return 'Clean -p1 patch against f4911f2; see patch results'
 if rel.endswith('.zip'):return 'Original input or compact original evidence archive, labeled by filename'
 if rel.endswith('.ps1'):return 'PowerShell tool or read/hash-only historical recipe reference; see report'
 if rel.endswith(('.py','.sh','.cs')):return 'Own implementation build, validation or native resource tool'
 if rel.endswith('.json'):return 'Frozen source identity, verification or evidence record'
 if 'report' in rel or 'notes' in rel or 'continue' in rel:return 'Results, limits, commands or continuation instructions'
 return 'Dated source/evidence checksum or documented check result'
manifest=d/'MANIFEST_20261025.txt';assert not manifest.exists();rows=[]
for f in sorted(d.rglob('*')):
 if f.is_file():
  rel=f.relative_to(d).as_posix();rows.append((rel,hashlib.sha256(f.read_bytes()).hexdigest(),purpose(rel)))
manifest.write_text('# SHA256  relative file | one-line purpose\n# All payload files listed; MANIFEST_20261025.txt itself excluded. Outer ZIP SHA authenticates it.\n'+''.join(f'{digest}  {rel} | {why}\n' for rel,digest,why in rows))
archive=h/'forge_sol_return_20261025.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(d.rglob('*')):
  if f.is_file():
   rel=f.relative_to(d).as_posix();info=zipfile.ZipInfo(rel,(2026,10,25,0,0,0));info.compress_type=zipfile.ZIP_STORED if f.suffix=='.zip' else zipfile.ZIP_DEFLATED;info.external_attr=(0o100755 if f.suffix=='.sh' else 0o100644)<<16;z.writestr(info,f.read_bytes())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(set(z.namelist()))==len(rows)+1
 for rel,digest,_ in rows:assert hashlib.sha256(z.read(rel)).hexdigest()==digest
 assert all(not n.endswith('.exe') for n in z.namelist()),'No Linux ELF .exe may be mispresented as Windows binary'
result={'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':archive.name,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'archive_bytes':archive.stat().st_size,'payload_files':len(rows),'manifest':'MANIFEST_20261025.txt','all_payload_sha256_verified_after_zip_readback':True,'native_Windows_exes_included':False,'patches':proofs}
(h/'forge_sol_delivery_integrity_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
