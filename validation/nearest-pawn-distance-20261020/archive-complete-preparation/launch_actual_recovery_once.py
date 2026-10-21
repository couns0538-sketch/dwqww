#!/usr/bin/env python3
"""One separately root-authorized actual21 recovery into a NEW nonexistent scratch tree."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,sys
ROOT=Path('/workspace/dwqww');OUT=ROOT/'validation/nearest-pawn-distance-20261020/archive-complete'
DEST=Path('/workspace/.cloud-setup/forge21-recovery-check-attempt1')
HELPER=OUT/'restore_new_scratch.py';NAME='forge-nearest-pawn-2e151d0-20261020-complete.manifest.json';MANIFEST=OUT/NAME
EXPECTED_HELPER='1efc0d1998d33973eed109e28e042ed047237ffc3ddcc94d4651ef3eb91050fc'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
assert Path(__file__).resolve().parent==OUT, 'Preparation is not executable; root must promote reviewed files'
clear=json.loads((OUT/'ROOT-ACTUAL-RECOVERY-CLEAR.json').read_text())
assert clear.get('authorized') is True and clear['authorization']=='ROOT_AUTHORIZES_ONE_ACTUAL_FRESH_SCRATCH_RECOVERY_ONLY' and clear['provided_by']=='/root'
assert clear['source_commit']=='2e151d019bc58dff2ab4e76e99ef99516af8d222' and clear['target']==str(DEST) and clear['must_be_new_empty_destination'] is True
assert sha(HELPER)==clear['helper_sha256']==EXPECTED_HELPER
assert re.fullmatch('[0-9a-f]{64}',clear['manifest_sha256']) and sha(MANIFEST)==clear['manifest_sha256']
audit=OUT/'INDEPENDENT-ARCHIVE-AUDIT.json';assert sha(audit)==clear['independent_archive_audit_sha256']
assert json.loads(audit.read_text())['status']=='PASS_INDEPENDENT_COMPLETE_21_ARCHIVE_AUDIT'
assert not DEST.exists() and not DEST.is_symlink()
for name in ['ACTUAL-RECOVERY-COMMAND.json','ACTUAL-RECOVERY-EXIT.json','actual-recovery.stdout','actual-recovery.stderr']:assert not (OUT/name).exists()
# Explicit manifest-name preserves the unchanged helper whose historical default names20.
command=[sys.executable,'-B',str(HELPER),'--parts',str(OUT),'--destination',str(DEST),'--manifest-sha256',clear['manifest_sha256'],'--manifest-name',NAME]
started=now();save('ACTUAL-RECOVERY-COMMAND.json',{'status':'ROOT_AUTHORIZED_BEFORE_ONE_ACTUAL_RECOVERY','started_utc':started,'command':command,'cwd':str(ROOT),'root_clearance_sha256':sha(OUT/'ROOT-ACTUAL-RECOVERY-CLEAR.json'),'helper_sha256':sha(HELPER),'manifest_sha256':sha(MANIFEST),'independent_archive_audit_sha256':sha(audit),'destination_absent_before_execution':True,'launcher_sha256':sha(Path(__file__)),'original_absolute_paths_are_not_write_targets_static_scope':True,'scope_qualification':'Static helper/command scope only; not a syscall trace.'})
with (OUT/'actual-recovery.stdout').open('xb') as stdout,(OUT/'actual-recovery.stderr').open('xb') as stderr:
    done=subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr,check=False)
receipt={'status':'PASS_ACTUAL_RECOVERY_COMMAND_EXIT' if done.returncode==0 else 'FAILED_ACTUAL_RECOVERY_COMMAND_EXIT_PRESERVED_NO_RETRY','started_utc':started,'completed_utc':now(),'command':command,'exit_code':done.returncode,'stdout_sha256':sha(OUT/'actual-recovery.stdout'),'stderr_sha256':sha(OUT/'actual-recovery.stderr'),'destination':str(DEST),'destination_retained':DEST.is_dir(),'engines_compilers_git_executed':False}
save('ACTUAL-RECOVERY-EXIT.json',receipt);print(json.dumps(receipt,indent=2));sys.exit(done.returncode)
