from pathlib import Path,PurePosixPath
import tarfile,hashlib,json,re,difflib
pack=Path('/workspace/attachments/4cb294e3-3035-4b64-9df8-9df6c20e1c84/forge_handoff_full_20261025_1435.tar.xz')
root='forge_handoff_full_20261025_1435/'
out=Path(__file__).resolve().parent
old=out.parent/'forge_sol_jobpack_24jobs_20261025/files'
old_roots={'L':old/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src','Lprime':old/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src','B':old/'01b_base_h256_e12_buffix/forge_h256_e12_buffix_src'}
prefixes={'L':root+'files/01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src/','Lprime':root+'files/01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src/','B':root+'files/01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src/'}
hashes={};sizes={};capture={};problems=[]
with tarfile.open(pack,'r|xz') as t:
 for m in t:
  if not m.isfile():continue
  if m.name.startswith('/') or '..' in PurePosixPath(m.name).parts:raise RuntimeError(m.name)
  f=t.extractfile(m);h=hashlib.sha256();buf=[]
  take=m.name.endswith(('.sha256','SHA256SUMS_20261025_1435.txt','ZIP_SHA256SUMS_20261025_1435.txt','CMakeLists.txt','MISSING_INPUTS_20261025.md','README_FINAL.txt','forge_final_sent.txt','QA_sol_S05_return_20261025.md'))
  while True:
   b=f.read(1024*1024)
   if not b:break
   h.update(b)
   if take:buf.append(b)
  hashes[m.name]=h.hexdigest();sizes[m.name]=m.size
  if take:capture[m.name]=b''.join(buf)
manifest_results=[]
for name in [root+'files/SHA256SUMS_20261025_1435.txt',root+'ZIP_SHA256SUMS_20261025_1435.txt']:
 data=capture.get(name)
 if data is None:manifest_results.append({'manifest':name,'status':'MISSING'});continue
 parent=str(PurePosixPath(name).parent)+'/'
 entries=[];invalid=[];mismatch=[];seen=set()
 for line in data.decode().splitlines():
  if not line:continue
  m=re.fullmatch(r'([0-9a-fA-F]{64}) [ *](.+)',line)
  if not m:invalid.append(line);continue
  digest,rel=m.groups();rel=rel.removeprefix('./');target=parent+rel
  if rel.startswith('/') or '..' in PurePosixPath(rel).parts:invalid.append(line);continue
  if target in seen:invalid.append('duplicate '+target)
  seen.add(target);entries.append(target)
  if hashes.get(target)!=digest.lower():mismatch.append({'path':target,'expected':digest.lower(),'actual':hashes.get(target)})
 manifest_results.append({'manifest':name,'manifest_sha256':hashes[name],'entries':len(entries),'status':'PASS' if not invalid and not mismatch else'FAIL','invalid':invalid,'mismatch':mismatch,'unlisted_regular_paths_below_manifest_parent':[k for k in hashes if k.startswith(parent) and k not in seen and k!=name]})
comparisons={}
for label,pref in prefixes.items():
 inventory={n[len(pref):]:{'sha256':h,'bytes':sizes[n],'tar_member':n} for n,h in hashes.items() if n.startswith(pref)}
 changed=[];same=[];new=[]
 for rel,r in inventory.items():
  src=old_roots[label]/rel
  if not src.exists():new.append(rel);continue
  old_sha=hashlib.sha256(src.read_bytes()).hexdigest()
  if old_sha==r['sha256']:same.append(rel)
  else:changed.append({'path':rel,'old_sha256':old_sha,**r})
 removed=[str(f.relative_to(old_roots[label])) for f in old_roots[label].rglob('*') if f.is_file() and str(f.relative_to(old_roots[label])) not in inventory]
 cm=capture[pref+'CMakeLists.txt'].decode();old_cm=(old_roots[label]/'CMakeLists.txt').read_text()
 comparisons[label]={'tar_prefix':pref,'old_comparison_source':str(old_roots[label]),'files':len(inventory),'total_bytes':sum(x['bytes'] for x in inventory.values()),'identical_count':len(same),'changed':changed,'new':[inventory[n]|{'path':n} for n in new],'old_only':removed,'all_production_src_include_identical':all(n in same for n in inventory if n.startswith(('src/','include/'))),'cmake_sha256':inventory['CMakeLists.txt']['sha256'],'tests_sha256':inventory['tests/tests.cpp']['sha256'],'CMake_change_vs_old':''.join(difflib.unified_diff(old_cm.splitlines(True),cm.splitlines(True))), 'inventory':inventory}
