"""Qualification cannot be inferred from counters without per-test outcomes."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import pack_scoped

def suite_fixture():
    nodes=[f'astra_r8/datafilter/tests/test_fixture.py::test_{i}' for i in range(564)]
    nodes+=['tests/test_fixture.py::test_case[KK]','tests/test_fixture.py::test_case[kk]']
    receipt=dict(exit_code=0,stop_reason=None,priority='Idle',threads=1)
    results=dict(exitstatus=0,failed=0,collected=len(nodes),results=[dict(nodeid=node,when='call',outcome='passed',kind='test') for node in nodes])
    collection=dict(count=len(nodes),nodeids=nodes)
    return receipt,results,collection

class QualificationTests(unittest.TestCase):
    def test_complete_case_sensitive_collection(self):
        receipt,results,collection=suite_fixture()
        self.assertEqual(pack_scoped.validate_suite(receipt,results,collection),566)

    def test_counter_success_cannot_hide_omitted_or_skipped_tests(self):
        for corruption in ('omitted','skipped','empty','duplicate','bool_exit','bool_failed','node_count','subtest_only'):
            with self.subTest(corruption=corruption):
                receipt,results,collection=suite_fixture()
                if corruption=='omitted': results['results'].pop()
                if corruption=='skipped': results['results'][0]['outcome']='skipped'
                if corruption=='empty': results['results']=[]
                if corruption=='duplicate': results['results'].append(copy.deepcopy(results['results'][0]))
                if corruption=='bool_exit': receipt['exit_code']=False
                if corruption=='bool_failed': results['failed']=False
                if corruption=='node_count': collection['nodeids'].pop()
                if corruption=='subtest_only': results['results'][0]['kind']='subtest'
                with self.assertRaises(ValueError):
                    pack_scoped.validate_suite(receipt,results,collection)

    def test_subtests_are_additional_evidence(self):
        receipt,results,collection=suite_fixture()
        subtest=copy.deepcopy(results['results'][0])
        subtest['kind']='subtest'
        results['results'].append(subtest)
        self.assertEqual(pack_scoped.validate_suite(receipt,results,collection),566)
        subtest['outcome']='failed'
        with self.assertRaises(ValueError):
            pack_scoped.validate_suite(receipt,results,collection)

if __name__=='__main__':
    unittest.main()
