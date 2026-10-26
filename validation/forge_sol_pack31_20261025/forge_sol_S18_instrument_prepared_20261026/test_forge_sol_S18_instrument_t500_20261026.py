"""Pure, bounded fixtures only: no data child, live /proc reads or Torch."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('s18_instrument',HERE/'forge_sol_S18_instrument_t500_20261026.py')
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)

class PureTests(unittest.TestCase):
    def test_stat_comm_parentheses_fields_and_identity(self):
        tail=['S','7','44','0','0','0','0','0','0','0','0','123','45','0','0','0','0','3','0','999']+['0']*30
        row=m.parse_stat('44 (name (with) space) '+' '.join(tail),44)
        self.assertEqual((row['utime_ticks'],row['stime_ticks'],row['start_ticks'],row['pgrp']),(123,45,999,44))
        self.assertEqual(row['threads'],3)
        with self.assertRaises(ValueError):m.parse_stat('44 (x) '+' '.join(tail),45)
    def test_stat_malformed(self):
        for s in ['','a (x) S','44 (x) S 7','44 no closing paren']:
            with self.assertRaises(ValueError):m.parse_stat(s,44)
    def test_schedstat(self):
        self.assertEqual(m.parse_schedstat('123 456 7\n'),{'runtime_ns':123,'runqueue_ns':456,'timeslices':7})
        for s in ['1 2','1 a 3','-1 2 3','1 2 3 4']:
            with self.assertRaises(ValueError):m.parse_schedstat(s)
    def test_integer_map(self):
        self.assertEqual(m.parse_integer_map('rchar: 12\nwchar: 30\n'),{'rchar':12,'wchar':30})
        self.assertEqual(m.parse_integer_map('usage_usec 90\nnr_throttled 3\n',colon=False),{'usage_usec':90,'nr_throttled':3})
        for s in ['rchar: bad','rchar: -1','rchar: 1\nrchar: 2']:
            with self.assertRaises(ValueError):m.parse_integer_map(s)
    def test_pressure(self):
        r=m.parse_pressure('some avg10=0.00 avg60=1.25 avg300=2.50 total=123\n')
        self.assertEqual(r['some']['total'],123)
        for s in ['some nonsense','some avg10=nan','some total=-1','weird total=1']:
            with self.assertRaises(ValueError):m.parse_pressure(s)
    def test_unavailable_and_truncated_are_not_zero(self):
        r=m.observe_text('/not/used',reader=lambda _: (_ for _ in ()).throw(PermissionError('fixture')))
        self.assertFalse(r['available']);self.assertIn('PermissionError',r['error'])
        r=m.observe_text('/not/used',reader=lambda _: 'x'*5000)
        self.assertFalse(r['available']);self.assertIn('limit',r['error'])
    def test_bounded_capture_retains_prefix_and_flags(self):
        f=io.BytesIO();c=m.BoundedCapture(f,5)
        c.write(b'abc');c.write(b'defgh')
        self.assertEqual(f.getvalue(),b'abcde');self.assertTrue(c.truncated)
        self.assertEqual((c.seen,c.written),(8,5))
    def test_bounded_telemetry(self):
        f=io.BytesIO();c=m.BoundedCapture(f,5)
        self.assertFalse(m.emit_json(c,{'large':'x'*40}));self.assertTrue(c.truncated)
    def test_tree_stats_no_follow_bounded(self):
        with tempfile.TemporaryDirectory(prefix='s18_pure_') as t:
            p=Path(t);(p/'x').write_bytes(b'ab');(p/'y').write_bytes(b'c');(p/'link').symlink_to('/proc')
            r=m.tree_sizes(p,max_entries=2)
            self.assertTrue(r['truncated']);self.assertEqual(len(r['entries']),2)
            r=m.tree_sizes(p,max_entries=8)
            self.assertTrue(any(x['kind']=='symlink' for x in r['entries']))
            self.assertEqual(sum(x.get('bytes',0) for x in r['entries'] if x['kind']=='file'),3)
    def test_output_guard(self):
        with tempfile.TemporaryDirectory(prefix='s18_pure_') as t:
            p=Path(t)
            self.assertEqual(m.guard_new_output(p/'new',blocked=[]),p/'new')
            for bad in [p,p/'..'/'escape',p/'locks'/'new',p/'baseline'/'new',p/'.git'/'new']:
                with self.assertRaises(ValueError):m.guard_new_output(bad,blocked=[])
            (p/'sym').symlink_to(p,target_is_directory=True)
            with self.assertRaises(ValueError):m.guard_new_output(p/'sym'/'new',blocked=[])
            with self.assertRaises(ValueError):m.guard_new_output(p/'forbidden'/'new',blocked=[p/'forbidden'])
    def test_fixed_argv(self):
        pins={'sample':'/tmp/sample','python':'/python','train_names':['t0.pos','t1.pos'],'holdout':'h000.pos','seed':20261025,'threshold':500}
        args=m.child_argv(pins,Path('/tmp/new'),Path('/tmp/own/tool.py'))
        self.assertEqual(args[args.index('--seed')+1],'20261025')
        self.assertEqual(args[args.index('--disagreement-threshold')+1],'500')
        self.assertEqual(args[args.index('--out')+1],'/tmp/new/sealed')
        self.assertEqual(args[args.index('--work-dir')+1],'/tmp/new/scratch')
    def test_describe_never_spawns_or_creates(self):
        with mock.patch.object(m.subprocess,'Popen',side_effect=AssertionError('must not spawn')),mock.patch('builtins.print'):
            self.assertEqual(m.main(['--describe']),0)
    def test_execute_requires_window_reference(self):
        with mock.patch.object(m.subprocess,'Popen',side_effect=AssertionError('must not spawn')):
            with self.assertRaises(SystemExit):m.main(['--execute','--out','/tmp/new_never_created'])
    def test_no_acceptance_status(self):
        for cause,rc in [('exited',0),('exited',1),('deadline',-9),('observer_error',None)]:
            r=m.diagnostic_result(cause,rc)
            self.assertFalse(r['acceptance']);self.assertNotIn('PASS',r['status'])
            self.assertEqual(r['previous_failure_status'],'FAIL_UNCHANGED')
    def test_child_identity_unavailable_is_explicit(self):
        with mock.patch.object(m,'observe_text',return_value={'available':False,'error':'fixture'}):
            r=m.sample_child(44,999)
        self.assertFalse(r['identity_verified']);self.assertFalse(r['stat']['available'])
    def test_identity_mismatch_disables_other_proc_reads(self):
        fake={'available':True,'raw':'x','value':{'start_ticks':1000,'pgrp':44}}
        with mock.patch.object(m,'observe_text',return_value=fake) as rd:
            r=m.sample_child(44,999)
        self.assertFalse(r['identity_verified']);self.assertEqual(rd.call_count,1)
    def test_tree_errors_are_entry_bounded(self):
        class Entry:
            def stat(self,**kwargs):raise PermissionError('fixture')
        class Directory:
            def __enter__(self):return iter([Entry()]*100)
            def __exit__(self,*a):pass
        with mock.patch.object(m.os,'scandir',return_value=Directory()),mock.patch.object(Path,'exists',return_value=True):
            r=m.tree_sizes('/tmp/not_used',max_entries=3)
        self.assertEqual(r['visited_entries'],3);self.assertEqual(len(r['errors']),3);self.assertTrue(r['truncated'])
    def test_cgroup_unavailable_is_not_empty_success(self):
        with mock.patch.object(m,'observe_text',return_value={'available':False,'error':'denied'}):
            r=m.cgroup_observation()
        self.assertFalse(r['membership']['available']);self.assertNotIn('cpu.stat',r)
    def test_cgroup_parent_escape_not_opened(self):
        with mock.patch.object(m,'observe_text',return_value={'available':True,'raw':'0::/../../outside\n'}) as reader:
            r=m.cgroup_observation()
        self.assertFalse(r['available']);self.assertEqual(reader.call_count,1)
    def test_plain_child_sample_records_own_fields(self):
        rows=[{'available':True,'value':{'start_ticks':999,'pgrp':44}},
              {'available':False,'error':'schedstat denied'}, {'available':True,'raw':'0'},
              {'available':True,'value':{'rchar':4}}, {'available':True,'raw':'VmRSS: 100 kB\n'}]
        with mock.patch.object(m,'observe_text',side_effect=rows) as reader:r=m.sample_child(44,999)
        self.assertTrue(r['identity_verified']);self.assertEqual(reader.call_count,5)
        self.assertFalse(r['schedstat']['available']);self.assertEqual(r['io']['value']['rchar'],4)
    def test_pins_and_dependencies_are_exact(self):
        p=m.load_pins()
        self.assertEqual((p['seed'],p['threshold'],p['maximum_seconds']),(20261025,500,120))
        for name,h in p['filter_source'].items():self.assertEqual(m.sha(HERE/name),h)
        self.assertEqual(m.sha(HERE/p['cleanup_helper']),p['cleanup_helper_sha256'])

if __name__=='__main__':unittest.main()
