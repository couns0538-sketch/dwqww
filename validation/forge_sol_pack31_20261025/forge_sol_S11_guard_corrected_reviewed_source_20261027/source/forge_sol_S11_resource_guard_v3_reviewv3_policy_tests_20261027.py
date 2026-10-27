#!/usr/bin/env python3
"""Pure fake-/proc policy controls; no subprocess/compiler/engine launch."""
from pathlib import Path
import copy
import importlib.util
import os
import types
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('resource_v3',HERE/'forge_sol_S11_resource_guard_v3_reviewv3_20261027.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class Fake(module.OwnedResourceGuard):
    def __init__(self):
        self.now=0.;self.event=None;self.free=10**10;self.rss={};self.stats={};self.tree=[];self.scans=[]
        self.stats[os.getpid()]={'pid':os.getpid(),'start_ticks':100,'pgrp':99,'ppid':1,'state':'R'};self.rss[os.getpid()]=1000
        self.external=types.SimpleNamespace(_STOP_REQUESTED=False,_all_members=self.members)
        self.output={};super().__init__(Path('/PURE_FIXTURE_NO_OUTPUT'),10.,self.external,self.output)
    def _clock(self):return self.now
    def _disk_free(self):return self.free
    def _pid_stat(self,pid):return copy.deepcopy(self.stats.get(pid))
    def _read_rss(self,pid):return self.rss.get(pid)
    def _event(self):return copy.deepcopy(self.event)
    def members(self,group):
        self.scans.append(group)
        return [copy.deepcopy(row) for row in self.tree if self.stats.get(row['pid'],{}).get('pgrp')==group]
    def start(self,pid=500,birth=200,token=1):
        value={'pid':pid,'start_ticks':birth,'pgrp':pid,'ppid':os.getpid(),'state':'R'}
        self.stats[pid]=value;self.rss[pid]=2000;self.tree=[value]
        self.event={'token':token,'pid':pid}
    def exit(self,pid=500):
        self.stats.pop(pid,None);self.rss.pop(pid,None);self.tree=[r for r in self.tree if r['pid']!=pid]


class GuardTests(unittest.TestCase):
    def test_empty_prelaunch_and_stage_first_scan(self):
        g=Fake();self.assertIsNone(g.reason());self.assertEqual(g.scans,[])
        g.start();self.assertIsNone(g.reason());self.assertEqual(g.scans,[500]);self.assertEqual(g.output['maximum_observed_owned_RSS_bytes'],3000)

    def test_every_loop_clock_stop_identity_but_sampling_intervals(self):
        g=Fake();g.start();self.assertIsNone(g.reason());samples=g.counts['RSS_samples']
        for point in [.001,.01,.02,.049]:g.now=point;self.assertIsNone(g.reason())
        self.assertEqual(g.scans,[500]);self.assertEqual(g.counts['RSS_samples'],samples)
        self.assertEqual(g.counts['owner_identity_checks'],5);self.assertEqual(g.counts['leader_identity_checks'],5)
        g.now=.05;self.assertIsNone(g.reason());self.assertEqual(g.counts['RSS_samples'],samples+1)
        g.now=.999;self.assertIsNone(g.reason());self.assertEqual(g.scans,[500])
        g.now=1.;self.assertIsNone(g.reason());self.assertEqual(g.scans,[500,500])

    def test_stage_transition_clears_old_members_and_forces_refresh(self):
        g=Fake();g.start();g.reason();g.exit();g.start(600,300,2)
        self.assertIsNone(g.reason());self.assertEqual(g.group,600);self.assertNotIn(500,g.cached)
        self.assertEqual(g.scans,[500,500,600]);self.assertEqual(g.counts['stage_changes'],2)

    def test_open_previous_group_blocks_new_stage(self):
        g=Fake();g.start();g.reason();g.start(600,300,2)
        # Preserve actual previous member in simulated /proc/group enumeration.
        g.tree.append(g.stats[500])
        self.assertEqual(g.reason(),'PREVIOUS_OWNED_GROUP_OPEN')

    def test_normal_exit_drain_and_prelaunch_after_reap(self):
        g=Fake();g.start();g.reason();g.exit()
        self.assertIsNone(g.reason());self.assertTrue(g.stage_closed)
        self.assertIsNone(g.reason());self.assertIsNone(g.finalize())
        self.assertEqual(g.cached.keys(),{os.getpid()});self.assertEqual(g.counts['final_scans'],1)

    def test_short_stage_exited_before_first_observation(self):
        g=Fake();g.event={'token':1,'pid':500}
        self.assertIsNone(g.reason());self.assertTrue(g.stage_closed)
        self.assertIsNone(g.finalize())

    def test_birth_group_and_controller_drift_fail(self):
        for field in ['start_ticks','pgrp']:
            g=Fake();g.start();g.reason();g.stats[500][field]+=1
            self.assertEqual(g.reason(),'OWNED_STAGE_IDENTITY_CHANGED')
        g=Fake();g.start();g.reason();g.stats[os.getpid()]['start_ticks']+=1
        self.assertEqual(g.reason(),'CONTROLLER_IDENTITY_CHANGED')

    def test_same_pid_new_event_cannot_reset_live_birth_guard(self):
        g=Fake();g.start();g.reason();g.stats[500]['start_ticks']+=1;g.event['token']=2
        self.assertEqual(g.reason(),'OWNED_STAGE_IDENTITY_CHANGED')

    def test_new_child_visibility_on_membership_refresh_and_aggregate_cap(self):
        g=Fake();g.start();g.reason()
        child={'pid':501,'start_ticks':201,'pgrp':500,'ppid':500,'state':'R'}
        g.stats[501]=child;g.tree.append(child);g.rss[501]=module.CAP
        g.now=.05;self.assertIsNone(g.reason());self.assertNotIn(501,g.cached)
        g.now=1.;self.assertEqual(g.reason(),'OWNED_RSS_LIMIT');self.assertIn(501,g.cached)
        self.assertGreater(g.output['maximum_observed_owned_RSS_bytes'],module.CAP)

    def test_existing_member_birth_drift_at_sample_blocks(self):
        g=Fake();g.start();child={'pid':501,'start_ticks':201,'pgrp':500,'ppid':500,'state':'R'}
        g.stats[501]=child;g.tree.append(child);g.rss[501]=100;g.reason()
        g.stats[501]['start_ticks']+=1;g.now=.05
        self.assertEqual(g.reason(),'OWNED_MEMBER_IDENTITY_CHANGED')

    def test_clock_stop_and_disk_block_even_between_RSS_samples(self):
        for kind in ['total','command_end','stop','disk']:
            g=Fake();g.start();g.reason();g.now=.01
            if kind=='total':g.deadline=.009;expected='OWNED_DEADLINE';end=None
            elif kind=='command_end':expected='OWNED_DEADLINE';end=.009
            elif kind=='stop':g.external._STOP_REQUESTED=True;expected='EXTERNAL_STOP';end=None
            else:g.free=0;expected='DISK_FREE_FLOOR';end=None
            self.assertEqual(g.reason(end=end),expected)

    def test_long_membership_scan_cannot_hide_deadline_or_stop(self):
        for change in ['clock','stop']:
            g=Fake();g.start();old=g.external._all_members
            def wrapped(group):
                result=old(group)
                if change=='clock':g.now=11.
                else:g.external._STOP_REQUESTED=True
                return result
            g.external._all_members=wrapped
            self.assertEqual(g.reason(),'OWNED_DEADLINE' if change=='clock' else 'EXTERNAL_STOP')

    def test_unregistered_group_and_missing_event_fail_closed(self):
        g=Fake();g.start();g.stats[500]['pgrp']=999
        self.assertEqual(g.reason(),'OWNED_STAGE_IDENTITY_CHANGED')
        g=Fake();g.start();g.reason();g.event=None
        self.assertEqual(g.reason(),'OWNED_EVENT_MISSING')

    def test_final_full_scan_even_after_sampling_window(self):
        g=Fake();g.start();g.reason();before=len(g.scans);g.now=.01
        self.assertIsNone(g.finalize());self.assertEqual(len(g.scans),before+1)
        self.assertEqual(g.snapshot()['RSS_cap_bytes'],4*1024**3)
        self.assertIn('not continuous',g.snapshot()['visibility_gap'])


if __name__=='__main__':unittest.main(verbosity=2)
