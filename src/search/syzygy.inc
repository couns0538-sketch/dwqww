// Search module: Syzygy endgame tablebase reader and probes (forge/syzygy.hpp).
//
// Own implementation from the public description of the Syzygy formats
// (see opus_round1/C1/IDEA_SOURCE.md). In outline:
//  - a WDL file (.rtbw) holds one table per side to move (one if the material
//    is symmetric) and, with pawns, per file a-d of the leading pawn; a DTZ
//    file (.rtbz) holds one side to move only;
//  - a position maps to an index: the leading group (the leading pawns, or
//    three unique pieces, or the two kings) after mirroring the board into a
//    canonical region, then every further group of identical pieces as a
//    combination of the squares still free; the group order of the index is
//    a per-table parameter (the order nibbles of the header);
//  - values are RePair symbols coded with a canonical Huffman code in blocks
//    of 2^b bytes; a sparse index finds the block of an index value;
//  - WDL tables need not be right where a capture (or, for DTZ, a winning
//    zeroing move) is best, and ignore en passant: the probes below always
//    resolve captures first.
// Compiled as part of src/search.cpp, included last. Every function here is
// [[gnu::cold]]: it is placed in .text.unlikely, after all search code, so the
// search keeps its AL1 s198 code placement while no tables are loaded.

#include <filesystem>
#include <fstream>
#include <memory>
#include <string_view>
#include <system_error>

namespace forge::syzygy {

std::atomic<int> search_cardinality{0};
std::atomic<int> root_display{0};
std::atomic<int> root_display_score{0};
std::atomic<std::uint64_t> probe_hits{0};
bool tb_scores = false;

namespace {

constexpr std::uint32_t WdlMagic = 0x5d23e871U;
constexpr std::uint32_t DtzMagic = 0xa50c66d7U;
constexpr int TableMaxPieces = 7;

bool g_heap_loading = false;

[[gnu::cold]] std::uint16_t read16(const std::uint8_t* p) {
    return static_cast<std::uint16_t>(p[0] | (p[1] << 8));
}
[[gnu::cold]] std::uint32_t read32(const std::uint8_t* p) {
    return static_cast<std::uint32_t>(p[0]) | (static_cast<std::uint32_t>(p[1]) << 8) |
           (static_cast<std::uint32_t>(p[2]) << 16) | (static_cast<std::uint32_t>(p[3]) << 24);
}

// Read-only view of a whole table file (memory map, or heap copy for tests).
[[gnu::cold]] bool map_file(const std::filesystem::path& path, const std::uint8_t*& data, std::size_t& size);
[[gnu::cold]] void unmap_file(const std::uint8_t* data, std::size_t size);

class FileView {
public:
    FileView() = default;
    FileView(const FileView&) = delete;
    FileView& operator=(const FileView&) = delete;
    [[gnu::cold]] ~FileView() { release(); }
    [[gnu::cold]] bool open(const std::filesystem::path& path) {
        release();
        if (g_heap_loading) {
            std::ifstream in(path, std::ios::binary);
            if (!in) return false;
            in.seekg(0, std::ios::end);
            const std::streamoff length = in.tellg();
            if (length <= 0) return false;
            in.seekg(0, std::ios::beg);
            heap_ = std::make_unique<std::uint8_t[]>(static_cast<std::size_t>(length));
            if (!in.read(reinterpret_cast<char*>(heap_.get()), length)) {
                heap_.reset();
                return false;
            }
            data_ = heap_.get();
            size_ = static_cast<std::size_t>(length);
            return true;
        }
        mapped_ = map_file(path, data_, size_);
        return mapped_;
    }
    [[gnu::cold]] void release() {
        if (mapped_) unmap_file(data_, size_);
        heap_.reset();
        mapped_ = false;
        data_ = nullptr;
        size_ = 0;
    }
    [[nodiscard]] const std::uint8_t* data() const { return data_; }
    [[nodiscard]] std::size_t size() const { return size_; }

private:
    const std::uint8_t* data_ = nullptr;
    std::size_t size_ = 0;
    bool mapped_ = false;
    std::unique_ptr<std::uint8_t[]> heap_;
};

// ---------------------------------------------------------------------------
// Index geometry of the format, computed once per load.
struct Geometry {
    // choose[k][n] = C(n, k).
    std::array<std::array<std::uint64_t, 65>, 8> choose{};
    // Pawn squares a2..h7 ordered for the leading-pawn rule: the leading pawn
    // is the one with the largest value (nearest an edge file, then lowest
    // rank, a-side before h-side); values 0..47, -1 on ranks 1 and 8.
    std::array<int, 64> pawn_rank{};
    // Placements of the leading pawn group: offset by the leading pawn's square
    // and the total per file a-d, for 1..5 leading pawns.
    std::array<std::array<std::uint64_t, 64>, 6> lead_offset{};
    std::array<std::array<std::uint64_t, 4>, 6> lead_total{};
    // a1-d1-d4 triangle: b1 c1 d1 c2 d2 d3 -> 0..5, a1 b2 c3 d4 -> 6..9.
    std::array<int, 64> triangle{};
    // Squares below the a1-h8 diagonal (file > rank) -> 0..27 in square order.
    std::array<int, 64> below{};
    // The 462 placements of two kings with the first in the triangle.
    std::array<std::array<int, 64>, 10> king_pair{};
    bool valid = false;
};

[[gnu::cold]] int diagonal_offset(int square) { return rank_of(square) - file_of(square); }

[[gnu::cold]] void build_geometry(Geometry& g) {
    for (int n = 0; n <= 64; ++n) {
        g.choose[0][static_cast<std::size_t>(n)] = 1;
        for (int k = 1; k < 8; ++k) {
            g.choose[static_cast<std::size_t>(k)][static_cast<std::size_t>(n)] =
                n == 0 ? 0 : g.choose[static_cast<std::size_t>(k - 1)][static_cast<std::size_t>(n - 1)] +
                                 g.choose[static_cast<std::size_t>(k)][static_cast<std::size_t>(n - 1)];
        }
    }
    g.pawn_rank.fill(-1);
    int order = 47;
    for (int file = 0; file < 4; ++file) {
        for (int rank = 1; rank <= 6; ++rank) {
            g.pawn_rank[static_cast<std::size_t>(make_square(file, rank))] = order--;
            g.pawn_rank[static_cast<std::size_t>(make_square(7 - file, rank))] = order--;
        }
    }
    for (int count = 1; count <= 5; ++count) {
        for (int file = 0; file < 4; ++file) {
            std::uint64_t total = 0;
            for (int rank = 1; rank <= 6; ++rank) {
                const int square = make_square(file, rank);
                g.lead_offset[static_cast<std::size_t>(count)][static_cast<std::size_t>(square)] = total;
                total += g.choose[static_cast<std::size_t>(count - 1)]
                                 [static_cast<std::size_t>(g.pawn_rank[static_cast<std::size_t>(square)])];
            }
            g.lead_total[static_cast<std::size_t>(count)][static_cast<std::size_t>(file)] = total;
        }
    }
    g.triangle.fill(-1);
    g.below.fill(-1);
    int code = 0;
    for (int square = 0; square < 64; ++square) {
        if (file_of(square) <= 3 && diagonal_offset(square) < 0 && rank_of(square) <= 3) {
            g.triangle[static_cast<std::size_t>(square)] = code++;
        }
    }
    for (int square = 0; square < 64; ++square) {
        if (file_of(square) <= 3 && diagonal_offset(square) == 0) g.triangle[static_cast<std::size_t>(square)] = code++;
    }
    code = 0;
    for (int square = 0; square < 64; ++square) {
        if (diagonal_offset(square) < 0) g.below[static_cast<std::size_t>(square)] = code++;
    }
    // King pairs: the first king in the triangle; with the first king on the
    // diagonal the second is not above it; pairs with both kings on the
    // diagonal are numbered last.
    for (auto& row : g.king_pair) row.fill(-1);
    std::array<int, 64> first_of{};
    first_of.fill(-1);
    for (int square = 0; square < 64; ++square) {
        if (g.triangle[static_cast<std::size_t>(square)] >= 0) first_of[static_cast<std::size_t>(g.triangle[static_cast<std::size_t>(square)])] = square;
    }
    int next = 0;
    for (int pass = 0; pass < 2; ++pass) {
        for (int t = 0; t < 10; ++t) {
            const int k1 = first_of[static_cast<std::size_t>(t)];
            for (int k2 = 0; k2 < 64; ++k2) {
                if (square_distance(k1, k2) <= 1) continue;
                if (diagonal_offset(k1) == 0 && diagonal_offset(k2) > 0) continue;
                const bool both_diagonal = diagonal_offset(k1) == 0 && diagonal_offset(k2) == 0;
                if (both_diagonal != (pass == 1)) continue;
                g.king_pair[static_cast<std::size_t>(t)][static_cast<std::size_t>(k2)] = next++;
            }
        }
    }
    g.valid = next == 462 && order == -1;
}

// ---------------------------------------------------------------------------
// One compressed table (one side to move and, with pawns, one leading file).
struct Table {
    // Encoding: piece codes (format: P=1 N=2 B=3 R=4 Q=5 K=6, +8 for the
    // second colour) in the table's order, the groups and their factors.
    std::array<std::uint8_t, TableMaxPieces> pieces{};
    std::array<int, TableMaxPieces + 1> group_len{};
    std::array<std::uint64_t, TableMaxPieces + 1> group_factor{};
    int groups = 0;
    std::uint64_t size = 0;  // number of index values

