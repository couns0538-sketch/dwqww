"""Replay captured engine bytes; execute only the isolated parser AST, never engines."""
import ast
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
SOURCE = Path(os.environ.get('BENCH_PARSER_DATA', str(ROOT.parents[1] / '.github/hosted-tt-refresh-strength/run_hosted.py')))
tree = ast.parse(SOURCE.read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == 'verify_candidate_bench_signature')
namespace = {'re': re}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), 'exec'), namespace)
verify = namespace['verify_candidate_bench_signature']


class CapturedCanonicalBytes(unittest.TestCase):
    def accept_capture(self, name, expected_ms, expected_nps, expected_nodes=385781):
        stdout = (ROOT / 'captures' / name).read_bytes().decode('ascii')
        stderr = (ROOT / 'captures' / name.split('.')[0]).with_suffix('.stderr.bin').read_bytes().decode('ascii')
        try:
            result = verify(stdout, stderr, 0, expected_nodes)
        except ValueError as error:
            self.fail(f'Parser rejected preserved canonical capture {name}: {error}')
        self.assertEqual(result, {'engine_nodes': expected_nodes, 'engine_ms': expected_ms,
            'engine_nps': expected_nps, 'scope': 'Signature readiness only; no speed comparison'})

    def test_historical18_cannot_pass_genuine22_baseline_signature(self):
        data=(ROOT/'captures/native18.stdout.bin').read_bytes().decode('ascii')
        with self.assertRaises(ValueError):verify(data,'',0,292545)

    def test_actual_native18_lf_capture(self):
        self.accept_capture('native18.stdout.bin',1738,185219,321912)

    def test_explicitly_derived_native18_crlf(self):
        self.accept_capture('native18.derived-crlf.stdout.bin',1738,185219,321912)

    def test_old17_signature_cannot_pass_frozen18_expectation(self):
        data=(ROOT/'captures/native.stdout.bin').read_bytes().decode('ascii')
        with self.assertRaises(ValueError):verify(data,'',0,321912)

    def test_actual_native_lf_capture(self):
        self.accept_capture('native.stdout.bin', 1016, 379705)

    def test_actual_hosted_lf_capture(self):
        self.accept_capture('hosted.stdout.bin', 222, 1737752)

    def test_explicitly_derived_native_crlf(self):
        self.accept_capture('native.derived-crlf.stdout.bin', 1016, 379705)

    def test_explicitly_derived_hosted_crlf(self):
        self.accept_capture('hosted.derived-crlf.stdout.bin', 222, 1737752)


class RejectInvalidBytes(unittest.TestCase):
    def setUp(self):
        self.good = (ROOT / 'captures/hosted.stdout.bin').read_bytes().decode('ascii')

    def reject(self, stdout, stderr='', code=0, nodes=385781):
        with self.assertRaises(ValueError):
            verify(stdout, stderr, code, nodes)

    def test_invented_prefixless_previous_good_is_rejected(self):
        self.reject(self.good.removeprefix('info string '))

    def test_wrong_prefix_or_leading_whitespace(self):
        for line in ('info '+self.good, ' '+self.good, self.good.replace('info string ', 'INFO STRING ')):
            with self.subTest(line=line): self.reject(line)

    def test_empty_or_missing_signature(self):
        for line in ('', 'info string ready\n'):
            with self.subTest(line=line): self.reject(line)

    def test_duplicate_canonical_or_mixed_malformed_records(self):
        for line in (self.good+self.good, self.good+self.good.replace('time 222', 'time nan')):
            with self.subTest(line=line): self.reject(line)

    def test_node_signature_and_expected_nodes_remain_strict(self):
        for nodes in (385792, 419798, True, None, '385781', 385781.0):
            with self.subTest(nodes=nodes): self.reject(self.good, nodes=nodes)
        self.reject(self.good.replace('385781', '385792'))

    def test_wrong_depth_or_numeric_token(self):
        for old, new in [('depth 11', 'depth 10'), ('time 222', 'time nan'),
                         ('time 222', 'time -1'), ('time 222', 'time 2.2'),
                         ('nps 1737752', 'nps inf'), ('nps 1737752', 'nps -1'),
                         ('nps 1737752', 'nps 1737752garbage'),
                         ('nodes 385781', 'nodes ３８５７８１')]:
            with self.subTest(old=old,new=new): self.reject(self.good.replace(old,new))

    def test_nonzero_exit_is_rejected(self):
        for code in (1, 66, -9):
            with self.subTest(code=code): self.reject(self.good, code=code)

    def test_any_stderr_is_rejected(self):
        for stderr in (' ', '\n', 'warning\n'):
            with self.subTest(stderr=stderr): self.reject(self.good, stderr=stderr)

    def test_bare_bracket_and_uci_warnings_or_errors_are_rejected(self):
        for warning in ('Warning: fault\n', ' ERROR fault\n', '[WARN ] fault\n',
                        '[ERROR ] fault\n', '[FATAL ] fault\n',
                        'info string warning fault\n', 'info string error fault\n'):
            with self.subTest(warning=warning): self.reject(self.good+warning)

    def test_unexpected_extra_line_or_trailing_blank_is_rejected(self):
        for line in (self.good+'unexpected\n', self.good+'\n', 'unexpected\n'+self.good):
            with self.subTest(line=line): self.reject(line)

    def test_malformed_line_end_or_trailing_space_is_rejected(self):
        for line in (self.good.replace('\n','\r'), self.good.replace('\n',' \n'), self.good+'\x00'):
            with self.subTest(line=line): self.reject(line)


if __name__ == '__main__':
    unittest.main(verbosity=2)
