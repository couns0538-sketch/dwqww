from pathlib import Path
import datetime,gzip,tarfile,hashlib,json,subprocess,shutil,time
source=Path('/tmp/forge_sol_S18_none_smoke_failed_checkpoint_20261027')
archive=Path('/tmp/forge_sol_S18_none_failed_publication_v2_20261027/forge_sol_S18_none_failed_original_evidence_20261027.tar.gz')
restored=Path('/tmp/forge_sol_S18_none_failed_GNU_roundtrip_v2_20261027')
out=Path('/tmp/forge_sol_S18_none_failed_publication_final_20261027');out.mkdir(exist_ok=False)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()
rows=[]
for original in sorted(path for path in source.rglob('*') if path.is_file()):
 rel=original.relative_to(source).as_posix();copy=restored/rel
 assert not original.is_symlink() and not copy.is_symlink()
 assert original.stat().st_size==copy.stat().st_size
 assert (original.stat().st_mode&0o777)==(copy.stat().st_mode&0o777)
 assert sha(original)==sha(copy)
 rows.append({'path':rel,'bytes':original.stat().st_size,'sha256':sha(original),'mode':original.stat().st_mode&0o777})
assert len(rows)==39
with tarfile.open(archive,'r:gz') as reader:
 members=reader.getmembers();assert [m.name for m in members]==[row['path'] for row in rows]
 for member,row in zip(members,rows):
  assert member.isfile() and member.size==row['bytes'] and member.mode&0o777==row['mode']
  assert hashlib.sha256(reader.extractfile(member).read()).hexdigest()==row['sha256']
command=['tar','--compare','--gzip','--file',str(archive),'--directory',str(restored)]
start=time.monotonic();completed=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
(out/'forge_sol_S18_none_failed_GNU_compare_20261027.stdout').write_bytes(completed.stdout)
(out/'forge_sol_S18_none_failed_GNU_compare_20261027.stderr').write_bytes(completed.stderr)
assert completed.returncode==0 and not completed.stdout and not completed.stderr
shutil.copy2(archive,out/archive.name);assert sha(out/archive.name)==sha(archive)
first=Path('/tmp/forge_sol_S18_none_failed_publication_20261027')
assert sha(first/archive.name)==sha(archive)
for filepath in [Path('/tmp/forge_sol_S18_archive_failed_none_20261027.py'),Path('/tmp/forge_sol_S18_archive_failed_none_v2_20261027.py'),Path(__file__),first/'forge_sol_S18_GNU_default_mode_failure_20261027.json']:
 shutil.copy2(filepath,out/filepath.name)
receipt={'status':'PASS_ORIGINAL_FAILURE_CHECKPOINT_PRESERVATION','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_run_status':'FAIL_S18_TRAINING; not relabeled','source':str(source),'archive':archive.name,'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'files':rows,'original_logical_bytes':sum(row['bytes'] for row in rows),'Python_reader':'39/39 exact bytes/modes/sizes','GNU_extracted_reader':'39/39 exact bytes/modes/sizes with --same-permissions','GNU_independent_compare':{'argv':command,'returncode':completed.returncode,'elapsed_seconds':time.monotonic()-start},'original_inputs_unchanged':True,'archive_encodings_byte_identical':True,'failed_packaging_approaches_preserved':['v1 bytes matched; GNU default umask masked group/other mode bits','v2 all byte/mode checks passed, then metadata writer reused Path variable as subprocess result; AttributeError; original script/outputs unchanged'],'native_retry_or_data_reconstruction':False}
(out/'forge_sol_S18_none_failed_archive_receipt_20261027.json').write_text(json.dumps(receipt,indent=2)+'\n')
(out/'forge_sol_S18_none_failed_archive_checkpoint_20261027.md').write_text('Complete original39-file failed S18 smoke checkpoint, including training outputs, data copies, raw logs and prelaunch grant. Child completed training and50000-row postscore, but controller RSS_UNAVAILABLE made the overall smoke FAIL. All39 files verified byte/mode/size equal through Python and independently GNU tar. No engine/network adoption, qualified smoke or training/Elo gain. Original runtime and both packaging-check mistakes preserved; archive data never changed. Next: source-only RSS transition reproducer and reviewed successor, other arms held.\n')
print(json.dumps({key:receipt[key] for key in ['status','archive_bytes','archive_sha256','original_logical_bytes']},sort_keys=True))