    std::uint8_t flags = 0;
    bool constant = false;
    int constant_value = 0;

    int block_bits = 0;
    int index_bits = 0;
    std::uint64_t real_blocks = 0;
    std::uint64_t block_entries = 0;  // real blocks plus padding entries
    std::uint64_t index_entries = 0;
    const std::uint8_t* index_table = nullptr;  // 6 bytes per entry: block (u32), offset (u16)
    const std::uint8_t* block_sizes = nullptr;  // u16 per block: values in the block minus 1
    const std::uint8_t* blocks = nullptr;

    int min_len = 0;
    int max_len = 0;
    const std::uint8_t* first_symbol = nullptr;  // u16 per code length min_len..max_len
    std::vector<std::uint64_t> code_base;        // smallest code of each length, left-aligned
    const std::uint8_t* tree = nullptr;          // 3 bytes per symbol: two 12-bit halves
    std::uint32_t symbols = 0;
    std::vector<std::uint16_t> span;             // values per symbol minus 1

    // DTZ value maps (win, loss, cursed win, blessed loss).
    std::array<const std::uint8_t*, 4> map{};
    std::array<std::uint32_t, 4> map_len{};

    [[gnu::cold]] std::uint32_t left(std::uint32_t symbol) const {
        const std::uint8_t* w = tree + 3 * static_cast<std::size_t>(symbol);
        return static_cast<std::uint32_t>(w[0]) | (static_cast<std::uint32_t>(w[1] & 0x0F) << 8);
    }
    [[gnu::cold]] std::uint32_t right(std::uint32_t symbol) const {
        const std::uint8_t* w = tree + 3 * static_cast<std::size_t>(symbol);
        return (static_cast<std::uint32_t>(w[1]) >> 4) | (static_cast<std::uint32_t>(w[2]) << 4);
    }

    // Stored value at `index`, or -1 if the table data is inconsistent.
    [[gnu::cold]] int value(std::uint64_t index) const;
};

[[gnu::cold]] int Table::value(std::uint64_t index) const {
    if (constant) return constant_value;
    if (index >= size) return -1;
    const std::uint64_t entry = index >> index_bits;
    if (entry >= index_entries) return -1;
    const std::uint8_t* e = index_table + 6 * entry;
    std::uint64_t block = read32(e);
    // Position of `index` relative to the value in the middle of its section,
    // whose block and offset the entry stores.
    const std::int64_t half = std::int64_t{1} << (index_bits - 1);
    std::int64_t offset = static_cast<std::int64_t>(read16(e + 4)) +
                          static_cast<std::int64_t>(index & ((std::uint64_t{1} << index_bits) - 1)) - half;
    while (offset < 0) {
        if (block == 0) return -1;
        --block;
        offset += static_cast<std::int64_t>(read16(block_sizes + 2 * block)) + 1;
    }
    for (;;) {
        if (block >= block_entries) return -1;
        const std::int64_t in_block = static_cast<std::int64_t>(read16(block_sizes + 2 * block)) + 1;
        if (offset < in_block) break;
        offset -= in_block;
        ++block;
    }
    if (block >= real_blocks) return -1;

    // Walk the canonical Huffman codes of the block (bits most significant
    // first) to the symbol that covers `offset`.
    const std::size_t block_bytes = std::size_t{1} << block_bits;
    const std::uint8_t* p = blocks + block * block_bytes;
    const std::uint8_t* const end = p + block_bytes;
    std::uint64_t window = 0;
    int bits = 0;              // valid bits at the top of the window
    std::uint64_t used = 0;    // bits consumed
    const std::uint64_t limit = static_cast<std::uint64_t>(block_bytes) * 8;
    std::uint32_t symbol = 0;
    for (;;) {
        while (bits <= 56) {
            const std::uint64_t byte = p < end ? *p++ : 0;
            window |= byte << (56 - bits);
            bits += 8;
        }
        int len = min_len;
        while (window < code_base[static_cast<std::size_t>(len - min_len)]) {
            if (++len > max_len) return -1;
        }
        symbol = read16(first_symbol + 2 * static_cast<std::size_t>(len - min_len)) +
                 static_cast<std::uint32_t>((window - code_base[static_cast<std::size_t>(len - min_len)]) >> (64 - len));
        if (symbol >= symbols) return -1;
        const std::int64_t count = static_cast<std::int64_t>(span[symbol]) + 1;
        if (offset < count) break;
        offset -= count;
        window <<= len;
        bits -= len;
        used += static_cast<std::uint64_t>(len);
        if (used >= limit) return -1;
    }
    // Expand the RePair symbol down to the single value at `offset`.
    while (span[symbol] != 0) {
        const std::uint32_t l = left(symbol);
        const std::int64_t count = static_cast<std::int64_t>(span[l]) + 1;
        if (offset < count) {
            symbol = l;
        } else {
            offset -= count;
            symbol = right(symbol);
        }
    }
    return static_cast<int>(left(symbol));
}

// ---------------------------------------------------------------------------
// Material of a table, from its file name ("KRPvKR": white KRP, black KR).
struct Material {
    std::array<int, 16> count{};  // by format piece code
    int pieces = 0;
    bool pawns = false;
    bool symmetric = false;
    std::uint64_t key_as_named = 0;    // white = first part
    std::uint64_t key_swapped = 0;     // white = second part
};

// Piece counts of one side packed in 4-bit fields (pawn..queen).
[[gnu::cold]] std::uint64_t side_code(const std::array<int, 16>& count, int colour_offset) {
    std::uint64_t code = 0;
    for (int type = 1; type <= 5; ++type) {
        code |= static_cast<std::uint64_t>(count[static_cast<std::size_t>(type + colour_offset)]) << (4 * (type - 1));
    }
    return code;
}

[[gnu::cold]] std::uint64_t board_key(const Board& board) {
    std::uint64_t white = 0;
    std::uint64_t black = 0;
    for (int type = Pawn; type <= Queen; ++type) {
        white |= static_cast<std::uint64_t>(popcount(board.pieces(White, static_cast<PieceType>(type)))) << (4 * (type - 1));
        black |= static_cast<std::uint64_t>(popcount(board.pieces(Black, static_cast<PieceType>(type)))) << (4 * (type - 1));
    }
    return white | (black << 20);
}

[[gnu::cold]] bool parse_material(std::string_view name, Material& m) {
    const std::size_t v = name.find('v');
    if (v == std::string_view::npos || name.find('v', v + 1) != std::string_view::npos) return false;
    const std::string_view sides[2] = {name.substr(0, v), name.substr(v + 1)};
    for (int side = 0; side < 2; ++side) {
        const std::string_view s = sides[side];
        if (s.empty() || s[0] != 'K') return false;
        for (std::size_t i = 1; i < s.size(); ++i) {
            int type = 0;
            switch (s[i]) {
            case 'Q': type = Queen; break;
            case 'R': type = Rook; break;
            case 'B': type = Bishop; break;
            case 'N': type = Knight; break;
            case 'P': type = Pawn; break;
            default: return false;
            }
            ++m.count[static_cast<std::size_t>(type + 8 * side)];
        }
        ++m.count[static_cast<std::size_t>(King + 8 * side)];
    }
    for (const int c : m.count) m.pieces += c;
    if (m.pieces < 3 || m.pieces > TableMaxPieces) return false;
    m.pawns = m.count[Pawn] + m.count[Pawn + 8] > 0;
    const std::uint64_t first = side_code(m.count, 0);
    const std::uint64_t second = side_code(m.count, 8);
    m.symmetric = first == second;
    m.key_as_named = first | (second << 20);
    m.key_swapped = second | (first << 20);
    return true;
}

// ---------------------------------------------------------------------------
// A table file: WDL (two sides unless symmetric) or DTZ (one side).
struct TableFile {
    FileView file;
    bool dtz = false;
    bool pawns = false;
    bool split = false;
    int pieces = 0;
    int files = 1;
    int sides = 1;
    std::uint8_t lead_code = 0;  // pawn code of the leading colour
    int lead_count = 0;
    int other_pawns = 0;         // pawns of the other colour
    bool triple = false;         // pawnless: leading group of 3 unique pieces
    std::array<std::array<Table, 2>, 4> table{};  // [file][side]
    std::size_t tail = 0;        // bytes after the last block (checksum)
};

struct Parser {
    const std::uint8_t* base = nullptr;
    std::size_t size = 0;
    std::size_t pos = 0;
    bool ok = true;

