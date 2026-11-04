#!/usr/bin/env python3
"""o30_v2int16.py <v2port scratch repo> - Opus 30-h job: store the v2 first layer (w1) as int16, as in the file, instead
of float32 (own code; anchored edits, refused if an anchor is missing or not unique).
Why: a KB4 net's w1 is 3.1 MB as float32 (the lock net's 0.79 MB fits a core's L2); in real games the v2 exe searched
0.12-0.15 ply less than the lock at equal time. int16 halves the table (KB4: 1.57 MB; the two perspectives' hot
buckets 2 x 393 KB, the lock's float size).
Exactness: every int16 * 2^-12 is exactly representable in float32, so `acc -= float(w) * 2^-12` computes the same
bits as the old `acc -= w_float` with w_float = float(w) / 4096 (also exact) - accumulators, evaluations and node
counts stay identical (to be shown by parity x3, the walk and the identity pins, not assumed).
Touches include/forge/nnue_v2.hpp (buffer template, Net::w1 type, column(), apply_columns, refresh, refresh_cached,
update) and src/nnue.cpp (the loader stores the raw int16). The output layer (w2, b2) and b1 stay float.
"""
import sys
from pathlib import Path

EDITS_HPP = [
    # 1 the aligned buffer becomes a template; AlignedFloats keeps its name
    ('''// 64-byte aligned float array.
class AlignedFloats {
public:
    AlignedFloats() = default;
    AlignedFloats(const AlignedFloats&) = delete;
    AlignedFloats& operator=(const AlignedFloats&) = delete;
    ~AlignedFloats() { release(); }
    void allocate(std::size_t count) {
        release();
        data_ = static_cast<float*>(::operator new(count * sizeof(float), std::align_val_t{64}));
        size_ = count;
        std::fill(data_, data_ + count, 0.0F);
    }
    [[nodiscard]] float* data() const { return data_; }
    [[nodiscard]] std::size_t size() const { return size_; }

private:
    void release() {
        if (data_ != nullptr) ::operator delete(data_, std::align_val_t{64});
        data_ = nullptr;
        size_ = 0;
    }
    float* data_ = nullptr;
    std::size_t size_ = 0;
};''',
     '''// 64-byte aligned array.
template <typename T>
class AlignedArray {
public:
    AlignedArray() = default;
    AlignedArray(const AlignedArray&) = delete;
    AlignedArray& operator=(const AlignedArray&) = delete;
    ~AlignedArray() { release(); }
    void allocate(std::size_t count) {
        release();
        data_ = static_cast<T*>(::operator new(count * sizeof(T), std::align_val_t{64}));
        size_ = count;
        std::fill(data_, data_ + count, T{});
    }
    [[nodiscard]] T* data() const { return data_; }
    [[nodiscard]] std::size_t size() const { return size_; }

private:
    void release() {
        if (data_ != nullptr) ::operator delete(data_, std::align_val_t{64});
        data_ = nullptr;
        size_ = 0;
    }
    T* data_ = nullptr;
    std::size_t size_ = 0;
};
using AlignedFloats = AlignedArray<float>;
// First-layer weights stay int16 as in the file (half the memory of float32); every use multiplies by W1Unit.
// Exact: int16 * 2^-12 is a float32 value, so the accumulators get the same bits as with de-quantised floats.
constexpr float W1Unit = 1.0F / 4096.0F;'''),
    ('    AlignedFloats w1;   // [king_buckets][InputCount][HiddenSize]',
     '    AlignedArray<std::int16_t> w1;   // [king_buckets][InputCount][HiddenSize], raw int16 (value * W1Unit)'),
    ('''[[nodiscard]] inline const float* column(const Net& net, Color perspective, KingKey key, Piece piece, int square) {''',
     '''[[nodiscard]] inline const std::int16_t* column(const Net& net, Color perspective, KingKey key, Piece piece, int square) {'''),
    ('''inline void apply_columns(const float* src, float* dst, const float* const* sub, const float* const* add) {
    for (int h = 0; h < HiddenSize; ++h) {
        float value = src[h];
        for (int i = 0; i < Subs; ++i) value -= sub[i][h];
        for (int i = 0; i < Adds; ++i) value += add[i][h];
        dst[h] = value;
    }
}''',
     '''inline void apply_columns(const float* src, float* dst, const std::int16_t* const* sub, const std::int16_t* const* add) {
    for (int h = 0; h < HiddenSize; ++h) {
        float value = src[h];
        for (int i = 0; i < Subs; ++i) value -= static_cast<float>(sub[i][h]) * W1Unit;
        for (int i = 0; i < Adds; ++i) value += static_cast<float>(add[i][h]) * W1Unit;
        dst[h] = value;
    }
}'''),
    ('''        const float* col = column(net, perspective, key, board.piece_at(square), square);
        for (int h = 0; h < HiddenSize; ++h) values[h] += col[h];''',
     '''        const std::int16_t* col = column(net, perspective, key, board.piece_at(square), square);
        for (int h = 0; h < HiddenSize; ++h) values[h] += static_cast<float>(col[h]) * W1Unit;'''),
    ('''    std::array<const float*, 64> sub;
    std::array<const float*, 64> add;''',
     '''    std::array<const std::int16_t*, 64> sub;
    std::array<const std::int16_t*, 64> add;'''),
    ('''        for (int i = 0; i < subs; ++i) {
            const float* col = sub[static_cast<std::size_t>(i)] + h0;
            for (int k = 0; k < Chunk; ++k) chunk[k] -= col[k];
        }
        for (int i = 0; i < adds; ++i) {
            const float* col = add[static_cast<std::size_t>(i)] + h0;
            for (int k = 0; k < Chunk; ++k) chunk[k] += col[k];
        }''',
     '''        for (int i = 0; i < subs; ++i) {
            const std::int16_t* col = sub[static_cast<std::size_t>(i)] + h0;
            for (int k = 0; k < Chunk; ++k) chunk[k] -= static_cast<float>(col[k]) * W1Unit;
        }
        for (int i = 0; i < adds; ++i) {
            const std::int16_t* col = add[static_cast<std::size_t>(i)] + h0;
            for (int k = 0; k < Chunk; ++k) chunk[k] += static_cast<float>(col[k]) * W1Unit;
        }'''),
    ('''    std::array<const float*, 4> sub{};
    std::array<const float*, 4> add{};''',
     '''    std::array<const std::int16_t*, 4> sub{};
    std::array<const std::int16_t*, 4> add{};'''),
    ('''        const float* col = column(net, perspective, key, change.piece, change.square);''',
     '''        const std::int16_t* col = column(net, perspective, key, change.piece, change.square);'''),
]
EDITS_CPP = [
    ('''    for (std::size_t i = 0; i < w1_count; ++i, offset += 2) net->w1.data()[i] = static_cast<float>(read_i16(bytes, offset)) / WeightScale;''',
     '''    for (std::size_t i = 0; i < w1_count; ++i, offset += 2) net->w1.data()[i] = read_i16(bytes, offset);   // raw; used * W1Unit'''),
]


def apply(path, edits):
    raw = path.read_bytes().decode('utf-8')
    crlf = '\r\n' in raw
    text = raw.replace('\r\n', '\n')
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            sys.exit(f'{path}: anchor found {n} times (need 1): {old.splitlines()[0][:80]!r}')
        text = text.replace(old, new, 1)
    path.write_bytes((text.replace('\n', '\r\n') if crlf else text).encode('utf-8'))
    print(f'{path}: {len(edits)} edits ({"CRLF" if crlf else "LF"})')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    repo = Path(sys.argv[1])
    hpp, cpp = repo / 'include' / 'forge' / 'nnue_v2.hpp', repo / 'src' / 'nnue.cpp'
    if 'W1Unit' in hpp.read_text(encoding='utf-8'):
        sys.exit('refusing: the tree already stores w1 as int16')
    apply(hpp, EDITS_HPP)
    apply(cpp, EDITS_CPP)


if __name__ == '__main__':
    main()
