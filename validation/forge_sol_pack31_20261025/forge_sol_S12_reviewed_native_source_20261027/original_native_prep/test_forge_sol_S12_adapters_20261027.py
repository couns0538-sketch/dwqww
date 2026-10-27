"""Pure negative controls for source-prepared S12 adapters; no native launch."""
from pathlib import Path
import copy
import unittest
import forge_sol_S12_alias_run_20261027 as alias
import forge_sol_S12_feature_qualify_20261027 as feature
import forge_sol_S12_helpers_build_20261027 as build
import forge_sol_S12_helpers_run_20261027 as run
import forge_sol_S12_qualify_native_20261027 as qual


class SyntheticAdapterFixtures(unittest.TestCase):
    def first(self):
        return dict(schema='forge.S12.first_runtime.v1',status='PASS',profile='Release',build_receipt_sha256='build',
            engine_sha256='engine',commands_sent=['bench 11','quit'],no_UCI_before_bench=True,bench_nodes=308972,
            returncode=0,source_unchanged=True,all_artifacts_unchanged=True,all_engine_groups_closed=True)

    def test_exact_first_fixture_accepts(self): qual.verify_first(self.first(),'build','engine','Release')

    def test_first_rejects_UCI_before_bench(self):
        row=self.first();row['commands_sent']=['uci','bench 11','quit']
        with self.assertRaisesRegex(ValueError,'FIRST'):qual.verify_first(row,'build','engine','Release')

    def test_first_rejects_boolean_returncode(self):
        row=self.first();row['returncode']=False
        with self.assertRaisesRegex(ValueError,'FIRST'):qual.verify_first(row,'build','engine','Release')

    def test_first_rejects_replaced_engine(self):
        with self.assertRaisesRegex(ValueError,'FIRST'):qual.verify_first(self.first(),'build','foreign','Release')

    def test_link_map_requires_real_Worker_and_NNUE(self):
        core=Path('/tmp/fixture/libforge_core.a')
        text=f'{core}(search.cpp.o)\n{core}(nnue.cpp.o)\nLOAD {core}\n'
        self.assertTrue(build.verify_link_map(text,core)['actual_Worker_from_core'])
        with self.assertRaisesRegex(ValueError,'Worker'):build.verify_link_map(text.replace('(search.cpp.o)','(board.cpp.o)'),core)

    def test_link_map_rejects_foreign_core(self):
        core=Path('/tmp/fixture/libforge_core.a')
        text=f'{core}(search.cpp.o)\n{core}(nnue.cpp.o)\nLOAD {core}\nLOAD /tmp/foreign/libforge_core.a\n'
        with self.assertRaisesRegex(ValueError,'ambiguous'):build.verify_link_map(text,core)

    def test_zero_regression_failures_do_not_make_base_RED(self):
        text=''.join('PASS synthetic fixture '+str(i)+'\n' for i in range(120))+'CHECKS 120 FAILURES 0\n'
        with self.assertRaisesRegex(ValueError,'baseline RED'):run.regression(text,b'',0,True)
        self.assertEqual(run.regression(text,b'',0,False)['status'],'PASS_ACTUAL_WORKER_REGRESSION')

    def test_regression_never_waives_actual_float_parity_failure(self):
        text=''.join('PASS synthetic fixture '+str(i)+'\n' for i in range(120))
        text+='FAIL null all actual float words equal fresh refresh\nCHECKS 121 FAILURES 1\n'
        with self.assertRaisesRegex(ValueError,'baseline RED'):run.regression(text,b'',1,True)

    def test_regression_rejects_sanitizer_stderr(self):
        with self.assertRaisesRegex(ValueError,'stderr'):run.regression('CHECKS 0 FAILURES 0\n',b'ERROR: AddressSanitizer',1,False)

    def test_parity_rejects_baseline_vs_itself(self):
        left=dict(base='B',profile='Release',role='baseline',feature='OFF',core_sha256='same',source='/same')
        right=dict(left,role='candidate',feature='ON')
        with self.assertRaisesRegex(ValueError,'itself'):alias.require_pair(left,right)

    def test_candidate_OFF_is_not_ON_alias_proof(self):
        left=dict(base='B',profile='Release',role='baseline',feature='OFF',core_sha256='left',source='/left')
        right=dict(left,role='candidate',core_sha256='right',source='/right')
        with self.assertRaisesRegex(ValueError,'feature-capable'):alias.require_pair(left,right)

    def test_actual_counter_accounting_rejects_missing_update(self):
        off=dict(positions=8192,selected_nulls=8000,legal_children=2000,nulls=11000,verified_evaluations=20000,
            fresh_mismatches=0,state_mismatches=0,refreshes=0,zero_dirty_edges=11000,evaluations=20000,updates=13000)
        on=dict(off,updates=2000,copies_avoided=11000)
        self.assertEqual(alias.summary_pair(off,on)['status'],'PASS_MEASURED_ALIAS_ACCOUNTING')
        on['updates']+=1
        with self.assertRaisesRegex(ValueError,'accounting'):alias.summary_pair(off,on)

    def test_independent_legality_checks_ponder_after_bestmove(self):
        self.assertEqual(feature.legal_terminal(['bestmove e2e4 ponder e7e5'])['ponder'],'e7e5')
        with self.assertRaisesRegex(ValueError,'ponder'):feature.legal_terminal(['bestmove e2e4 ponder e2e4'])

    def test_independent_legality_rejects_illegal_bestmove(self):
        with self.assertRaisesRegex(ValueError,'bestmove'):feature.legal_terminal(['bestmove e2e5'])


if __name__=='__main__':unittest.main(verbosity=2)