    [[gnu::cold]] bool need(std::uint64_t bytes) {
        if (!ok || pos > size || bytes > size - pos) ok = false;
        return ok;
    }
};

// Groups and index factors of one table from its piece order and the order
// nibbles (`order`: position of the leading group in the index, `order2`:
// of the second colour's pawns, 0xF if none).
[[gnu::cold]] bool setup_encoding(const Geometry& g, const TableFile& f, Table& t, int order, int order2, int file) {
    int leading = f.pawns ? 0 : (f.triple ? 3 : 2);
    int n = 0;
    t.group_len.fill(0);
    t.group_factor.fill(0);
    t.group_len[0] = 1;
    for (int i = 1; i < f.pieces; ++i) {
        if (--leading > 0 || t.pieces[static_cast<std::size_t>(i)] == t.pieces[static_cast<std::size_t>(i - 1)]) {
            ++t.group_len[static_cast<std::size_t>(n)];
        } else {
            t.group_len[static_cast<std::size_t>(++n)] = 1;
        }
    }
    t.groups = n + 1;
    // Each code forms one run after the leading group.
    std::array<int, 16> seen{};
    int start = t.group_len[0];
    for (int group = 1; group < t.groups; ++group) {
        const std::uint8_t code = t.pieces[static_cast<std::size_t>(start)];
        if (seen[code]++ != 0) return false;
        start += t.group_len[static_cast<std::size_t>(group)];
    }
    const bool second_pawns = f.pawns && f.other_pawns > 0;
    if (second_pawns) {
        if (t.groups < 2 || t.group_len[1] != f.other_pawns || t.pieces[static_cast<std::size_t>(f.lead_count)] != (f.lead_code ^ 8)) return false;
    }
    if (f.pawns && t.group_len[0] != f.lead_count) return false;
    int next = second_pawns ? 2 : 1;
    int free_squares = 64 - t.group_len[0] - (second_pawns ? t.group_len[1] : 0);
    std::uint64_t factor = 1;
    std::array<bool, TableMaxPieces + 1> assigned{};
    for (int k = 0; next < t.groups || k == order || k == order2; ++k) {
        if (k > 15) return false;
        if (k == order) {
            t.group_factor[0] = factor;
            assigned[0] = true;
            const std::uint64_t lead = f.pawns ? g.lead_total[static_cast<std::size_t>(t.group_len[0])][static_cast<std::size_t>(file)]
                                               : (f.triple ? 31332U : 462U);
            factor *= lead;
        } else if (k == order2) {
            if (!second_pawns) return false;
            t.group_factor[1] = factor;
            assigned[1] = true;
            factor *= g.choose[static_cast<std::size_t>(t.group_len[1])][static_cast<std::size_t>(48 - t.group_len[0])];
        } else {
            if (next >= t.groups) return false;
            t.group_factor[static_cast<std::size_t>(next)] = factor;
            assigned[static_cast<std::size_t>(next)] = true;
            factor *= g.choose[static_cast<std::size_t>(t.group_len[static_cast<std::size_t>(next)])][static_cast<std::size_t>(free_squares)];
            free_squares -= t.group_len[static_cast<std::size_t>(next)];
            ++next;
        }
    }
    for (int group = 0; group < t.groups; ++group) {
        if (!assigned[static_cast<std::size_t>(group)]) return false;
    }
    t.size = factor;
    return t.size > 0;
}

// Symbol expansion lengths, with a check that the pair tree is acyclic.
[[gnu::cold]] bool compute_spans(Table& t) {
    t.span.assign(t.symbols, 0);
    std::vector<std::uint8_t> state(t.symbols, 0);  // 0 new, 1 in progress, 2 done
    std::vector<std::uint32_t> stack;
    for (std::uint32_t root = 0; root < t.symbols; ++root) {
        if (state[root] == 2) continue;
        stack.push_back(root);
        while (!stack.empty()) {
            const std::uint32_t s = stack.back();
            if (t.right(s) == 0xFFF) {  // terminal symbol: one value
                t.span[s] = 0;
                state[s] = 2;
                stack.pop_back();
                continue;
            }
            const std::uint32_t l = t.left(s);
            const std::uint32_t r = t.right(s);
            if (l >= t.symbols || r >= t.symbols) return false;
            if (state[s] == 0) {
                state[s] = 1;
                if (state[l] == 1 || state[r] == 1) return false;
                if (state[l] == 0) stack.push_back(l);
                if (state[r] == 0) stack.push_back(r);
                continue;
            }
            if (state[l] != 2 || state[r] != 2) {
                if (state[l] == 1 || state[r] == 1) return false;
                if (state[l] == 0) stack.push_back(l);
                if (state[r] == 0) stack.push_back(r);
                continue;
            }
            const std::uint32_t total = static_cast<std::uint32_t>(t.span[l]) + t.span[r] + 1;
            if (total > 0xFFFF) return false;
            t.span[s] = static_cast<std::uint16_t>(total);
            state[s] = 2;
            stack.pop_back();
        }
    }
    return true;
}

// Header of one compressed table: index parameters, Huffman code lengths,
// RePair symbols (or a constant value).
[[gnu::cold]] bool parse_table_header(Parser& in, Table& t) {
    if (!in.need(2)) return false;
    const std::uint8_t* h = in.base + in.pos;
    t.flags = h[0];
    if ((t.flags & 0x80) != 0) {
        t.constant = true;
        t.constant_value = h[1];
        in.pos += 2;
        return true;
    }
    if (!in.need(10)) return false;
    t.block_bits = h[1];
    t.index_bits = h[2];
    const std::uint64_t padding = h[3];
    t.real_blocks = read32(h + 4);
    t.block_entries = t.real_blocks + padding;
    t.max_len = h[8];
    t.min_len = h[9];
    if (t.block_bits < 1 || t.block_bits > 20 || t.index_bits < 1 || t.index_bits > 40 || t.min_len < 1 ||
        t.max_len < t.min_len || t.max_len > 32 || t.real_blocks == 0) {
        return false;
    }
    const std::size_t lengths = static_cast<std::size_t>(t.max_len - t.min_len + 1);
    in.pos += 10;
    if (!in.need(2 * lengths + 2)) return false;
    t.first_symbol = in.base + in.pos;
    t.symbols = read16(in.base + in.pos + 2 * lengths);
    in.pos += 2 * lengths + 2;
    if (t.symbols == 0 || !in.need(3 * static_cast<std::uint64_t>(t.symbols))) return false;
    t.tree = in.base + in.pos;
    in.pos += 3 * static_cast<std::size_t>(t.symbols) + (t.symbols & 1U);
    // Canonical code: longer codes have smaller values; first_symbol[i] is the
    // first symbol of length min_len + i, symbols of longer codes come first.
    t.code_base.assign(lengths, 0);
    for (std::size_t i = lengths - 1; i-- > 0;) {
        const std::int64_t count = static_cast<std::int64_t>(read16(t.first_symbol + 2 * i)) -
                                   static_cast<std::int64_t>(read16(t.first_symbol + 2 * (i + 1)));
        if (count < 0) return false;
        t.code_base[i] = (t.code_base[i + 1] + static_cast<std::uint64_t>(count)) / 2;
    }
    for (std::size_t i = 0; i < lengths; ++i) {
        const int len = t.min_len + static_cast<int>(i);
        if (t.code_base[i] >= (std::uint64_t{1} << len)) return false;
        t.code_base[i] <<= 64 - len;
    }
    return compute_spans(t);
}

[[gnu::cold]] bool parse_file(const Geometry& g, const Material& m, bool dtz, TableFile& f) {
    Parser in{f.file.data(), f.file.size(), 0, true};
    if (!in.need(6)) return false;
    if (read32(in.base) != (dtz ? DtzMagic : WdlMagic)) return false;
    const std::uint8_t header = in.base[4];
    f.dtz = dtz;
    f.split = (header & 1) != 0;
    f.pawns = (header & 2) != 0;
    f.pieces = header >> 4;
    if (f.pieces != m.pieces || f.pawns != m.pawns) return false;
    if (!dtz && f.split == m.symmetric) return false;
    f.files = f.pawns ? 4 : 1;
    f.sides = dtz ? 1 : (f.split ? 2 : 1);
    int unique = 0;
    for (const int c : m.count) unique += c == 1 ? 1 : 0;
    f.triple = !f.pawns && unique >= 3;
    const bool both_pawns = m.count[Pawn] > 0 && m.count[Pawn + 8] > 0;
    in.pos = 5;
    std::array<std::array<int, 2>, 4> order{};
    std::array<std::array<int, 2>, 4> order2{};
    for (int file = 0; file < f.files; ++file) {
        const int order_bytes = both_pawns ? 2 : 1;
        if (!in.need(static_cast<std::uint64_t>(order_bytes + f.pieces))) return false;
        const std::uint8_t* p = in.base + in.pos;
        for (int side = 0; side < f.sides; ++side) {
            const int shift = side == 0 ? 0 : 4;
            order[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)] = (p[0] >> shift) & 0xF;
            order2[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)] = both_pawns ? (p[1] >> shift) & 0xF : 0xF;
            Table& t = f.table[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)];
            std::array<int, 16> count{};
            for (int i = 0; i < f.pieces; ++i) {
                const std::uint8_t code = static_cast<std::uint8_t>((p[order_bytes + i] >> shift) & 0xF);
                t.pieces[static_cast<std::size_t>(i)] = code;
                ++count[code];
            }
            if (count != m.count) return false;
        }
        in.pos += static_cast<std::size_t>(order_bytes + f.pieces);
    }
    if (f.pawns) {
        f.lead_code = f.table[0][0].pieces[0];
        if (f.lead_code != Pawn && f.lead_code != Pawn + 8) return false;
        f.lead_count = m.count[f.lead_code];
        f.other_pawns = m.count[f.lead_code ^ 8];
    }
    for (int file = 0; file < f.files; ++file) {
        for (int side = 0; side < f.sides; ++side) {
            Table& t = f.table[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)];
            if (f.pawns) {
                for (int i = 0; i < f.lead_count; ++i) {
                    if (t.pieces[static_cast<std::size_t>(i)] != f.lead_code) return false;
                }
            } else if (f.triple) {
                for (int i = 0; i < 3; ++i) {
                    if (m.count[t.pieces[static_cast<std::size_t>(i)]] != 1) return false;
                }
            } else {
                if (t.pieces[0] + t.pieces[1] != King + King + 8 || t.pieces[0] == t.pieces[1]) return false;
            }
            if (!setup_encoding(g, f, t, order[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)],
                                order2[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)], file)) {
                return false;
            }
        }
    }
    in.pos += in.pos & 1U;
    for (int file = 0; file < f.files; ++file) {
        for (int side = 0; side < f.sides; ++side) {
            Table& t = f.table[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)];
            if (!parse_table_header(in, t)) return false;
            if (!t.constant) {
                t.index_entries = (t.size + (std::uint64_t{1} << t.index_bits) - 1) >> t.index_bits;
            }
        }
    }
    if (dtz) {
        // Value maps of the DTZ tables that use them (flag bit 1), 8-bit or
        // (flag bit 4) 16-bit entries, in the category order win, loss,
        // cursed win, blessed loss.
        for (int file = 0; file < f.files; ++file) {
            Table& t = f.table[static_cast<std::size_t>(file)][0];
            if ((t.flags & 2) == 0) continue;
            const bool wide = (t.flags & 16) != 0;
            if (wide) in.pos += in.pos & 1U;
            for (std::size_t category = 0; category < 4; ++category) {
                if (wide) {
                    if (!in.need(2)) return false;
                    const std::uint32_t n = read16(in.base + in.pos);
                    if (!in.need(2 + 2 * static_cast<std::uint64_t>(n))) return false;
                    t.map[category] = in.base + in.pos + 2;
                    t.map_len[category] = n;
                    in.pos += 2 + 2 * static_cast<std::size_t>(n);
                } else {
                    if (!in.need(1)) return false;
                    const std::uint32_t n = in.base[in.pos];
                    if (!in.need(1 + static_cast<std::uint64_t>(n))) return false;
                    t.map[category] = in.base + in.pos + 1;
                    t.map_len[category] = n;
                    in.pos += 1 + static_cast<std::size_t>(n);
                }
            }
        }
        in.pos += in.pos & 1U;
    }
    for (int file = 0; file < f.files; ++file) {
        for (int side = 0; side < f.sides; ++side) {
            Table& t = f.table[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)];
            if (!in.need(6 * t.index_entries)) return false;
            t.index_table = in.base + in.pos;
            in.pos += static_cast<std::size_t>(6 * t.index_entries);
        }
    }
    for (int file = 0; file < f.files; ++file) {
        for (int side = 0; side < f.sides; ++side) {
            Table& t = f.table[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)];
            if (!in.need(2 * t.block_entries)) return false;
            t.block_sizes = in.base + in.pos;
            in.pos += static_cast<std::size_t>(2 * t.block_entries);
        }
    }
    for (int file = 0; file < f.files; ++file) {
        for (int side = 0; side < f.sides; ++side) {
            Table& t = f.table[static_cast<std::size_t>(file)][static_cast<std::size_t>(side)];
            in.pos = (in.pos + 63) & ~static_cast<std::size_t>(63);
            const std::uint64_t bytes = t.constant ? 0 : (t.real_blocks << t.block_bits);
            if (!in.need(bytes)) return false;
            t.blocks = in.base + in.pos;
            in.pos += static_cast<std::size_t>(bytes);
        }
    }
    f.tail = in.size - in.pos;
    return in.ok;
}

