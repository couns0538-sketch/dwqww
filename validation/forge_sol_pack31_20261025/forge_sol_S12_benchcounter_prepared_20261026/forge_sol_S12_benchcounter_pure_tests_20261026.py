#!/usr/bin/env python3
"""PURE synthetic controls. No C++ compiler, engine, or native benchmark."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


producer = load('s12counterproducer', HERE / 'forge_sol_S12_benchcounter_source_producer_20261026.py')
parser = load('s12counterrecords', HERE / 'forge_sol_S12_benchcounter_records_20261026.py')


class SourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = {name: (producer.BASE / name).read_text() for name in producer.INPUT_SHA}

    def extract(self, uci=None, board=None, tool=None):
        return producer.extract(uci if uci is not None else self.inputs['src/uci.cpp'],
            board if board is not None else self.inputs['include/forge/board.hpp'],
            tool if tool is not None else self.inputs['tools/search_benchmark.cpp'])

    def test_exact_actual_eight_fens_and_semantics(self):
        result = self.extract()
        self.assertEqual(len(result['fens']), 8)
        self.assertEqual(len(set(result['fens'])), 8)
        self.assertEqual(result['suite_sha256'], producer.sha(('\n'.join(result['fens']) + '\n').encode()))

    def test_rejects_bench_semantic_mutants(self):
        mutations = [
            ('forge::Searcher bench_searcher(16);', 'forge::Searcher bench_searcher(32);'),
            ('bench_searcher.clear();', ''),
            ('limits.depth = depth;', 'limits.depth = depth + 1;'),
            ('bench_board, limits, false, forge::Searcher::TTAccess::Exclusive', 'bench_board, limits, true, forge::Searcher::TTAccess::Exclusive'),
            ('forge::Searcher::TTAccess::Exclusive).nodes', 'forge::Searcher::TTAccess::Shared).nodes'),
            ('constexpr std::array<std::string_view, 8> fens', 'constexpr std::array<std::string_view, 7> fens'),
            ('forge::Board::StandardStartFen,', '"invented",'),
        ]
        for old, new in mutations:
            self.assertIn(old, self.inputs['src/uci.cpp'])
            with self.subTest(mutation=old), self.assertRaises(ValueError):
                self.extract(uci=self.inputs['src/uci.cpp'].replace(old, new))

    def test_rejects_duplicate_branch_and_guessed_startpos(self):
        with self.assertRaises(ValueError):
            self.extract(uci=self.inputs['src/uci.cpp'] * 2)
        with self.assertRaises(ValueError):
            self.extract(board='unknown header')

    def test_rejects_missing_existing_initialization_example(self):
        with self.assertRaises(ValueError):
            self.extract(tool=self.inputs['tools/search_benchmark.cpp'].replace('forge::Board board;', ''))

    def test_byte_identical_source_production_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='forge_sol_S12_pure_source_') as folder:
            root = Path(folder)
            a, b = producer.emit(root / 'a'), producer.emit(root / 'b')
            self.assertEqual(a, b)
            self.assertEqual((root / 'a/forge_sol_S12_benchcounter_helper_20261026.cpp').read_bytes(),
                             (root / 'b/forge_sol_S12_benchcounter_helper_20261026.cpp').read_bytes())
            with self.assertRaises(FileExistsError):
                producer.emit(root / 'a')

    def test_changed_actual_source_pin_refused_before_output(self):
        with tempfile.TemporaryDirectory(prefix='forge_sol_S12_pure_mutation_') as folder:
            root = Path(folder)
            for name, text in self.inputs.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text.replace('bench_searcher(16)', 'bench_searcher(32)'))
            with mock.patch.object(producer, 'BASE', root), self.assertRaisesRegex(ValueError, 'canonical input changed'):
                producer.emit(root / 'out')
            self.assertFalse((root / 'out').exists())


class SyntheticRecords(unittest.TestCase):
    """The numbers below are explicitly SYNTHETIC parser fixtures, not games/bench."""
    @classmethod
    def setUpClass(cls):
        cls.binding = json.loads((HERE / 'generated_final/forge_sol_S12_benchcounter_source_binding_20261026.json').read_text())

    def records(self, mode):
        b = self.binding
        header = {'record': 'binding', 'mode': mode, 'requested_depth': 11,
            'suite_count': 8, 'hash_mib': 16, 'threads': 1,
            'canonical_uci_sha256': b['canonical_input_sha256']['src/uci.cpp'],
            'bench_block_sha256': b['bench_block_sha256'], 'suite_sha256': b['suite_sha256'],
            'candidate_header_sha256': b['candidate_header_sha256'], 'candidate_patch_sha256': b['candidate_patch_sha256']}
        rows = []
        for i, fen in enumerate(b['fens']):
            stats = {'refreshes': 1, 'updates': 10 if mode == 'OFF' else 8,
                     'zero_dirty_edges': 2, 'copies_avoided': 0 if mode == 'OFF' else 2,
                     'alias_hits': 0 if mode == 'OFF' else 1, 'evaluations': 12}
            rows.append({'record': 'per_fen', 'mode': mode, 'requested_depth': 11, 'index': i,
                         'fen': fen, 'nodes': 100 if i < 7 else 308272, 'completed_depth': 11, 'stats': stats})
        total = {'record': 'total', 'mode': mode, 'requested_depth': 11, 'positions': 8,
                 'nodes': 308972, 'reference_nodes': 308972, 'node_reference_match': True,
                 'completed_depths_match': True, 'stats': {field: sum(x['stats'][field] for x in rows) for field in parser.FIELDS}}
        return [header, *rows, total]

    def text(self, records, include_diagnostics=True):
        mode = records[0]['mode']
        lines = [json.dumps(records[0])]
        for index, row in enumerate(records[1:-1]):
            if mode == 'ON' and include_diagnostics:
                if index == 0:
                    lines.append('info string NnueLazyAcc active')
                lines.append('info string NnueLazyAcc stats ' + ' '.join(f'{key} {row["stats"][key]}' for key in parser.FIELDS))
            lines.append(json.dumps(row))
        lines.append(json.dumps(records[-1]))
        return '\n'.join(lines) + '\n'

    def validate(self, records):
        return parser.validate(self.text(records), self.binding, records[0]['mode'], 11)

    def test_synthetic_valid_off_on_pair(self):
        off, on = self.validate(self.records('OFF')), self.validate(self.records('ON'))
        result = parser.compare(off, on)
        self.assertEqual(result['status'], 'PASS_COUNTER_AND_NODE_PAIR')
        self.assertFalse(result['speed_or_Elo_claim'])

    def test_per_fen_count_order_depth_nodes_mutants(self):
        for mutation in ['skip', 'duplicate', 'reorder', 'early', 'wrong_nodes', 'wrong_fen']:
            rows = self.records('OFF')
            if mutation == 'skip':
                rows.pop(3)
            elif mutation == 'duplicate':
                rows[2] = copy.deepcopy(rows[1])
            elif mutation == 'reorder':
                rows[1], rows[2] = rows[2], rows[1]
            elif mutation == 'early':
                rows[1]['completed_depth'] = 10
            elif mutation == 'wrong_nodes':
                rows[1]['nodes'] += 1
            else:
                rows[1]['fen'] = rows[2]['fen']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.validate(rows)

    def test_counter_types_overflow_missing_and_aggregate_mutants(self):
        for bad in [-1, 1.0, True, '1', 1 << 64]:
            rows = self.records('OFF'); rows[1]['stats']['updates'] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError):
                self.validate(rows)
        for mutation in ['missing', 'aggregate', 'no_refresh', 'off_skip', 'zero_on']:
            rows = self.records('ON' if mutation == 'zero_on' else 'OFF')
            if mutation == 'missing':
                del rows[1]['stats']['updates']
            elif mutation == 'aggregate':
                rows[-1]['stats']['evaluations'] += 1
            elif mutation == 'no_refresh':
                rows[1]['stats']['refreshes'] = 0
            elif mutation == 'off_skip':
                rows[1]['stats']['copies_avoided'] = 1
            else:
                for row in rows[1:]:
                    row['stats']['copies_avoided'] = row['stats']['zero_dirty_edges'] = 0
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.validate(rows)

    def test_header_and_diagnostic_binding_mutants(self):
        for key, bad in [('hash_mib', 32), ('threads', 2), ('suite_sha256', 'wrong'), ('hash_mib', 16.0)]:
            rows = self.records('OFF'); rows[0][key] = bad
            with self.subTest(key=key, value=bad), self.assertRaises(ValueError):
                self.validate(rows)
        on = self.records('ON')
        with self.assertRaises(ValueError):
            parser.validate(self.text(on, False), self.binding, 'ON', 11)
        with self.assertRaises(ValueError):
            parser.validate(self.text(on) + 'info string NnueLazyAcc active\n', self.binding, 'ON', 11)

    def test_pair_accounting_rejects_changed_search_or_values(self):
        off = self.validate(self.records('OFF'))
        for mutation in ['nodes', 'evaluations', 'updates', 'zero_dirty_edges']:
            on = self.validate(self.records('ON'))
            if mutation == 'nodes':
                on['rows'][0]['nodes'] += 1
            else:
                on['rows'][0]['stats'][mutation] += 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                parser.compare(off, on)


if __name__ == '__main__':
    unittest.main(verbosity=2)
