"""R10: UCI option EvalFileHalfKA (string, default <empty> = off). Run from the worktree root."""
from pathlib import Path

p = Path("src/uci.cpp")
raw = p.read_bytes().decode("utf-8")
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")
edits = [
    ('#include "forge/nnue.hpp"\n', '#include "forge/nnue.hpp"\n#include "forge/nnue_halfka.hpp"\n'),
    ('            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n',
     '            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\\n";\n'
     '            // R10: a K32H3^ (HalfKAv2_hm family) .nnue from the nnue-pytorch trainer; empty = off (the lock\'s eval)\n'
     '            std::cout << "option name EvalFileHalfKA type string default <empty>\\n";\n'),
    ("""            } else if (name == "UseNNUE") {""",
     """            } else if (name == "EvalFileHalfKA") {
                std::string rest;
                std::getline(input, rest);
                std::string path = value_text + rest;
                while (!path.empty() && (path.back() == ' ' || path.back() == '\\r')) path.pop_back();
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                if (path.empty() || path == "<empty>") {
                    forge::halfka::unload();
                    std::cout << "info string EvalFileHalfKA off" << std::endl;
                } else {
                    std::string error;
                    if (forge::halfka::load(path, error)) {
                        std::cout << "info string EvalFileHalfKA loaded " << forge::halfka::description() << std::endl;
                    } else {
                        forge::halfka::unload();
                        std::cout << "info string ERROR EvalFileHalfKA: " << error << " (HalfKA eval off)" << std::endl;
                    }
                }
                searcher.clear_hash();
            } else if (name == "UseNNUE") {"""),
]
for old, new in edits:
    assert s.count(old) == 1, old[:80]
    s = s.replace(old, new)
p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print(f"uci.cpp: {len(edits)} edits")
