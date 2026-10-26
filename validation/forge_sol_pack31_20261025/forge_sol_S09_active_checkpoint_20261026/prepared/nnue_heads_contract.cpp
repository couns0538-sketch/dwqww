// S09 requires an actual H256 residual net; unavailable NNUE cannot pass.
#include "forge/nnue.hpp"

#include <iostream>
#include <string_view>

int main(int argc, char** argv) {
    if (argc != 2 || (std::string_view(argv[1]) != "1" && std::string_view(argv[1]) != "8")) {
        std::cerr << "usage: forge_nnue_heads_contract EXPECTED_STORED_HEADS(1|8)\n";
        return 2;
    }
    const int expected = argv[1][0] - '0';
    const bool available = forge::nnue::available();
    const bool residual = forge::nnue::residual();
    const int stored = forge::nnue::stored_output_heads();
    std::cout << "available=" << available << " residual=" << residual
              << " hidden=" << forge::nnue::HiddenSize << " stored_heads=" << stored << '\n';
    return available && residual && forge::nnue::HiddenSize == 256 && stored == expected ? 0 : 1;
}
