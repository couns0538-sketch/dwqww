#!/bin/sh
# Production invocation: sh this_script.sh owner_config.json
set -eu
if [ "$#" -ne 1 ]; then
    echo 'Usage: sh forge_sol_S16_overlap_runner_20261026.sh owner_config.json' >&2
    exit 2
fi
script_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
exec "${FORGE_PYTHON:-python3}" -B "$script_dir/forge_sol_datafilter_v2_20261026.py" --config "$1"
