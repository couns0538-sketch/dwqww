#!/bin/bash
# $1=exe $2=opt $3=positions $4=tag
python3 runner.py "$1" "$3" 12 rows "$4" 100000 1 "$2" > "rows/$4.stdout" 2>&1
echo "$4 rc=$?"
