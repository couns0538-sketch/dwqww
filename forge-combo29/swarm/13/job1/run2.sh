#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
date -u >> stamps.txt
python3 ref_par.py R_1301.fens raw_ref.txt 1,2,3,4 4 > ref_par.log 2>&1
echo "ref_par_exit=$?" >> run2.status
date -u >> stamps.txt
echo RUNDONE >> run2.status
