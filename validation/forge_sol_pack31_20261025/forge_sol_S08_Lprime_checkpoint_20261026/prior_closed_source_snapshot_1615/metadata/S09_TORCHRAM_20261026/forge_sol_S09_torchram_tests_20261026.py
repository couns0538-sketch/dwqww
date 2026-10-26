"""Toy-only gzip/hash/sealing checks. Never reads the real archive or Torch."""
import errno
import fcntl
import gzip
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import contextlib
import io

ROOT=Path(__file__).resolve().parent
TOOL=ROOT/'forge_sol_S09_torchram_probe_20261026.py'
if TOOL.exists():
    spec=importlib.util.spec_from_file_location('torchram_probe',TOOL)
    tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
else:tool=None


class ToyMemfdTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(tool,'sealed gzip-to-memfd probe is not implemented')
        self.root=Path(tempfile.mkdtemp(prefix='forge_sol_S09_toy_',dir=ROOT))
        self.raw=bytes(range(256))*31; self.path=self.root/'toy.gz'
        self.path.write_bytes(gzip.compress(self.raw,mtime=0))
        self.kw={'compressed_size':self.path.stat().st_size,
                 'compressed_sha256':hashlib.sha256(self.path.read_bytes()).hexdigest(),
                 'raw_size':len(self.raw),'raw_sha256':hashlib.sha256(self.raw).hexdigest()}
    def tearDown(self):
        if hasattr(self,'root'):shutil.rmtree(self.root)
    def load(self,**changes):return tool.sealed_memfd_from_gzip(self.path,**dict(self.kw,**changes))

    def test_roundtrip_exact_bytes_offset_and_all_immutable_seals(self):
        fd=self.load()
        try:
            self.assertEqual(os.read(fd,len(self.raw)+1),self.raw)
            flags=fcntl.fcntl(fd,1034)  # Linux UAPI F_GET_SEALS
            wanted=0x000f
            self.assertEqual(flags&wanted,wanted)
        finally:os.close(fd)

    def test_write_grow_shrink_and_reseal_fail_with_permission_error(self):
        fd=self.load()
        try:
            for action in [lambda:os.write(fd,b'x'),lambda:os.ftruncate(fd,len(self.raw)+1),
                           lambda:os.ftruncate(fd,len(self.raw)-1),lambda:fcntl.fcntl(fd,1033,0x0008)]:
                with self.assertRaises(OSError) as caught:action()
                self.assertEqual(caught.exception.errno,errno.EPERM)
        finally:os.close(fd)

    def test_compressed_hash_and_size_mismatches_fail_closed(self):
        for change in [{'compressed_sha256':'0'*64},{'compressed_size':self.kw['compressed_size']-1},
                       {'compressed_size':self.kw['compressed_size']+1}]:
            with self.assertRaisesRegex(ValueError,'compressed'):self.load(**change)

    def test_raw_hash_and_size_mismatches_fail_closed(self):
        for change in [{'raw_sha256':'0'*64},{'raw_size':len(self.raw)-1},{'raw_size':len(self.raw)+1}]:
            with self.assertRaisesRegex(ValueError,'raw'):self.load(**change)

    def test_failed_validation_does_not_leak_memfds_or_change_source(self):
        before=self.path.read_bytes();fds=len(os.listdir('/proc/self/fd'))
        for _ in range(3):
            with self.assertRaises(ValueError):self.load(raw_sha256='0'*64)
        self.assertEqual(len(os.listdir('/proc/self/fd')),fds)
        self.assertEqual(self.path.read_bytes(),before)

    def test_corrupt_gzip_with_matching_outer_hash_is_rejected(self):
        bad=b'not gzip';self.path.write_bytes(bad)
        with self.assertRaises(ValueError):self.load(compressed_size=len(bad),compressed_sha256=hashlib.sha256(bad).hexdigest())

    def test_existing_output_is_refused_before_real_candidate_work(self):
        out=self.root/'existing';out.mkdir();marker=out/'marker';marker.write_bytes(b'unchanged')
        error=io.StringIO()
        with contextlib.redirect_stderr(error):result=tool.main(['--authorized-build-window','f022-BUILD','--out',str(out)])
        self.assertEqual(result,2)
        self.assertEqual(marker.read_bytes(),b'unchanged')
        self.assertEqual(list(out.iterdir()),[marker])

    def test_evidence_archive_is_deterministic_exact_and_hash_verified(self):
        source=self.root/'proof.bin';source.write_bytes(self.raw)
        expected=hashlib.sha256(self.raw).hexdigest()
        self.assertEqual(tool.verified_file_hash(source,expected),expected)
        with self.assertRaisesRegex(ValueError,'hash'):tool.verified_file_hash(source,'0'*64)
        a=self.root/'a.gz';b=self.root/'b.gz'
        first=tool.preserve_evidence(source,a);second=tool.preserve_evidence(source,b)
        self.assertEqual(gzip.decompress(a.read_bytes()),self.raw)
        self.assertEqual(a.read_bytes(),b.read_bytes())
        self.assertEqual(first['raw_sha256'],expected)
        self.assertEqual(first['compressed_sha256'],second['compressed_sha256'])
        with self.assertRaises(FileExistsError):tool.preserve_evidence(source,a)


if __name__=='__main__':unittest.main(verbosity=2)
