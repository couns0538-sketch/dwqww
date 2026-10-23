import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import stat
import unittest
from unittest.mock import patch
import zipfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import multipart_dataset as tool
except ModuleNotFoundError:
    tool = None


class MultipartTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(tool, 'Streaming multipart helper is missing')
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self):
        records = []
        for name, data in [('empty', b''), ('one', b'x'), ('boundary', bytes(range(113))), ('many', bytes(range(256))*5)]:
            path = self.root/name; path.write_bytes(data); path.chmod(0o640)
            records.append({'source':str(path), 'member':'data/'+name,
                            'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data)})
        source = self.root/'declarations.json'
        source.write_text(json.dumps({'status':'CLOSED_INPUTS_FROZEN', 'files':records,
            'aliases':[{'source':str(self.root/'many'), 'member':'audit/train.npz', 'target':'data/many'}]}))
        return source

    def test_small_crossings_zip64_and_seekable_readback_without_full_zip(self):
        with patch.object(zipfile, 'ZIP64_LIMIT', 64):
            manifest = tool.pack(self.fixture(), self.root/'parts', part_bytes=113)
            result = tool.verify(self.root/'parts/RECOVERY-MANIFEST.json', tool.sha(self.root/'parts/RECOVERY-MANIFEST.json'))
        self.assertEqual(result['members_verified'], 4)
        self.assertGreater(len(manifest['parts']), 10)
        self.assertTrue(all(0 < part['bytes'] <= 113 for part in manifest['parts']))
        self.assertEqual(list((self.root/'parts').glob('*.zip')), [])
        original = b''.join((self.root/'parts'/part['name']).read_bytes() for part in manifest['parts'])
        with tool.PartsReader(self.root/'parts', manifest['parts']) as stream:
            stream.seek(105); self.assertEqual(stream.read(250), original[105:355])
            stream.seek(-22, 2); self.assertEqual(stream.read(), original[-22:])
            stream.seek(0); stream.seek(112, 1); self.assertEqual(stream.read(3), original[112:115])

    def test_corruption_and_reordered_parts_fail_closed(self):
        manifest = tool.pack(self.fixture(), self.root/'parts', part_bytes=113)
        manifest_path = self.root/'parts/RECOVERY-MANIFEST.json'; digest = tool.sha(manifest_path)
        first = self.root/'parts'/manifest['parts'][0]['name']; original = first.read_bytes()
        first.write_bytes(bytes([original[0]^1])+original[1:])
        with self.assertRaisesRegex(ValueError, 'hash'): tool.verify(manifest_path, digest)
        first.write_bytes(original)
        manifest['parts'][0], manifest['parts'][1] = manifest['parts'][1], manifest['parts'][0]
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'order|part'): tool.verify(manifest_path, tool.sha(manifest_path))

    def test_alias_restore_and_declared_hash_guard(self):
        source = self.fixture(); tool.pack(source, self.root/'parts', part_bytes=113)
        manifest_path = self.root/'parts/RECOVERY-MANIFEST.json'
        tool.restore(manifest_path, tool.sha(manifest_path), self.root/'restored')
        self.assertEqual((self.root/'restored/audit/train.npz').read_bytes(), bytes(range(256))*5)
        self.assertEqual((self.root/'restored/data/many').stat().st_ino, (self.root/'restored/audit/train.npz').stat().st_ino)
        declarations = json.loads(source.read_text()); declarations['files'][1]['sha256'] = '0'*64
        source.write_text(json.dumps(declarations))
        with self.assertRaisesRegex(ValueError, 'source|hash'): tool.pack(source, self.root/'failed', part_bytes=113)
        self.assertFalse((self.root/'failed/RECOVERY-MANIFEST.json').exists())

    def test_unsafe_member_and_symlink_source_reject_before_commit(self):
        source = self.fixture(); declarations = json.loads(source.read_text())
        declarations['files'][0]['member'] = '../escape'
        source.write_text(json.dumps(declarations))
        with self.assertRaises(ValueError): tool.pack(source, self.root/'bad-name', part_bytes=113)
        source = self.fixture(); declarations = json.loads(source.read_text())
        link = self.root/'link'; link.symlink_to(self.root/'one')
        declarations['files'][1]['source'] = str(link);source.write_text(json.dumps(declarations))
        with self.assertRaisesRegex(ValueError, 'symlink|regular'): tool.pack(source, self.root/'bad-link', part_bytes=113)

    def test_dot_path_rejects(self):
        try:
            with self.assertRaises(ValueError): tool.safe_name('.')
        except IndexError: self.fail('Dot member reaches an unchecked empty path')
    def test_late_source_or_declaration_change_rejects(self):
        actual_verify = tool.verify_records
        for changed in ('source','declarations'):
            with self.subTest(changed=changed):
                declarations = self.fixture()
                def mutate_after_verify(*args):
                    result = actual_verify(*args)
                    if changed == 'source': (self.root/'one').write_bytes(b'y')
                    else: declarations.write_text(declarations.read_text()+' ')
                    return result
                with patch.object(tool, 'verify_records', side_effect=mutate_after_verify):
                    with self.assertRaisesRegex(ValueError, 'source|declaration'):
                        tool.pack(declarations,self.root/('late-'+changed),part_bytes=113)
                self.assertFalse((self.root/('late-'+changed)/'RECOVERY-MANIFEST.json').exists())

    def test_namespace_prefix_and_casefold_collision_reject(self):
        for name in ('data', 'DATA/one'):
            with self.subTest(name=name):
                source = self.fixture(); declarations = json.loads(source.read_text())
                declarations['aliases'].append({'source':str(self.root/'one'),'member':name,'target':'data/one'})
                source.write_text(json.dumps(declarations))
                with self.assertRaisesRegex(ValueError, 'collision|namespace'):
                    tool.pack(source,self.root/('collision-'+name.replace('/','-')),part_bytes=113)

    def test_restore_reuses_the_same_verified_manifest_snapshot(self):
        tool.pack(self.fixture(),self.root/'parts',part_bytes=113)
        path = self.root/'parts/RECOVERY-MANIFEST.json'; digest = tool.sha(path)
        changed = json.loads(path.read_text()); changed['aliases'][0]['path'] = 'unexpected-copy.npz'
        original_open = Path.open; mutated = False
        def replace_after_binary_read(target, mode='r', *args, **kwargs):
            if target != path or mode != 'rb': return original_open(target,mode,*args,**kwargs)
            @contextmanager
            def replaced():
                nonlocal mutated
                with original_open(target, mode, *args, **kwargs) as stream: yield stream
                if not mutated:
                    mutated = True
                    with original_open(path,'w') as stream: json.dump(changed,stream)
            return replaced()
        with patch.object(Path,'open',replace_after_binary_read):
            tool.restore(path,digest,self.root/'restored')
        self.assertTrue((self.root/'restored/audit/train.npz').is_file())
        self.assertFalse((self.root/'restored/unexpected-copy.npz').exists())

    def test_postcommit_directory_fsync_failure_reports_visible_manifest_honestly(self):
        original_fsync = os.fsync
        def fail_directory(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode): raise OSError('simulated directory fsync failure')
            return original_fsync(descriptor)
        with patch.object(os,'fsync',side_effect=fail_directory):
            with self.assertRaisesRegex(OSError,'directory fsync'):
                tool.pack(self.fixture(),self.root/'parts',part_bytes=113)
        manifest_path = self.root/'parts/RECOVERY-MANIFEST.json'
        self.assertTrue(manifest_path.exists())
        failure = json.loads((self.root/'parts/FAILURE.json').read_text())
        self.assertEqual(failure['status'],'COMMITTED_VERIFIED_DURABILITY_UNCONFIRMED')
        self.assertEqual(failure['manifest_sha256'],tool.sha(manifest_path))


if __name__ == '__main__': unittest.main(verbosity=2)
