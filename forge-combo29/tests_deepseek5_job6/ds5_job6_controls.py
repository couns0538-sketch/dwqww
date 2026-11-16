#!/usr/bin/env python3
"""job6 Part 2: the five controls THROUGH the new harness."""
import sys
sys.path.insert(0, "/tmp/glmflash")
import ds5_job6_storms as H

out = {}
H.ENGINE = "/tmp/ds5_tsan_p3/build/forge"
out["H1"] = H.block("H1", "T1x20", 20, 7361, threads_init=4)
out["H2"] = H.block("H2", "T1x20", 20, 7362, threads_init=1)
H.ENGINE = "/tmp/ds5_tsan/build/forge"
out["H3"] = H.block("H3", "T1x20", 20, 7363, threads_init=4)
H.ENGINE = "/tmp/ds5_asan_p3/build/forge"
out["H4"] = H.block("H4", "T1x5", 5, 7364, threads_init=1)
H.ENGINE = "/tmp/ds5_asan/build/forge"
out["H5"] = H.block("H5", "T1x5", 5, 7365, threads_init=1)
import json
json.dump(out, open("/tmp/glmflash/ds5j6/controls.json", "w"), indent=1)
print(json.dumps(out, indent=1))
