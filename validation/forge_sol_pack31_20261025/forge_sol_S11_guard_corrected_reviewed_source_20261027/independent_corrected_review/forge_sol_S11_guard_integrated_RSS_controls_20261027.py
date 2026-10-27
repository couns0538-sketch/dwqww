"""Independent pure integration controls against actual final Guard.reason()."""
from pathlib import Path
import copy,importlib.util,os,types,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
TARGET=Path('/tmp/forge_sol_S11_resource_guard_v3_prep_20261027/forge_sol_S11_resource_guard_v3_reviewv3_20261027.py')
spec=importlib.util.spec_from_file_location('independent_final_guard',TARGET);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
REAL=Path
CAP=4294967296
PID=275331;TID=275333
CAPTURE=Path('/tmp/forge_sol_S18_rss_scope_v3_checkpoint_20261027/probe_runtime')
LEADER=(CAPTURE/'forge_sol_S18_actual_leader_original_20261027.status').read_text();WORKER=(CAPTURE/'forge_sol_S18_actual_task_275333_original_20261027.status').read_text()
def taskstat(pid,birth,state='Z'):
 return f'{pid} (INDEPENDENT) '+' '.join([state,'1',str(PID)]+['0']*16+[str(birth)]+['0']*4)+'\n'
class World:
 def __init__(self,label,owner_kib=1,worker=True,live_missing=False):
  self.root=ROOT/('fixture_'+label);self.root.mkdir();self.now=0.;self.owner=os.getpid()
  self.stats={self.owner:{'pid':self.owner,'start_ticks':100,'pgrp':99,'ppid':1,'state':'R'},PID:{'pid':PID,'start_ticks':20,'pgrp':PID,'ppid':self.owner,'state':'Z'}}
  self.put(f'{self.owner}/status',f'Pid: {self.owner}\nTgid: {self.owner}\nState: R\nVmRSS: {owner_kib} kB\n')
  self.put(f'{PID}/status',LEADER.replace('Z (zombie)','R (running)') if live_missing else LEADER)
  self.put(f'{PID}/task/{PID}/status',LEADER);self.put(f'{PID}/task/{PID}/stat',taskstat(PID,20))
  if worker:self.put(f'{PID}/task/{TID}/status',WORKER);self.put(f'{PID}/task/{TID}/stat',taskstat(TID,21,'S'))
  world=self
  class Guard(m.OwnedResourceGuard):
   def _clock(self):return world.now
   def _disk_free(self):return 10**10
   def _pid_stat(self,pid):return copy.deepcopy(world.stats.get(pid))
   def _event(self):return {'token':1,'pid':PID}
  owned=types.SimpleNamespace(_STOP_REQUESTED=False,_all_members=lambda group:[copy.deepcopy(self.stats[PID])] if PID in self.stats and group==PID else [])
  self.result={};self.guard=Guard(self.root/'out',10.,owned,self.result)
 def put(self,name,text):
  p=self.root/'proc'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 def path(self,*args):
  return self.root/'proc'/REAL(*(str(x) for x in args[1:])) if args and str(args[0])=='/proc' else REAL(*args)
class Integrated(unittest.TestCase):
 def test_fallback_aggregate_cap_exact_boundary_stays_4GiB(self):
  for delta,expected in ((-1,None),(0,None),(1,'OWNED_RSS_LIMIT')):
   world=World('cap_'+str(delta),owner_kib=4194304-12572+delta)
   with patch.object(m,'Path',side_effect=world.path):reason=world.guard.reason()
   self.assertEqual(reason,expected);self.assertEqual(world.result['maximum_observed_owned_RSS_bytes'],CAP+1024*delta)
   self.assertEqual(world.guard.RSS_scope_counts.get('OWNED_LIVE_THREAD_SHARED_MM'),1)
 def test_actual_Z_status_all_dead_normal_drain_then_reap(self):
  world=World('normal_dead',worker=False)
  with patch.object(m,'Path',side_effect=world.path):
   self.assertIsNone(world.guard.reason());self.assertEqual(world.guard.last_RSS_observation['scope'],'OWNED_VERIFIED_ALL_TASKS_EXITED')
   world.stats.pop(PID);self.assertIsNone(world.guard.reason());self.assertTrue(world.guard.stage_closed);self.assertIsNone(world.guard.finalize())
 def test_unknown_non_Z_missing_RSS_stops_actual_guard(self):
  world=World('unknown',live_missing=True)
  with patch.object(m,'Path',side_effect=world.path):reason=world.guard.reason()
  self.assertEqual(reason,'OWNED_RESOURCE_OBSERVER_ERROR')
 def test_slow_RSS_fallback_cannot_hide_total_deadline(self):
  world=World('slow_read');original=m.read_proc_status
  def read(path):
   value=original(path)
   if str(path).endswith(f'/task/{TID}/status'):world.now=11.
   return value
  with patch.object(m,'Path',side_effect=world.path),patch.object(m,'read_proc_status',side_effect=read):reason=world.guard.reason()
  self.assertEqual(reason,'OWNED_DEADLINE')
 def test_leader_disappears_after_task_RSS_read_then_closes_normally(self):
  world=World('exit_during_RSS');original=m.read_proc_status
  def read(path):
   value=original(path)
   if str(path).endswith(f'/task/{TID}/status'):world.stats.pop(PID,None)
   return value
  with patch.object(m,'Path',side_effect=world.path),patch.object(m,'read_proc_status',side_effect=read):
   self.assertIsNone(world.guard.reason());self.assertIsNone(world.guard.reason());self.assertTrue(world.guard.stage_closed)
if __name__=='__main__':unittest.main(verbosity=2)
