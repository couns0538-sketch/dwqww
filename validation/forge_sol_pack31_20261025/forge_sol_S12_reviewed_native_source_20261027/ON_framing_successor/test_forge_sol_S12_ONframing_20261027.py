"""Pure source-framed synthetic controls, never engine/native evidence."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest

OLD=Path('/workspace/dwqww/releases/forge_sol_pack31_20261025/S25_v2/forge_sol_S25_outcontract_20261025.py')
HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def fixture(references=((11,308972),)):
    # Literal field order and emission order come from frozen v2 search.cpp
    # lines1631-1644 and uci.cpp421-423. Numbers are synthetic, not measured.
    raw=b'info string NnueLazyAcc active\n'
    for depth,nodes in references:
        for index in range(8):
            raw+=(f'info string NnueLazyAcc stats refreshes 1 updates {index+3} '
                'zero_dirty_edges 2 copies_avoided 2 alias_hits 1 evaluations 100\n').encode()
        raw+=f'info string bench depth {depth} nodes {nodes} time 1 nps {nodes*1000}\n'.encode()
    return raw


def receipt(raw,stderr=b''):
    return {'returncode':0,'stdout_complete':True,'stderr_complete':True,'close_protocol_valid':True,
        'reader_queues_cleared':True,'captures':{name:{'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()}
        for name,value in (('stdout',raw),('stderr',stderr))}}


class SourceFramedSyntheticControls(unittest.TestCase):
    def inspect(self,raw=None,stderr=b'',record=None,references=((11,308972),)):
        raw=fixture(references) if raw is None else raw
        api=load('s12_ON_contract_fixture',HERE/'forge_sol_S12_ONbench_contract_20261027.py')
        return api.inspect_ON_bench_sequence(raw,stderr,receipt(raw,stderr) if record is None else record,references)

    def test_required_ON_source_frame_must_pass(self):
        # RED mode reproduces the exact old call site without changing its file.
        if __import__('os').environ.get('FORGE_S12_REPRO_OLD')=='1':
            actual=load('s12_old_S25_repro',OLD).inspect_bench(fixture(),b'',0)
        else:actual=self.inspect()
        self.assertEqual(actual['status'],'PASS',actual)

    def test_normal_OFF_parser_remains_strict(self):
        actual=load('s12_unchanged_OFF_contract',OLD).inspect_bench(fixture(),b'',0)
        self.assertEqual(actual['status'],'FAIL')
        self.assertIn('bench_prefix_bytes',[x['code'] for x in actual['errors']])

    def test_bare_OFF_terminal_does_not_prove_ON(self):
        raw=fixture().splitlines(keepends=True)[-1]
        self.assertEqual(load('s12_OFF_control_fixture',OLD).inspect_bench(raw,b'',0)['status'],'PASS')
        self.assertEqual(self.inspect(raw)['status'],'FAIL')

    def test_successor_import_resolves_new_validator_and_frozen_dependencies(self):
        module=load('s12_minimal_successor_fixture',HERE/'forge_sol_S12_feature_qualify_successor_20261027.py')
        self.assertEqual(Path(module.ON_contract.__file__).resolve(),HERE/'forge_sol_S12_ONbench_contract_20261027.py')
        self.assertEqual(module.common.HERE,Path('/tmp/forge_sol_S12_native_prep_20261027'))
        self.assertEqual(module.ON_contract.inspect_ON_bench_sequence(fixture(),b'',receipt(fixture()),[(11,308972)])['status'],'PASS')

    def test_changed_parser_rejected_before_import(self):
        with tempfile.TemporaryDirectory(prefix='forge_s12_parser_pin_') as d:
            root=Path(d)
            runner=HERE/'forge_sol_S12_feature_qualify_successor_20261027.py'
            parser=HERE/'forge_sol_S12_ONbench_contract_20261027.py'
            (root/runner.name).write_bytes(runner.read_bytes())
            (root/parser.name).write_bytes(parser.read_bytes()+b'\n# mutation fixture\n')
            with self.assertRaisesRegex(RuntimeError,'changed before import'):
                load('s12_changed_parser_negative_fixture',root/runner.name)

    def test_foreign_module_path_rejected_even_with_same_source_bytes(self):
        with tempfile.TemporaryDirectory(prefix='forge_s12_parser_path_') as d:
            root=Path(d)
            runner=HERE/'forge_sol_S12_feature_qualify_successor_20261027.py'
            parser=HERE/'forge_sol_S12_ONbench_contract_20261027.py'
            (root/runner.name).write_bytes(runner.read_bytes())
            (root/parser.name).write_bytes(parser.read_bytes())
            with self.assertRaisesRegex(RuntimeError,'another source path'):
                load('s12_wrong_parser_path_negative_fixture',root/runner.name)

    def test_repeated_same_process_active_once(self):
        self.assertEqual(self.inspect(references=((11,308972),(11,308972)))['status'],'PASS')

    def test_all_five_fixed_depth_frames(self):
        refs=((11,308972),(13,745494),(16,2460422),(20,11901452),(22,31111774))
        self.assertEqual(self.inspect(references=refs)['status'],'PASS')

    def test_independent_reviewer_source_frame(self):
        path=HERE/'forge_sol_S12_reviewer_synthetic_ON_fixture_20261027.txt'
        raw=path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'4f8fef2134c2de96f3e990de8fbe0655ea96240ba9a41bc2a1500bb098bb2479')
        self.assertEqual(self.inspect(raw)['status'],'PASS')

    def test_unknown_prefix_is_not_stripped(self):
        self.assertEqual(self.inspect(b'info string alien\n'+fixture())['status'],'FAIL')

    def test_duplicate_active_rejected(self):
        self.assertEqual(self.inspect(b'info string NnueLazyAcc active\n'+fixture())['status'],'FAIL')

    def test_active_after_stats_rejected(self):
        lines=fixture().splitlines(keepends=True);lines[0],lines[1]=lines[1],lines[0]
        self.assertEqual(self.inspect(b''.join(lines))['status'],'FAIL')

    def test_missing_stats_rejected(self):
        lines=fixture().splitlines(keepends=True);del lines[3]
        self.assertEqual(self.inspect(b''.join(lines))['status'],'FAIL')

    def test_malformed_counter_order_rejected(self):
        self.assertEqual(self.inspect(fixture().replace(b'copies_avoided 2 alias_hits 1',b'alias_hits 1 copies_avoided 2',1))['status'],'FAIL')

    def test_uint64_overflow_rejected(self):
        self.assertEqual(self.inspect(fixture().replace(b'updates 3',b'updates 18446744073709551616',1))['status'],'FAIL')

    def test_wrong_node_reference_rejected(self):
        self.assertEqual(self.inspect(fixture().replace(b'nodes 308972',b'nodes 308973'))['status'],'FAIL')

    def test_duplicate_summary_rejected(self):
        self.assertEqual(self.inspect(fixture()+fixture().splitlines(keepends=True)[-1])['status'],'FAIL')

    def test_post_summary_bytes_and_blank_lines_rejected(self):
        for suffix in (b'junk',b'\n',b'info string NnueLazyAcc active\n'):
            self.assertEqual(self.inspect(fixture()+suffix)['status'],'FAIL')

    def test_missing_final_line_ending_rejected(self):
        self.assertEqual(self.inspect(fixture()[:-1])['status'],'FAIL')

    def test_incomplete_capture_rejected(self):
        row=receipt(fixture());row['stdout_complete']=False
        self.assertEqual(self.inspect(record=row)['status'],'FAIL')

    def test_boolean_exit_code_rejected(self):
        row=receipt(fixture());row['returncode']=False
        self.assertEqual(self.inspect(record=row)['status'],'FAIL')

    def test_missing_capture_records_rejected(self):
        row=receipt(fixture());row['captures']=None
        self.assertEqual(self.inspect(record=row)['status'],'FAIL')

    def test_open_close_protocol_rejected(self):
        row=receipt(fixture());row['close_protocol_valid']=False
        self.assertEqual(self.inspect(record=row)['status'],'FAIL')

    def test_replaced_raw_capture_rejected(self):
        row=receipt(fixture());row['captures']['stdout']['sha256']='0'*64
        self.assertEqual(self.inspect(record=row)['status'],'FAIL')

    def test_stderr_is_never_ignored(self):
        self.assertEqual(self.inspect(stderr=b'ERROR\n')['status'],'FAIL')

    def test_ON_counter_path_proof_required(self):
        raw=fixture().replace(b'zero_dirty_edges 2 copies_avoided 2',b'zero_dirty_edges 0 copies_avoided 0')
        self.assertEqual(self.inspect(raw)['status'],'FAIL')

    def test_terminal_source_formula_rejected(self):
        raw=fixture().replace(b'time 1 nps 308972000',b'time 1 nps 1')
        self.assertEqual(self.inspect(raw)['status'],'FAIL')


if __name__=='__main__':unittest.main(verbosity=2)
