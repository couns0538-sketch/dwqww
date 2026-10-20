from pathlib import Path
import datetime,hashlib,json,re
HERE=Path(__file__).resolve().parent
BUILD=Path('/workspace/.cloud-setup/windows6418-build')
COMMIT='fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((HERE/'WINDOWS-BUILD-CLEAR.json').read_text())['authorization']=='18 WINDOWS BUILD CLEAR'
runtime=HERE/'runtime-attempt1/result.json';record=json.loads(runtime.read_text())
assert record['status']=='passed' and record['source_and_tests_commit']==COMMIT
assert len(record['checks'])==9 and all(c['exit_code']==0 for c in record['checks'])
assert record['input_sha256_before']==record['input_sha256_after']
raw=HERE/'runtime-attempt1/bench-stdout.log';stdin=HERE/'runtime-attempt1/bench-stdin.txt'
signature=re.findall(r'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$',raw.read_text(),re.M)
assert signature==[str(record['bench11_nodes'])] and record['bench11_nodes']>0
assert sha(BUILD/'forge.exe')==record['input_sha256_after']['forge.exe']
assert not (HERE/'BENCH-SIGNATURE-FREEZE.json').exists()
assert not (HERE/'package-phase-command.json').exists()
freeze={'source_and_tests_commit':COMMIT,'bench11_nodes':record['bench11_nodes'],'engine_sha256':sha(BUILD/'forge.exe'),'raw_bench_stdout_sha256':sha(raw),'raw_bench_stdin_sha256':sha(stdin),'runtime_result_sha256':sha(runtime),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_independent':True,'origin':'First actual candidate18 Windows/Wine bench11 run after full9checks; no prior/native node expectation.','hash_mib':16,'threads':1,'scope':'Freeze of actual logical work signature only; no time/NPS/Elo/native hardware comparison.'}
(HERE/'BENCH-SIGNATURE-FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
print(json.dumps(freeze,indent=2))
