"""Synthetic parser/stream controls only; these are never engine evidence."""
from pathlib import Path
import copy
import gzip
import hashlib
import json
import tempfile
import unittest
import forge_sol_S12_alias_transport_20261027 as wire


class SyntheticWireFixtures(unittest.TestCase):
    def summary(self, mode=2):
        value = dict(positions=8192, record_bytes=2068, header_bytes=36, mode=mode,
            implementation_present=int(mode != 0), worker_constructions=1, history_clears_after_construction=0,
            transition_roots=1024, oracle_root_refreshes=8192, selected_nulls=8000, legal_children=2000,
            nulls=11000, verified_evaluations=20000, fresh_mismatches=0, state_mismatches=0,
            refreshes=0, updates=2000, zero_dirty_edges=11000, copies_avoided=11000, alias_hits=9000, evaluations=20000)
        if mode == 0:
            for key in ('refreshes','updates','zero_dirty_edges','copies_avoided','alias_hits','evaluations'): value[key] = 0
        if mode == 1: value.update(copies_avoided=0, alias_hits=0)
        return value

    def parse(self, value, mode=2):
        return wire.parse_summary(json.dumps(value).encode(), 8192, 1024, mode)

    def test_three_distinct_modes_accept_fixture_contract(self):
        for mode in range(3): self.assertEqual(self.parse(self.summary(mode), mode)['mode'], mode)

    def test_on_without_copy_avoidance_rejected(self):
        value = self.summary(); value['copies_avoided'] = 0
        with self.assertRaisesRegex(ValueError, 'alias path'): self.parse(value)

    def test_on_without_actual_alias_hit_rejected(self):
        value = self.summary(); value['alias_hits'] = 0
        with self.assertRaisesRegex(ValueError, 'alias path'): self.parse(value)

    def test_off_claiming_alias_rejected(self):
        value = self.summary(1); value['copies_avoided'] = 1
        with self.assertRaisesRegex(ValueError, 'OFF'): self.parse(value, 1)

    def test_baseline_invented_counter_rejected(self):
        value = self.summary(0); value['evaluations'] = 1
        with self.assertRaisesRegex(ValueError, 'unavailable'): self.parse(value, 0)

    def test_per_row_worker_construction_rejected(self):
        value = self.summary(); value['worker_constructions'] = 8192
        with self.assertRaisesRegex(ValueError, 'binding'): self.parse(value)

    def test_mismatch_is_never_a_known_failure(self):
        for key in ('fresh_mismatches','state_mismatches'):
            value = self.summary(); value[key] = 1
            with self.assertRaisesRegex(ValueError, 'binding'): self.parse(value)

    def test_bool_counter_rejected(self):
        value = self.summary(); value['fresh_mismatches'] = False
        with self.assertRaisesRegex(ValueError, 'schema'): self.parse(value)

    def test_old_S11_magic_rejected(self):
        header = wire.HEADER.pack(0x4b313146, 1, 256, 2068, 8192, 1024, 0x1f80)
        with self.assertRaisesRegex(ValueError, 'header'): wire.parse_header(header, 8192, 1024)

    def streams(self, root):
        raw = wire.HEADER.pack(0x4b323146, 1, 256, 2068, 3, 1, 0x1f80) + bytes(2068 * 3)
        for label in ('left','right'):
            with wire.ChunkedGzip(root, label, 3, 1, chunk_records=2) as stream: stream.write(raw)
        return root/'left.stdout.chunks.json', root/'right.stdout.chunks.json'

    def test_exact_original_bytes_accept_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            left, right = self.streams(Path(d))
            self.assertEqual(wire.compare_chunked(left, right, 3, 1)['bytes_compared'], 36+3*2068)

    def test_truncated_original_gzip_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            left, right = self.streams(Path(d)); value = json.loads(right.read_text())
            part = right.parent/value['chunks'][0]['path']; part.write_bytes(part.read_bytes()[:-1])
            with self.assertRaisesRegex(ValueError, 'compressed'): wire.compare_chunked(left, right, 3, 1)

    def test_reordered_chunks_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            left, right = self.streams(Path(d)); value = json.loads(right.read_text()); value['chunks'].reverse()
            right.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'gap/reorder'): wire.compare_chunked(left, right, 3, 1)

    def test_changed_payload_detected_even_with_resealed_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            left, right = self.streams(Path(d)); value = json.loads(right.read_text()); row = value['chunks'][0]
            part = right.parent/row['path']; raw = bytearray(gzip.decompress(part.read_bytes())); raw[40] ^= 1
            part.write_bytes(gzip.compress(raw, compresslevel=1, mtime=0)); row.update(gzip_bytes=part.stat().st_size,
                gzip_sha256=wire.sha(part), raw_sha256=hashlib.sha256(raw).hexdigest())
            right.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'differs at byte'): wire.compare_chunked(left, right, 3, 1)


if __name__ == '__main__': unittest.main(verbosity=2)
