"""Pure independent regressions: original frozen guard must not report false0RSS.
No subprocess, native/compiler/engine or /proc modification occurs.
"""
from pathlib import Path
import importlib.util,unittest,types,os
from unittest.mock import patch
P=Path('/tmp/forge_sol_S11_resource_guard_v3_prep_20261027/forge_sol_S11_resource_guard_v3_20261027.py')
spec=importlib.util.spec_from_file_location('review_target',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
C=Path('/tmp/forge_sol_S18_rss_scope_v3_checkpoint_20261027/probe_runtime')
LEADER=(C/'forge_sol_S18_actual_leader_original_20261027.status').read_text()
WORKER=(C/'forge_sol_S18_actual_task_275333_original_20261027.status').read_text()
ORIGINAL=Path.read_text
class Controls(unittest.TestCase):
 def test_actual_Z_leader_capture_does_not_become_zero_shared_memory(self):
  def read(path,*a,**k):
   if str(path)=='/proc/275331/status':return LEADER
   if str(path)=='/proc/275331/task/275333/status':return WORKER
   return ORIGINAL(path,*a,**k)
  guard=object.__new__(m.OwnedResourceGuard)
  with patch.object(Path,'read_text',new=read):sample=guard._read_rss(275331)
  self.assertTrue(sample is None or sample>0,'A proven live12,572KiB same-Tgid worker must be counted or RSS rejected, never reported as0')
 def test_non_Z_missing_RSS_cannot_pass_aggregate_reason(self):
  pid=275331;owner=os.getpid()
  class Guard(m.OwnedResourceGuard):
   def _clock(self):return 0.
   def _disk_free(self):return 10**10
   def _pid_stat(self,p):
    if p==owner:return {'pid':p,'start_ticks':1,'pgrp':99,'ppid':1,'state':'R'}
    if p==pid:return {'pid':p,'start_ticks':2,'pgrp':pid,'ppid':owner,'state':'R'}
   def _event(self):return {'token':1,'pid':pid}
   def _read_rss(self,p):return 1024 if p==owner else super()._read_rss(p)
  def read(path,*a,**k):
   if str(path)==f'/proc/{pid}/status':return LEADER.replace('Z (zombie)','R (running)')
   return ORIGINAL(path,*a,**k)
  owned=types.SimpleNamespace(_STOP_REQUESTED=False,_all_members=lambda group:[{'pid':pid,'start_ticks':2,'ppid':owner,'state':'R'}])
  g=Guard('/PURE_NO_WRITES',10.,owned,{})
  with patch.object(Path,'read_text',new=read):reason=g.reason()
  self.assertIsNotNone(reason,'Unknown non-zombie missingRSS must fail closed, not authorize the sample as0')
if __name__=='__main__':unittest.main(verbosity=2)
