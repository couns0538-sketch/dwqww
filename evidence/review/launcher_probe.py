"""Manual launcher regression fixture; never accesses production inputs."""
import json
import os
import time
from pathlib import Path
import psutil
process=psutil.Process()
record=dict(pid=os.getpid(),affinity=process.cpu_affinity(),priority=process.nice(),
            cpu=int(os.environ['ASTRA_R13_CPU']),temp=os.environ['TEMP'],
            cuda=os.environ['CUDA_VISIBLE_DEVICES'],hip=os.environ['HIP_VISIBLE_DEVICES'])
assert record['affinity']==[record['cpu']]
assert record['priority']==psutil.IDLE_PRIORITY_CLASS
assert record['cuda']==record['hip']=='-1'
print(json.dumps(record),flush=True)
if os.environ.get('R13_PROBE_TIMEOUT')=='1':
    time.sleep(10)
