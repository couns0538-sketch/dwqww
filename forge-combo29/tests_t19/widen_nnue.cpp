// Reads the lock net (src/nnue_weights.inc) and writes a 512-wide net.
// Hidden units 0..255 of each side are copied. Units 256..511 have input
// weights 0, bias 0 and output weight 0.
//
// Layout, matching src/nnue.cpp:
//   NnueW1[feature * Hidden + hidden]  -- hidden runs fastest
//   NnueB1[hidden]
//   NnueW2[0 .. Hidden)                 -- side to move
//   NnueW2[Hidden .. 2 * Hidden)        -- opponent
//   NnueB2                              -- scalar
// Widening inserts the zero units at the end of each W1 column and in the
// middle of W2 (after the copied own-side weights, before the opponent weights).

#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <system_error>
#include <vector>

namespace {

constexpr int kInputs = 768;
constexpr int kOldHidden = 256;
constexpr int kNewHidden = 512;

[[noreturn]] void fail(const std::string& message) {
    std::cerr << "widen_nnue: " << message << '\n';
    std::exit(1);
}

std::string read_file(const std::string& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) fail("cannot read " + path);
    std::ostringstream buffer;
    buffer << input.rdbuf();
    return buffer.str();
}

std::vector<int> parse_array(const std::string& text, const std::string& name, std::size_t expected) {
    const std::string marker = name + "[";
    const std::size_t at = text.find(marker);
    if (at == std::string::npos) fail("missing " + name);
    const std::size_t open = text.find('{', at);
    const std::size_t close = text.find("};", open == std::string::npos ? at : open);
    if (open == std::string::npos || close == std::string::npos || close < open) fail("bad braces for " + name);
    std::vector<int> values;
    values.reserve(expected);
    const char* p = text.data() + open + 1;
    const char* end = text.data() + close;
    while (p < end) {
        while (p < end && (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r' || *p == ',')) ++p;
        if (p >= end) break;
        char* next = nullptr;
        const long long parsed = std::strtoll(p, &next, 10);
        if (next == p) fail("bad integer in " + name);
        if (parsed < -32768 || parsed > 32767) fail("value out of int16 in " + name);
        values.push_back(static_cast<int>(parsed));
        p = next;
    }
    if (values.size() != expected) {
        fail(name + " has " + std::to_string(values.size()) + " values, expected " + std::to_string(expected));
    }
    return values;
}

int parse_b2(const std::string& text) {
    const std::size_t at = text.find("NnueB2");
    if (at == std::string::npos) fail("missing NnueB2");
    const std::size_t eq = text.find('=', at);
    if (eq == std::string::npos) fail("bad NnueB2");
    char* next = nullptr;
    const long long parsed = std::strtoll(text.c_str() + eq + 1, &next, 10);
    if (next == text.c_str() + eq + 1) fail("bad NnueB2 integer");
    if (parsed < -32768 || parsed > 32767) fail("NnueB2 out of int16");
    return static_cast<int>(parsed);
}

void write_array(std::ostream& out, const char* name, const std::vector<int>& values) {
    out << "static const std::int16_t " << name << '[' << values.size() << "] = {\n";
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i % 24 == 0) out << "  ";
        out << values[i] << ',';
        if (i % 24 == 23 || i + 1 == values.size()) out << '\n';
        else out << ' ';
    }
    out << "};\n";
}

std::uint64_t fingerprint(const std::vector<int>& values) {
    std::uint64_t hash = 14695981039346656037ull;
    for (const int value : values) {
        hash ^= static_cast<std::uint64_t>(static_cast<std::uint32_t>(value));
        hash *= 1099511628211ull;
    }
    return hash;
}

std::filesystem::path resolved(const std::filesystem::path& path) {
    std::error_code error;
    const std::filesystem::path canonical = std::filesystem::weakly_canonical(path, error);
    return error ? path.lexically_normal() : canonical;
}

bool same_target(const std::filesystem::path& left, const std::filesystem::path& right) {
    if (resolved(left) == resolved(right)) return true;
    std::error_code error;
    return std::filesystem::equivalent(left, right, error);
}

