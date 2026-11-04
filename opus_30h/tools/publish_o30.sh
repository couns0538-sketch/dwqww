#!/usr/bin/env bash
# publish_o30.sh - Opus 30-h job: copy the branch's top documents to the paths the prompt names, D:\o30\TOOLS.md and
# D:\o30\FINAL_REPORT.md, each with one provenance line on top (branch commit; relative paths in the text are relative
# to D:\o30\wt\opus_30h), and regenerate D:\o30\nets\INDEX.md. Re-runnable (the copies are generated files).
set -uo pipefail
. "$(cd "$(dirname "$0")" && pwd)/idle.sh"; o30_pin_self 0x3 || { echo "cannot pin to Idle / CPUs 0-1 (fail closed)" >&2; exit 78; }
W=/d/o30/wt; PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
head=$(git -C "$W" rev-parse --short=8 HEAD)
for doc in TOOLS.md FINAL_REPORT.md; do
  src="$W/opus_30h/$doc"; dst="/d/o30/$doc"
  { printf '<!-- generated copy of opus_30h/%s at branch opus-30h-20261103 commit %s by tools/publish_o30.sh; relative paths = D:\\o30\\wt\\opus_30h -->\n' "$doc" "$head"
    cat "$src"; } > "$dst.new" && mv -f "$dst.new" "$dst"
  tail -n +2 "$dst" | cmp -s - "$src" && echo "published $dst (= opus_30h/$doc at $head)" || { echo "MISMATCH $dst" >&2; exit 1; }
done
"$PY" -I -B "$W/opus_30h/a/make_net_index.py"
