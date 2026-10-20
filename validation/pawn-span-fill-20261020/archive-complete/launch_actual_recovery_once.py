#!/usr/bin/env python3
"""Root-authorized one-shot scratch recovery launch; no engines or original writes."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
ROOT=Path('/workspace/dwqww')
OUT=ROOT/'validation/pawn-span-fill-20261020/archive-complete'
DEST=Path('/workspace/.cloud-setup/forge20-recovery-check-attempt1')
HELPER=OUT/'restore_new_scratch.py'
MANIFEST=OUT/'forge-pawn-span-fc23918-20261020-complete.manifest.json'
CLEAR=OUT/'ROOT-ACTUAL-RECOVERY-CLEAR.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write_new(name,obj):
    with (OUT/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
clear=json.loads(CLEAR.read_text())
assert clear['authorization']=='ROOT_AUTHORIZES_ONE_ACTUAL_FRESH_SCRATCH_RECOVERY_ONLY'
assert clear['target']==str(DEST) and clear['must_be_new_empty_destination'] is True
assert sha(HELPER)==clear['helper_sha256']=='1efc0d1998d33973eed109e28e042ed047237ffc3ddcc94d4651ef3eb91050fc'
assert sha(MANIFEST)==clear['manifest_sha256']=='9f12841fbdba3a9575d53c36bae5e6ae105d3f5c78a42c44b358c696fb789478'
assert not DEST.exists() and not DEST.is_symlink()
audit=OUT/'INDEPENDENT-ARCHIVE-AUDIT.json'
assert sha(audit)=='20f9e01a4897442b8209a7ebe47e0c2705f8c451e0fe62e7f64df3114fa0d628'
for name in ['ACTUAL-RECOVERY-COMMAND.json','ACTUAL-RECOVERY-EXIT.json','actual-recovery.stdout','actual-recovery.stderr']:
    assert not (OUT/name).exists()
command=[sys.executable,'-B',str(HELPER),'--parts',str(OUT),'--destination',str(DEST),'--manifest-sha256',clear['manifest_sha256']]
started=now()
write_new('ACTUAL-RECOVERY-COMMAND.json',{'status':'ROOT_AUTHORIZED_ONE_SHOT_RECOVERY_BEFORE_EXECUTION','started_utc':started,'command':command,'cwd':str(ROOT),'root_clearance_sha256':sha(CLEAR),'helper_sha256':sha(HELPER),'manifest_sha256':sha(MANIFEST),'independent_archive_audit_sha256':sha(audit),'destination_absent_before_execution':True,'wrapper_sha256':sha(Path(__file__)),'no_engine_compiler_git_or_original_absolute_path_writes':True})
with (OUT/'actual-recovery.stdout').open('xb') as out,(OUT/'actual-recovery.stderr').open('xb') as err:
    result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err,check=False)
receipt={'status':'PASS_ACTUAL_RECOVERY_COMMAND_EXIT' if result.returncode==0 else 'FAILED_ACTUAL_RECOVERY_COMMAND_EXIT_PRESERVED_NO_RETRY','started_utc':started,'completed_utc':now(),'exit_code':result.returncode,'command':command,'stdout_sha256':sha(OUT/'actual-recovery.stdout'),'stderr_sha256':sha(OUT/'actual-recovery.stderr'),'stdout_bytes':(OUT/'actual-recovery.stdout').stat().st_size,'stderr_bytes':(OUT/'actual-recovery.stderr').stat().st_size,'destination':str(DEST),'destination_retained':DEST.is_dir(),'engines_compilers_git_executed':False}
write_new('ACTUAL-RECOVERY-EXIT.json',receipt)
print(json.dumps(receipt,indent=2))
sys.exit(result.returncode)
