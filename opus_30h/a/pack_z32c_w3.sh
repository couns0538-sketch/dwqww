#!/usr/bin/env bash
# pack_z32c_w3.sh - Opus 30-h job, window 3: when CPU 0 is free (Y8's match has ended), pack the soup Z32c (Z32's five
# members + the native KB32 seeds r24 / r25; the best S31 of the job, offline only, never played) with net_pack.sh on
# CPU 0, so the crew has a checked file. Exit code taken on its own line (BH-2).
set -u
busy() {
    powershell -NoProfile -Command "Get-Process python,fastchess -ErrorAction SilentlyContinue | Where-Object { [int64]\$_.ProcessorAffinity -eq 1 } | Measure-Object | Select-Object -ExpandProperty Count"
}
until [ "$(busy | tr -d '\r')" = "0" ]; do sleep 20; done
echo "$(date '+%F %T') CPU 0 free"
cd /d/o30 || exit 1
O30_MASK=0x1 bash /d/o30/wt/opus_30h/a/net_pack.sh o30_gpu_soupZ32c_w3 /c/o30g/gpu/soups/soupZ32c_w3_nets/soupZ32c_w3-1.nnue2 \
    /d/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe /d/o30/harness/h1 > /d/o30/logs/net_pack_o30_gpu_soupZ32c_w3.out 2>&1
rc=$?
echo "$(date '+%F %T') net_pack exit $rc: $(tail -1 /d/o30/logs/net_pack_o30_gpu_soupZ32c_w3.out | cut -c1-150)"
exit $rc