// ---------------------------------------------------------------------------
struct Entry {
    std::string name;
    Material material;
    std::unique_ptr<TableFile> wdl;
    std::unique_ptr<TableFile> dtz;
};

struct Slot {
    std::uint64_t key = 0;
    std::int32_t entry = -1;
    bool swapped = false;
};

struct Registry {
    Geometry geometry;
    std::vector<std::unique_ptr<Entry>> entries;
    std::vector<Slot> slots;  // open addressing, power-of-two size
    int max_pieces = 0;

    [[gnu::cold]] static std::size_t hash(std::uint64_t key, std::size_t mask) {
        return static_cast<std::size_t>((key * 0x9E3779B97F4A7C15ULL) >> 32) & mask;
    }
    [[gnu::cold]] void insert(std::uint64_t key, std::int32_t entry, bool swapped) {
        const std::size_t mask = slots.size() - 1;
        for (std::size_t i = hash(key, mask);; i = (i + 1) & mask) {
            if (slots[i].entry < 0) {
                slots[i] = Slot{key, entry, swapped};
                return;
            }
            if (slots[i].key == key) return;  // first table found wins
        }
    }
    [[gnu::cold]] const Slot* find(std::uint64_t key) const {
        if (slots.empty()) return nullptr;
        const std::size_t mask = slots.size() - 1;
        for (std::size_t i = hash(key, mask);; i = (i + 1) & mask) {
            if (slots[i].entry < 0) return nullptr;
            if (slots[i].key == key) return &slots[i];
        }
    }
};

