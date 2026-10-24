#!/usr/bin/env python3
"""Exercise the bounded oracle runner with real subprocess byte streams."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).with_name("nnue_million_oracle.py")


class OracleRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def producer(self, name, mode="equal"):
        path = self.root / name
        path.write_text("""#!/usr/bin/env python3
import struct, sys, time
n = int(sys.argv[sys.argv.index('--positions') + 1])
record_size = 104 + 2 * (512 * 4 + 8)
h = [0x314f4d4e, 1, 256, record_size, n, 0, 0x85a308d3, 0x243f6a88,
     0x1f80, 0, 192, 10, 2, 0, 0, 0]
data = bytearray(struct.pack('<16I', *h))
for i in range(n):
    data += struct.pack('<QQIIIIII', i, i * 17, 0, i, 2, 0, i % 2, 0)
    data += bytes([0] * 64)
    for j in range(2):
        data += struct.pack('<512fII', *([0.25 + i / 4096] * 512), i, 1)
t = [0] * 64
t[0:16] = [0x544f4d4e, 1, n, 0, n, 0, n-1, 0, n-1, 0, n-1, 0, 1, 0, 1, 0]
t[16:42] = [1] * 26
t[16:18] = [(n-1)//2, n-1-(n-1)//2]
data += struct.pack('<64I', *t)
mode = MODE
if mode == 'float': data[64 + 104] ^= 1
if mode == 'eval': data[64 + 104 + 2048] ^= 1
if mode == 'truncate': data = data[:-17]
sys.stdout.buffer.write(data)
sys.stdout.buffer.flush()
if mode == 'exit': sys.exit(7)
if mode == 'hang': time.sleep(30)
""".replace("MODE", repr(mode)))
        path.chmod(0o700)
        return path

    def compare(self, off_mode="equal", on_mode="equal", output_name="results", reference=None):
        self.assertTrue(RUNNER.exists(), "bounded oracle runner is not implemented")
        off = self.producer("off", off_mode)
        on = self.producer("on", on_mode)
        out = self.root / output_name
        command = [sys.executable, str(RUNNER), "--off", str(off),
                   "--on", str(on), "--positions", "128",
                   "--chunk-records", "31", "--timeout-seconds", "1", "--output", str(out)]
        if reference is not None:
            command += ["--dedup-reference-result", str(reference)]
        result = subprocess.run(command,
                                capture_output=True, text=True)
        self.assertTrue((out / "result.json").exists(), result.stderr)
        return result, out, json.loads((out / "result.json").read_text())

    def test_equal_streams_are_compared_hashed_and_losslessly_retained(self):
        result, out, report = self.compare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["records"], 128)
        self.assertEqual(report["off"]["sha256"], report["on"]["sha256"])
        for side in ("off", "on"):
            reconstructed = b"".join(gzip.decompress((out / c[side]["gzip"]).read_bytes())
                                     for c in report["chunks"])
            self.assertEqual(hashlib.sha256(reconstructed).hexdigest(), report[side]["sha256"])
        self.assertTrue(all(c["raw_cmp_exit"] == 0 for c in report["chunks"]))
        self.assertTrue(all("gzip_roundtrip_sha256" in c[side]
                            for c in report["chunks"] for side in ("off", "on")),
                        "each compressed original must be round-trip verified")
        self.assertTrue(all(c[side]["gzip_roundtrip_sha256"] == c[side]["raw_sha256"]
                            for c in report["chunks"] for side in ("off", "on")))
        self.assertEqual([c["cmp_exit"] for c in report["negative_controls"]], [1, 1])

    def test_changed_accumulator_bit_is_rejected_and_preserved(self):
        result, out, report = self.compare(on_mode="float")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["chunks"][0]["raw_cmp_exit"], 1)
        self.assertTrue((out / "chunk-000000.on.raw").exists())

    def test_changed_eval_integer_bit_is_rejected(self):
        result, _, report = self.compare(on_mode="eval")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["chunks"][0]["raw_cmp_exit"], 1)

    def test_identically_truncated_streams_are_rejected(self):
        result, _, report = self.compare("truncate", "truncate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("truncated", report["error"])
        self.assertEqual(report["off"]["bytes"], 64 + 128 * 4216 + 256 - 17)

    def test_nonzero_producer_exit_after_equal_bytes_is_rejected(self):
        result, _, report = self.compare(on_mode="exit")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["on"]["exit_code"], 7)
        self.assertIn("producer", report["error"])

    def test_hung_producer_is_killed_and_reported_with_actual_exit_code(self):
        result, _, report = self.compare(on_mode="hang")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timeout", report["error"])
        self.assertLess(report["on"]["exit_code"], 0)

    def test_fresh_equal_run_can_deduplicate_to_verified_prior_archives(self):
        result, old, prior = self.compare()
        self.assertEqual(result.returncode, 0, result.stderr)
        old_manifest = (old / "result.json").read_bytes()
        result, new, report = self.compare(output_name="second", reference=old / "result.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((old / "result.json").read_bytes(), old_manifest)
        self.assertEqual(report["off"]["sha256"], prior["off"]["sha256"])
        for current, canonical in zip(report["chunks"], prior["chunks"]):
            proof = current["reference_dedup"]
            self.assertEqual(proof["canonical_sha256_before"], proof["canonical_sha256_after"])
            for side in ("off", "on"):
                self.assertEqual((new / current[side]["gzip"]).stat().st_ino,
                                 (old / canonical["off"]["gzip"]).stat().st_ino)
        self.assertEqual(report["dedup_reference_result"]["sha256"],
                         hashlib.sha256(old_manifest).hexdigest())

    def test_corrupt_canonical_archive_is_rejected_without_losing_new_outputs(self):
        result, old, prior = self.compare()
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = old / prior["chunks"][0]["off"]["gzip"]
        archive.chmod(0o644)
        bad = bytearray(archive.read_bytes())
        bad[-1] ^= 1
        archive.write_bytes(bad)
        archive.chmod(0o444)
        result, new, report = self.compare(output_name="second", reference=old / "result.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical", report["error"])
        self.assertTrue((new / "chunk-000000.off.raw").exists())
        self.assertTrue((new / "chunk-000000.on.raw").exists())
        self.assertEqual(archive.read_bytes(), bytes(bad))


if __name__ == "__main__":
    unittest.main()
