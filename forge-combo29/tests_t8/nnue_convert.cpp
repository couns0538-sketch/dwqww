#include "forge/nnue.hpp"
#include "nnue_weights.inc"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>

namespace {

void write_u32(std::ostream& out, std::uint32_t value) {
    const unsigned char bytes[4] = {
        static_cast<unsigned char>(value),
        static_cast<unsigned char>(value >> 8),
        static_cast<unsigned char>(value >> 16),
        static_cast<unsigned char>(value >> 24),
    };
    out.write(reinterpret_cast<const char*>(bytes), 4);
}

void write_i16(std::ostream& out, std::int16_t value) {
    const auto bits = static_cast<std::uint16_t>(value);
    const unsigned char bytes[2] = {
        static_cast<unsigned char>(bits),
        static_cast<unsigned char>(bits >> 8),
    };
    out.write(reinterpret_cast<const char*>(bytes), 2);
}

void write_i16s(std::ostream& out, const std::int16_t* data, std::size_t count) {
    for (std::size_t i = 0; i < count; ++i) write_i16(out, data[i]);
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: nnue_convert <output>\n";
        return 2;
    }
    std::ofstream out(argv[1], std::ios::binary);
    if (!out) {
        std::cerr << "cannot write " << argv[1] << '\n';
        return 1;
    }
    out.write("FORGENET", 8);
    write_u32(out, 1);
    write_u32(out, static_cast<std::uint32_t>(forge::nnue::HiddenSize));
    write_i16s(out, NnueW1, sizeof(NnueW1) / sizeof(NnueW1[0]));
    write_i16s(out, NnueB1, sizeof(NnueB1) / sizeof(NnueB1[0]));
    write_i16s(out, NnueW2, sizeof(NnueW2) / sizeof(NnueW2[0]));
    write_i16(out, NnueB2);
    if (!out) {
        std::cerr << "write failed\n";
        return 1;
    }
    std::cout << "wrote " << argv[1] << " hidden " << forge::nnue::HiddenSize << '\n';
    return 0;
}
