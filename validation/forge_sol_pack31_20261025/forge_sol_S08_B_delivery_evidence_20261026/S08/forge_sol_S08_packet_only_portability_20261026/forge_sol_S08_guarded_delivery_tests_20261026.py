import os,sys,runpy
blocked=['/workspace/dwqww/releases/forge_sol_pack31_20261025/S08', '/workspace/forge-pack24-20261026/S08/', '/workspace/forge-pack24-20261026/S08_corpus_20261026/']
def guard(event,args):
 if event=="open" and args and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.fsdecode(args[0])
  if any(p==r or p.startswith(r.rstrip("/")+"/") for r in blocked):raise PermissionError("old workspace path blocked: "+p)
sys.addaudithook(guard)
runpy.run_module("unittest",run_name="__main__")
