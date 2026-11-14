#pragma once

#include <istream>

namespace forge {

// Compiled only when FORGE_UCI_TEST_LOOP is 1 (default 0). The lock build keeps
// main() reading std::cin. Tests pass another stream; output stays on std::cout.
int uci_loop(std::istream& in);

}  // namespace forge
