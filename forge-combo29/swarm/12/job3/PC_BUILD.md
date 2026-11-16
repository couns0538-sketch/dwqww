# PC r15 build (FABLE_TO_swarm_5.md) — pinned

patch sha256: d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a
  (file 5 states it starts d6bd72c531f785f4 - MATCHES)
exe: /home/ubuntu/build/pc_r15/forge
sha256: 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
id name: id name Chess Engine Forge 6.4.24 candidate
options listed: 92
build: cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1, g++-13, -march=x86-64-v4
applied: cd forge-combo29 && patch -p1 --fuzz=0 < pc_r15.patch  (11 files, EXIT=0)
date_utc: 2026-11-16T22:20:07Z

pins (pc_pins.py, one fresh process per line): all 8 match FABLE_TO_swarm_5.md