std::atomic<const Registry*> g_registry{nullptr};

[[gnu::cold]] const Registry* registry() { return g_registry.load(std::memory_order_acquire); }

// ---------------------------------------------------------------------------
// Position -> table and index.
struct Lookup {
    const Entry* entry = nullptr;
    bool flip = false;  // swap colours and mirror ranks to match the table
    int side = 0;       // side to move in table orientation (0 = first-named side)
};

[[gnu::cold]] bool find_entry(const Registry& r, const Board& board, Lookup& out) {
    const Slot* slot = r.find(board_key(board));
    if (slot == nullptr) return false;
    out.entry = r.entries[static_cast<std::size_t>(slot->entry)].get();
    // Symmetric materials store only the first side to move: mirror the
    // position whenever the second side is to move.
    out.flip = out.entry->material.symmetric ? board.side_to_move() == Black : slot->swapped;
    out.side = (board.side_to_move() == Black) != out.flip ? 1 : 0;
    return true;
}

[[gnu::cold]] void sort_squares(int* first, int* last) {
    for (int* i = first + 1; i < last; ++i) {
        const int value = *i;
        int* j = i;
        while (j > first && *(j - 1) > value) {
            *j = *(j - 1);
            --j;
        }
        *j = value;
    }
}

// Selects the table (side `side`; the file follows from the leading pawn)
// and computes the index of the position. Returns nullptr on a mismatch.
[[gnu::cold]] const Table* locate(const Geometry& g, const TableFile& f, const Board& board, bool flip, int side,
                                  std::uint64_t& index) {
    std::array<std::array<int, TableMaxPieces>, 16> by_code{};
    std::array<int, 16> available{};
    const int colour_flip = flip ? 8 : 0;
    const int rank_flip = flip ? 56 : 0;
    for (const Color colour : {White, Black}) {
        for (int type = Pawn; type <= King; ++type) {
            Bitboard bb = board.pieces(colour, static_cast<PieceType>(type));
            const std::size_t code = static_cast<std::size_t>((type + (colour == Black ? 8 : 0)) ^ colour_flip);
            while (bb != 0) {
                if (available[code] >= TableMaxPieces) return nullptr;
                by_code[code][static_cast<std::size_t>(available[code]++)] = pop_lsb(bb) ^ rank_flip;
            }
        }
    }
    int file_index = 0;
    int mirror = 0;
    if (f.pawns) {
        auto& lead = by_code[f.lead_code];
        if (available[f.lead_code] != f.lead_count) return nullptr;
        int best = 0;
        for (int i = 1; i < f.lead_count; ++i) {
            if (g.pawn_rank[static_cast<std::size_t>(lead[static_cast<std::size_t>(i)])] >
                g.pawn_rank[static_cast<std::size_t>(lead[static_cast<std::size_t>(best)])]) {
                best = i;
            }
        }
        std::swap(lead[0], lead[static_cast<std::size_t>(best)]);
        const int file = file_of(lead[0]);
        file_index = file < 4 ? file : 7 - file;
        mirror = file < 4 ? 0 : 7;
    }
    const Table& t = f.table[static_cast<std::size_t>(file_index)][static_cast<std::size_t>(side)];
    std::array<int, TableMaxPieces> sq{};
    std::array<int, 16> taken{};
    for (int i = 0; i < f.pieces; ++i) {
        const std::size_t code = t.pieces[static_cast<std::size_t>(i)];
        if (taken[code] >= available[code]) return nullptr;
        sq[static_cast<std::size_t>(i)] = by_code[code][static_cast<std::size_t>(taken[code]++)] ^ mirror;
    }

    std::uint64_t lead_index = 0;
    int placed = 0;
    if (f.pawns) {
        const int count = t.group_len[0];
        lead_index = g.lead_offset[static_cast<std::size_t>(count)][static_cast<std::size_t>(sq[0])];
        // Other leading pawns: a combination of pawn-rank values below the
        // leading pawn's, taken in ascending order.
        for (int i = 1; i < count; ++i) {
            for (int j = i + 1; j < count; ++j) {
                if (g.pawn_rank[static_cast<std::size_t>(sq[static_cast<std::size_t>(j)])] <
                    g.pawn_rank[static_cast<std::size_t>(sq[static_cast<std::size_t>(i)])]) {
                    std::swap(sq[static_cast<std::size_t>(i)], sq[static_cast<std::size_t>(j)]);
                }
            }
        }
        for (int i = 1; i < count; ++i) {
            lead_index += g.choose[static_cast<std::size_t>(i)]
                                  [static_cast<std::size_t>(g.pawn_rank[static_cast<std::size_t>(sq[static_cast<std::size_t>(i)])])];
        }
        placed = count;
    } else {
        // Mirror so that the first piece is on files a-d, ranks 1-4, and the
        // first leading piece off the a1-h8 diagonal is below it.
        if (file_of(sq[0]) >= 4) {
            for (int i = 0; i < f.pieces; ++i) sq[static_cast<std::size_t>(i)] ^= 7;
        }
        if (rank_of(sq[0]) >= 4) {
            for (int i = 0; i < f.pieces; ++i) sq[static_cast<std::size_t>(i)] ^= 56;
        }
        const int lead_len = t.group_len[0];
        for (int i = 0; i < lead_len; ++i) {
            const int d = diagonal_offset(sq[static_cast<std::size_t>(i)]);
            if (d == 0) continue;
            if (d > 0) {
                for (int j = i; j < f.pieces; ++j) {
                    const int s = sq[static_cast<std::size_t>(j)];
                    sq[static_cast<std::size_t>(j)] = ((s >> 3) | (s << 3)) & 63;
                }
            }
            break;
        }
        const int s0 = sq[0];
        const int s1 = sq[1];
        if (g.triangle[static_cast<std::size_t>(s0)] < 0) return nullptr;
        if (f.triple) {
            const int s2 = sq[2];
            const int a1 = s1 > s0 ? 1 : 0;
            const int a2 = (s2 > s0 ? 1 : 0) + (s2 > s1 ? 1 : 0);
            std::int64_t v = 0;
            if (diagonal_offset(s0) != 0) {
                v = (static_cast<std::int64_t>(g.triangle[static_cast<std::size_t>(s0)]) * 63 + (s1 - a1)) * 62 + (s2 - a2);
            } else if (diagonal_offset(s1) != 0) {
                v = 6 * 63 * 62 + (static_cast<std::int64_t>(rank_of(s0)) * 28 + g.below[static_cast<std::size_t>(s1)]) * 62 + (s2 - a2);
            } else if (diagonal_offset(s2) != 0) {
                v = 6 * 63 * 62 + 4 * 28 * 62 + static_cast<std::int64_t>(rank_of(s0)) * 7 * 28 +
                    static_cast<std::int64_t>(rank_of(s1) - a1) * 28 + g.below[static_cast<std::size_t>(s2)];
            } else {
                v = 6 * 63 * 62 + 4 * 28 * 62 + 4 * 7 * 28 + static_cast<std::int64_t>(rank_of(s0)) * 7 * 6 +
                    static_cast<std::int64_t>(rank_of(s1) - a1) * 6 + (rank_of(s2) - a2);
            }
            if (v < 0 || v >= 31332) return nullptr;
            lead_index = static_cast<std::uint64_t>(v);
        } else {
            const int v = g.king_pair[static_cast<std::size_t>(g.triangle[static_cast<std::size_t>(s0)])][static_cast<std::size_t>(s1)];
            if (v < 0) return nullptr;
            lead_index = static_cast<std::uint64_t>(v);
        }
        placed = lead_len;
    }

    index = lead_index * t.group_factor[0];
    for (int group = 1; group < t.groups; ++group) {
        const int len = t.group_len[static_cast<std::size_t>(group)];
        sort_squares(sq.data() + placed, sq.data() + placed + len);
        const int pawn_shift = (f.pawns && group == 1 && f.other_pawns > 0) ? 8 : 0;
        std::uint64_t sub = 0;
        for (int j = 0; j < len; ++j) {
            const int s = sq[static_cast<std::size_t>(placed + j)];
            int below_count = 0;
            for (int k = 0; k < placed; ++k) below_count += sq[static_cast<std::size_t>(k)] < s ? 1 : 0;
            const int v = s - below_count - pawn_shift;
            if (v < 0) return nullptr;
            sub += g.choose[static_cast<std::size_t>(j + 1)][static_cast<std::size_t>(v)];
        }
        index += sub * t.group_factor[static_cast<std::size_t>(group)];
        placed += len;
    }
    if (index >= t.size) return nullptr;
    return &t;
}

