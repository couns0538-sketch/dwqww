"""Independent read-only restored-byte/mode audit; imports no archive/restore producer."""
from pathlib import Path,PurePosixPath
import hashlib,json,stat,datetime,os,sys,traceback
BASE=Path('/workspace/dwqww/validation/tt-refresh-20261021/archive-complete')
DEST=Path('/workspace/.cloud-setup/forge-tt-refresh-1d3ed25-recovery-scratch-attempt1')
ROOT=DEST/'files'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while data:=f.read(1048576):h.update(data)
 return h.hexdigest()
report={'status':'RUNNING','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'destination':str(DEST),'checks':[],'findings':[],'engines_builds_git_or_original_writes':False,'restored_tree_writes':False,'producer_or_restore_imports':False}
def check(name,ok,**detail):
 row={'name':name,'passed':bool(ok),**detail};report['checks'].append(row)
 if not ok:report['findings'].append(row)
try:
 assert sha(BASE/'forge-tt-refresh-1d3ed25-20261021-complete.manifest.json')=='90eb616d701bd06212880aa14a24dbec85452fd8fe73e6223221675c785f9740'
 manifest=json.loads((BASE/'forge-tt-refresh-1d3ed25-20261021-complete.manifest.json').read_text())
 modes=json.loads((BASE/'LIVE-BEFORE.json').read_text());originals={r['payload_path']:r for r in modes['files']};names={r['path'] for r in manifest['files']}
 assert DEST.is_dir() and not DEST.is_symlink() and not DEST.is_relative_to(Path('/workspace/dwqww'))
 check('Restored embedded mode-map bytes equal frozen original ledger',(ROOT/'archive-provenance/LIVE-FILES-AND-MODES.json').read_bytes()==(BASE/'LIVE-BEFORE.json').read_bytes())
 for row in manifest['files']:
  p=ROOT/row['path'];before=p.lstat();actual=sha(p);after=p.lstat()
  check('Restoredpayload:'+row['path'],stat.S_ISREG(after.st_mode) and not p.is_symlink() and actual==row['sha256'] and after.st_size==row['size'] and (before.st_size,before.st_mode,before.st_mtime_ns)==(after.st_size,after.st_mode,after.st_mtime_ns))
  if row['path'] in originals:
   expected=originals[row['path']];check('Restoredoriginalmode+mtime:'+row['path'],stat.S_IMODE(after.st_mode)==expected['mode'] and after.st_mtime_ns==expected['mtime_ns'])
  else:check('Restoredprovenancegeneric0600:'+row['path'],stat.S_IMODE(after.st_mode)==0o600)
 for row in modes['directories']:
  p=ROOT/row['payload_path'];check('Recordeddirectorymode:'+row['payload_path'],p.is_dir() and not p.is_symlink() and stat.S_IMODE(p.stat().st_mode)==row['mode'])
 files=set();dirs=set();special=[]
 for current,children,leaves in os.walk(ROOT,followlinks=False):
  for name in children+leaves:
   p=Path(current)/name;mode=p.lstat().st_mode;relative=p.relative_to(ROOT).as_posix()
   if stat.S_ISLNK(mode):special.append(relative)
   elif stat.S_ISREG(mode):files.add(relative)
   elif stat.S_ISDIR(mode):dirs.add(relative)
   else:special.append(relative)
 expected_dirs={str(parent) for name in names for parent in PurePosixPath(name).parents if str(parent)!='.'}|{r['payload_path'] for r in modes['directories']}
 check('Exactrestoredfileinventory',files==names and not special,missing=sorted(names-files),extra=sorted(files-names),special=special)
 check('Exactrestoredrecordedandstructuraldirectoryinventory',dirs==expected_dirs,missing=sorted(expected_dirs-dirs),extra=sorted(dirs-expected_dirs))
 report.update(payload_files_verified=len(names),original_file_modes_and_mtimes_verified=len(originals),recorded_original_directory_modes_verified=len(modes['directories']),structural_directory_count=len(dirs),qualifications=['Only219recorded directoryscope modes are restored and verified; generated structural ancestors retain scratchdefaults, without claiming unrecorded originalancestor permissions.','All2241physically restoredpayloads are hashed after extraction; generic ZIP0600 is not executable restoration by itself.','Fresh scratchonly. No engine execution, correctness revalidation, speed, Elo or nativehardware claim.'])
except Exception as error:report['findings'].append({'name':'Exception','type':type(error).__name__,'message':str(error)});traceback.print_exc()
report.update(status='PASS_INDEPENDENT_NEW_SCRATCH_RECOVERY_AUDIT' if not report['findings'] else 'FAIL_INDEPENDENT_NEW_SCRATCH_RECOVERY_AUDIT',check_count=len(report['checks']),failed_check_count=len(report['findings']),checker_sha256=sha(Path(__file__)),completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (BASE/'INDEPENDENT-RECOVERY-AUDIT.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks']},indent=2))
sys.exit(0 if not report['findings'] else 1)
