# Closed full-data zero20 child — recoverable training checkpoint

This archive preserves the completed first full-data zero-initialized training run only. The recorded zero child771830 actually returned0 and was reaped by its parent controller. Its original summary is completed20epochs/input_integritypassed,1,000,000 training rows and4,149 validation rows. The outer orchestration tool47264 was still running the separate warm-start run at metadata-preflight time; no outer completion is asserted and no live warm files are included.

Every initial+20epoch checkpoint, export (.inc/.bin/.json), original per-epoch report, input-manifest snapshot and final summary is retained. Checkpoints preserve original optimizer/RNG/model state without deserialization during packaging. This packaging did not load any model or compute new losses. All21 export hashes were authenticated against original metadata. Original stdout/stderr, command/START/childresult, fixed PROTOCOL/DATA-GATE/preparation-closure snapshot, actual controller/selector source/reviews, preregistered selection rule and exact ten frozen functional source files are included.

The zero-run best recorded on the ORIGINAL4,149-row selection set is epoch3, teacherMSE0.006025381044581158. It is a per-run selection result, not the final selected network, independent heldout evidence or Elo evidence. The warm run remains separate and the preregistered final selector must wait for both actual closures. The accepted shipped network and search source remain unchanged. No independent-audit data or model outputs were read by this archive task. The initial preflight verifier incorrectly expected compact final stdout to equal the entire summary. Its failed report and isolated corrected report are preserved; the corrected check matches the intended status/hce_baseline/best fields without rerunning training. Evidence limitation: the initial failed preflight used tool stdin; its complete initial source and locally redirected raw streams were not captured. Its actual offending assertion and combined tool-response quote are retained, explicitly labeled as saved after execution. An isolated corrected checker was then saved before execution and actually ran exit0 with its own original command/stdout/stderr/result. The evidence-limitations receipt distinguishes these histories without fabricating missing logs. This limitation does not affect the original frozen trainer/controller source, raw training streams, exported checkpoints or actual child closure.

Main data manifest SHA:0bce5a466e51449dace54bd65f38a0ff2c79a7e0755a963096fa97fb1ea39216. Datasets are deliberately not duplicated. Recover the already verified/published full prepared-data archive from:
https://github.com/couns0538-sketch/dwqww/tree/d4ee5cd6eb2785f7425719ab497080e9fef64246/validation/nnue-pipeline-20261023/full-prepared-data-recovery-attempt1
Its ARCHIVE-MANIFEST SHA is b21a1bd10c6c4cdc0c328d75676edf4f4bd75965e7fd438ad60860637d083667. Follow its README/numbered parts and raw-legacy recovery references. The included data-recovery reference preserves exact identities. Source branch:
https://github.com/couns0538-sketch/dwqww/tree/forge/nnue-pipeline-20261023
Original engine source1ab50b2d and executed training protocol commit e52ea1b0 are explicit in DEPENDENCIES.json; the archive freezes actual ten source bytes by SHA so a later branch update cannot change the experiment.

Every ZIP member, including CONTENT-MANIFEST, is bound by ARCHIVE-MANIFEST by path/bytes/mode/SHA. Packaging physically reassembles its31MiB-or-smaller parts and streams every member/CRC/path/mode/hash check, then rehashes every original source. No payload execution occurs during readback. Historical absolute paths require explicit remapping when restoring elsewhere. Recover using standard-library Python after authenticating the external manifest SHA from Git:

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

Use a NEW extraction directory. Preserve all failed approaches and original receipts. This archive promotes no network and proves no playing-strength gain.
