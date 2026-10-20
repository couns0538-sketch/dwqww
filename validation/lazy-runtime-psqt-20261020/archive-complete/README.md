# Recoverable Forge6.4.19 evidence archive

The single archive process completed with exit0 and empty stderr. All1,762 frozen
originals (298,643,155bytes) matched beforecopy, afterstaging and afterarchive.
The unchangedtrustedhelper verified full split reassembly and all1,774payloads.
A fresh independent audit passed: both parts/combinedZIP/embeddedmanifest, all
1,774payloads against staging, and all1,762live originals directly against
archive bytes. Original/stage filemodes and299directory modes matched.
INDEPENDENT-ARCHIVE-AUDIT.json records its separate one-shot result.

Combined ZIP112,207,796bytes, SHA256:
`d90110e326c6d24c3045c8601ed4dd37ba7b9fbfc35c1bffcabddab6cf733f31`.
Two orderedparts contain67,108,864 and45,098,932bytes. RESULTS.json and the
externalmanifest identify allpayloads/parts; ARCHIVE-SHA256SUMS records actual
partnames and manifest. No redundant unsplitZIP is created in this output.

Scope includes the fullprototype/source snapshots/build/artifacts/failurehistory,
allNative19evidence (251listedentries plus selfmanifest), all524nativeoutside
source/build originals, fullWindows19source/build/capture/raw/runtime/release,
consumedbaseline18source/engine/core/source/build receipts, settledrootproofs and
REMOTE-PUBLICATION.json, stableAGENTS/3docs/machineledger, and immutable actual-five
producercaptures with the exactexecuted helperde13.

Mutable futureperformancepackage is excluded except actual-five-captures. Mutable
coordination, skillchanges and unrelatedvalidation trees are outside the snapshot.
Aftercopy checks use the exactfrozenlist, so futurecoordination extras are neither
silently included nor treated as oldinput mutations. Originalprototype242record
SHAcoverage remains honestly historical after adding REMOTE-PUBLICATION.json;
the archive's ownmanifest covers the exact selectedsnapshot. Root may refresh
that prototype manifest only after finalSTABLE from the freshaudit.

All publishedflatraws remain; zeroignorecandidates and no untracking/deletions.
All originals and independent staging remain local. Original prelaunch/preparation
errors, firstnativeaudit and precise corrections, rootWindowschecker attempt0,
RED/GREEN/warning/test-refinement and sourceprovenance qualifications remain
unaltered and recoverable. Postexecution reconstruction is not relabeled as a
preexecution snapshot.

Native33CTest/56coldwarmparity/8activeUCI and Windows10Wine/1184artifactchecks are
separate finiteproofs in the originalrecords. Actual-five producer time/CPUvalues
are not calibratedspeed/NPS/Elo evidence. The archive accepts no strengthgain,
physicalRyzen/nativeWindowsperformance or Stockfish claim. No engines, compilers,
Git/index/source edits or originalfile changes occurred in this archive task.
Source61f598056572dfade6994af8ad2e38817cd28aa3 and consumed18origins are preserved
using savedroot-auditedprovenance; no independentGit authenticity audit is claimed.


## Recover permissions into a new scratch destination

The unchanged trusted ZIP helper records generic `0600` external file modes.
Unzip alone does not produce executable engine files. Original file/directory
modes are preserved in the embedded `LIVE-FILES-AND-MODES.json` and on staging.
The independent audit checked those original/staging modes; it did **not** run a
fresh extraction/chmod recovery. The following recovery instructions were not
executed during this archive task.

Use a new scratch destination that does not exist. Never extract over an existing
working tree. Edit only the downloaded-parts location and, if needed, choose a
new unique path under `/tmp`. The destination creation refuses existing paths:

```python
from pathlib import Path
import hashlib, io, json, os, zipfile

parts = Path("/path/to/downloaded/archive-complete").resolve()
destination = Path("/tmp/forge-6.4.19-recovery-new")
if destination.exists() or destination.is_symlink():
    raise RuntimeError("Choose a NEW nonexistent scratch destination")
manifest_bytes = (parts / "forge-runtime-psqt-61f5980-20261020-complete.manifest.json").read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest() == "905893a4d808c904e5189540a945e38b3d000e0891a62e88b1f707027394e37d"
manifest = json.loads(manifest_bytes)
blocks = []
for item in manifest["parts"]:
    block = (parts / item["file"]).read_bytes()
    assert len(block) == item["size"]
    assert hashlib.sha256(block).hexdigest() == item["sha256"]
    blocks.append(block)
combined = b"".join(blocks)
assert hashlib.sha256(combined).hexdigest() == manifest["archive"]["sha256"]
with zipfile.ZipFile(io.BytesIO(combined)) as archive:
    for name in archive.namelist():
        path = Path(name)
        assert not path.is_absolute() and ".." not in path.parts
    destination.mkdir(parents=False, exist_ok=False)
    archive.extractall(destination)
records = json.loads((destination / "files/archive-provenance/LIVE-FILES-AND-MODES.json").read_text())
for row in records["directories"]:
    (destination / "files" / row["payload_path"]).mkdir(parents=True, exist_ok=True)
for row in records["files"]:
    path = destination / "files" / row["payload_path"]
    assert path.stat().st_size == row["size"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    os.chmod(path, row["mode"])
    os.utime(path, ns=(row["mtime_ns"], row["mtime_ns"]))
for row in sorted(records["directories"], key=lambda r: len(Path(r["payload_path"]).parts), reverse=True):
    os.chmod(destination / "files" / row["payload_path"], row["mode"])
```

Recovered original paths are under the scratch destination's `files/payload/`
hierarchy. No command above writes to the original absolute `original` paths.
Keep the parts, manifest, all original files and staging; no cleanup/untracking
is needed to use this additional recoverable snapshot.
