import json,os,sys,time
from pathlib import Path
Path('D:\\a14\\evidence\\test_logs\\r14\\qc\\setup-red01\\pytest\\test_setup_preserves_caller_en1\\child.json').write_text(json.dumps({k:os.environ.get(k) for k in ['TEMP', 'TMP', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE', 'CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'PIP_CACHE_DIR']}))
time.sleep(0)
sys.exit(7)
