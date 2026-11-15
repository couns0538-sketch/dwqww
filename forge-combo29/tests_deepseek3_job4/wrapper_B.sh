#!/bin/bash
# Part B wrapper: the packc28 options are search tunables the engine accepts on
# setoption. This wrapper writes them before handing the rest of stdin to the
# engine, so the options arrive even for a match runner that sends none itself.
# Usage: wrapper_B.sh <exe> <opt=value> [<opt=value> ...]
exe=$1; shift
{ for kv in "$@"; do printf 'setoption name %s value %s\n' "${kv%%=*}" "${kv#*=}"; done
  cat
} | "$exe"
