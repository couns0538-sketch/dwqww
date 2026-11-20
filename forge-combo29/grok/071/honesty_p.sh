#!/usr/bin/env bash
# Honesty check of exe P: one fresh process per line, no setoption.
set -u
S=$(cat ~/grok_seat.txt)
REPO=$(cat ~/grok_repo.txt)
DIR="$REPO/forge-combo29/grok/$S"
EXE=/tmp/build-work/forge
cd "$DIR"
sha=$(sha256sum "$EXE" | awk '{print $1}')
idname=$(printf 'uci\nquit\n' | "$EXE" | sed -n 's/^id name //p' | head -1)
run_one() {
  local name="$1" cmd="$2"
  {
    echo "exe=$EXE"
    echo "sha256=$sha"
    echo "id_name=$idname"
    echo "command=$cmd"
    echo "options_sent=none"
  } > "$DIR/${name}.meta"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/${name}.txt"
}
run_one honesty_p_bench11 "bench 11"
run_one honesty_p_bench13 "bench 13"
run_one honesty_p_bench16 "bench 16"
run_one honesty_p_perft5 "go perft 5"
python3 - << 'PY'
import pathlib, re
d = pathlib.Path(".").resolve()
rows = [("bench 11","honesty_p_bench11.txt",312866),("bench 13","honesty_p_bench13.txt",862329),("bench 16","honesty_p_bench16.txt",3024920),("go perft 5","honesty_p_perft5.txt",4865609)]
lines=["command\texpected\tnodes\tmatch"]
ok=True
for cmd,name,expected in rows:
    text=(d/name).read_text(errors="replace")
    found=[int(n) for n in re.findall(r"nodes (\d+)", text)]
    nodes=found[-1] if found else -1
    match=nodes==expected
    ok=ok and match
    lines.append(f"{cmd}\t{expected}\t{nodes}\t{'yes' if match else 'NO'}")
lines.append("all_match\t"+("yes" if ok else "NO"))
(d/"HONESTY_P.txt").write_text("\n".join(lines)+"\n")
print("\n".join(lines))
PY
