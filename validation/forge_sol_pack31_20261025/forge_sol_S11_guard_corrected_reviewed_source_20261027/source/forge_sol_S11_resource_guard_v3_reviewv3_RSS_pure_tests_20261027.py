#!/usr/bin/env python3
"""Pure bounded proc-file fixtures; original S18 status text is read-only data."""
from pathlib import Path
import importlib.util
import json
import os
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
TARGET=Path(os.environ.get('FORGE_S11_RSS_TEST_TARGET',str(HERE/'forge_sol_S11_resource_guard_v3_reviewv3_20261027.py')))
spec=importlib.util.spec_from_file_location('S11_RSS_PURE',TARGET);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def status(pid,tgid,state,rss=None):
    value=f'Name:\tPURE_FIXTURE\nState:\t{state} (fixture)\nTgid:\t{tgid}\nPid:\t{pid}\n'
    return value+(f'VmRSS:\t{rss} kB\n' if rss is not None else '')


def stat(pid,group,birth=20,state='Z'):
    fields=[state,'1',str(group)]+['0']*16+[str(birth)]+['0']*4
    return f'{pid} (PURE_FIXTURE) '+' '.join(fields)+'\n'


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='S11_PURE_RSS_');self.root=Path(self.temp.name)
        self.pid=700;self.tid=701
    def tearDown(self):self.temp.cleanup()
    def put(self,relative,text):
        p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    def path(self,*args):
        if args and str(args[0])=='/proc':return self.root.joinpath(*(str(x) for x in args[1:]))
        return Path(*args)
    def fixture(self,worker=True,value=12572):
        self.put('700/status',status(700,700,'Z'))
        self.put('700/task/700/status',status(700,700,'Z'));self.put('700/task/700/stat',stat(700,700))
        if worker:
            self.put('700/task/701/status',status(701,700,'S',value));self.put('700/task/701/stat',stat(701,700,21,'S'))
    def read(self):
        guard=object.__new__(m.OwnedResourceGuard)
        guard.RSS_scope_counts={};guard.last_RSS_observation=None;guard.first_RSS_fallback_observation=None
        with mock.patch.object(m,'Path',side_effect=self.path):value=guard._read_rss(self.pid)
        return value,guard

    def test_zombie_leader_live_shared_MM_is_counted_once(self):
        self.fixture();value,g=self.read();self.assertEqual(value,12572*1024)
        if hasattr(m,'read_owned_rss_bytes'):
            self.assertEqual(g.last_RSS_observation['scope'],'OWNED_LIVE_THREAD_SHARED_MM')
            self.assertIn('never sum',g.last_RSS_observation['aggregation'])

    def test_missing_RSS_on_live_leader_is_not_zero(self):
        self.put('700/status',status(700,700,'S'))
        with self.assertRaises(ValueError):self.read()

    def test_genuine_all_tasks_dead_normal_EOF_zero(self):
        self.fixture(worker=False);value,g=self.read();self.assertEqual(value,0)
        self.assertEqual(g.last_RSS_observation['scope'],'OWNED_VERIFIED_ALL_TASKS_EXITED')

    def test_explicit_live_task_zero_RSS_is_known_not_missing(self):
        self.fixture(value=0);value,g=self.read();self.assertEqual(value,0)
        self.assertEqual(g.last_RSS_observation['scope'],'OWNED_LIVE_THREAD_SHARED_MM')

    def test_multiple_threads_use_max_shared_MM_not_sum(self):
        self.fixture();self.put('700/task/702/status',status(702,700,'R',12572));self.put('700/task/702/stat',stat(702,700,22,'R'))
        value,g=self.read();self.assertEqual(value,12572*1024)

    def test_unknown_live_task_missing_RSS_fails_closed(self):
        self.fixture();self.put('700/task/701/status',status(701,700,'S'))
        with self.assertRaises(ValueError):self.read()

    def test_duplicate_units_and_wrong_tgid_fail(self):
        mutations=[status(700,999,'Z'),status(700,700,'S',1)+'VmRSS: 2 kB\n',status(700,700,'S',1).replace('kB','MB')]
        for raw in mutations:
            self.put('700/status',raw)
            with self.subTest(raw=raw),self.assertRaises(ValueError):self.read()

    def test_wrong_live_task_tgid_or_group_fails(self):
        self.fixture();self.put('700/task/701/status',status(701,999,'S',12572))
        with self.assertRaises(ValueError):self.read()
        self.fixture();self.put('700/task/701/stat',stat(701,999,21,'S'))
        with self.assertRaises(ValueError):self.read()

    def test_status_and_task_inventory_caps(self):
        self.put('700/status','x'*8193)
        with self.assertRaises(ValueError):self.read()
        self.fixture(worker=False)
        for tid in range(701,765):(self.root/f'700/task/{tid}').mkdir()
        with self.assertRaises(ValueError):self.read()

    def test_task_birth_race_rejected(self):
        self.fixture();original=m._owned_task_identity;calls=0
        def changed(pid,tid):
            nonlocal calls
            value=original(pid,tid)
            if tid==701:
                calls+=1
                if calls==2:value=(value[0],value[1]+1,value[2])
            return value
        with mock.patch.object(m,'_owned_task_identity',side_effect=changed),self.assertRaises(ValueError):self.read()

    def test_task_inventory_change_rejected(self):
        self.fixture();original=m.owned_task_ids;calls=0
        def changed(pid):
            nonlocal calls
            calls+=1;value=original(pid);return value if calls==1 else value+[702]
        with mock.patch.object(m,'owned_task_ids',side_effect=changed),self.assertRaises(ValueError):self.read()

    def test_original_actual_S18_status_fixture(self):
        root=Path('/tmp/forge_sol_S18_rss_scope_v3_checkpoint_20261027/probe_runtime')
        leader=(root/'forge_sol_S18_actual_leader_original_20261027.status').read_text()
        worker=(root/'forge_sol_S18_actual_task_275333_original_20261027.status').read_text()
        def field(raw,key):return next(line.split(':',1)[1].strip() for line in raw.splitlines() if line.startswith(key+':'))
        self.pid=int(field(leader,'Pid'));tid=int(field(worker,'Pid'))
        self.put(f'{self.pid}/status',leader)
        self.put(f'{self.pid}/task/{self.pid}/status',leader);self.put(f'{self.pid}/task/{self.pid}/stat',stat(self.pid,self.pid))
        self.put(f'{self.pid}/task/{tid}/status',worker);self.put(f'{self.pid}/task/{tid}/stat',stat(tid,self.pid,21,'S'))
        value,g=self.read();self.assertEqual(value,12572*1024)


if __name__=='__main__':unittest.main(verbosity=2)
