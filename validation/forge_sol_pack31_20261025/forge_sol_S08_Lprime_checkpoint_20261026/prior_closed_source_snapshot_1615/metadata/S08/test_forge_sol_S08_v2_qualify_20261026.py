"""Pure qualification-gate/packet tests; no native process execution."""
import importlib.util
from pathlib import Path
import unittest
MODULE=Path(__file__).with_name('forge_sol_S08_v2_qualify_20261026.py')
class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),'qualification controller missing')
        spec=importlib.util.spec_from_file_location('s08qualify',MODULE);self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)
    def test_first_runtime_gate_requires_matching_success_and_pre_UCI_bare_pin(self):
        row={'label':'Release','pass':True,'returncode':0,'bench_counts':[308972],'binary_sha256_before':self.api.ELF_SHA,'binary_sha256_after':self.api.ELF_SHA,'first_runtime_bare_bench':True,'no_uci_before_bench':True,'stderr_sha256':self.api.EMPTY_SHA}
        self.api.verify_first({'status':'PASS','results':[row]})
        for key,value in [('binary_sha256_after','changed'),('returncode',1),('no_uci_before_bench',False),('bench_counts',[1])]:
            with self.subTest(key=key),self.assertRaises(ValueError):self.api.verify_first({'status':'PASS','results':[dict(row,**{key:value})]})
    def test_ctest_all15_and_exact_four_known_source_cases(self):
        text='\n'.join('1: '+line for line in self.api.KNOWN)+'\n100% tests passed, 0 tests failed out of 15\n'
        self.api.verify_ctest(text,0)
        for bad in [text.replace('out of 15','out of 14'),text+'\n1: FAIL: unexpected\n',text.replace('got 661','got 620')]:
            with self.assertRaises(ValueError):self.api.verify_ctest(bad,0)
    def test_promotion_known_finding_obeys_source_bound_not_invented_exact_score(self):
        text='\n'.join('1: '+line for line in self.api.KNOWN)+'\n100% tests passed, 0 tests failed out of 15\n'
        text=text.replace('score 607 at d1','score 642 at d1')
        self.api.verify_ctest(text,0)
        for bad in (text.replace('score 642 at d1','score 100 at d1'),text.replace('got c6d7','got c6e7'),text.replace('score 642 at d1','score 642 at d2')):
            with self.assertRaises(ValueError):self.api.verify_ctest(bad,0)
    def test_profile_disabled_rejects_any_packet_and_startpos_move_is_legal(self):
        self.api.verify_search(['bestmove e2e4'],False)
        with self.assertRaises(ValueError):self.api.verify_search(['info string prof schema 1','bestmove e2e4'],False)
        with self.assertRaises(ValueError):self.api.verify_search(['bestmove e2e5'],False)

class TailFenceTests(unittest.TestCase):
    def test_delayed_disabled_case_output_is_rejected_before_T2(self):
        from unittest.mock import patch
        import collections
        spec=importlib.util.spec_from_file_location('s08qualify_tail',MODULE);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
        counts={name:0 for name in api.collector.COUNTERS};counts['nodes']=10;counts['main_nodes']=10
        packet=['info string prof schema 1 scope search_only setup_excluded 1 overflow 0']
        for name,den in api.collector.COUNTERS.items():
            opp=counts[den];pct=str(100*counts[name]/opp) if opp else 'unknown'
            packet.append(f'info string prof {name} count {counts[name]} denominator {den} opportunities {opp} pct {pct}')
        packet.append('bestmove e2e4')
        class Transport:
            def __init__(self,*args):self.queue=collections.deque();self.profile=False;self.infinite=False;self.goes=0
            def send(self,command):
                if command=='uci':self.queue.append('uciok')
                elif command=='isready':self.queue.append('readyok')
                elif command.startswith('setoption name Profile value '):
                    if self.infinite:self.queue.extend(packet);self.infinite=False
                    self.profile=command.endswith('true')
                elif command=='go infinite':self.goes+=1;self.infinite=True;self.queue.append('info depth 1 nodes 10')
                elif command.startswith('go nodes '):
                    self.goes+=1;self.queue.extend(packet if self.profile else ['bestmove e2e4'])
                    if self.goes==5:self.queue.append('info depth 99 unexpected delayed disabled output')
            def until(self,predicate):
                consumed=[]
                while self.queue:
                    line=self.queue.popleft();consumed.append(line)
                    if predicate(line):return consumed
                raise AssertionError('fixture exhausted protocol replies')
            def close(self,successful):pass
        with patch.object(api,'Process',Transport):
            with self.assertRaisesRegex(ValueError,'late.*disabled|late.*toggle'):
                api.lifecycle(Path('/unused'),Path('/unused'),None,[])

if __name__=='__main__':unittest.main(verbosity=2)
