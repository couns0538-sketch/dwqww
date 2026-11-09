#!/usr/bin/env bash
# make_manifests.sh [pack dir] - MANIFEST.md5 and MANIFEST.sha256: every file of the pack except the two manifests, paths relative to the pack, sorted. Writes nothing else.
# Verify in the pack folder: md5sum -c MANIFEST.md5 && sha256sum -c MANIFEST.sha256 (files are stored with LF, so check out with core.autocrlf=false).
set -eu
D=${1:-/d/forge_jobs_20261107/opus1/repo/opus_syzygy_gaps}
cd "$D"
find . -type f ! -name MANIFEST.md5 ! -name MANIFEST.sha256 -printf '%P\n' | LC_ALL=C sort > "$D/../.pack_files.tmp"
: > MANIFEST.md5
: > MANIFEST.sha256
while IFS= read -r p; do
  md5sum -b -- "$p" | sed 's/ \*/  /' >> MANIFEST.md5
  sha256sum -b -- "$p" | sed 's/ \*/  /' >> MANIFEST.sha256
done < "$D/../.pack_files.tmp"
n=$(wc -l < "$D/../.pack_files.tmp")
: > "$D/../.pack_files.tmp"
md5sum -c --quiet MANIFEST.md5
sha256sum -c --quiet MANIFEST.sha256
echo "manifests: $n files verified"
