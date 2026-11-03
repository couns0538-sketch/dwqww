import os,json,sys
from pathlib import Path
Path('D:\\a14\\evidence\\test_logs\\r14\\qc\\launcher-cap-red01\\pytest\\test_child_environment_and_par0\\child.json').write_text(json.dumps(dict(executable=sys.executable,env={k:os.environ.get(k) for k in ['CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES', 'TEMP', 'PYTHONPATH', 'ASTRA_R14_DEADLINE', 'ASTRA_R13_DEADLINE']})))
