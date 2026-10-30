#!/usr/bin/env python3
"""Real-file round-trip and rejection tests for transport chunks, not archives.
IDEA_SOURCE: user durable-evidence requirements and Python standard library.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / 'validation/astra-a1-data/transport_parts.py'


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='forge-transport-test-'))
        print('retained transport fixture ' + str(self.root), file=sys.stderr)
        self.assertTrue(SCRIPT.is_file(), 'transport utility not implemented')
        spec = importlib.util.spec_from_file_location('transport_parts', SCRIPT)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.source = self.root / 'forge_original.tar.xz'
        self.payload = bytes(range(256)) * 5 + b'\r\n\x00\xffbinary\n'
        self.source.write_bytes(self.payload)

    def split(self):
        return self.tool.split(self.source, self.root / 'parts', 97)

    def test_binary_roundtrip_offsets_and_hashes(self):
        manifest = self.split()
        data = self.tool.verify(manifest)
        self.assertEqual(data['whole']['size'], len(self.payload))
        self.assertEqual(data['whole']['sha256'], hashlib.sha256(self.payload).hexdigest())
        offset = 0
        for part in data['parts']:
            self.assertEqual(part['offset'], offset)
            self.assertLessEqual(part['size'], 97)
            offset += part['size']
        joined = self.root / 'joined.tar.xz'
        self.tool.join(manifest, joined)
        self.assertEqual(joined.read_bytes(), self.payload)
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertTrue(joined.with_name(joined.name + '.partial').exists())

    def test_existing_directories_and_destinations_are_untouched(self):
        manifest = self.split()
        with self.assertRaises(FileExistsError):
            self.tool.split(self.source, manifest.parent, 97)
        joined = self.root / 'existing'
        joined.write_bytes(b'original destination')
        with self.assertRaises(FileExistsError):
            self.tool.join(manifest, joined)
        self.assertEqual(joined.read_bytes(), b'original destination')

    def test_corruption_rejected_before_final_publication(self):
        manifest = self.split()
        data = json.loads(manifest.read_text())
        part = manifest.parent / data['parts'][1]['name']
        part.write_bytes(b'x' * part.stat().st_size)
        with self.assertRaisesRegex(ValueError, 'digest'):
            self.tool.verify(manifest)
        target = self.root / 'never_published'
        with self.assertRaises(ValueError):
            self.tool.join(manifest, target)
        self.assertFalse(target.exists())

    def test_missing_extra_and_wrong_size_parts_rejected(self):
        manifest = self.split()
        data = json.loads(manifest.read_text())
        first = manifest.parent / data['parts'][0]['name']
        saved = first.with_suffix('.retained')
        first.rename(saved)
        with self.assertRaisesRegex(ValueError, 'files'):
            self.tool.verify(manifest)
        saved.rename(first)
        extra = manifest.parent / 'unexpected.txt'
        extra.write_text('retain fixture')
        with self.assertRaisesRegex(ValueError, 'files'):
            self.tool.verify(manifest)
        extra.rename(self.root / 'retained-extra.txt')
        first.write_bytes(b'short')
        with self.assertRaisesRegex(ValueError, 'size'):
            self.tool.verify(manifest)

    def test_manifest_traversal_offsets_and_whole_digest_rejected(self):
        manifest = self.split()
        original = manifest.read_text()
        for mutate in ('traversal', 'windows_traversal', 'offset', 'whole_digest', 'oversize'):
            data = json.loads(original)
            if mutate == 'traversal': data['parts'][0]['name'] = '../forge_original.tar.xz'
            if mutate == 'windows_traversal': data['whole']['name'] = '..\\outside.zip'
            if mutate == 'offset': data['parts'][0]['offset'] = 1
            if mutate == 'whole_digest': data['whole']['sha256'] = '0' * 64
            if mutate == 'oversize': data['part_bytes'] = 1800000001
            manifest.write_text(json.dumps(data))
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.tool.verify(manifest)
        manifest.write_text(original)

    def test_invalid_part_sizes_do_not_create_output(self):
        for size in (0, -1, 1800000001, True):
            destination = self.root / ('invalid_' + str(size))
            with self.assertRaises(ValueError):
                self.tool.split(self.source, destination, size)
            self.assertFalse(destination.exists())

    def test_source_mutation_retains_parts_without_success_manifest(self):
        original_check = self.tool.check_bytes

        def mutate_after_part_check(*args, **kwargs):
            original_check(*args, **kwargs)
            self.source.write_bytes(b'changed source while splitting')

        with mock.patch.object(self.tool, 'check_bytes', side_effect=mutate_after_part_check):
            with self.assertRaisesRegex(ValueError, 'source archive changed'):
                self.split()
        directory = self.root / 'parts'
        self.assertFalse((directory / 'transport_manifest.json').exists())
        retained = sorted(directory.glob('transport_part_*.bin'))
        self.assertTrue(retained)
        self.assertEqual(b''.join(path.read_bytes() for path in retained), self.payload)

    def test_late_destination_race_retains_partial_and_original_destination(self):
        manifest = self.split()
        target = self.root / 'race.tar.xz'
        original_link = self.tool.os.link

        def create_destination_first(source, destination):
            Path(destination).write_bytes(b'concurrent original')
            return original_link(source, destination)

        with mock.patch.object(self.tool.os, 'link', side_effect=create_destination_first):
            with self.assertRaises(FileExistsError):
                self.tool.join(manifest, target)
        self.assertEqual(target.read_bytes(), b'concurrent original')
        self.assertEqual(target.with_name(target.name + '.partial').read_bytes(), self.payload)

    def test_existing_partial_is_retained_and_not_reused(self):
        manifest = self.split()
        target = self.root / 'retry.tar.xz'
        partial = target.with_name(target.name + '.partial')
        partial.write_bytes(b'prior failed attempt')
        with self.assertRaises(FileExistsError):
            self.tool.join(manifest, target)
        self.assertEqual(partial.read_bytes(), b'prior failed attempt')
        self.assertFalse(target.exists())

    def test_empty_file_roundtrip(self):
        self.source.write_bytes(b'')
        manifest = self.split()
        self.assertEqual(self.tool.verify(manifest)['parts'], [])
        target = self.root / 'empty_joined'
        self.tool.join(manifest, target)
        self.assertEqual(target.read_bytes(), b'')

    @unittest.skipUnless(hasattr(Path, 'symlink_to'), 'symlinks unavailable')
    def test_symlinked_part_is_rejected(self):
        manifest = self.split()
        data = json.loads(manifest.read_text())
        first = manifest.parent / data['parts'][0]['name']
        saved = self.root / 'original-part-retained'
        first.rename(saved)
        try:
            first.symlink_to(saved)
        except OSError as error:
            self.skipTest(str(error))
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.tool.verify(manifest)


if __name__ == '__main__':
    unittest.main(verbosity=2)
