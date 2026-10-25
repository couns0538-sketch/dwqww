from pathlib import Path,PurePosixPath
import tarfile,hashlib,json,re,os,shutil
p=Path(__file__).resolve().parent;d=json.loads((p/'forge_sol_handoff1435_audit_20261025.json').read_text());inv=json.loads((p/'forge_sol_handoff1435_tar_inventory_20261025.json').read_text());root='forge_handoff_full_20261025_1435/';selection=p/'selected';selection.mkdir(exist_ok=False)
prefs=[x['tar_prefix'] for x in d['source_comparisons'].values()];expected={}
for line in (p/'forge_sol_handoff1435_SHA256SUMS_20261025_1435.txt').read_text().splitlines():
 m=re.fullmatch(r'([0-9a-fA-F]{64}) [ *](.+)',line)
 if m:expected[root+'files/'+m.group(2).removeprefix('./')]=m.group(1).lower()
for rec in d['source_comparisons'].values():
 for x in rec['inventory'].values():expected[x['tar_member']]=x['sha256']
selected=set()
for m in inv['members']:
 n=m['name']
 if m['type']!='0':continue
 if any(n.startswith(pref) for pref in prefs) or n.count('/')==1 or n in [root+'files/SHA256SUMS_20261025_1435.txt',root+'files/FILES_MANIFEST_20261025_1435.md',root+'files/MISSING_INPUTS_20261025.md',root+'files/00_lock_bin/forge_h256_e12.exe'] or n.startswith(root+'files/00_lock_bin/docs/') or n.startswith(root+'files/04_refs/') or n.startswith(root+'files/01c_lockderived_jobC_S01/merge_record/') or ('/09_sol_returns/' in n and 'QA_' in PurePosixPath(n).name) or ('/01_lock_src_h256_e12/' in n and '/forge_h256_e12_1ab50b2d_src/' not in n and not n.endswith('.zip')) or (n.endswith('.sha256') and ('/01b_base_h256_e12_buffix/' in n or '/01c_lockderived_jobC_S01/' in n)):
  selected.add(n)
size=sum(x['size'] for x in inv['members'] if x['name'] in selected);assert shutil.disk_usage(p).free>size+16*1024*1024
records=[]
with tarfile.open(d['tar_path'],'r|xz') as t:
 for m in t:
  if m.name not in selected:continue
  assert m.isfile() and not m.name.startswith('/') and '..' not in PurePosixPath(m.name).parts
  dst=selection.joinpath(*PurePosixPath(m.name).parts);assert dst.is_relative_to(selection)
  dst.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();length=0
  with dst.open('xb') as w:
   f=t.extractfile(m)
   while True:
    b=f.read(1024*1024)
    if not b:break
    w.write(b);h.update(b);length+=len(b)
  assert length==m.size and hashlib.sha256(dst.read_bytes()).hexdigest()==h.hexdigest()
  if m.name in expected:assert h.hexdigest()==expected[m.name],m.name
  os.chmod(dst,m.mode&0o777)
  records.append({'archive_member':m.name,'selected_path':str(dst),'bytes':length,'sha256':h.hexdigest(),'global_or_source_manifest_digest_match':m.name in expected})
assert len(records)==len(selected)
assert hashlib.sha256(Path(d['tar_path']).read_bytes()).hexdigest()==d['tar_sha256']
by={x['archive_member']:x for x in records};trees={}
for label,r in d['source_comparisons'].items():
 path=selection/r['tar_prefix'];actual={str(f.relative_to(path)) for f in path.rglob('*') if f.is_file()};assert actual==set(r['inventory'])
 for rel,x in r['inventory'].items():assert by[x['tar_member']]['sha256']==x['sha256']
 trees[label]={'path':str(path),'files':len(actual),'exact_tar_source_inventory':'PASS','CMake_sha256':r['cmake_sha256'],'tests_sha256':r['tests_sha256']}
result={'status':'PASS_EXACT_SELECTIVE_EXTRACTION','date':'2026-10-25','selected_root':str(selection),'files':len(records),'bytes':sum(r['bytes'] for r in records),'trees':trees,'PC_exe':by[d['S05_PC_lock_exe']['tar_member']],'tar_sha256_unchanged':True,'overwrites':False,'hardlinks':False,'root_VERIFY_executed':False,'native_engine_executed':False,'records':records}
f=p/'forge_sol_handoff1435_selected_receipt_20261025.json';f.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
