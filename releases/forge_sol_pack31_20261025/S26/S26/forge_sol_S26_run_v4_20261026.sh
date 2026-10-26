#!/bin/sh
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
exec python3 -B "$script_dir/successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py" "$@"
