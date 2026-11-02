#!/usr/bin/env bash
# R14 Main 2: kit v2.3 -Expose builds - s2on (FORGE_SEARCH_SPEED2 default 1) pc1 + pc2, then s2off (default 0) pc1 only.
K=/d/grok-pc-data/dwqww/.claude/worktrees/o13-p2/opus_r13/p2/speed2/kit_build_r14.sh
date '+start %F %T'
bash $K /d/o14a/p2/speed2on s2on; echo "s2on kit exit $?"
KIT_SIDES=pc1 bash $K /d/o14a/p2/speed2 s2off; echo "s2off kit exit $?"
echo "lock FD3A5190 sha256: $(sha256sum /c/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe | cut -c1-64)"
date '+end %F %T'
