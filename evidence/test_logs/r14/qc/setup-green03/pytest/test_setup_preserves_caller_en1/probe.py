import json,os,sys,time,subprocess,psutil
from pathlib import Path
values={k:os.environ.get(k) for k in ['TEMP', 'TMP', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE', 'CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'PIP_CACHE_DIR']}
values['_pid']=os.getpid()
values['_priority']=int(psutil.Process().nice())
Path('D:\\a14\\evidence\\test_logs\\r14\\qc\\setup-green03\\pytest\\test_setup_preserves_caller_en1\\child.json').write_text(json.dumps(values))
time.sleep(0)
sys.exit(7)
