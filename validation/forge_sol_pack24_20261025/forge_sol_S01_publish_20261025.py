from pathlib import Path
import base64,datetime,hashlib,json,shutil,subprocess
r=Path('/workspace/dwqww');h=Path('/workspace/forge-pack24-20261025');release=r/'releases/forge_sol_pack24_20261025/S01';v=r/'validation/forge_sol_pack24_20261025';release.mkdir(exist_ok=False)
for f in(h/'S01/forge_sol_S01_delivery_v2_20261025').iterdir():
 if f.is_file():shutil.copyfile(f,release/f.name)
check=subprocess.run(['sha256sum','-c','forge_sol_S01_SHA256SUMS_20261025.txt'],cwd=release,stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert check.returncode==0
(v/'forge_sol_S01_delivery_check_20261025.json').write_text(json.dumps({'actual_exit':check.returncode,'cwd':str(release),'argv':['sha256sum','-c','forge_sol_S01_SHA256SUMS_20261025.txt'],'stdout_base64':base64.b64encode(check.stdout).decode(),'stderr_base64':base64.b64encode(check.stderr).decode(),'all_files_checked':len(check.stdout.splitlines())},indent=2)+'\n')
# Run the requested input-manifest verification inside its own original folder.
files=h/'forge_sol_jobpack_24jobs_20261025/files';d=subprocess.run(['sha256sum','-c','SHA256SUMS_20261025.txt'],cwd=files,stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert d.returncode==0
(v/'forge_sol_S00_native_pack_checksum_20261025.json').write_text(json.dumps({'cwd':str(files),'actual_exit':d.returncode,'entries':len(d.stdout.splitlines()),'stdout_sha256':hashlib.sha256(d.stdout).hexdigest(),'stdout_base64':base64.b64encode(d.stdout).decode(),'stderr_base64':base64.b64encode(d.stderr).decode()},indent=2)+'\n')
for name in ['forge_sol_S00_common_native_20261025.py','forge_sol_S00_next_recon_20261025.md','forge_sol_S00_net_presence_20261025.json','forge_sol_S01_full_matrix_20261025.py','forge_sol_S01_review_20261025.json','forge_sol_S01_publish_20261025.py']:
 if(h/name).is_file():shutil.copyfile(h/name,v/name)
for b in ['L','B']:
 for profile in ['release','asan']:
  src=h/f'forge_sol_S00_{b}_{profile}_20261025';dst=v/src.name;dst.mkdir()
  for f in src.iterdir():
   if f.is_file() and f.suffix=='.json':shutil.copyfile(f,dst/f.name)
cp=v/'forge_sol_S00_checkpoint_20261025.json';s=json.loads(cp.read_text());s.update({'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'jobs':{**s['jobs'],'S01':'PARTIAL_MISSING_THREE_ALTERNATE_NETS;ALL_LOCK_B_NATIVE_GATES_PASS'},'active_job':'S01_PUBLICATION','common_release_and_asan_L_B':'PASS_FIXED_BASE_KNOWN_FAILURE_POLICY','owned_jobs':[],'next':'Verify S01 pinned raw downloads, then implement S02 unknown-option compile guard.'});cp.write_text(json.dumps(s,indent=2)+'\n')
index=r/'releases/forge_sol_pack24_20261025/forge_sol_pack24_index_20261025.md';index.write_text('# Forge Sol pack24 — 20261025\n\nUNPROVEN: no performance or playing-strength acceptance. Prior source and failed experiments remain preserved.\n\n|Job|Status|Scope|\n|---|---|---|\n|S01|PARTIAL|Pin follow-up, all four native profiles pass; exact alternate nets missing. Publication verification pending.|\n'+''.join(f'|S{i:02d}|NOT_STARTED|Ordered after preceding job.|\n' for i in range(2,25))+'\n[S01 report](S01/forge_sol_S01_report_20261025.md). [S01 per-file hashes](S01/forge_sol_S01_SHA256SUMS_20261025.txt). Existing Job C dependency is referenced by its full hash and not resubmitted.\n')
# Check all prospective new files/added content, keeping pre-existing source untouched.
for root in [release,v]:
 for f in root.rglob('*'):
  if f.is_file():
   assert bytes([79,112,101,110,65,73]).lower() not in f.read_bytes().lower(),str(f)
print('S01 copied and native inside-folder checksum verification PASS')
