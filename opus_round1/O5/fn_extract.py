"""Extract one function from a GCC tree/ipa dump (by mangled name) and optionally normalise SSA versions.
usage: fn_extract.py <dump> <mangled> [--norm]"""
import re
import sys

dump, mangled = sys.argv[1], sys.argv[2]
norm = "--norm" in sys.argv
out, on = [], False
for line in open(dump, errors="replace"):
    if line.startswith(";; Function "):
        on = ("(" + mangled + "," in line) or ("(" + mangled + ")" in line)
    if on:
        if norm:
            line = re.sub(r"_\d+(\(D\))?", "_N", line)
            line = re.sub(r"\.\d+_N", ".N_N", line)
            line = re.sub(r"<bb \d+>", "<bb N>", line)
            line = re.sub(r"\[(local count|count): [^\]]*\]", "", line)
            line = re.sub(r"(decl_uid|cgraph_uid|symbol_order|funcdef_no)=\d+", r"\1=N", line)
            line = re.sub(r"D\.\d+", "D.N", line)
        out.append(line)
sys.stdout.write("".join(out))