windows=[{'tar_member':n,'sha256':hashes[n],'bytes':sizes[n]} for n in hashes if n.endswith('.exe')]
primary_exe=root+'files/00_lock_bin/forge_h256_e12.exe'
audit={'status':'PASS_MANIFESTS_AND_SAFE_MEMBERS' if all(x['status']=='PASS' for x in manifest_results) else'REVIEW_MANIFEST_ISSUES','date':'2026-10-25','tar_path':str(pack),'tar_sha256':hashlib.sha256(pack.read_bytes()).hexdigest(),'regular_files_hashed':len(hashes),'regular_bytes_streamed':sum(sizes.values()),'full_extract_performed':False,'native_engine_or_benchmark_executed':False,'git_mutations':False,'manifests':manifest_results,'source_comparisons':comparisons,'windows_executables':windows,'S05_PC_lock_exe':{'tar_member':primary_exe,'sha256':hashes.get(primary_exe),'bytes':sizes.get(primary_exe),'expected_prompt_sha_prefix_match':hashes.get(primary_exe,'').startswith('456743d9'),'execution':'NOT_EXECUTED; only inspect disassembly later','purpose':'Windows zero-register-copy clamp witness for held S05-1 fix-up'},'strategy':['Do not full extract. Stream-verify every global manifest record before any selective copy.','Reconstruct new immutable L from old L only after complete per-file hash match; do not mutate old pack.','For Lprime and B, create fresh directories, copy identical old-tree bytes with shutil.copy2 or verified reflink; copy only listed changed/new tar members through a validated regular-file extraction function; do not hardlink editable candidate sources.','Verify every reconstructed tree file against tar hashes and its supplied tree_sources manifest; reject missing/additional files before patch experiments.','For immediate fix-ups materialize all three complete small source trees plus their small manifests, not duplicate nets/datasets/return evidence. Preserve the tar as the source of all further inputs.','Selectively extract only the 3828330-byte Windows PC lock exe and FMA checker/QA notes when S05 is reached; do not execute PC recipes or Windows exe.','Use git-generated new-file mode headers on newly authored/reworked patches; preserve earlier delivered patches and audit them separately.'],'minimal_unique_changed_input_bytes':sum(x['bytes'] for label,r in comparisons.items() for x in r['changed']+r['new']),'three_complete_tree_total_bytes':sum(r['total_bytes'] for r in comparisons.values())}
# Bind actual root records and the independently uploaded full prompt; the prose's
# root ZIP manifest is absent, which is disclosed rather than invented.
audit['root_regular_members']=[{'path':n,'sha256':hashes[n],'bytes':sizes[n]} for n in hashes if n.count('/')==1]
audit['top_level_manifest_note']='The prose requests ZIP_SHA256SUMS_20261025_1435.txt, but that member is absent. All1942 listed global digests pass. Three root files and four nested hash manifests plus the global manifest itself account for the1950 regular members. The prompt count1927 is stale.'
external_prompt=Path('/workspace/attachments/62ff8f4f-0cf2-4b19-a9e9-b14bd6bc3739/HANDOFF_PROMPT_FULL_20261025_1435.md')
audit['uploaded_full_prompt_matches_tar_prompt']={'actual_equal':hashlib.sha256(external_prompt.read_bytes()).hexdigest()==hashes[root+'HANDOFF_PROMPT_FULL_20261025_1435.md'],'sha256':hashes[root+'HANDOFF_PROMPT_FULL_20261025_1435.md'],'bytes':sizes[root+'HANDOFF_PROMPT_FULL_20261025_1435.md']}
source_manifest_names={'L':root+'files/01_lock_src_h256_e12/h256_e12_sources_73files.sha256','Lprime':root+'files/01c_lockderived_jobC_S01/tree_sources_lockderived_jobC_S01_20261025_1215.sha256','B':root+'files/01b_base_h256_e12_buffix/tree_sources_buffix_jobC_S01_20261025_1215.sha256'}
audit['source_manifest_checks']={}
for label,name in source_manifest_names.items():
 entries=0;bad=[];listed=set()
 for line in capture[name].decode().splitlines():
  m=re.fullmatch(r'([0-9a-fA-F]{64}) [ *](.+)',line)
  if not m:bad.append({'invalid':line});continue
  digest,rel=m.groups();rel=rel.removeprefix('./');entries+=1;listed.add(rel)
  if hashes.get(prefixes[label]+rel)!=digest.lower():bad.append({'path':rel,'expected':digest.lower(),'actual':hashes.get(prefixes[label]+rel)})
 audit['source_manifest_checks'][label]={'manifest':name,'manifest_sha256':hashes[name],'entries':entries,'status':'PASS' if not bad else'FAIL','mismatch':bad,'additional_tree_paths':sorted(set(comparisons[label]['inventory'])-listed)}
inv=json.loads((out/'forge_sol_handoff1435_tar_inventory_20261025.json').read_text())
audit['path_safety']={'status':'PASS' if not inv['path_type_issues'] and not inv['duplicate_names'] else'FAIL','traversals_links_devices_or_fifos':inv['path_type_issues'],'duplicate_names':inv['duplicate_names']}
audit['status']='PASS_ALL1942_LISTED_DIGESTS_WITH_DISCLOSED_UNLISTED_ROOT_METADATA' if manifest_results[0]['status']=='PASS' and all(x['status']=='PASS' for x in audit['source_manifest_checks'].values()) and audit['path_safety']['status']=='PASS' else'FAIL_AUDIT'
audit['all_regular_member_digest_inventory']=[{'path':n,'bytes':sizes[n],'sha256':hashes[n]} for n in sorted(hashes)]
(out/'forge_sol_handoff1435_audit_20261025.json').write_text(json.dumps(audit,indent=2)+'\n')
# Small trusted manifests only; these are audit copies, not whole-source extraction.
for n,data in capture.items():
 if n.endswith(('files/SHA256SUMS_20261025_1435.txt','ZIP_SHA256SUMS_20261025_1435.txt','tree_sources_lockderived_jobC_S01_20261025_1215.sha256','tree_sources_buffix_jobC_S01_20261025_1215.sha256')):
  (out/('forge_sol_handoff1435_'+PurePosixPath(n).name)).write_bytes(data)
print(json.dumps({k:v for k,v in audit.items() if k not in ['source_comparisons','manifests']},indent=2))
print('MANIFESTS',[(x['manifest'],x['status'],x.get('entries')) for x in manifest_results])
for label,r in comparisons.items():print(label,{k:v for k,v in r.items() if k not in ['inventory','CMake_change_vs_old']})
