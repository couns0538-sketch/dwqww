#!/usr/bin/env bash
# Honesty check of the partner build. One fresh process per line. No setoption.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
EXE="${1:-/tmp/forge-partner/forge}"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk '/^id name /{print; exit}')
run_one() {
  local tag="$1" cmd="$2"
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$DIR/partner_honesty_${tag}.txt"
  {
    echo "exe $EXE"
    echo "sha256 $SHA"
    echo "$IDNAME"
    echo "options none"
    echo "command $cmd"
  } > "$DIR/partner_honesty_${tag}.meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
python3 - "$DIR" << 'PY'
import pathlib, sys
d = pathlib.Path(sys.argv[1])
def bench_nodes(name):
    text = (d / name).read_text(errors="replace").splitlines()
    for line in text:
        if "bench depth" in line and " nodes " in line:
            parts = line.split()
            return parts[parts.index("nodes") + 1]
    return "MISSING"
def perft_nodes(name):
    last = "MISSING"
    for line in (d / name).read_text(errors="replace").splitlines():
        if line.startswith("nodes "):
            last = line.split()[1]
    return last
rows = [
    ("bench 11", bench_nodes("partner_honesty_bench11.txt"), "312866"),
    ("bench 13", bench_nodes("partner_honesty_bench13.txt"), "862329"),
    ("bench 16", bench_nodes("partner_honesty_bench16.txt"), "3024920"),
    ("go perft 5", perft_nodes("partner_honesty_perft5.txt"), "4865609"),
]
out = ["line\texpected\tgot\tmatch"]
ok = True
for label, got, exp in rows:
    match = "yes" if got == exp else "NO"
    ok = ok and match == "yes"
    out.append(f"{label}\t{exp}\t{got}\t{match}")
out.append("ALL_MATCH\t" + ("yes" if ok else "no"))
text = "\n".join(out) + "\n"
(d / "PARTNER_HONESTY.txt").write_text(text)
print(text, end="")
PY
