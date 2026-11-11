#!/usr/bin/env python3
from pathlib import Path
r = Path(__file__).parent / "eval_init_evidence"
s = (r / "baseline.cpp").read_text()
start = s.index("struct EvalInfo {")
end = s.index("\n};", start) + 3
original = s[start:end]
for name in ("conservative", "selective"):
    candidate = original
    for field in ("attacked_twice", "mobility_area", "king_zone", "king_square", "passed"):
        candidate = candidate.replace(field + "{};", field + ";")
    if name == "selective":
        candidate = candidate.replace("attacked_by{};", "attacked_by;")
    x = s[:start] + "#if FORGE_SPD_EVAL_INIT\n" + candidate + "\n#else\n" + original + "\n#endif" + s[end:]
    init = "    EvalInfo info;"
    if name == "selective":
        init += "\n    for (const Color color : {White, Black})\n        for (int type = Knight; type <= Queen; ++type)\n            info.attacked_by[color][type] = 0;"
    x = x.replace("    EvalInfo info{};", "#if FORGE_SPD_EVAL_INIT\n" + init + "\n#else\n    EvalInfo info{};\n#endif")
    (r / (name + ".cpp")).write_text(x)
