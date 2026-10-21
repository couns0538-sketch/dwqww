#!/usr/bin/env python3
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
OUT=Path(__file__).resolve().parent
HELPER=OUT/'fetch_public_archive.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(name,data):
 with (OUT/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
assert sha(HELPER)=='7bc05adb7ecc60200635a67f0163bbb227a32bcf4048ac4144c95cabd61b6a0b'
command=[sys.executable,'-B',str(HELPER)]
started=now()
put('LAUNCH.json',{'started_utc':started,'command':command,'cwd':'/workspace/dwqww','helper_sha256':sha(HELPER),'launcher_sha256':sha(Path(__file__)),'network_actions':'Four read-only unauthenticated commit-pinned public HTTPS GETs','only_output_directory':str(OUT)})
with (OUT/'transport.stdout').open('xb') as out,(OUT/'transport.stderr').open('xb') as err:
 result=subprocess.run(command,cwd='/workspace/dwqww',stdout=out,stderr=err,check=False)
receipt={'status':'PASS_TRANSPORT_COMMAND_EXIT' if result.returncode==0 else 'FAILED_TRANSPORT_COMMAND_EXIT_PRESERVED','started_utc':started,'completed_utc':now(),'exit_code':result.returncode,'stdout_bytes':(OUT/'transport.stdout').stat().st_size,'stdout_sha256':sha(OUT/'transport.stdout'),'stderr_bytes':(OUT/'transport.stderr').stat().st_size,'stderr_sha256':sha(OUT/'transport.stderr'),'helper_unchanged_after_execution':sha(HELPER)=='7bc05adb7ecc60200635a67f0163bbb227a32bcf4048ac4144c95cabd61b6a0b'}
put('EXIT.json',receipt)
print(json.dumps(receipt,indent=2))
sys.exit(result.returncode)