// Stored WDL value of the position itself (no capture resolution, en passant ignored).
[[gnu::cold]] bool table_wdl(const Registry& r, const Board& board, int& wdl) {
    if (popcount(board.occupied()) == 2) {
        wdl = 0;
        return true;
    }
    Lookup at;
    if (!find_entry(r, board, at) || !at.entry->wdl) return false;
    const TableFile& f = *at.entry->wdl;
    if (at.side >= f.sides) return false;
    std::uint64_t index = 0;
    const Table* t = locate(r.geometry, f, board, at.flip, at.side, index);
    if (t == nullptr) return false;
    const int v = t->value(index);
    if (v < 0 || v > 4) return false;
    wdl = v - 2;
    return true;
}

enum class DtzLookup { Ok, OtherSide, Fail };

// Stored DTZ of the position, in plies, for its known WDL value.
[[gnu::cold]] DtzLookup table_dtz(const Registry& r, const Board& board, int wdl, int& plies, bool& rounded) {
    Lookup at;
    if (!find_entry(r, board, at) || !at.entry->dtz) return DtzLookup::Fail;
    const TableFile& f = *at.entry->dtz;
    std::uint64_t index = 0;
    const Table* t = locate(r.geometry, f, board, at.flip, 0, index);
    if (t == nullptr) return DtzLookup::Fail;
    // One side to move per file is stored (flag bit 0); symmetric pawnless
    // materials serve both.
    if ((t->flags & 1) != at.side && !(at.entry->material.symmetric && !f.pawns)) return DtzLookup::OtherSide;
    int v = t->value(index);
    if (v < 0) return DtzLookup::Fail;
    if ((t->flags & 2) != 0) {
        const std::size_t category = wdl == 2 ? 0 : wdl == -2 ? 1 : wdl == 1 ? 2 : 3;
        if (static_cast<std::uint32_t>(v) >= t->map_len[category]) return DtzLookup::Fail;
        v = (t->flags & 16) != 0 ? read16(t->map[category] + 2 * static_cast<std::size_t>(v))
                                 : t->map[category][static_cast<std::size_t>(v)];
    }
    // Stored in moves unless the plies flag of a plain win (bit 2) or loss (bit 3)
    // is set. A value in moves is rounded: the true distance is one ply longer
    // when its parity is not the stored one (DTZ50'' rounding).
    const bool in_plies = (wdl == 2 && (t->flags & 4) != 0) || (wdl == -2 && (t->flags & 8) != 0);
    plies = (in_plies ? v : 2 * v) + 1;
    rounded = !in_plies;
    return DtzLookup::Ok;
}

// Value of a position reached by a capture (so no en passant is possible):
// the best of its own stored value and all its captures, alpha-beta bounded.
[[gnu::cold]] bool resolve_captures(const Registry& r, Board& board, int alpha, int beta, int& out) {
    if (popcount(board.occupied()) == 2) {
        out = 0;
        return true;
    }
    const MoveList moves = board.legal_moves(true);
    for (const Move move : moves) {
        if (!move.is_capture()) continue;
        Undo undo;
        (void)board.make_move(move, undo);
        int v = 0;
        const bool ok = resolve_captures(r, board, -beta, -alpha, v);
        board.unmake_move(move, undo);
        if (!ok) return false;
        v = -v;
        if (v > alpha) {
            if (v >= beta) {
                out = v;
                return true;
            }
            alpha = v;
        }
    }
    int stored = 0;
    if (!table_wdl(r, board, stored)) return false;
    out = std::max(alpha, stored);
    return true;
}

struct NodeValue {
    int wdl = 0;
    bool zeroing = false;  // a capture (or, if asked, pawn move) achieves the value: DTZ table not usable
    bool mated = false;
};

// Exact WDL of a position that may allow en passant: captures (and, for DTZ,
// pawn moves) are resolved, the stored value covers the other moves. If every
// legal move was examined the stored value is not used at all.
[[gnu::cold]] bool node_wdl(const Registry& r, Board& board, bool pawn_moves, NodeValue& out) {
    out = NodeValue{};
    if (popcount(board.occupied()) == 2) return true;
    const MoveList legal = board.legal_moves();
    if (legal.empty()) {
        out.mated = board.in_check();
        out.wdl = out.mated ? -2 : 0;
        return true;
    }
    int best = -3;
    std::size_t examined = 0;
    for (const Move move : legal) {
        const bool capture = move.is_capture();
        if (!capture && !(pawn_moves && piece_type(board.moved_piece(move)) == Pawn)) continue;
        ++examined;
        Undo undo;
        (void)board.make_move(move, undo);
        int v = 0;
        bool ok = true;
        if (capture) {
            ok = resolve_captures(r, board, -2, -best, v);
            v = -v;
        } else {
            NodeValue child;
            ok = node_wdl(r, board, false, child);
            v = -child.wdl;
        }
        board.unmake_move(move, undo);
        if (!ok) return false;
        if (v > best) {
            best = v;
            if (best == 2) {
                out.wdl = 2;
                out.zeroing = true;
                return true;
            }
        }
    }
    if (examined == legal.size()) {
        out.wdl = best;
        out.zeroing = true;
        return true;
    }
    int stored = 0;
    if (!table_wdl(r, board, stored)) return false;
    if (best >= stored) {
        out.wdl = best;
        out.zeroing = best > 0;
        return true;
    }
    out.wdl = stored;
    return true;
}

// DTZ of a position whose best move is zeroing (capture or pawn move).
[[gnu::cold]] int zeroing_dtz(int wdl) {
    return wdl == 2 ? 1 : wdl == 1 ? 101 : wdl == -1 ? -101 : wdl == -2 ? -1 : 0;
}

