# Forge NNUE full prepared-data recovery checkpoint

This checkpoint contains the original successful full preparation, its authentic generated games and UCI traces, the unchanged fresh-only reference dataset, actual frozen preparer/probe and generator-v1 source, reviewed current data tools, and all original data-workflow logs. The original false closure assertion and its FAILED marker are preserved; FULL-PREP-CLOSED-v2.json is the corrected successful gate. No engine strength or Elo improvement is asserted.

The main data manifest SHA-256 is 0bce5a466e51449dace54bd65f38a0ff2c79a7e0755a963096fa97fb1ea39216. It binds 1,000,000 training positions (14,895 fresh, 985,105 legacy) and the unchanged 4,149 held-out positions from 56 represented validation games. There are 200 assigned training-game IDs, of which 196 have retained rows; the four zero-retained games and exact reasons are recorded in integrity-v2. Legacy game IDs and original teacher source identity are unknown and never invented. Legacy records are training only; exact first-four-FEN validation keys were excluded from every training source.

All nine legacy inputs were fully examined (13,500,000 rows). The declared seed-20261023 Algorithm R reservoir sampled eligible unique legacy positions across all nine files, rather than a prefix. Native HCE/features came from the actual Forge C++ probe. All 3,038 successful native batch receipts are retained, but their full derived stdin/stdout streams were deliberately not stored; receipts bind byte counts and stream hashes. Original input text, source-line recipes, native probe and the build/source identities permit replay. Failure paths retained original streams. This is an evidence limitation, not a claim that successful native streams are present.

The 888 MB legacy text and original uploaded archive bytes are not duplicated here. Recover the original six parts from couns0538-sketch/dwqww at validation/nnue-pipeline-20261023/original-selfplay-parts, following the included reference MANIFEST/README and legacy-input-inspection hashes. Combined original 7z SHA-256: 3900947d2555b3fce43132f8b4b4cbe2e0bb85ee07df18118f138fde674ec6f4. The genuine 256-game generation used archived frozen generator-v1; newer reviewed failure-only guards were added after that run and are not relabeled as the executed generator.

Recovery uses Python's standard library on Linux or Windows. Download ARCHIVE-MANIFEST.json and every numbered .zip.00N part into one new directory. Authenticate the manifest against the Git-published SHA first. Concatenate parts in its declared order; verify every part's bytes/SHA and the reconstructed archive's bytes/SHA. The code below verifies all member bytes, CRCs, paths and permission bits before extracting into a NEW directory. It does not execute any recovered code. Paths inside historical provenance are original absolute workspace paths; retain them as evidence and explicitly remap paths when replaying on a different machine. The archived Linux executable is not a Windows engine build.

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

NPZ arrays have exactly features:int16[N,2,32] with -1 padding, hce:int32[N], score:int32[N], result_stm:float32[N]. Scores/HCE/results use side-to-move POV. The retained accepted residual architecture is unchanged (768→128×2 SCReLU). Use the shared strict residual_train.load_prepared_data validator after restoring/remapping declared source paths. Source and network remain in Git; this archive is a data/evidence checkpoint, not a promoted network.
