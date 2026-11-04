import json,os,sys,time,subprocess,psutil
from pathlib import Path
values={k:os.environ.get(k) for k in ['TEMP', 'TMP', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE', 'CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'PIP_CACHE_DIR']}
values['_pid']=os.getpid()
values['_priority']=int(psutil.Process().nice())
values['_descendant']=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(30)'],stdout=sys.stdout,stderr=sys.stderr).pid
Path('D:\\a14\\evidence\\test_logs\\r14\\qc\\setup-pipe-red01\\pytest\\test_live_refusal_stops_only_o1\\child.json').write_text(json.dumps(values))
time.sleep(30)
sys.exit(0)
