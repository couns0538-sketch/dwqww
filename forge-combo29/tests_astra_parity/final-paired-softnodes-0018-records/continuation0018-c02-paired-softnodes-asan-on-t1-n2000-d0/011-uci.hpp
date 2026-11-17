#pragma once

#include <istream>

namespace forge {

// Reads UCI commands from `in` until EOF or `quit`. `main` passes `std::cin`.
// Output stays on `std::cout`. Behaviour matches the engine's stdin loop.
int uci_loop(std::istream& in);

}  // namespace forge
