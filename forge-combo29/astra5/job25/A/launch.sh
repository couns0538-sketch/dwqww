set -eu
base=/workspace/work/run23
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/work/tactic3/deps
threads=$1
case "$threads" in
  1) cpu_r=0; cpu_k=2;;
  2) cpu_r=0,1; cpu_k=2,3;;
  4) cpu_r=0,1,2,3; cpu_k=0,1,2,3;;
esac
run_one() {
 build=$1; cpu=$2
 dir="$base/job25work/A/A$threads/$build"
 mkdir -p "$dir"
 taskset -c "$cpu" python3 "$base/job25work/A/search_driver.py" "$build" "$threads" "$base/builds/$build-znver4/forge" "$base/net/net768.nnue" "$base/job25work/input/first30.epd" "$base/job25work/step0/pc20.txt" "$dir" > "$dir/progress.txt" 2>&1
}
if [ "$threads" = 4 ]; then
 run_one r15d "$cpu_r"
 run_one kF "$cpu_k"
 exit 0
fi
run_one r15d "$cpu_r" &
a=$!
run_one kF "$cpu_k" &
b=$!
rc=0
wait "$a" || rc=1
wait "$b" || rc=1
exit "$rc"
