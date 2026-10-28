"""List the FORGE_NNUE_O2 blocks made by `diff -D` whose branches have unbalanced preprocessor conditionals."""
import re
import sys

lines = open(sys.argv[1], "rb").read().decode("utf-8").split("\n")
opens = re.compile(r"^\s*#\s*(if|ifdef|ifndef)\b")
closes = re.compile(r"^\s*#\s*endif\b")
i = 0
bad = 0
while i < len(lines):
    l = lines[i]
    if l.startswith("#ifdef FORGE_NNUE_O2") or l.startswith("#ifndef FORGE_NNUE_O2"):
        start = i
        branches, cur = [], []
        i += 1
        while not lines[i].startswith("#endif /* FORGE_NNUE_O2 */") and not lines[i].startswith("#endif /* ! FORGE_NNUE_O2 */"):
            if lines[i].startswith("#else /* FORGE_NNUE_O2 */") or lines[i].startswith("#else /* ! FORGE_NNUE_O2 */"):
                branches.append(cur); cur = []
            else:
                cur.append(lines[i])
            i += 1
        branches.append(cur)
        for b in branches:
            depth = 0
            ok = True
            for x in b:
                if opens.match(x):
                    depth += 1
                elif closes.match(x):
                    depth -= 1
                    if depth < 0:
                        ok = False
                elif re.match(r"^\s*#\s*(else|elif)\b", x) and depth == 0:
                    ok = False
            if depth != 0 or not ok:
                bad += 1
                print(f"UNBALANCED block at line {start + 1}: {lines[start]}")
                break
    i += 1
print("unbalanced blocks:", bad)
