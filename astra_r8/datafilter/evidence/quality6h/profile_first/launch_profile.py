"""One owned read-only audit child, with fixed source order and a bounded deadline."""
from datetime import datetime, timezone
import json, os, subprocess, sys, time
from pathlib import Path
TOOLS=Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
ROOT=Path('C:/astra8_data/quality6h_20261102')
sys.path.insert(0,str(TOOLS))
import chess
from profile_corpus import low_priority,sha256
from resource_policy import storage_guard
low_priority();storage_guard(ROOT,allowance=20_000_000)
numbers=[1,2,3,6,9,12,15,18,21,24,27,30,33,36,39]
command=[sys.executable,str(TOOLS/'profile_corpus.py'),str(ROOT/'corpus_profile'),
         '--sources',*[f'D:/grok-pc-data/selfplay_out/forge_selfplay_{n:03}.txt' for n in numbers]]
runtime={'python':sys.version,'chess_version':chess.__version__,
         'files':{str(p):sha256(p) for p in [Path(chess.__file__),TOOLS/'profile_corpus.py',TOOLS/'resource_policy.py']}}
identity=dict(command=command,runtime=runtime,workers=1,priority='BelowNormal',strength='UNPROVEN',
              source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=TOOLS,text=True).strip(),
              started_utc=datetime.now(timezone.utc).isoformat(),
              deadline_utc='2026-11-03T03:11:00+00:00')
with (ROOT/'profile_launch.json').open('x',encoding='utf-8') as fh:json.dump(identity,fh,indent=2)
deadline=datetime.fromisoformat(identity['deadline_utc']).timestamp()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='-1',HIP_VISIBLE_DEVICES='-1',
         ROCR_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
try:
    with (ROOT/'corpus_profile.stdout.log').open('xb') as out,(ROOT/'corpus_profile.stderr.log').open('xb') as err:
        result=subprocess.run(command,stdout=out,stderr=err,env=env,cwd=TOOLS,
                              timeout=max(1,deadline-time.time()),creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    receipt=dict(status='PASS' if result.returncode==0 else 'FAIL',exit_code=result.returncode)
except subprocess.TimeoutExpired:
    receipt=dict(status='TIMEOUT',reason='only this owned audit child terminated at the recorded deadline')
receipt.update(finished_utc=datetime.now(timezone.utc).isoformat(),
    stdout_sha256=sha256(ROOT/'corpus_profile.stdout.log'),stderr_sha256=sha256(ROOT/'corpus_profile.stderr.log'),
    runtime_unchanged=all(sha256(path)==digest for path,digest in runtime['files'].items()))
with (ROOT/'profile_exit.json').open('x',encoding='utf-8') as fh:json.dump(receipt,fh,indent=2)
print(json.dumps(receipt,indent=2))
raise SystemExit(0 if receipt['status']=='PASS' and receipt['runtime_unchanged'] else 1)
