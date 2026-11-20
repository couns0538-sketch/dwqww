#!/usr/bin/env bash
# Append the AddressSanitizer symbol count to a run's .meta file.
set -u
exe=$1
meta=$2
count=$(nm -C "$exe" | grep -c __asan_ || true)
{
  echo "nm_command: nm -C $exe | grep -c __asan_"
  echo "asan_symbol_count: $count"
} >> "$meta"
echo "asan_symbol_count: $count"
