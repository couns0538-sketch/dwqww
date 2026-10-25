#!/usr/bin/env python3
"""Transport, preflight, isolation and oracle tests; no engine build or match."""
from __future__ import annotations
import argparse
import base64
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('--fixture-tree', required=True)
parser.add_argument('--fixture-net', required=True)
parser.add_argument('--pin-helper', required=True)
args, rest = parser.parse_known_args()
sys.argv = [sys.argv[0]] + rest
HERE = Path(__file__).resolve().parent
TOOL = HERE / 'forge_sol_S28_lock_transition_20261025.py'
spec = importlib.util.spec_from_file_location('s28_kit', TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class KitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='forge_sol_S28_tests_', dir=HERE)
        self.root = Path(self.temp.name)
        self.out = self.root / 'forge_sol_S28_new_20261025'
        self.cli = [sys.executable, '-B', str(TOOL), '--tree', args.fixture_tree,
                    '--net', args.fixture_net, '--pin-helper', args.pin_helper, '--out', str(self.out)]

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, extra=()):
        return subprocess.run(self.cli + list(extra), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), check=False)

    def test_default_dryrun_is_new_small_output_only(self):
        before = m.snapshot(m.input_files(Path(args.fixture_tree)) + [Path(args.fixture_net)])
        p = self.invoke()
        self.assertEqual(p.returncode, 0, p.stderr)
        reply = json.loads(p.stdout)
        self.assertEqual(reply['status'], 'DRY_RUN')
        result = json.loads((self.out / 'forge_sol_S28_results_20261025.json').read_text())
        self.assertTrue(result['input_immutability']['equal'])
        self.assertEqual(result['stages'], [])
        self.assertEqual(before, m.snapshot(m.input_files(Path(args.fixture_tree)) + [Path(args.fixture_net)]))
        self.assertEqual(len(list(self.out.iterdir())), 3)
        self.assertFalse(any(p.is_dir() for p in self.out.iterdir()))
        self.assertEqual(subprocess.run(['sha256sum', '-c', 'forge_sol_S28_SHA256SUMS_20261025.txt'],
                                       cwd=self.out, capture_output=True).returncode, 0)

    def test_existing_output_unchanged(self):
        self.out.mkdir()
        token = self.out / 'forge_sol_S28_marker_20261025.txt'
        token.write_bytes(b'unchanged')
        p = self.invoke()
        self.assertEqual(p.returncode, 2)
        self.assertEqual(list(self.out.iterdir()), [token])
        self.assertEqual(token.read_bytes(), b'unchanged')

    def test_dangling_output_symlink_rejected(self):
        self.out.symlink_to(self.root / 'missing')
        self.assertEqual(self.invoke().returncode, 2)
        self.assertTrue(self.out.is_symlink())

    def test_output_parent_symlink_rejected(self):
        link = self.root / 'link'
        link.symlink_to(self.root, target_is_directory=True)
        i = self.cli.index('--out') + 1
        self.cli[i] = str(link / 'forge_sol_S28_collision_20261025')
        self.assertEqual(self.invoke().returncode, 2)
        self.assertFalse((self.root / 'forge_sol_S28_collision_20261025').exists())

    def test_output_inside_input_rejected_without_write(self):
        inside = Path(args.fixture_tree) / 'forge_sol_S28_forbidden_20261025'
        self.cli[self.cli.index('--out') + 1] = str(inside)
        self.assertEqual(self.invoke().returncode, 2)
        self.assertFalse(inside.exists())

    def test_baseline_and_dist_outputs_rejected(self):
        for name in ('baseline', 'dist-lock'):
            parent = self.root / name
            parent.mkdir()
            dest = parent / 'forge_sol_S28_new_20261025'
            self.cli[self.cli.index('--out') + 1] = str(dest)
            self.assertEqual(self.invoke().returncode, 2)
            self.assertFalse(dest.exists())

    def test_wrong_declared_net_sha_rejected_before_mkdir(self):
        self.assertEqual(self.invoke(['--net-sha256', '0' * 64]).returncode, 2)
        self.assertFalse(self.out.exists())

    def test_unknown_net_rejected_before_mkdir(self):
        net = self.root / 'forge_sol_S28_bad_net_20261025.inc'
        net.write_bytes(b'not an allowed network')
        self.cli[self.cli.index('--net') + 1] = str(net)
        self.assertEqual(self.invoke().returncode, 2)
        self.assertFalse(self.out.exists())

    def test_helper_sha_rejected_before_mkdir(self):
        helper = self.root / 'forge_sol_S28_bad_helper_20261025.py'
        helper.write_text('pass\n')
        self.cli[self.cli.index('--pin-helper') + 1] = str(helper)
        self.assertEqual(self.invoke().returncode, 2)
        self.assertFalse(self.out.exists())

    def make_queue(self, rows):
        path = self.root / 'forge_sol_S28_queue_20261025.json'
        path.write_text(json.dumps(rows))
        return path

    def patch_fixture(self, content=b'--- a/value\n+++ b/value\n@@ -1 +1 @@\n-old\n+new\n'):
        path = self.root / 'forge_sol_S28_fixture_20261025.patch'
        path.write_bytes(content)
        return {'id': 'fixture', 'path': str(path), 'sha256': m.sha(path), 'option': 'Fixture', 'value': 1}

    def test_duplicate_queue_rejected_before_mkdir(self):
        row = self.patch_fixture()
        queue = self.make_queue([row, row])
        self.assertEqual(self.invoke(['--queue', str(queue)]).returncode, 2)
        self.assertFalse(self.out.exists())

    def test_patch_sha_mismatch_rejected_before_mkdir(self):
        row = self.patch_fixture()
        row['sha256'] = '0' * 64
        queue = self.make_queue([row])
        self.assertEqual(self.invoke(['--queue', str(queue)]).returncode, 2)
        self.assertFalse(self.out.exists())

    def test_patch_parent_traversal_rejected_before_mkdir(self):
        row = self.patch_fixture(b'--- a/../outside\n+++ b/../outside\n@@ -1 +1 @@\n-a\n+b\n')
        queue = self.make_queue([row])
        self.assertEqual(self.invoke(['--queue', str(queue)]).returncode, 2)
        self.assertFalse(self.out.exists())

    def test_nonzero_on_value_required(self):
        row = self.patch_fixture()
        row['value'] = 0
        queue = self.make_queue([row])
        self.assertEqual(self.invoke(['--queue', str(queue)]).returncode, 2)
        self.assertFalse(self.out.exists())

    def test_bench_parser_lf_crlf_and_wrong_depth(self):
        for newline in (b'\n', b'\r\n'):
            data = b'info string bench depth 11 nodes 308972 time 42 nps 7356476' + newline
            self.assertEqual(m.bench_count(data, 11), 308972)
            with self.assertRaises(ValueError):
                m.bench_count(data, 13)
            with self.assertRaises(ValueError):
                m.bench_count(data + data, 11)
        with self.assertRaises(ValueError):
            m.bench_count(b'info string malformed\n', 11)

    def test_uci_on_control_is_advertised_and_active_value_valid(self):
        line = b'option name RefutLmr type spin default 0 min 0 max 1\r\n'
        self.assertEqual(m.active_option(line, 'RefutLmr', 1)['default'], 0)
        for name, value in [('Other', 1), ('RefutLmr', 0), ('RefutLmr', 2)]:
            with self.assertRaises(ValueError):
                m.active_option(line, name, value)
        with self.assertRaises(ValueError):
            m.active_option(line.replace(b'default 0', b'default 1'), 'RefutLmr', 1)

    def test_fma_scan_instruction_mnemonic_only(self):
        self.assertEqual(m.fma_count(b'0010 <vfmadd_symbol>:\n 10: vmulps %ymm0,%ymm1,%ymm2\n'), 0)
        self.assertEqual(m.fma_count(b' 10: vfmadd213ps %ymm0,%ymm1,%ymm2\n 20: vfnmsub132ss %xmm0,%xmm1,%xmm2\n'), 2)

    def test_raw_encoding_keeps_exact_crlf_and_nontext(self):
        data = b'abc\r\n\xff\x00'
        record = m.raw(data)
        self.assertEqual(base64.b64decode(record['data']), data)
        self.assertEqual(record['sha256'], hashlib.sha256(data).hexdigest())

    def test_metadata_appends_preserving_all_original_bytes(self):
        dest = self.root / 'forge_sol_S28_meta_20261025'
        dest.mkdir()
        old = b'original text\r\nwithout final newline'
        (dest / 'README.md').write_bytes(old)
        receipt = m.append_metadata(dest, next(iter(m.NETS)), 'fixture')
        self.assertTrue((dest / 'README.md').read_bytes().startswith(old))
        self.assertEqual(receipt['README.md']['old_bytes'], len(old))

    def test_oracles_are_fixed_independent_and_never_adopt_candidate(self):
        values = list(m.NETS.values())
        self.assertEqual(values[0]['refs'], [308972, 745494, 2460422, 11901452, 31111774])
        self.assertEqual(values[1]['refs'], [328459, 945640, 3024381, 9162399, 20421972])
        self.assertIn('not_adopted', values[1]['label'])

    def test_exact_old_known_failures_only(self):
        data = ('\n'.join(m.OLD_FAILS + [m.OLD_FAILS[-1]]) + '\n').encode()
        self.assertEqual(m.known_failures(data, next(iter(m.NETS)), {})['status'], 'OBSERVED_KNOWN_ONLY')
        with self.assertRaises(ValueError):
            m.known_failures(data + b'FAIL: new regression\n', next(iter(m.NETS)), {})

    def test_queue_off_pin_drift_rejected_even_when_own_allowlist_agrees(self):
        base = {'pin_signature': [{'case': 'WAC001', 'bestmove': 'f6h5', 'score_kind': 'cp',
                                  'score': 642, 'depth': 12, 'pv': ['f6h5']}],
                'known_fail_lines': ['FAIL: WAC 001 score 642 below 31997']}
        queued = json.loads(json.dumps(base))
        m.require_base_pins(base, queued)
        queued['pin_signature'][0]['score'] = 643
        queued['known_fail_lines'] = ['FAIL: WAC 001 score 643 below 31997']
        with self.assertRaises(ValueError):
            m.require_base_pins(base, queued)

    def test_pin_signature_preserves_bestmove_score_depth_and_pv(self):
        pins = {'cases': [{'case': 'a', 'bestmove': 'a1a2', 'score_kind': 'cp', 'score': 100,
                           'depth': 1, 'pv': ['a1a2'], 'pid': 123}]}
        sig = m.pin_signature(pins)
        self.assertEqual(sig, [{'case': 'a', 'bestmove': 'a1a2', 'score_kind': 'cp', 'score': 100,
                               'depth': 1, 'pv': ['a1a2']}])
        self.assertNotIn('pid', sig[0])

    def test_printed_stage_summary_contains_native_counts_without_reinterpretation(self):
        stage = {'id': 'fixture', 'off': [{'depth': 11, 'nodes': 308972}], 'on': None,
                 'perft': [{'position': 'startpos', 'nodes': 4865609}, {'position': 'kiwipete', 'nodes': 193690690}],
                 'fma': [{'scope': 'engine', 'count': 0}, {'scope': 'nnue_object', 'count': 0}]}
        summary = m.stage_summary(stage)
        encoded = json.dumps(summary)
        for value in ('308972', '4865609', '193690690'):
            self.assertIn(value, encoded)
        self.assertEqual(summary['fma'], {'engine': 0, 'nnue_object': 0})
        self.assertEqual(summary['off'], {'11': 308972})

    def load_postchecker(self):
        path = HERE / 'forge_sol_S28_native_pin_postcheck_20261025.py'
        spec = importlib.util.spec_from_file_location('s28_postcheck', path)
        post = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(post)
        return post

    def test_postcheck_verifies_manifest_before_trusting_modified_pin_file(self):
        post = self.load_postchecker()
        out = self.root / 'forge_sol_S28_sealed_fixture_20261025'
        out.mkdir()
        pin = out / 'forge_sol_S28_pin_fixture_20261025.json'
        pin.write_text('{"status":"PASS"}\n')
        m.seal(out)
        receipt = post.check_manifest(out)
        self.assertEqual(receipt['exit'], 0)
        pin.write_text('{"status":"PASS","tampered":true}\n')
        with self.assertRaises(ValueError):
            post.check_manifest(out)

    def test_postcheck_rejects_nonclosed_pin_capture_despite_status_pass(self):
        post = self.load_postchecker()
        good = {'status': 'PASS', 'cases': [
            {'case': name, 'status': 'OBSERVED', 'exit': 0, 'stream_capture_complete': True, 'unclosed_pid': None}
            for name in ('WAC001', 'promotion_white', 'promotion_black')]}
        post.check_pin_capture(good)
        bad = json.loads(json.dumps(good))
        bad['cases'][0]['stream_capture_complete'] = False
        with self.assertRaises(ValueError):
            post.check_pin_capture(bad)
        bad = json.loads(json.dumps(good))
        bad['cases'][1]['exit'] = 1
        with self.assertRaises(ValueError):
            post.check_pin_capture(bad)

    def test_original_patch_failure_retained_before_repair(self):
        src = self.root / 'forge_sol_S28_apply_fixture_20261025'
        src.mkdir()
        (src / 'value').write_text('old\n')
        row = self.patch_fixture(b'--- a/value\n+++ b/value\n@@ -1 +1 @@\n-wrong\n+new\n')
        repair = self.root / 'forge_sol_S28_fixture_repair_20261025.patch'
        repair.write_bytes(b'--- a/value\n+++ b/value\n@@ -1 +1 @@\n-old\n+new\n')
        row.update(repair_path=str(repair), repair_sha256=m.sha(repair))
        receipts = self.root / 'forge_sol_S28_apply_receipts_20261025'
        receipts.mkdir()
        receipt = m.apply_queue(m.Runner(receipts), src, row)
        self.assertEqual(receipt['original_dryrun_exit'], 1)
        self.assertTrue(receipt['used_repair'])
        self.assertEqual(receipt['apply_exit'], 0)
        self.assertEqual((src / 'value').read_text(), 'new\n')
        self.assertEqual(len(list(receipts.glob('*raw*.json'))), 3)

    def test_successful_original_does_not_use_supplied_repair(self):
        src = self.root / 'forge_sol_S28_apply_fixture_20261025'
        src.mkdir()
        (src / 'value').write_text('old\n')
        row = self.patch_fixture()
        row.update(repair_path='/does/not/exist', repair_sha256='0' * 64)
        receipts = self.root / 'forge_sol_S28_apply_receipts_20261025'
        receipts.mkdir()
        receipt = m.apply_queue(m.Runner(receipts), src, row)
        self.assertFalse(receipt['used_repair'])
        self.assertEqual(receipt['original_dryrun_exit'], 0)

if __name__ == '__main__':
    unittest.main()
