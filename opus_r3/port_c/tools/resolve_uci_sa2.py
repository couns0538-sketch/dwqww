"""Resolve the two src/uci.cpp conflicts of the opus-sol-SA2 merge as a union (R3 port C).

1. Option listing: the stack's whole block is kept; NnueInt16 is listed right after UseNNUE (SA2's place),
   only in builds with FORGE_NNUE_INT16.
2. setoption chain: the stack's chain is kept up to IntendedThreefold; SA2's NnueInt16 branch follows under
   FORGE_NNUE_INT16, then the common UseNNUE branch.
usage: python -I -B resolve_uci_sa2.py <src/uci.cpp>
"""
import pathlib
import sys

HEAD = "<<<<<<< HEAD\n"
MID = "=======\n"
END = ">>>>>>> origin/opus-sol-SA2\n"


def split_conflict(s, start_hint):
    a = s.index(HEAD + start_hint)
    m = s.index(MID, a)
    e = s.index(END, m)
    return a, s[a + len(HEAD):m], s[m + len(MID):e], e + len(END)


def main():
    p = pathlib.Path(sys.argv[1])
    s = p.read_bytes().decode("utf-8")
    assert "\r\n" not in s

    # 1. option listing
    use_line = '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n'
    a, head, theirs, e = split_conflict(s, use_line)
    assert head.startswith(use_line), head[:200]
    assert "NnueInt16" in theirs and "UseNNUE" in theirs
    listing = ("#if FORGE_NNUE_INT16\n"
               "            // S-A2 (build switch FORGE_NNUE_INT16): integer inference with the compiled-in network.\n"
               '            if (forge::nnue::available()) std::cout << "option name NnueInt16 type check default false\\n";\n'
               "#endif\n")
    s = s[:a] + use_line + listing + head[len(use_line):] + s[e:]

    # 2. setoption chain
    a, head, theirs, e = split_conflict(s, "")
    assert head.rstrip().endswith('std::cout << "info string invalid value for option IntendedThreefold" << std::endl;')
    assert theirs.startswith('            } else if (name == "NnueInt16") {')
    close = "                }\n"
    after = s[e:]
    assert after.startswith(close + '            } else if (name == "UseNNUE") {')
    s = s[:a] + head + close + "#if FORGE_NNUE_INT16\n" + theirs + close + "#endif\n" + after[len(close):]
    assert HEAD not in s and END not in s
    p.write_bytes(s.encode("utf-8"))
    print("resolved", p)


if __name__ == "__main__":
    main()
