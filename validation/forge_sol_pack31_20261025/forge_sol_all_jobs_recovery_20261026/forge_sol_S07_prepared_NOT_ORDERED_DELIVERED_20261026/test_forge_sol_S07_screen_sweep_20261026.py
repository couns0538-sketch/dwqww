#!/usr/bin/env python3
"""S07 tests: synthetic subprocesses only; no native chess engine execution."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
TOOL = HERE / 'forge_sol_S07_screen_sweep_20261026.py'
SOURCE = Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')
SUITE = Path('/workspace/forge-sol-next-20261024/int16-review/wac300.epd')

# The double is a deliberately synthetic process, never a chess-engine result.
FAKE = r'''
import json, os, signal, subprocess, sys, time
mode, trace = sys.argv[1:3]
opts = {}; incoming = []
def emit(line): print(line, flush=True)
if mode=='orphanbadfirst':
 child=subprocess.Popen([sys.executable,'-c','import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)'])
 open(trace+'.orphan.pid','w').write(str(child.pid))
for line in sys.stdin:
 c=line.strip(); incoming.append(c)
 with open(trace,'a') as f: f.write(json.dumps({'pid':os.getpid(),'command':c})+'\n')
 if c=='uci':
  emit('id name SYNTHETIC S07 TEST DOUBLE')
  for n in ['Threads','Hash','OwnBook','RefutLmr','RefutLmrMinR','RefutLmrPlies','Clear Hash']:
   if not (mode=='unadvertised' and n.startswith('Refut')): emit('option name '+n+' type string default 0')
  emit('uciok')
 elif c.startswith('setoption name '):
  name, _, value = c[15:].partition(' value '); opts[name]=value
  if name=='BadOption': emit('info string unknown option BadOption')
 elif c=='isready': emit('readyok')
 elif c.startswith('bench '):
  d=int(c.split()[1])
  if mode=='hang' and c=='bench 13':
   signal.signal(signal.SIGTERM, signal.SIG_IGN)
   while True: time.sleep(1)
  refs={11:308972,13:745494,16:2460422,20:11901452,22:31111774}
  n=refs[d]
  if opts.get('RefutLmr')=='4' and mode!='inert':
   n={11:308972,13:745494,16:2460426,20:10250343,22:24154132}[d]
  if mode in ('badfirst','orphanbadfirst') and len(incoming)==1: n=1
  emit('info string bench depth %d nodes %d time 1 nps %d'%(d,n,n*1000))
  if mode=='duplicate': emit('info string bench depth %d nodes 123 time 1 nps 123000'%d)
 elif c.startswith('go movetime '):
  if opts.get('OwnBook')!='false': sys.exit(12)
  emit('info depth 1 score cp 0 nodes 1 time 1 pv g3g6')
  emit('bestmove g3g6')
 elif c=='quit':
  if mode=='tailoverflow': emit('X'*1024)
  if mode=='deleteinput': os.unlink(sys.argv[0])
  if mode=='exit7': sys.exit(7)
  break
'''

def module():
    if not TOOL.exists():
        raise AssertionError('S07 implementation missing')
    spec = importlib.util.spec_from_file_location('s07', TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

class AnalysisTests(unittest.TestCase):
    def test_guard_checks_reductions_and_exact_twenty_percent_boundary(self):
        m = module()
        base = {11:100,13:100,16:100,20:100,22:100}
        self.assertEqual(m.compare_nodes(base, {**base,20:80,22:120})['guard_status'], 'PASS')
        self.assertEqual(m.compare_nodes(base, {**base,20:79})['guard_status'], 'FAIL')
        self.assertEqual(m.compare_nodes(base, {**base,22:121})['guard_status'], 'FAIL')

    def test_precheck_uses_first_changed_depth_not_hardcoded_d11(self):
        m = module()
        r = m.compare_nodes(m.FIXED_REFS, {11:308972,13:745494,16:2460426,20:10250343,22:24154132})
        self.assertEqual(r['pc_precheck'], {'depth':16,'off_nodes':2460422,'on_nodes':2460426})
        self.assertEqual(r['guard_status'], 'FAIL')
        self.assertIsNone(m.compare_nodes(m.FIXED_REFS,m.FIXED_REFS)['pc_precheck'])

    def test_incomplete_or_zero_depth_series_is_not_pass(self):
        m = module()
        for row in ({11:1}, {**m.FIXED_REFS,22:0}):
            with self.assertRaises(ValueError): m.compare_nodes(m.FIXED_REFS,row)

    def test_actual_supplied_artifact_and_document_table_import(self):
        m = module(); r = m.import_p23b(SOURCE)
        self.assertEqual(r['artifact_series']['REL_RefutLmr=1']['22'],22307140)
        self.assertEqual(r['artifact_series']['LOCK']['16'],2460422)
        self.assertEqual(len(r['settings']),12)
        self.assertEqual(r['settings']['m1 r4']['guard_status'],'FAIL')
        self.assertEqual(r['settings']['m4 r6']['pc_precheck']['depth'],16)
        self.assertEqual(r['settings']['m1 r5']['guard_status'],'FAIL')
        self.assertEqual(r['evidence_kind'],'SUPPLIED_ARTIFACT_IMPORT_NO_RERUN')
        self.assertIn('historical_label',r['settings']['m1 r4'])

    def test_bench_summary_rejects_wrong_depth_duplicate_or_malformed(self):
        m = module()
        row='info string bench depth 11 nodes 308972 time 1 nps 308972000'
        self.assertEqual(m.parse_bench([row],11),308972)
        for rows,depth in [([row],13),([row,row],11),([row.replace('nodes 308972','nodes 0')],11),(['garbage'],11)]:
            with self.assertRaises(ValueError): m.parse_bench(rows,depth)

    def test_option_commands_reject_core_override_and_injection(self):
        m=module()
        for options in ({'OwnBook':True},{'RefutLmr':'1\nquit'},{'RefutLmr value 3':1},{'X':[]}):
            with self.assertRaises(ValueError): m.option_commands(options)
        self.assertEqual(m.option_commands({'RefutLmr':0})[-1],'setoption name RefutLmr value 0')

class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='s07_synthetic_',dir=HERE)
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.fake=self.root/'synthetic_uci.py'; self.fake.write_text(FAKE)
        self.trace=self.root/'trace.jsonl'
    def run_tool(self, mode='normal', extra=None):
        argv=[sys.executable,'-B',str(self.fake),mode,str(self.trace)]
        timeout='0.3' if mode=='hang' else '2'
        cmd=[sys.executable,'-B',str(TOOL),'sweep','--engine-argv-json',json.dumps(argv),'--out',str(self.root/'output'),'--timeout',timeout]
        return subprocess.run(cmd+(extra or []),capture_output=True,text=True,timeout=30)
    def result(self): return json.loads((self.root/'output'/'result.json').read_text())

    def test_actual_subprocess_first_bare_bench_and_explicit_off_on(self):
        p=self.run_tool(extra=['--off-options-json','{"RefutLmr":0}','--on-options-json','{"RefutLmr":4,"RefutLmrMinR":6}'])
        self.assertEqual(p.returncode,1,p.stderr) # current absolute node guard catches -22.4%
        r=self.result(); self.assertEqual(r['comparison']['pc_precheck']['depth'],16)
        rows=[json.loads(x) for x in self.trace.read_text().splitlines()]
        first=rows[0]['pid']; self.assertEqual([x['command'] for x in rows if x['pid']==first],['bench 11','quit'])
        for receipt in r['processes'][1:]:
            stdin=(self.root/'output'/receipt['stdin']['path']).read_text()
            self.assertIn('setoption name OwnBook value false\n',stdin)
            self.assertIn('setoption name RefutLmr value ',stdin)
            self.assertTrue(receipt['child_waited']); self.assertTrue(receipt['capture_complete'])
            self.assertEqual(receipt['returncode'],0)
        self.assertEqual(r['off_nodes']['22'],31111774)

    def test_lock_fixed_reference_control_passes_with_no_on_options(self):
        p=self.run_tool(); self.assertEqual(p.returncode,0,p.stderr)
        r=self.result(); self.assertEqual(r['reference_status'],'PASS')
        self.assertEqual(r['status'],'PASS'); self.assertIsNone(r['comparison']['pc_precheck'])

    def test_bad_initial_signature_prevents_all_uci(self):
        p=self.run_tool('badfirst'); self.assertEqual(p.returncode,1,p.stderr)
        self.assertEqual(len(self.result()['processes']),1)
        self.assertNotIn('uci',[json.loads(x)['command'] for x in self.trace.read_text().splitlines()])

    def test_timeout_is_fail_and_ignoring_child_is_reaped(self):
        p=self.run_tool('hang'); self.assertEqual(p.returncode,1,p.stderr)
        r=self.result(); self.assertEqual(r['status'],'FAIL')
        timed=[x for x in r['processes'] if x['timed_out']]; self.assertEqual(len(timed),1)
        self.assertTrue(timed[0]['child_waited']); self.assertEqual(timed[0]['cleanup'],'kill')
        with self.assertRaises(ProcessLookupError): os.kill(timed[0]['pid'],0)

    def test_nonzero_exit_is_not_pass(self):
        p=self.run_tool('exit7'); self.assertEqual(p.returncode,1,p.stderr)
        self.assertEqual(self.result()['processes'][0]['returncode'],7)
        self.assertEqual(len(self.result()['processes']),1)

    def test_duplicate_summary_after_expected_reply_is_not_pass(self):
        p=self.run_tool('duplicate'); self.assertEqual(p.returncode,1,p.stderr)
        self.assertEqual(self.result()['status'],'FAIL')
        self.assertEqual(len(self.result()['processes']),1)

    def test_normally_exited_parent_does_not_leave_pipe_holding_child(self):
        p=self.run_tool('orphanbadfirst'); self.assertEqual(p.returncode,1,p.stderr)
        pid=int(Path(str(self.trace)+'.orphan.pid').read_text())
        stat=Path('/proc/%d/stat'%pid)
        alive=stat.exists() and stat.read_text().split()[2]!='Z'
        if alive: os.kill(pid,9) # prevent a broken implementation leaking this fixture
        self.assertFalse(alive,'descendant survived tool process cleanup')

    def test_silent_unknown_option_rejected_even_when_other_option_is_live(self):
        p=self.run_tool(extra=['--on-options-json','{"RefutLmr":4,"RefutLmrTypo":6}'])
        self.assertEqual(p.returncode,1,p.stderr)
        self.assertIn('not advertised',self.result()['failure'])

    def test_capture_overflow_after_final_reply_is_fail(self):
        m=module(); out=self.root/'capture'; out.mkdir()
        cap=m.Capture(out,[sys.executable,'-B',str(self.fake),'tailoverflow',str(self.trace)],0.3,max_output_bytes=128)
        def operation(send,until):
            send('bench 11'); return until(lambda line:line.startswith('info string bench'))
        _,receipt=cap.exchange('overflow',operation)
        self.assertEqual(receipt['status'],'FAIL'); self.assertTrue(receipt['output_truncated'])

    def test_deleted_input_still_has_failed_result_and_receipts(self):
        p=self.run_tool('deleteinput'); self.assertEqual(p.returncode,1,p.stderr)
        r=self.result(); self.assertEqual(r['status'],'FAIL')
        self.assertIn('input',r['failure'])

    def test_unknown_option_diagnostic_is_fail(self):
        p=self.run_tool(extra=['--on-options-json','{"BadOption":1}'])
        self.assertEqual(p.returncode,1,p.stderr); self.assertEqual(self.result()['status'],'FAIL')

    def test_inert_advertised_on_option_does_not_pass_live_check(self):
        p=self.run_tool('inert',extra=['--on-options-json','{"RefutLmr":4}'])
        self.assertEqual(p.returncode,1,p.stderr)
        self.assertIn('inert',self.result()['failure'])

    def test_explicit_release_tunable_allowlist_is_recorded_as_caller_declaration(self):
        p=self.run_tool('unadvertised',extra=['--on-options-json','{"RefutLmr":4}','--allow-unadvertised-options-json','["RefutLmr"]'])
        self.assertEqual(p.returncode,1,p.stderr) # node guard fails; option configuration succeeded
        r=self.result(); self.assertEqual(r['comparison']['pc_precheck']['depth'],16)
        self.assertEqual(r['caller_allowed_unadvertised_options'],['RefutLmr'])

    def test_process_raw_receipt_hashes_match_saved_bytes(self):
        import hashlib
        p=self.run_tool('badfirst'); self.assertEqual(p.returncode,1,p.stderr)
        for receipt in self.result()['processes']:
            for stream in ('stdin','stdout','stderr'):
                record=receipt[stream]; data=(self.root/'output'/record['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(),record['sha256'])
                self.assertEqual(len(data),record['bytes'])

    def test_existing_output_is_rejected_without_replacing_it(self):
        out=self.root/'output'; out.mkdir(); (out/'keep').write_text('kept')
        p=self.run_tool(); self.assertNotEqual(p.returncode,0)
        self.assertEqual((out/'keep').read_text(),'kept'); self.assertFalse(self.trace.exists())

    def test_wac_subprocess_preserves_all_rows_and_illegal_exceptions(self):
        argv=[sys.executable,'-B',str(self.fake),'normal',str(self.trace)]
        p=subprocess.run([sys.executable,'-B',str(TOOL),'wac300','--engine-argv-json',json.dumps(argv),'--suite',str(SUITE),'--movetime-ms','1','--out',str(self.root/'output'),'--timeout','0.5'],capture_output=True,text=True,timeout=12)
        self.assertEqual(p.returncode,1,p.stderr)
        r=self.result(); self.assertEqual(r['evaluated'],300)
        self.assertGreater(r['illegal_moves'],0); self.assertEqual(r['suite']['positions'],300)
        self.assertEqual(len(r['processes']),2)
        self.assertTrue(all('bestmove_allowed' in x for x in r['results']))
        self.assertTrue(all(x['child_waited'] for x in r['processes']))

class WacTests(unittest.TestCase):
    def test_actual_corpus_hash_count_and_accepted_move_sets(self):
        m=module(); rows,proof=m.load_wac(SUITE)
        self.assertEqual(proof['sha256'],'9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46')
        self.assertEqual(proof['positions'],300); self.assertEqual(proof['multiple_bm_positions'],37)
        row=next(r for r in rows if r['id']=='WAC.274')
        for move in ('g6g5','g6b6'): self.assertTrue(m.score_bestmove(row,move)['bestmove_allowed'])
        self.assertFalse(m.score_bestmove(row,'g6d6')['bestmove_allowed'])
        self.assertFalse(m.score_bestmove(row,'a1a8')['legal'])
        self.assertTrue(m.score_bestmove(row,'not_a_move')['exception'])

    def test_truncated_suite_rejected_before_engine(self):
        m=module()
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            p=Path(d)/'truncated.epd'; p.write_text(SUITE.read_text().splitlines()[0]+'\n')
            with self.assertRaises(ValueError): m.load_wac(p)

if __name__=='__main__': unittest.main()
