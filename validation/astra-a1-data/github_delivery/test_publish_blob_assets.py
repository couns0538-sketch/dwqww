"""Original bounded fixtures for the GitHub blob-to-release delivery contract.
IDEA_SOURCE: user evidence-preservation requirements and GitHub API metadata.
"""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('publish_blob_assets.py')
REPO = 'couns0538-sketch/dwqww'
TAG = 'astra-a1-data-results-20261030'
RID = 428684041


def blob(payload):
    sha = hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
    return {'sha': sha, 'size': len(payload), 'encoding': 'base64',
            'content': base64.b64encode(payload).decode()}


class FakeAPI:
    def __init__(self, blobs, existing=()):
        self.blobs = blobs
        self.assets = list(existing)
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        if '/git/blobs/' in path:
            return self.blobs[path.rsplit('/', 1)[1]]
        if '/assets?' in path:
            return self.assets
        return {'id': RID, 'tag_name': TAG}


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'publisher not implemented')
        spec = importlib.util.spec_from_file_location('publisher', SCRIPT)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.root = Path(tempfile.mkdtemp(prefix='forge-github-delivery-test-'))
        print('retained fixture ' + str(self.root), file=sys.stderr)
        self.payload = b'original\x00binary\r\npayload\xff'
        self.chunks = [self.payload[:9], self.payload[9:]]
        offset = 0
        entries, blobs = [], {}
        for part in self.chunks:
            item = blob(part); blobs[item['sha']] = item
            entries.append({'sha': item['sha'], 'offset': offset, 'bytes': len(part),
                            'sha256': hashlib.sha256(part).hexdigest()})
            offset += len(part)
        self.asset = {'name': 'forge_test_20261030.bin', 'bytes': len(self.payload),
                      'sha256': hashlib.sha256(self.payload).hexdigest(), 'chunks': entries}
        self.data = {'format': 'forge-github-blob-delivery-v1', 'repository': REPO,
                     'release_id': RID, 'release_tag': TAG, 'assets': [self.asset]}
        self.manifest = self.root / 'manifest.json'
        self.save()
        self.api = FakeAPI(blobs)
        self.uploads = []

    def save(self):
        self.manifest.write_text(json.dumps(self.data))

    def upload(self, path, repository, tag, logs):
        self.assertEqual((repository, tag), (REPO, TAG))
        content = path.read_bytes(); self.uploads.append(content)
        self.api.assets.append({'name': path.name, 'size': len(content), 'state': 'uploaded',
                                'digest': 'sha256:' + hashlib.sha256(content).hexdigest()})

    def run_publish(self):
        return self.tool.publish(self.manifest, self.root / 'output', self.api, self.upload)

    def test_binary_reassembly_upload_and_remote_digest(self):
        receipt = self.run_publish()
        self.assertEqual(receipt['status'], 'PASS')
        self.assertEqual(self.uploads, [self.payload])
        self.assertEqual((self.root / 'output/assets' / self.asset['name']).read_bytes(), self.payload)
        self.assertEqual(receipt['assets'][0]['decision'], 'uploaded_verified')

    def test_exact_existing_asset_skips_upload_and_blob_fetch(self):
        self.api.assets = [{'name': self.asset['name'], 'size': len(self.payload),
                            'state': 'uploaded', 'digest': 'sha256:' + self.asset['sha256']}]
        receipt = self.run_publish()
        self.assertEqual(receipt['assets'][0]['decision'], 'existing_verified')
        self.assertEqual(self.uploads, [])
        self.assertFalse(any('/git/blobs/' in path for path in self.api.calls))

    def test_existing_name_collision_fails_without_upload(self):
        self.api.assets = [{'name': self.asset['name'], 'size': len(self.payload),
                            'state': 'uploaded', 'digest': 'sha256:' + '0' * 64}]
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.run_publish()
        self.assertEqual(self.uploads, [])
        self.assertEqual(json.loads((self.root / 'output/receipt.json').read_text())['status'], 'FAIL')

    def test_corrupt_blob_sha1_and_sha256_rejected(self):
        first = self.asset['chunks'][0]
        response = self.api.blobs[first['sha']]
        response['content'] = base64.b64encode(b'x' * first['bytes']).decode()
        with self.assertRaisesRegex(ValueError, 'digest'):
            self.run_publish()
        self.assertEqual(self.uploads, [])

    def test_bad_repository_tag_names_offsets_and_extra_chunks_rejected(self):
        mutations = [('repository', 'attacker/repo'), ('release_tag', 'wrong-tag')]
        for key, value in mutations:
            data = json.loads(json.dumps(self.data)); data[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.tool.validate(data)
        for name in ('../outside.bin', 'bad\nname', 'CON.zip', 'bad\\file'):
            data = json.loads(json.dumps(self.data)); data['assets'][0]['name'] = name
            with self.subTest(name=name), self.assertRaises(ValueError): self.tool.validate(data)
        for mode in ('offset', 'extra', 'sha'):
            data = json.loads(json.dumps(self.data)); chunks = data['assets'][0]['chunks']
            if mode == 'offset': chunks[1]['offset'] += 1
            if mode == 'extra': chunks.append(chunks[-1].copy())
            if mode == 'sha': chunks[0]['sha'] = 'not-a-git-sha'
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.tool.validate(data)

    def test_manifest_changes_are_not_reported_as_success(self):
        original = self.upload
        def changing_upload(*args):
            original(*args)
            self.manifest.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            self.tool.publish(self.manifest, self.root / 'output', self.api, changing_upload)
        self.assertEqual(json.loads((self.root / 'output/receipt.json').read_text())['status'], 'FAIL')

    def test_existing_output_is_not_modified(self):
        out = self.root / 'output'; out.mkdir(); (out / 'sentinel').write_bytes(b'old')
        with self.assertRaises(FileExistsError): self.run_publish()
        self.assertEqual([p.name for p in out.iterdir()], ['sentinel'])

    def test_more_than_128_small_chunks_supported_for_large_delivery(self):
        item = blob(b'x'); data = json.loads(json.dumps(self.data)); asset = data['assets'][0]
        asset['bytes'] = 256; asset['sha256'] = hashlib.sha256(b'x' * 256).hexdigest()
        asset['chunks'] = [{'sha': item['sha'], 'bytes': 1, 'offset': i,
                            'sha256': hashlib.sha256(b'x').hexdigest()} for i in range(256)]
        self.tool.validate(data)

    def test_valid_git_blob_with_wrong_manifest_sha256_is_rejected(self):
        self.asset['chunks'][0]['sha256'] = '0' * 64; self.save()
        with self.assertRaisesRegex(ValueError, 'digest'): self.run_publish()
        self.assertEqual(self.uploads, [])

    def test_wrong_server_digest_after_upload_is_not_success(self):
        original = self.upload
        def wrong_server_digest(*args):
            original(*args); self.api.assets[-1]['digest'] = 'sha256:' + '0' * 64
        with self.assertRaisesRegex(ValueError, 'server digest'):
            self.tool.publish(self.manifest, self.root / 'output', self.api, wrong_server_digest)


if __name__ == '__main__':
    unittest.main(verbosity=2)
