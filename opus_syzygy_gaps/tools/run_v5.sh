#!/usr/bin/env bash
# run_v5.sh - the full suite on candidate v5 and the sanitizer runs (one engine set at a time so that four CPUs suffice).
set -u
J=/d/forge_jobs_20261107/opus1
T=$J/repo/opus_syzygy_gaps/tools
ON="SyzygyTbBounds=3 SyzygyRootExact=3 SyzygyRule50=3"
QUAL_JOBS=3 QUAL_STEPS='root uci toggle warm playout misc' bash "$T/qual_all.sh" v5on cand_v5_plain v5 h5 $ON
QUAL_JOBS=3 QUAL_STEPS='claims' bash "$T/qual_all.sh" v5on cand_v5_plain v5 h5 $ON
bash "$T/run_partial.sh" p6 p6b p6_plain
bash "$T/run_partial.sh" v5on v5 cand_v5_plain $ON
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/run_san.ps1" -Tag v5 -Jobs 2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T/run_flip_asan.ps1" -Tag v5
echo done
