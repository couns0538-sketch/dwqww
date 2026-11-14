#include "forge/nnue.hpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>

#include "nnue_weights.inc"

namespace {

void put_u32(std::ostream& out, std::uint32_t value) {
    const unsigned char bytes[4] = {
        static_cast<unsigned char>(value),
        static_cast<unsigned char>(value >> 8),
        static_cast<unsigned char>(value >> 16),
        static_cast<unsigned char>(value >> 24),
    };
    out.write(reinterpret_cast<const char*>(bytes), 4);
}

void put_i16s(std::ostream& out, const std::int16_t* data, std::size_t count) {
    for (std::size_t i = 0; i < count; ++i) {
        const auto bits = static_cast<std::uint16_t>(data[i]);
        const unsigned char bytes[2] = {
            static_cast<unsigned char>(bits),
            static_cast<unsigned char>(bits >> 8),
        };
        out.write(reinterpret_cast<const char*>(bytes), 2);
    }
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: forgenet_convert <out.bin>\n";
        return 2;
    }
    std::ofstream out(argv[1], std::ios::binary);
    if (!out) {
        std::cerr << "cannot open " << argv[1] << '\n';
        return 1;
    }
    const char magic[8] = {'F', 'O', 'R', 'G', 'E', 'N', 'E', 'T'};
    out.write(magic, 8);
    put_u32(out, 1U);
    put_u32(out, static_cast<std::uint32_t>(forge::nnue::HiddenSize));
    put_i16s(out, NnueW1, sizeof(NnueW1) / sizeof(NnueW1[0]));
    put_i16s(out, NnueB1, sizeof(NnueB1) / sizeof(NnueB1[0]));
    put_i16s(out, NnueW2, sizeof(NnueW2) / sizeof(NnueW2[0]));
    put_i16s(out, &NnueB2, 1);
    if (!out) {
        std::cerr << "write failed\n";
        return 1;
    }
    return 0;
}
