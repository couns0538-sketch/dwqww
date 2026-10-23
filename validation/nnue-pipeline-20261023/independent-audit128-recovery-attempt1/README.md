# Forge NNUE independent audit128 recovery checkpoint

This is a CLOSED, UNUSED, UNEVALUATED independent audit. No model forwards, NNUE outputs, model losses, training, tuning, candidate selection or Elo inference occurred. Root must freeze exactly one final full-data candidate solely from the original4,149-position validation before evaluating this separate audit once. All arrays named train are UNUSED and must remain unused.

The audit was preregistered before generation. Seed20271023 for both generation and game-hash split has a possible ten-attempt opening-seed range disjoint from the original256-game run. Actual original engine02d6ba26/source1ab50b2d/shipped network41487f32 generated128 completed games with2 workers, Threads1, Hash16, OwnBookfalse,5000nodes. Both owned native engines closed cleanly; the complete original raw UCI logs, generatedJSONL and exact executed generator902b1c70/helpers are included.

Original fresh preparation contains8,899 validation positions and1,321 UNUSED train positions. There are111 declared validation partition gameIDs, but109 games have represented eligible rows. Do not infer111 represented games. The separate raw HCE-only replay verified all10,220 original prepared positions against the actual frozen native probe d2f400df, retaining every original stdin/stdout/stderr and process receipt. HCE integer scores and unordered active perspective feature sets match exactly; no NNUE inference was requested.

The first audit finalizer (actual session86162) correctly stopped on the original FAILED main closure marker before masking. The main data job itself had actually exited0; its checker incorrectly demanded retained rows from all200 assigned training games.196 retained games and4 valid zero-row games are documented. Root explicitly authorized a separately preserved v2 closure gate and second audit controller; neither data generation nor training was repeated. All original failures, source versions, tests, logs, protocols and corrected success receipts remain present.

The first actual mask execution (controller33309 exit0) removed18 audit validation rows whose first-four-FEN key occurred in authenticated1M main training or original4,149 validation recipes. The masked audit contains8,881 rows from109 represented games (111 declared partition IDs). Every array and provenance row is an exact ordered subset of original data. The1,321 UNUSED train arrays are byte-identical copies.128 authentic audit gameIDs are disjoint from the canonical256 original gameIDs. Legacy identities in main training remain explicitly unknown; none were invented. Masked manifest SHA:d7a9a4e01cfcbc1c0bd25ec0aec9d38cf8786ce4309dba9b4d6bef6e659c7c74.

The main1M arrays, full train/validation recipes and3,038 native receipts are not duplicated. Recover them from full-prepared-data-recovery-attempt1/ using its authoritative ARCHIVE-MANIFEST.json, README and forge-nnue-full-prepared-20261023.zip.001 onward. That separate archive was still packaging at this audit build time: require its own verified PASS_ARCHIVE_READBACK and actual tool closure; do not treat this reference as a success claim. The included main manifest and MAIN-DATA-RECOVERY-REFERENCE.json bind exact recipe SHAs/counts for independent overlap inspection. Raw888MB legacy inputs are excluded; their separate recovery reference is in the main archive.

ARCHIVE-MANIFEST.json binds every member (including CONTENT-MANIFEST.json) by path, bytes, mode and SHA. CONTENT-MANIFEST lists source payload mappings without its own self-hash; the external full manifest closes that relation. Packaging reassembles its actual31MiB-or-smaller parts and verifies every member/CRC/path/mode/hash plus unchanged original source bytes. All sources are preserved; no recovered code is executed during readback. Historical provenance uses original absolute paths: explicitly remap them when replaying elsewhere. The archived native binary is Linux, not a Windows engine build.

Recover on Linux or Windows with the following standard-library code after authenticating ARCHIVE-MANIFEST.json against the published Git SHA:

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
        assert not name.is_absolute() and '..' not in name.parts and '\\\\' not in info.filename
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

Use a NEW extraction directory. This archive preserves evidence and data only; it is not a promoted network or an Elo result.
