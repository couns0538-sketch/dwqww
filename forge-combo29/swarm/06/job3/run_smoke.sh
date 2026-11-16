#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
python3 harness_search.py ~/bld/release/forge smoke.fens out_smoke.txt meta_smoke.txt 10 S14