[[gnu::cold]] int sign_of(int v) { return (v > 0) - (v < 0); }

[[gnu::cold]] bool dtz_value(const Registry& r, Board& board, int& dtz, bool& rounded, int depth) {
    rounded = false;
    NodeValue node;
    if (!node_wdl(r, board, true, node)) return false;
    if (node.wdl == 0) {
        dtz = 0;
        return true;
    }
    if (node.mated) {
        dtz = -1;
        return true;
    }
    if (node.zeroing) {
        dtz = zeroing_dtz(node.wdl);
        return true;
    }
    int plies = 0;
    switch (table_dtz(r, board, node.wdl, plies, rounded)) {
    case DtzLookup::Ok:
        dtz = sign_of(node.wdl) * (plies + (node.wdl == 1 || node.wdl == -1 ? 100 : 0));
        return true;
    case DtzLookup::Fail:
        return false;
    case DtzLookup::OtherSide:
        break;
    }
    if (depth >= 2) return false;
    // The table stores the other side to move: one ply of search. A winner
    // takes the shortest, a loser the longest way to the next zeroing move.
    // A rounded child value is a lower bound of its magnitude (by at most one
    // ply): a winner's result is exact if an exact move reaches the minimum, a
    // loser's if no rounded move reaches the maximum.
    const MoveList legal = board.legal_moves();
    bool found = false;
    int best = 0;
    bool best_exact = false;    // winner: some exact move reaches best
    bool best_rounded = false;  // loser: some rounded move reaches best
    for (const Move move : legal) {
        const bool zeroing = move.is_capture() || piece_type(board.moved_piece(move)) == Pawn;
        Undo undo;
        (void)board.make_move(move, undo);
        int v = 0;
        bool ok = true;
        bool child_rounded = false;
        if (zeroing) {
            NodeValue child;
            ok = node_wdl(r, board, false, child);
            v = -zeroing_dtz(child.wdl);
        } else {
            int child = 0;
            ok = dtz_value(r, board, child, child_rounded, depth + 1);
            v = -child;
            if (ok && !(v == 1 && board.in_check() && !board.has_legal_move())) v += sign_of(v);
        }
        board.unmake_move(move, undo);
        if (!ok) return false;
        if (sign_of(v) != sign_of(node.wdl)) continue;
        if (!found || v < best) {
            best = v;
            found = true;
            best_exact = !child_rounded;
            best_rounded = child_rounded;
        } else if (v == best) {
            best_exact = best_exact || !child_rounded;
            best_rounded = best_rounded || child_rounded;
        }
    }
    if (!found) return false;
    dtz = best;
    rounded = node.wdl > 0 ? !best_exact : best_rounded;
    return true;
}

[[gnu::cold]] bool probe_allowed(const Registry* r, const Board& board) {
    return r != nullptr && board.castling_rights() == 0 && popcount(board.occupied()) <= r->max_pieces;
}

// True if some position since the last zeroing move occurred twice.
[[gnu::cold]] bool repeated_since_zeroing(const Board& board) {
    const auto& keys = board.key_history();
    if (keys.empty()) return false;
    const std::size_t last = keys.size() - 1;
    const std::size_t window = std::min<std::size_t>(static_cast<std::size_t>(board.halfmove_clock()), last);
    for (std::size_t i = last - window; i <= last; ++i) {
        for (std::size_t j = i + 4; j <= last; j += 2) {
            if (keys[i] == keys[j]) return true;
        }
    }
    return false;
}

// Root rank of a move from its DTZ (counted from the root position).
[[gnu::cold]] int dtz_rank(int dtz, int counter, bool repeated, bool rule50) {
    if (dtz > 0) {
        if (!rule50) return (repeated || dtz > 100) ? 2000 - std::min(dtz, 999) : 2000;
        // Certain win: zeroing before the 50-move rule even with DTZ rounding.
        if (dtz + counter <= 99) return repeated ? 2000 - dtz : 2000;
        return 1000 - std::min(dtz + counter, 999);  // only if the opponent errs
    }
    if (dtz < 0) {
        const int d = -dtz;
        if (!rule50) return -2000 + (d > 100 ? std::min(d, 999) : 0);
        if (d + counter >= 101) return -1000 + std::min(d + counter, 999);  // a 50-move draw is in reach
        return -2000;
    }
    return 0;
}

[[gnu::cold]] int wdl_rank(int wdl, bool rule50) {
    switch (wdl) {
    case 2: return 2000;
    case 1: return rule50 ? 500 : 1900;
    case -1: return rule50 ? -500 : -1900;
    case -2: return -2000;
    default: return 0;
    }
}

struct NamedFile {
    std::string stem;
    std::filesystem::path path;
};

[[gnu::cold]] const NamedFile* find_named(const std::vector<NamedFile>& files, const std::string& stem) {
    for (const NamedFile& f : files) {
        if (f.stem == stem) return &f;
    }
    return nullptr;
}

} // namespace

// ---------------------------------------------------------------------------
// Public interface.

[[gnu::cold]] void set_heap_loading(bool enabled) { g_heap_loading = enabled; }

[[gnu::cold]] int max_pieces() {
    const Registry* r = registry();
    return r != nullptr ? r->max_pieces : 0;
}

[[gnu::cold]] bool has_table(const std::string& name) {
    const Registry* r = registry();
    if (r == nullptr) return false;
    for (const auto& entry : r->entries) {
        if (entry->name == name) return entry->dtz != nullptr;
    }
    return false;
}

[[gnu::cold]] std::vector<TableInfo> loaded_tables() {
    std::vector<TableInfo> out;
    const Registry* r = registry();
    if (r == nullptr) return out;
    for (const auto& entry : r->entries) {
        out.push_back(TableInfo{entry->name + ".rtbw", entry->wdl->file.size(), entry->wdl->tail});
        if (entry->dtz) out.push_back(TableInfo{entry->name + ".rtbz", entry->dtz->file.size(), entry->dtz->tail});
    }
    return out;
}

