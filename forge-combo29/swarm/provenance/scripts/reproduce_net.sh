#!/bin/sh
# Reproduce the v3 test net from the COMMITTED generator and check all three figures
# the reports quote for it. A net file is data, not a binary, so if the generator is
# committed the artefact is resolvable -- which is what makes the 7 findings that cite
# it re-derivable.
#
# Usage: sh scripts/reproduce_net.sh [workdir]
set -u
REPO=${REPO:-/agent/repos/dwqww}
WORK=${1:-/tmp/prov-net}
mkdir -p "$WORK"

# The generator exists in three seats; seat 01's copy is the one the reports cite.
GEN_BLOB=$(git -C "$REPO" rev-list --all --objects \
           | grep 'make_v3_testnet.py' | head -1 | cut -d' ' -f1)
echo "generator blob : $GEN_BLOB"
git -C "$REPO" cat-file -p "$GEN_BLOB" > "$WORK/make_v3_testnet.py"

# It takes the output path as argv[1]; with no argument it raises IndexError, which is
# worth noting because a caller that ran it bare would report a tool failure as a
# missing artefact. It also opens with mode "xb", so a stale file from a previous run
# makes it fail rather than overwrite -- remove first.
rm -f "$WORK/test_v3.fnn3"
python3 "$WORK/make_v3_testnet.py" "$WORK/test_v3.fnn3" > "$WORK/gen.log" 2>&1
echo "generator exit : $?"
ls -l "$WORK/test_v3.fnn3" 2>/dev/null | awk '{print "bytes          : "$5}'

SHA=$(sha256sum "$WORK/test_v3.fnn3" | cut -d' ' -f1)
echo "sha256         : $SHA"
echo "reported       : 1db8525e4eeb3c4cf425faf89a5dbb7e5aec0a9d00fd7de2c7cd25a7673ffd4a"
[ "$SHA" = "1db8525e4eeb3c4cf425faf89a5dbb7e5aec0a9d00fd7de2c7cd25a7673ffd4a" ] \
  && echo "verdict        : REPRODUCED byte-exact" || echo "verdict        : DIFFERS"

python3 - "$WORK/test_v3.fnn3" <<'PY'
import sys
data = open(sys.argv[1], 'rb').read()
# The generator computes FNV-1a64 over the payload, THEN appends it as 8 bytes and
# writes the file. So the digest the report quotes is over data[:-8], not the whole
# file -- hashing the whole file "differs" and that is a bug in the CHECK, not in the
# artefact. This is the same trap the corpus documents: a hash compared over the wrong
# span looks like a provenance failure but is a harness failure.
payload = data[:-8]
h = 0xcbf29ce484222325
for b in payload:
    h ^= b
    h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
stored = int.from_bytes(data[-8:], 'little')
print(f"FNV-1a64 (payload)  : {h:016x}")
print(f"FNV-1a64 (trailer)  : {stored:016x}")
print("reported            : fdff70de72e4ca82")
ok = f"{h:016x}" == "fdff70de72e4ca82" and h == stored
print("verdict             : " + ("REPRODUCED, and the trailer agrees with the payload"
                                   if ok else "DIFFERS"))
print(f"bytes               : {len(data)}  (reported 6,309,096)")
PY
