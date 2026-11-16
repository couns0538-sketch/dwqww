#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
python3 harness_search.py ~/bld/release/forge G_353.fens out_G_d10.txt meta_G_d10.txt 10 S14
