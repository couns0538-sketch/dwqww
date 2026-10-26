import os,sys,runpy
from pathlib import Path
blocked=['/workspace/dwqww/releases/forge_sol_pack31_20261025/S08', '/workspace/forge-pack24-20261026/S08', '/workspace/forge-pack24-20261026/S08_corpus_20261026']
def guard(event,args):
 if event=="open" and args and isinstance(args[0],(str,bytes,os.PathLike)):
  p=str(Path(os.fsdecode(args[0])).absolute())
  if any(p==r or p.startswith(r+"/") for r in blocked):raise PermissionError("old workspace path blocked: "+p)
sys.addaudithook(guard)
try:
 Path(blocked[0]+'/forge_sol_S08_collect_profiles_substitute_20261026.py').read_bytes()
except PermissionError:print('guard positive control: PASS',flush=True)
else:raise AssertionError('old path was accessible')
sys.path.insert(0,str(Path.cwd()))
runpy.run_module("unittest",run_name="__main__")
