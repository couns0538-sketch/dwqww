"""Synthetic packaging tests; fixture directories are retained under /tmp.
IDEA_SOURCE: user evidence-preservation and safe-publication contract.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('package_results', Path(__file__).resolve().parents[2] / 'validation/astra-a1-data/package_results.py')
pack = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pack)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='astra_a1_package_unit_'))
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'summary.json').write_text('{"status":"SEALED"}\n')
        (self.source / 'manifest.json').write_text('{}\n')
        (self.source / 'data.bin').write_bytes(bytes(range(256)) * 4)
        self.mapping = [{'sourcepath': str(self.source), 'archiveprefix': 'completed/full10m', 'kind': 'sealed'}]
        self.output = self.root / 'astra_a1_test.tar.gz'

    def test_round_trip_with_failed_and_auxiliary_inputs(self):
        failed = self.root / 'failed'; failed.mkdir()
        (failed / 'failure.json').write_text('{"status":"FAILED_UNSEALED"}')
        log = self.root / 'console.log'; log.write_text('original log\n')
        self.mapping += [{'sourcepath':str(failed),'archiveprefix':'UNSEALED/attempt1','kind':'unsealed'}, {'sourcepath':str(log),'archiveprefix':'outer_logs/console.log','kind':'auxiliary'}]
        result = pack.package(self.mapping, self.output, [{'url':'https://github.com/example/repo/releases/tag/data','sha256':'a'*64,'bytes':100,'description':'original input reference'}])
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['archive_sha256'], hashlib.sha256(self.output.read_bytes()).hexdigest())
        with tarfile.open(self.output, 'r:gz') as archive:
            self.assertEqual(archive.extractfile('completed/full10m/data.bin').read(), (self.source/'data.bin').read_bytes())
            self.assertTrue(all(m.isfile() or m.isdir() for m in archive))
        self.assertTrue(Path(str(self.output)+'.receipt.json').is_file())
        self.assertTrue(Path(str(self.output)+'.partial').is_file())
        self.assertEqual(len(list(self.source.iterdir())), 3)

    def test_rejects_unsealed_completed_input(self):
        (self.source/'summary.json').write_text('{"status":"RUNNING"}')
        with self.assertRaises(ValueError): pack.package(self.mapping,self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_failure_marker_on_sealed_input(self):
        (self.source/'failure.json').write_text('bad')
        with self.assertRaises(ValueError): pack.package(self.mapping,self.output)

    def test_rejects_missing_manifest(self):
        separate=self.root/'incomplete';separate.mkdir()
        (separate/'summary.json').write_text('{"status":"SEALED"}')
        self.mapping[0]['sourcepath']=str(separate)
        with self.assertRaises(ValueError): pack.package(self.mapping,self.output)

    def test_rejects_unsafe_prefix(self):
        for prefix in ('../escape','/absolute','ok/../bad','C:\\bad','ok\\bad','ok//bad','NUL','bad.'):
            with self.subTest(prefix=prefix):
                self.mapping[0]['archiveprefix']=prefix
                with self.assertRaises(ValueError): pack.inventory(self.mapping)

    def test_unsealed_requires_visible_prefix(self):
        self.mapping[0]['kind']='unsealed'
        with self.assertRaises(ValueError): pack.inventory(self.mapping)

    def test_reserved_manifest_prefix_rejected_case_insensitively(self):
        for prefix in ('ASTRA_A1_PACKAGE_MANIFEST.JSON',
                       'astra_a1_package_manifest.json/subdir',
                       'ASTRA_A1_PACKAGE_MANIFEST.JSON/subdir'):
            with self.subTest(prefix=prefix):
                self.mapping[0]['archiveprefix']=prefix
                with self.assertRaisesRegex(ValueError,'reserved archive manifest'):
                    pack.inventory(self.mapping)

    def test_reserved_manifest_auxiliary_file_rejected(self):
        item={'sourcepath':str(self.source/'data.bin'),
              'archiveprefix':'ASTRA_A1_PACKAGE_MANIFEST.JSON','kind':'auxiliary'}
        with self.assertRaisesRegex(ValueError,'reserved archive manifest'):
            pack.inventory([item])

    def test_rejects_symlink_file_and_source(self):
        link=self.source/'linked.bin'
        try:link.symlink_to(self.source/'data.bin')
        except OSError:self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError):pack.inventory(self.mapping)
        self.mapping[0]['sourcepath']=str(link)
        self.mapping[0]['kind']='auxiliary'
        with self.assertRaises(ValueError):pack.inventory(self.mapping)

    def test_rejects_duplicate_archive_names(self):
        with self.assertRaises(ValueError):pack.inventory(self.mapping+self.mapping)

    def test_existing_output_is_never_changed(self):
        self.output.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):pack.package(self.mapping,self.output)
        self.assertEqual(self.output.read_bytes(),b'keep')

    def test_rejects_output_inside_source(self):
        with self.assertRaises(ValueError):pack.package(self.mapping,self.source/'result.tar.gz')

    def test_hardlinks_are_portable_regular_copies(self):
        import os
        os.link(self.source/'data.bin',self.source/'linked.bin')
        pack.package(self.mapping,self.output)
        with tarfile.open(self.output,'r:gz') as archive:
            self.assertTrue(archive.getmember('completed/full10m/linked.bin').isfile())

    def test_source_change_prevents_publication(self):
        real=pack.write_archive
        def changed(*args):
            real(*args)
            (self.source/'data.bin').write_bytes(b'changed')
        with mock.patch.object(pack,'write_archive',side_effect=changed):
            with self.assertRaises(ValueError):pack.package(self.mapping,self.output)
        self.assertFalse(self.output.exists())
        self.assertTrue(Path(str(self.output)+'.partial').exists())
        self.assertTrue(Path(str(self.output)+'.failure.json').exists())

    def test_size_limit_keeps_partial_without_splitting(self):
        with self.assertRaises(ValueError):pack.package(self.mapping,self.output,max_bytes=1)
        self.assertFalse(self.output.exists())
        self.assertTrue(Path(str(self.output)+'.partial').exists())

    def test_archive_payload_mismatch_rejected(self):
        files=pack.inventory(self.mapping)
        for row in files:row['sha256']=pack.hash_source(row)
        partial=self.root/'bad.tar.gz'
        pack.write_archive(partial,files,{'format':'synthetic'})
        files[0]['sha256']='0'*64
        with self.assertRaises(ValueError):pack.verify_archive(partial,files,{'format':'synthetic'})

    def test_empty_directories_are_preserved(self):
        (self.source/'empty').mkdir()
        pack.package(self.mapping,self.output)
        with tarfile.open(self.output,'r:gz') as archive:
            self.assertTrue(archive.getmember('completed/full10m/empty').isdir())

    def test_cli_full_cycle(self):
        mapping=self.root/'mapping.json';mapping.write_text(json.dumps(self.mapping))
        self.assertEqual(pack.main(['--mapping-json',str(mapping),'--output',str(self.output)]),0)


if __name__=='__main__':unittest.main()
