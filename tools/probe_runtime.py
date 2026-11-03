"""Read-only CPU dependency admission; no trainer construction or GPU calls."""
import importlib
import json
import os
from pathlib import Path
import sys

result={'python':sys.version,'executable':sys.executable,'modules':{},'temporary_root':os.environ.get('TEMP')}
for name in ('pytest','chess','numpy','psutil','torch'):
    module=importlib.import_module(name)
    result['modules'][name]={'version':getattr(module,'__version__',None),'path':module.__file__}
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
result['cpu_tensor_sum']=int(torch.tensor([1,2,3],device='cpu').sum())
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'astra_r8'/'datafilter'))
for name in ('npt_adapter','train'):
    module=importlib.import_module(name)
    result['modules'][name]={'path':module.__file__}
print(json.dumps(result,indent=2),flush=True)
