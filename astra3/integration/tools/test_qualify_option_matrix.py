#!/usr/bin/env python3
"""Synthetic matrix-parser regressions; never launch an engine.

IDEA_SOURCE: same-repository qualification parser and independent review findings.
--legacy-source executes only the three original parser assignments from the
saved pre-fix runner, proving RED against its actual parser rather than a mock.
"""
import argparse
import ast
import importlib.util
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest


def legacy_parser(path):
    tree = ast.parse(path.read_text())
    statements = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in ('found', 'bad'):
            statements.append(node)
        elif (isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
              and target.value.id == 'row' and isinstance(target.slice, ast.Constant)
              and target.slice.value == 'pass'):
            statements.append(node)
    if len(statements) != 3:
        raise RuntimeError('expected exactly the original three parser assignments')
    code = compile(ast.Module(body=sorted(statements, key=lambda n: n.lineno), type_ignores=[]),
                   str(path), 'exec')

    def parse(stdout, stderr, returncode, depth, expected_nodes):
        env = {'re': re, 'r': SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode),
               'row': {}, 'depth': depth, 'pin': expected_nodes,
               'digest': lambda _: 'unchanged', 'exe': None, 'binary_hash': 'unchanged'}
        exec(code, env)
        return env['row']
    return parse


argument_parser = argparse.ArgumentParser(add_help=False)
argument_parser.add_argument('--legacy-source', type=Path)
arguments, remaining = argument_parser.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
if arguments.legacy_source:
    parse = legacy_parser(arguments.legacy_source)
else:
    path = Path(__file__).with_name('qualify_option_matrix.py')
    spec = importlib.util.spec_from_file_location('qualify_option_matrix', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parse = module.parse_bench_result


class MatrixParserTests(unittest.TestCase):
    good = b'uciok\nreadyok\ninfo string bench depth 11 nodes 312866 time 7 nps 44695142\n'

    def accepts(self, output, *, stderr=b'', returncode=0, depth=11, nodes=312866):
        return parse(output, stderr, returncode, depth, nodes)['pass']

    def test_valid(self):
        self.assertTrue(self.accepts(self.good))
        self.assertTrue(self.accepts(self.good.replace(b'\n', b'\r\n')))

    def test_malformed_extra_bench(self):
        self.assertFalse(self.accepts(self.good + b'info string bench depth 11 nodes BROKEN time 7 nps 1\n'))

    def test_duplicate_valid_bench(self):
        self.assertFalse(self.accepts(self.good + self.good.splitlines(keepends=True)[-1]))

    def test_explicit_error(self):
        for message in (b'info string ERROR diagnostic failure\n', b'ERROR: diagnostic failure\n'):
            with self.subTest(message=message):
                self.assertFalse(self.accepts(self.good + message))
                self.assertFalse(self.accepts(self.good, stderr=message))

    def test_handshake_exactly_once(self):
        for token in (b'uciok\n', b'readyok\n'):
            for out in (self.good.replace(token, b''), self.good + token):
                with self.subTest(out=out):
                    self.assertFalse(self.accepts(out))

    def test_wrong_reference_or_exit(self):
        self.assertFalse(self.accepts(self.good, depth=13))
        self.assertFalse(self.accepts(self.good, nodes=1))
        self.assertFalse(self.accepts(self.good, returncode=2))

    def test_rejected_options(self):
        for message in (b'info string unknown option Test\n', b'info string invalid value for option Test\n',
                        b'info string SingularV2 refused: CorrExt is active\n'):
            with self.subTest(message=message):
                self.assertFalse(self.accepts(self.good + message))

    def test_numeric_record_must_be_complete(self):
        for record in (b'info string bench depth 11 nodes 312866 time 7 nps 1 junk',
                       b'info string bench depth 11 nodes 312866 time 7',
                       b'info string bench depth 11 nodes 312866 time -7 nps 1'):
            with self.subTest(record=record):
                self.assertFalse(self.accepts(b'uciok\nreadyok\n' + record + b'\n'))


if __name__ == '__main__':
    unittest.main()