[[gnu::cold]] LoadSummary load(const std::string& paths) {
    LoadSummary summary;
    search_cardinality.store(0, std::memory_order_relaxed);
    root_display.store(0, std::memory_order_relaxed);
    tb_scores = false;
    delete g_registry.exchange(nullptr, std::memory_order_acq_rel);
    std::string trimmed = paths;
    while (!trimmed.empty() && (trimmed.back() == ' ' || trimmed.back() == '\r' || trimmed.back() == '\n')) trimmed.pop_back();
    while (!trimmed.empty() && trimmed.front() == ' ') trimmed.erase(trimmed.begin());
    if (trimmed.empty() || trimmed == "<empty>") return summary;

    auto r = std::make_unique<Registry>();
    build_geometry(r->geometry);
    if (!r->geometry.valid) return summary;
#if defined(_WIN32)
    constexpr char separator = ';';
#else
    constexpr char separator = ':';
#endif
    // Table name -> file, first directory wins. (Plain vectors: no tree
    // templates, whose local clones GCC would place before the search code.)
    std::vector<NamedFile> wdl_files;
    std::vector<NamedFile> dtz_files;
    std::size_t start = 0;
    while (start <= trimmed.size()) {
        std::size_t end = trimmed.find(separator, start);
        if (end == std::string::npos) end = trimmed.size();
        const std::string dir = trimmed.substr(start, end - start);
        start = end + 1;
        if (dir.empty()) continue;
        const std::filesystem::path folder(std::u8string(reinterpret_cast<const char8_t*>(dir.data()), dir.size()));
        std::error_code ec;
        std::filesystem::directory_iterator it(folder, ec);
        for (; !ec && it != std::filesystem::directory_iterator(); it.increment(ec)) {
            std::error_code type_ec;
            if (!it->is_regular_file(type_ec) || type_ec) continue;
            const std::u8string file_name = it->path().filename().u8string();
            const std::string name(reinterpret_cast<const char*>(file_name.data()), file_name.size());
            if (name.size() < 6) continue;
            const std::string stem = name.substr(0, name.size() - 5);
            const std::string ext = name.substr(name.size() - 5);
            if (ext == ".rtbw" && find_named(wdl_files, stem) == nullptr) wdl_files.push_back(NamedFile{stem, it->path()});
            else if (ext == ".rtbz" && find_named(dtz_files, stem) == nullptr) dtz_files.push_back(NamedFile{stem, it->path()});
        }
    }

    for (const NamedFile& wdl : wdl_files) {
        Material material;
        if (!parse_material(wdl.stem, material)) continue;
        auto entry = std::make_unique<Entry>();
        entry->name = wdl.stem;
        entry->material = material;
        entry->wdl = std::make_unique<TableFile>();
        if (!entry->wdl->file.open(wdl.path) || !parse_file(r->geometry, material, false, *entry->wdl)) {
            ++summary.rejected;
            continue;
        }
        if (const NamedFile* dtz = find_named(dtz_files, wdl.stem)) {
            entry->dtz = std::make_unique<TableFile>();
            if (!entry->dtz->file.open(dtz->path) || !parse_file(r->geometry, material, true, *entry->dtz)) {
                ++summary.rejected;
                entry->dtz.reset();
            } else {
                ++summary.dtz_tables;
            }
        }
        ++summary.wdl_tables;
        r->max_pieces = std::max(r->max_pieces, material.pieces);
        r->entries.push_back(std::move(entry));
    }
    // A DTZ file without its WDL file is not used (the probes need WDL first).
    if (r->entries.empty()) return summary;
    std::size_t capacity = 16;
    while (capacity < 4 * r->entries.size()) capacity *= 2;
    r->slots.assign(capacity, Slot{});
    for (std::size_t i = 0; i < r->entries.size(); ++i) {
        const Material& m = r->entries[i]->material;
        r->insert(m.key_as_named, static_cast<std::int32_t>(i), false);
        if (!m.symmetric) r->insert(m.key_swapped, static_cast<std::int32_t>(i), true);
    }
    summary.max_pieces = r->max_pieces;
    g_registry.store(r.release(), std::memory_order_release);
    tb_scores = true;
    return summary;
}

[[gnu::cold]] bool probe_wdl(Board& board, int& wdl) {
    const Registry* r = registry();
    if (!probe_allowed(r, board)) return false;
    NodeValue node;
    if (!node_wdl(*r, board, false, node)) return false;
    wdl = node.wdl;
    return true;
}

[[gnu::cold]] bool probe_dtz(Board& board, int& dtz, bool& rounded) {
    const Registry* r = registry();
    if (!probe_allowed(r, board)) return false;
    return dtz_value(*r, board, dtz, rounded, 0);
}

[[gnu::cold]] bool probe_dtz(Board& board, int& dtz) {
    bool rounded = false;
    return probe_dtz(board, dtz, rounded);
}

[[gnu::cold]] bool probe_wdl_with_counter(Board& board, int& wdl) {
    int dtz = 0;
    bool rounded = false;
    if (!probe_dtz(board, dtz, rounded)) return false;
    const int counter = board.halfmove_clock();
    const int distance = (dtz < 0 ? -dtz : dtz) + counter;
    // A rounded distance of exactly 100 may truly be 101: undecided.
    if (dtz != 0 && rounded && distance == 100) return false;
    if (dtz == 0) wdl = 0;
    else if (dtz > 0) wdl = distance <= 100 ? 2 : 1;
    else wdl = distance <= 100 ? -2 : -1;
    return true;
}

[[gnu::cold]] bool rank_root_moves(Board& board, bool rule50, std::vector<RootRank>& ranks, bool& used_dtz) {
    ranks.clear();
    used_dtz = false;
    const Registry* r = registry();
    if (!probe_allowed(r, board)) return false;
    const MoveList legal = board.legal_moves();
    if (legal.empty()) return false;
    const int counter = board.halfmove_clock();
    const bool repeated = repeated_since_zeroing(board);

    bool ok = true;
    for (const Move move : legal) {
        Undo undo;
        (void)board.make_move(move, undo);
        int dtz = 0;
        bool rounded = false;
        const bool mate = board.in_check() && !board.has_legal_move();
        if (board.halfmove_clock() == 0) {
            NodeValue child;
            ok = node_wdl(*r, board, false, child);
            dtz = zeroing_dtz(-child.wdl);
        } else if (board.is_repetition() || (board.halfmove_clock() >= 100 && !mate)) {
            dtz = 0;
        } else {
            int child = 0;
            ok = dtz_value(*r, board, child, rounded, 0);
            dtz = -child;
            dtz += sign_of(dtz);
        }
        if (mate && dtz == 2) dtz = 1;
        board.unmake_move(move, undo);
        if (!ok) break;
        ranks.push_back(RootRank{move, dtz_rank(dtz, counter, repeated, rule50), dtz, rounded});
    }
    if (ok) {
        used_dtz = true;
        return true;
    }
    ranks.clear();
    for (const Move move : legal) {
        Undo undo;
        (void)board.make_move(move, undo);
        int wdl = 0;
        bool child_ok = true;
        const bool mate = board.in_check() && !board.has_legal_move();
        if (board.is_repetition() || (board.halfmove_clock() >= 100 && !mate)) {
            wdl = 0;
        } else {
            NodeValue child;
            child_ok = node_wdl(*r, board, false, child);
            wdl = -child.wdl;
        }
        board.unmake_move(move, undo);
        if (!child_ok) {
            ranks.clear();
            return false;
        }
        ranks.push_back(RootRank{move, wdl_rank(wdl, rule50), wdl, false});
    }
    return true;
}

} // namespace forge::syzygy

// ---------------------------------------------------------------------------
// Platform file mapping (kept last: <windows.h> macros reach nothing else).
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

namespace forge::syzygy {
namespace {

[[gnu::cold]] bool map_file(const std::filesystem::path& path, const std::uint8_t*& data, std::size_t& size) {
    data = nullptr;
    size = 0;
#if defined(_WIN32)
    HANDLE file = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING,
                              FILE_FLAG_RANDOM_ACCESS, nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;
    LARGE_INTEGER length{};
    if (GetFileSizeEx(file, &length) == 0 || length.QuadPart <= 0) {
        CloseHandle(file);
        return false;
    }
    HANDLE mapping = CreateFileMappingW(file, nullptr, PAGE_READONLY, 0, 0, nullptr);
    CloseHandle(file);
    if (mapping == nullptr) return false;
    void* view = MapViewOfFile(mapping, FILE_MAP_READ, 0, 0, 0);
    CloseHandle(mapping);
    if (view == nullptr) return false;
    data = static_cast<const std::uint8_t*>(view);
    size = static_cast<std::size_t>(length.QuadPart);
    return true;
#else
    const int fd = ::open(path.c_str(), O_RDONLY | O_CLOEXEC);
    if (fd < 0) return false;
    struct stat st {};
    if (::fstat(fd, &st) != 0 || st.st_size <= 0) {
        ::close(fd);
        return false;
    }
    const std::size_t length = static_cast<std::size_t>(st.st_size);
    void* view = ::mmap(nullptr, length, PROT_READ, MAP_SHARED, fd, 0);
    ::close(fd);
    if (view == MAP_FAILED) return false;
    (void)::madvise(view, length, MADV_RANDOM);
    data = static_cast<const std::uint8_t*>(view);
    size = length;
    return true;
#endif
}

[[gnu::cold]] void unmap_file(const std::uint8_t* data, std::size_t size) {
    if (data == nullptr) return;
#if defined(_WIN32)
    (void)size;
    UnmapViewOfFile(data);
#else
    ::munmap(const_cast<std::uint8_t*>(data), size);
#endif
}

} // namespace
} // namespace forge::syzygy