bool is_lock_weights(const std::filesystem::path& path) {
    const std::filesystem::path check = resolved(path);
    if (check.filename() != "nnue_weights.inc") return false;
    for (const std::filesystem::path& part : check) {
        if (part == "src") return true;
    }
    return false;
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: widen_nnue input.inc output.inc\n";
        return 2;
    }
    const std::string input_path = argv[1];
    const std::string output_path = argv[2];
    if (is_lock_weights(output_path) || same_target(input_path, output_path)) {
        std::cerr << "widen_nnue: refusing to overwrite the lock weights\n";
        return 2;
    }

    const std::string text = read_file(input_path);
    const std::vector<int> w1 = parse_array(text, "NnueW1", static_cast<std::size_t>(kInputs) * kOldHidden);
    const std::vector<int> b1 = parse_array(text, "NnueB1", kOldHidden);
    const std::vector<int> w2 = parse_array(text, "NnueW2", 2 * kOldHidden);
    const int b2 = parse_b2(text);

    std::vector<int> w1_wide(static_cast<std::size_t>(kInputs) * kNewHidden, 0);
    for (int feature = 0; feature < kInputs; ++feature) {
        for (int hidden = 0; hidden < kOldHidden; ++hidden) {
            w1_wide[static_cast<std::size_t>(feature * kNewHidden + hidden)] =
                w1[static_cast<std::size_t>(feature * kOldHidden + hidden)];
        }
    }
    std::vector<int> b1_wide(kNewHidden, 0);
    for (int hidden = 0; hidden < kOldHidden; ++hidden) b1_wide[static_cast<std::size_t>(hidden)] = b1[static_cast<std::size_t>(hidden)];

    // Own side first, then the other side. Zeros sit at the end of each half.
    std::vector<int> w2_wide(2 * kNewHidden, 0);
    for (int hidden = 0; hidden < kOldHidden; ++hidden) {
        w2_wide[static_cast<std::size_t>(hidden)] = w2[static_cast<std::size_t>(hidden)];
        w2_wide[static_cast<std::size_t>(kNewHidden + hidden)] = w2[static_cast<std::size_t>(kOldHidden + hidden)];
    }

    auto require = [](bool ok, const char* message) {
        if (!ok) fail(message);
    };
    require(w1_wide[0] == w1[0] && w1_wide[255] == w1[255] && w1_wide[256] == 0, "W1 column 0");
    require(w1_wide[512] == w1[256] && w1_wide[512 + 255] == w1[256 + 255] && w1_wide[512 + 256] == 0, "W1 column 1");
    require(w1_wide.back() == 0, "W1 tail");
    require(b1_wide[0] == b1[0] && b1_wide[255] == b1[255] && b1_wide[256] == 0 && b1_wide[511] == 0, "B1");
    require(w2_wide[0] == w2[0] && w2_wide[255] == w2[255] && w2_wide[256] == 0 && w2_wide[511] == 0, "W2 own");
    require(w2_wide[512] == w2[256] && w2_wide[767] == w2[511] && w2_wide[768] == 0 && w2_wide[1023] == 0, "W2 opponent");

    std::ofstream out(output_path, std::ios::binary);
    if (!out) fail("cannot write " + output_path);
    out << "// Generated by tests_t19/widen_nnue.cpp from the lock net.\n"
        << "// Hidden units 0..255 of each side are the lock units. Units 256..511\n"
        << "// have input weight 0, bias 0 and output weight 0.\n"
        << "// NnueW1 index = feature * 512 + hidden (hidden runs fastest).\n"
        << "// NnueW2 is own side [0, 512), then opponent [512, 1024).\n"
        << "#include <cstdint>\n"
        << "#define FORGE_NNUE_RESIDUAL 1\n"
        << "static_assert(forge::nnue::InputCount == 768 && forge::nnue::HiddenSize == 512,\n"
        << "              \"NNUE shape mismatch; rebuild with the correct FORGE_NNUE_HIDDEN\");\n"
        << "static_assert(forge::nnue::SigmoidK == 2.25F, \"NNUE output scale mismatch\");\n"
        << "static_assert(forge::nnue::WeightScale == 4096.0F && forge::nnue::OutputScale == 4096.0F,\n"
        << "              \"NNUE quantization scale mismatch\");\n";
    write_array(out, "NnueW1", w1_wide);
    write_array(out, "NnueB1", b1_wide);
    write_array(out, "NnueW2", w2_wide);
    out << "static const std::int16_t NnueB2 = " << b2 << ";\n";
    if (!out) fail("write failed for " + output_path);

    int w1_pad = 0;
    int w1_old_zeros = 0;
    for (int feature = 0; feature < kInputs; ++feature) {
        for (int hidden = 0; hidden < kNewHidden; ++hidden) {
            if (w1_wide[static_cast<std::size_t>(feature * kNewHidden + hidden)] != 0) continue;
            if (hidden < kOldHidden) ++w1_old_zeros;
            else ++w1_pad;
        }
    }
    int b1_pad = 0;
    for (int hidden = kOldHidden; hidden < kNewHidden; ++hidden) if (b1_wide[static_cast<std::size_t>(hidden)] == 0) ++b1_pad;
    int w2_pad = 0;
    for (int hidden = kOldHidden; hidden < kNewHidden; ++hidden) {
        if (w2_wide[static_cast<std::size_t>(hidden)] == 0) ++w2_pad;
        if (w2_wide[static_cast<std::size_t>(kNewHidden + hidden)] == 0) ++w2_pad;
    }
    std::cout << "input " << input_path << '\n'
              << "output " << output_path << '\n'
              << "read w1=" << w1.size() << " b1=" << b1.size() << " w2=" << w2.size() << " b2=" << b2 << '\n'
              << "write w1=" << w1_wide.size() << " b1=" << b1_wide.size() << " w2=" << w2_wide.size() << " b2=" << b2 << '\n'
              << "padding_zeros w1=" << w1_pad << " b1=" << b1_pad << " w2=" << w2_pad << '\n'
              << "lock_column_zeros w1=" << w1_old_zeros << '\n'
              << "fingerprint w1=" << fingerprint(w1_wide)
              << " b1=" << fingerprint(b1_wide)
              << " w2=" << fingerprint(w2_wide) << '\n';
    return 0;
}
