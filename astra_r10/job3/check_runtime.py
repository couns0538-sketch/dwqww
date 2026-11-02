"""Small CPU-only import check of private external dependencies; no NPT/training."""
import argparse, json, os, pathlib, sys
p=argparse.ArgumentParser();p.add_argument('--threads',type=int,choices=[1],required=True);p.parse_args()
root=pathlib.Path('D:/a10/job3/runtime')
if not pathlib.Path(sys.executable).resolve().is_relative_to(root):raise RuntimeError('wrong interpreter')
for key in ('CUDA_VISIBLE_DEVICES','HIP_VISIBLE_DEVICES','ROCR_VISIBLE_DEVICES'):os.environ[key]=''
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
sys.path.insert(0,str(root/'packages'))
import numpy, pytest, torch, chess, psutil
torch.set_num_threads(1);torch.set_num_interop_threads(1)
if torch.version.cuda is not None or torch.version.hip is not None or '+cpu' not in torch.__version__:raise RuntimeError('CPU-only Torch required')
for module in (numpy,pytest,torch,chess,psutil):
    if not pathlib.Path(module.__file__).resolve().is_relative_to(root):raise RuntimeError('external import escaped private runtime')
assert torch.tensor([2,3],device='cpu').sum().item()==5
assert int(numpy.array([2,3]).sum())==5
assert psutil.Process().nice()==psutil.IDLE_PRIORITY_CLASS
print(json.dumps({'status':'PASS','scope':'CPU dependency import/arithmetic only; no NPT, training or GPU',
 'python':sys.version,'torch':torch.__version__,'numpy':numpy.__version__,'pytest':pytest.__version__,
 'threads':torch.get_num_threads(),'interop_threads':torch.get_num_interop_threads(),'cuda':torch.version.cuda,'hip':torch.version.hip,
 'files':{m.__name__:m.__file__ for m in (numpy,pytest,torch,chess,psutil)}},indent=2))
