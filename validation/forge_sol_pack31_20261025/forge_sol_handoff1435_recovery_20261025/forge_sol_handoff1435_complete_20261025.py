from pathlib import Path,PurePosixPath
import tarfile,hashlib,json,shutil,os,subprocess,base64
p=Path(__file__).resolve().parent;d=json.loads((p/'forge_sol_handoff1435_audit_20261025.json').read_text());selected=p/'selected';expected={r['path']:r for r in d['all_regular_member_digest_inventory']};free=shutil.disk_usage(p).free
assert free>=90*1024*1024,('WAIT_SPACE',free)
existing=[];new=[]
for name,r in expected.items():
 dst=selected.joinpath(*PurePosixPath(name).parts)
 if dst.exists():
  assert dst.is_file() and not dst.is_symlink() and dst.stat().st_size==r['bytes'] and hashlib.sha256(dst.read_bytes()).hexdigest()==r['sha256'],('EXISTING_DIFF_ABORT_BEFORE_WRITE',name)
  existing.append(name)
 else:new.append(name)
assert len(existing)==319,('UNEXPECTED_EXISTING_COUNT',len(existing))
assert free>sum(expected[n]['bytes'] for n in new)+16*1024*1024
# Exact transport and all existing destinations are checked before creating a byte.
assert hashlib.sha256(Path(d['tar_path']).read_bytes()).hexdigest()==d['tar_sha256']
newset=set(new)
with tarfile.open(d['tar_path'],'r|xz') as t:
 for m in t:
  if not m.isfile():continue
  assert m.name in expected and not m.name.startswith('/') and '..' not in PurePosixPath(m.name).parts
  if m.name not in newset:continue
  dst=selected.joinpath(*PurePosixPath(m.name).parts);dst.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();count=0
  with dst.open('xb') as w:
   f=t.extractfile(m)
   while True:
    b=f.read(1024*1024)
    if not b:break
    count+=len(b);h.update(b);w.write(b)
  assert count==m.size==expected[m.name]['bytes'] and h.hexdigest()==expected[m.name]['sha256'],m.name
  os.chmod(dst,m.mode&0o777)
for name,r in expected.items():
 dst=selected.joinpath(*PurePosixPath(name).parts);assert dst.is_file() and hashlib.sha256(dst.read_bytes()).hexdigest()==r['sha256'],name
actual={str(f.relative_to(selected)) for f in selected.rglob('*') if f.is_file()};assert actual==set(expected),(len(actual),len(expected))
files=selected/'forge_handoff_full_20261025_1435/files';cmd=['sha256sum','-c','SHA256SUMS_20261025_1435.txt'];r=subprocess.run(cmd,cwd=files,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
raw={'format':'original_streams_base64_v1','argv':cmd,'cwd':str(files),'exit_code':r.returncode}
for name,b in [('stdout',r.stdout),('stderr',r.stderr)]:raw[name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
rawf=p/'forge_sol_handoff1435_full_manifest_raw_20261025.json';rawf.write_text(json.dumps(raw,indent=2)+'\n')
assert r.returncode==0 and r.stdout.count(b': OK\n')==1942
result={'status':'PASS_COMPLETE_EXACT_EXTRACTION_AND_SUPPLIED_GNU_MANIFEST','date':'2026-10-25','full_pack_root':str(files.parent),'files_root':str(files),'all_tar_regular_files':len(expected),'previous319_files_untouched_verified_before_and_after':True,'new_files_created':len(new),'new_bytes_written':sum(expected[n]['bytes'] for n in new),'total_original_bytes':sum(x['bytes'] for x in expected.values()),'tar_sha256':d['tar_sha256'],'inside_files_actual_GNU_sha256sum_exit':r.returncode,'manifest_OK_entries':1942,'original_sha256sum_streams_json':str(rawf),'root_ZIP_SHA_manifest_missing_disclosed':True,'engine_native_or_VERIFY_executed':False,'source_changed':False,'free_bytes_before':free,'free_bytes_after':shutil.disk_usage(p).free,'created_files':[expected[n] for n in new]}
f=p/'forge_sol_handoff1435_complete_receipt_20261025.json';f.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='created_files'},indent=2));print('receipt_sha256',hashlib.sha256(f.read_bytes()).hexdigest())
