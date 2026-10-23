# Linux selected-network qualification recovery

This archive retains BOTH original failed Linux profiles and the separate corrected-harness qualification. Original Release and ASan/UBSan each attempted all14 tests:13 passed, while forge_tests failed its depth8 start-position null-pruning counter assertion. Their failures remain original, not erased or reclassified. The bounded old/new-core diagnostic shows new NMP attempts/cutoffs at depth10; it is not a strength test.

Root replaced that evaluation-dependent coverage assertion with an explicit controlled two-node TT/null-child fixture. Complete old/new positive and private NMP-disabled negative controls are included under controlled-test-repair-proof. Any search.nmp-disabled.cpp/object/binary there is ONLY a deliberately defective isolated negative control, never the selected production engine or an accepted source change.

Selected production source is clean net-only commit6e9622fd5be18e0155fc3ed5fcf6c4586705cca6, network SHAa52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7. The corrected harness additionally uses exactly tests/tests.cpp from f4a1ed6be3921a024e0d876cac2433153a96c66c, SHA6dec8511d6107511cae182dc6169122b48b41e00c5033738f8b04ab027441dce. All74 source files were compared to that explicit contract. Original baseline1ab source differs only by selected weights and the documented corrected test. No production search/evaluation/header/tuning change is hidden in the harness repair.

Read corrected-harness-wrapper/FINAL-CLOSED.json and corrected-harness-trial/evidence/RESULT.json for the actual terminal result, first genuine new-net bench and repeat. Do not infer success merely from an archive. The original reviewed strict Linux runner and its explicit repaired variant, pinned tools, all command/stdin/stdout/stderr/result receipts, CMake/compile/link/test metadata, source bytes, complete four build trees (including tested forge/core/test binaries and original objects) are retained. No files within the enumerated included roots were excluded. Native binary roles/test execution must be read from original commands/results: a compiled forge_bench or compiler-ID executable was not automatically run by qualification.

ARCHIVE-MANIFEST.json enumerates every member's original path, size, mode and SHA256, and all explicit outside-scope exclusions. ZIP uses deflate6. Numbered parts are at most31MiB and were physically reassembled; every member's bytes/CRC/type/mode were checked from that reassembly, then all source files were rehashed unchanged. Original successful full-training native-derived streams are unrelated to this archive and were not reconstructed; their declared retention limits remain in the published data checkpoint.

Recover by downloading the published ARCHIVE-MANIFEST.json and .zip.001 onward into a new directory. Authenticate the manifest against Git, verify each part's declared bytes/SHA, concatenate strictly in manifest order, and verify the archive bytes/SHA before opening it. Validate exact unique member names, reject absolute/traversal/backslash/symlink paths, and stream-check every size/SHA/mode against the manifest before extracting to a NEW destination. README in the earlier full-prepared-data-recovery checkpoint contains a standard-library Python verification/extraction example using the same archive/parts/members schema. Preserve original absolute paths in provenance; explicitly remap replay paths on another machine rather than rewriting historical evidence. Do not execute recovered code automatically.

These are Linux GCC14 strict-float correctness/repeatability artifacts. They establish no native Windows/Ryzen qualification, NPS improvement, Elo gain, Stockfish result or promotion. No match/PGN evidence exists in this qualification because no match was run. The selected network/default acceptance decision remains with the separately frozen validation/strength protocol and root's report.

## Standalone standard-library recovery example

```python
import hashlib, json, os, pathlib, stat, zipfile
root = pathlib.Path('.')
m = json.loads((root / 'ARCHIVE-MANIFEST.json').read_text())
def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
archive = root / 'recovered.zip'
with archive.open('xb') as out:
    for part in m['parts']:
        p = root / part['name']
        assert p.stat().st_size == part['bytes'] and digest(p) == part['sha256']
        with p.open('rb') as f:
            for b in iter(lambda: f.read(1024*1024), b''): out.write(b)
assert archive.stat().st_size == m['archive']['bytes'] and digest(archive) == m['archive']['sha256']
expected = {v['path']: v for v in m['members']}
with zipfile.ZipFile(archive) as z:
    assert len(z.infolist()) == len(expected) and set(z.namelist()) == set(expected)
    for info in z.infolist():
        name = pathlib.PurePosixPath(info.filename)
        assert not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename
        assert not stat.S_ISLNK(info.external_attr >> 16)
        rec = expected[info.filename]
        h = hashlib.sha256(); size = 0
        with z.open(info) as f:
            for b in iter(lambda: f.read(1024*1024), b''): h.update(b); size += len(b)
        assert size == rec['bytes'] and h.hexdigest() == rec['sha256']
        assert stat.S_IMODE(info.external_attr >> 16) == rec['mode']
    target = root / 'restored-checkpoint'
    target.mkdir()  # Fails rather than overwriting an existing directory.
    z.extractall(target)
    if os.name != 'nt':
        for name, rec in expected.items(): (target / name).chmod(rec['mode'])
```
