// fpos2sf_mt: multi-threaded Forge FPOS v1 (.pos) -> Stockfish training data (.bin PackedSfenValue or .binpack),
// plus an independent verify mode. R7 J2 (2026-10-29).
//
// Licence: GPL-3.0. Built against nnue-pytorch's data-loader headers (lib/binpack.h, GPL-3.0) and derived from
// Grok Bot's F:\nnue_pytorch\forge_tools\fpos2sf.cpp (same conversion rules, same output bytes). Tool tree only
// (tools/nnue_pytorch_amd/); never copy it into Forge sources.
//
// FPOS v1 (Forge src/datagen.cpp): "FPOS", u32 version = 1, u64 n, n x 32-byte boards (nibble per square, a1 = 0,
// low nibble = even square; 0 empty, 1..6 white P N B R Q K, 7..12 black p n b r q k), n x i16 score (side to
// move, cp), n x u8 meta (bit0 black to move, bits1-2 White's result * 2: 0 loss, 1 draw, 2 win).
// FPOS has no castling / en passant / move / ply: castling "-", ep "-", ply = --ply (constant), move = a
// king-square null move. Because the ply is constant, binpack never chains entries (isContinuation needs
// ply + 1), so every entry is 32 packed bytes + a 2-byte zero move count, and the single-threaded writer flushes
// a chunk after exactly ceil(1 MiB / 34) = 30841 entries. This tool builds those chunks in parallel (each worker
// converts whole chunks) and writes them in order: the output is byte-identical to fpos2sf.exe.
//
// usage:
//   fpos2sf_mt <in.pos> <out.bin|out.binpack> [--max N] [--skip N] [--stride K] [--ply P] [--score-mult M]
//              [--threads T] [--fen-out f.txt]
//   fpos2sf_mt --verify <in.pos> <file.bin|file.binpack> [--max N] [--skip N] [--stride K] [--ply P]
//              [--score-mult M] [--threads T] [--reader-check 0|1]
//     Decodes every record of the output with the loader's own decoder (unpackEntry / packedSfenValue...) and
//     compares it with the FPOS record square by square (not through a FEN), plus side to move, score, result,
//     ply and move. --reader-check 1 (default) also streams a .binpack through the training loader's sequential
//     CompressedTrainingDataEntryReader and compares it record by record. Exit 0 only with 0 mismatches.
// Threads default to 3 (the PC's job cap); the main thread is one of them.
#include "lib/binpack.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#ifdef _WIN32
// kernel32 exports (declared by hand: <windows.h> pulls MapViewOfFileNuma2 into a static MinGW link)
struct R7ProcessMemoryCounters {
    unsigned long cb, PageFaultCount;
    std::size_t PeakWorkingSetSize, WorkingSetSize, QuotaPeakPagedPoolUsage, QuotaPagedPoolUsage,
        QuotaPeakNonPagedPoolUsage, QuotaNonPagedPoolUsage, PagefileUsage, PeakPagefileUsage;
};
extern "C" __declspec(dllimport) void* __stdcall GetCurrentProcess();
extern "C" __declspec(dllimport) int __stdcall K32GetProcessMemoryInfo(void*, R7ProcessMemoryCounters*, unsigned long);
#endif

namespace {

// Peak working set of this process in MB (Windows; -1 elsewhere): shows that the conversion streams.
double peak_mb() {
#ifdef _WIN32
    R7ProcessMemoryCounters pmc{};
    pmc.cb = sizeof(pmc);
    if (K32GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc))) return pmc.PeakWorkingSetSize / 1048576.0;
#endif
    return -1.0;
}

const char* PIECE_CH = ".PNBRQKpnbrqk";
constexpr std::uint64_t ENTRY_BYTES = sizeof(binpack::PackedTrainingDataEntry) + 2;  // + zero move count
constexpr std::uint64_t CHUNK_ENTRIES = (binpack::suggestedChunkSize + ENTRY_BYTES - 1) / ENTRY_BYTES;  // 30841

struct Options {
    std::uint64_t maxN = ~0ULL, skip = 0, stride = 1;
    int ply = 40;
    double mult = 1.0;
    int threads = 3;
    std::string fenOut;
    bool readerCheck = true;
};

struct Fpos {
    std::ifstream f;
    std::uint64_t n = 0;
    bool open(const std::string& path) {
        f.open(path, std::ios::binary);
        if (!f) { std::fprintf(stderr, "cannot open %s\n", path.c_str()); return false; }
        char magic[4]; std::uint32_t ver = 0;
        f.read(magic, 4); f.read(reinterpret_cast<char*>(&ver), 4); f.read(reinterpret_cast<char*>(&n), 8);
        if (std::memcmp(magic, "FPOS", 4) != 0 || ver != 1) { std::fprintf(stderr, "not FPOS v1\n"); return false; }
        f.seekg(0, std::ios::end);
        const auto size = static_cast<std::uint64_t>(f.tellg());
        if (size != 16 + 35 * n) {
            std::fprintf(stderr, "size mismatch: %llu vs %llu\n", (unsigned long long)size, (unsigned long long)(16 + 35 * n));
            return false;
        }
        return true;
    }
    // Records [first, first + count) of the file (contiguous source indices).
    bool read(std::uint64_t first, std::uint64_t count, std::vector<std::uint8_t>& boards, std::vector<std::int16_t>& scores,
              std::vector<std::uint8_t>& metas) {
        boards.resize(count * 32); scores.resize(count); metas.resize(count);
        f.seekg(16 + first * 32); f.read(reinterpret_cast<char*>(boards.data()), count * 32);
        f.seekg(16 + n * 32 + first * 2); f.read(reinterpret_cast<char*>(scores.data()), count * 2);
        f.seekg(16 + n * 34 + first); f.read(reinterpret_cast<char*>(metas.data()), count);
        return static_cast<bool>(f);
    }
};

inline int code_at(const std::uint8_t* b, int s) { return (s & 1) ? (b[s >> 1] >> 4) : (b[s >> 1] & 15); }

// The conversion rule of fpos2sf.cpp, unchanged: FEN text -> chess::Position::tryFromFen.
// Returns false for a bad record (invalid code, not exactly one king each, result > 2, unparsable FEN).
bool convert(const std::uint8_t* b, std::int16_t score, std::uint8_t meta, const Options& o,
             binpack::TrainingDataEntry& e, std::string& fen, std::uint64_t& clipped) {
    fen.clear();
    int wk = 0, bk = 0; bool okp = true;
    for (int r = 7; r >= 0; --r) {
        int empty = 0;
        for (int fi = 0; fi < 8; ++fi) {
            const int code = code_at(b, r * 8 + fi);
            if (code > 12) okp = false;
            if (code == 0 || code > 12) { ++empty; continue; }
            if (empty) { fen += char('0' + empty); empty = 0; }
            if (code == 6) ++wk;
            if (code == 12) ++bk;
            fen += PIECE_CH[code];
        }
        if (empty) fen += char('0' + empty);
        if (r) fen += '/';
    }
    const bool blackToMove = meta & 1; const int wr2 = (meta >> 1) & 3;
    if (!okp || wk != 1 || bk != 1 || wr2 > 2) return false;
    fen += blackToMove ? " b - - 0 1" : " w - - 0 1";
    auto pos = chess::Position::tryFromFen(fen);
    if (!pos) return false;
    e.pos = *pos;
    const chess::Square ksq = e.pos.kingSquare(e.pos.sideToMove());
    e.move = chess::Move{ksq, ksq};
    double sc = score * o.mult;
    if (sc > 32000) { sc = 32000; ++clipped; }
    if (sc < -32000) { sc = -32000; ++clipped; }
    e.score = static_cast<std::int16_t>(sc);
    e.ply = static_cast<std::uint16_t>(o.ply);
    const int whiteRes = wr2 - 1;
    e.result = static_cast<std::int16_t>(blackToMove ? -whiteRes : whiteRes);
    return true;
}

// Selected source indices: skip, skip + stride, ... (< n), at most maxN of them *written*. Bad records are
// skipped without counting towards maxN, exactly like fpos2sf.cpp, so the job is split by source position and
// trimmed to maxN written records while the chunks are emitted in order.
struct Work {
    std::uint64_t firstSel = 0;   // index into the selection sequence
    std::uint64_t count = 0;      // selected records in this unit
    std::vector<char> bytes;      // converted output (binpack entries + move counts, or PackedSfenValues)
    std::vector<std::uint8_t> ok; // per selected record: 1 converted, 0 bad
    std::string fens;
    std::uint64_t bad = 0, clipped = 0;
};

void convert_unit(Fpos& in, std::mutex& io, const Options& o, bool binpackOut, Work& w) {
    std::vector<std::uint8_t> boards; std::vector<std::int16_t> scores; std::vector<std::uint8_t> metas;
    const std::uint64_t firstSrc = o.skip + w.firstSel * o.stride;
    const std::uint64_t span = (w.count - 1) * o.stride + 1;
    {
        std::lock_guard<std::mutex> lock(io);
        if (!in.read(firstSrc, span, boards, scores, metas)) { std::fprintf(stderr, "read error at %llu\n", (unsigned long long)firstSrc); std::exit(1); }
    }
    w.bytes.clear(); w.ok.assign(w.count, 0); w.fens.clear(); w.bad = 0; w.clipped = 0;
    w.bytes.reserve(w.count * (binpackOut ? ENTRY_BYTES : sizeof(binpack::nodchip::PackedSfenValue)));
    binpack::TrainingDataEntry e; std::string fen;
    for (std::uint64_t j = 0; j < w.count; ++j) {
        const std::uint64_t k = j * o.stride;
        std::uint64_t clip = 0;
        if (!convert(boards.data() + k * 32, scores[k], metas[k], o, e, fen, clip)) { ++w.bad; continue; }
        w.ok[j] = clip ? 2 : 1;
        if (binpackOut) {
            const auto packed = binpack::packEntry(e);
            w.bytes.insert(w.bytes.end(), reinterpret_cast<const char*>(&packed), reinterpret_cast<const char*>(&packed) + sizeof(packed));
            w.bytes.push_back(0); w.bytes.push_back(0);  // movelist numPlies = 0 (big-endian u16)
        } else {
            const auto psv = binpack::trainingDataEntryToPackedSfenValue(e);
            w.bytes.insert(w.bytes.end(), reinterpret_cast<const char*>(&psv), reinterpret_cast<const char*>(&psv) + sizeof(psv));
        }
        if (!o.fenOut.empty()) { w.fens += fen; w.fens += " | "; w.fens += std::to_string(scores[k]); w.fens += " | "; w.fens += std::to_string(e.result); w.fens += "\n"; }
    }
}

std::uint64_t selection_size(std::uint64_t n, const Options& o) {
    if (o.skip >= n) return 0;
    return (n - o.skip + o.stride - 1) / o.stride;
}

void write_chunk(std::ofstream& out, const char* data, std::uint32_t size) {
    unsigned char header[8] = {'B', 'I', 'N', 'P', static_cast<unsigned char>(size), static_cast<unsigned char>(size >> 8),
                               static_cast<unsigned char>(size >> 16), static_cast<unsigned char>(size >> 24)};
    out.write(reinterpret_cast<const char*>(header), 8);
    out.write(data, size);
}

int run_convert(const std::string& inPath, const std::string& outPath, const Options& o) {
    Fpos in; if (!in.open(inPath)) return 1;
    const bool binpackOut = outPath.size() > 8 && outPath.substr(outPath.size() - 8) == ".binpack";
    const bool binOut = !binpackOut && outPath.size() > 4 && outPath.substr(outPath.size() - 4) == ".bin";
    if (!binpackOut && !binOut) { std::fprintf(stderr, "output must end in .bin or .binpack\n"); return 2; }
    { std::ifstream probe(outPath, std::ios::binary); if (probe) { std::fprintf(stderr, "output exists, refusing to overwrite: %s\n", outPath.c_str()); return 1; } }
    std::ofstream out(outPath, std::ios::binary | std::ios::trunc);
    std::ofstream fenf; if (!o.fenOut.empty()) fenf.open(o.fenOut);
    const auto t0 = std::chrono::steady_clock::now();
    const std::uint64_t sel = selection_size(in.n, o);
    // Units of CHUNK_ENTRIES selected records; bad records make a unit emit fewer entries, so the pending binpack
    // chunk is assembled from unit outputs in order and flushed exactly where the sequential writer would.
    const int T = std::max(1, o.threads);
    std::mutex io;
    std::vector<Work> ring(static_cast<std::size_t>(T));
    std::vector<char> pending; pending.reserve(binpack::suggestedChunkSize + binpack::maxMovelistSize + CHUNK_ENTRIES * ENTRY_BYTES);
    std::uint64_t written = 0, bad = 0, clipped = 0, nextSel = 0;
    bool done = false;
    while (!done && nextSel < sel && written < o.maxN) {
        int units = 0;
        for (int t = 0; t < T && nextSel < sel; ++t) {
            ring[t].firstSel = nextSel;
            ring[t].count = std::min<std::uint64_t>(CHUNK_ENTRIES, sel - nextSel);
            nextSel += ring[t].count; ++units;
        }
        std::vector<std::thread> pool;
        for (int t = 1; t < units; ++t) pool.emplace_back(convert_unit, std::ref(in), std::ref(io), std::cref(o), binpackOut, std::ref(ring[t]));
        convert_unit(in, io, o, binpackOut, ring[0]);
        for (auto& th : pool) th.join();
        for (int t = 0; t < units && !done; ++t) {
            Work& w = ring[t];
            const std::uint64_t rec = binpackOut ? ENTRY_BYTES : sizeof(binpack::nodchip::PackedSfenValue);
            std::uint64_t taken = 0, takenBad = 0;
            // emit converted records in order until maxN is reached
            std::uint64_t byteOff = 0; std::size_t fenOff = 0;
            for (std::uint64_t j = 0; j < w.count; ++j) {
                if (written >= o.maxN) { done = true; break; }
                if (!w.ok[j]) { ++takenBad; continue; }
                if (binpackOut) {
                    // the sequential writer flushes before adding an entry once the chunk holds >= 1 MiB
                    if (pending.size() >= binpack::suggestedChunkSize) { write_chunk(out, pending.data(), static_cast<std::uint32_t>(pending.size())); pending.clear(); }
                    pending.insert(pending.end(), w.bytes.data() + byteOff, w.bytes.data() + byteOff + rec);
                } else {
                    out.write(w.bytes.data() + byteOff, static_cast<std::streamsize>(rec));
                }
                if (fenf) { const std::size_t e = w.fens.find('\n', fenOff); fenf.write(w.fens.data() + fenOff, static_cast<std::streamsize>(e + 1 - fenOff)); fenOff = e + 1; }
                clipped += w.ok[j] == 2;
                byteOff += rec; ++taken; ++written;
            }
            bad += takenBad;
        }
    }
    if (binpackOut && !pending.empty()) write_chunk(out, pending.data(), static_cast<std::uint32_t>(pending.size()));
    out.close();
    const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    std::printf("in=%s n=%llu written=%llu bad=%llu clipped=%llu out=%s\n", inPath.c_str(), (unsigned long long)in.n,
                (unsigned long long)written, (unsigned long long)bad, (unsigned long long)clipped, outPath.c_str());
    std::printf("threads=%d seconds=%.2f records_per_s=%.0f peak_working_set_mb=%.1f\n", T, secs,
                written / std::max(secs, 1e-9), peak_mb());
    return out ? 0 : 1;
}

// ---------------------------------------------------------------- verify
struct Expect {
    int codes[64];
    bool blackToMove;
    std::int16_t score;
    std::int16_t result;
};

bool expected(const std::uint8_t* b, std::int16_t score, std::uint8_t meta, const Options& o, Expect& x) {
    int wk = 0, bk = 0;
    for (int s = 0; s < 64; ++s) {
        const int c = code_at(b, s);
        if (c > 12) return false;
        x.codes[s] = c; wk += c == 6; bk += c == 12;
    }
    const int wr2 = (meta >> 1) & 3;
    if (wk != 1 || bk != 1 || wr2 > 2) return false;
    x.blackToMove = meta & 1;
    double sc = score * o.mult; sc = std::min(32000.0, std::max(-32000.0, sc));
    x.score = static_cast<std::int16_t>(sc);
    x.result = static_cast<std::int16_t>(x.blackToMove ? -(wr2 - 1) : (wr2 - 1));
    return true;
}

// 0 = equal; otherwise a bit mask of what differs (1 board, 2 side, 4 score, 8 result, 16 ply, 32 move)
int compare(const binpack::TrainingDataEntry& e, const Expect& x, const Options& o) {
    int diff = 0;
    for (int s = 0; s < 64; ++s) {
        const chess::Piece p = e.pos.pieceAt(chess::fromOrdinal<chess::Square>(s));
        int code = 0;
        if (p.type() != chess::PieceType::None) code = 1 + chess::ordinal(p.type()) + 6 * chess::ordinal(p.color());
        if (code != x.codes[s]) { diff |= 1; break; }
    }
    if ((e.pos.sideToMove() == chess::Color::Black) != x.blackToMove) diff |= 2;
    if (e.score != x.score) diff |= 4;
    if (e.result != x.result) diff |= 8;
    if (e.ply != o.ply) diff |= 16;
    const chess::Square ksq = e.pos.kingSquare(e.pos.sideToMove());
    // binpack stores the from == to dummy move as Move::null() (from = to = square 64); .bin keeps it
    if (!((e.move.from == ksq && e.move.to == ksq) || e.move == chess::Move::null())) diff |= 32;
    return diff;
}

std::vector<char> slurp(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) { std::fprintf(stderr, "cannot open %s\n", path.c_str()); std::exit(1); }
    return std::vector<char>((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
}

int run_verify(const std::string& inPath, const std::string& dataPath, const Options& o) {
    Fpos in; if (!in.open(inPath)) return 1;
    in.f.close();
    const bool binpackIn = dataPath.size() > 8 && dataPath.substr(dataPath.size() - 8) == ".binpack";
    const auto t0 = std::chrono::steady_clock::now();
    const std::vector<char> pos = slurp(inPath);
    const auto* boards = reinterpret_cast<const std::uint8_t*>(pos.data() + 16);
    const auto* scores = reinterpret_cast<const std::int16_t*>(pos.data() + 16 + in.n * 32);
    const auto* metas = reinterpret_cast<const std::uint8_t*>(pos.data() + 16 + in.n * 34);
    const std::vector<char> data = slurp(dataPath);
    // 1) split the output into blocks: binpack chunks, or runs of CHUNK_ENTRIES PackedSfenValues
    std::vector<std::pair<std::uint64_t, std::uint64_t>> blocks;  // byte offset of the first record, records
    std::uint64_t formatErrors = 0;
    if (binpackIn) {
        std::uint64_t off = 0;
        while (off + 8 <= data.size()) {
            if (std::memcmp(data.data() + off, "BINP", 4) != 0) { ++formatErrors; break; }
            const std::uint32_t size = static_cast<unsigned char>(data[off + 4]) | (static_cast<unsigned char>(data[off + 5]) << 8) |
                                       (static_cast<unsigned char>(data[off + 6]) << 16) |
                                       (static_cast<std::uint32_t>(static_cast<unsigned char>(data[off + 7])) << 24);
            if (size % ENTRY_BYTES != 0 || off + 8 + size > data.size()) { ++formatErrors; break; }
            blocks.emplace_back(off + 8, size / ENTRY_BYTES);
            off += 8 + size;
        }
        if (off != data.size()) ++formatErrors;
    } else {
        if (data.size() % sizeof(binpack::nodchip::PackedSfenValue) != 0) ++formatErrors;
        const std::uint64_t recs = data.size() / sizeof(binpack::nodchip::PackedSfenValue);
        for (std::uint64_t r = 0; r < recs; r += CHUNK_ENTRIES)
            blocks.emplace_back(r * sizeof(binpack::nodchip::PackedSfenValue), std::min<std::uint64_t>(CHUNK_ENTRIES, recs - r));
    }
    std::uint64_t total = 0;
    std::vector<std::uint64_t> firstRec(blocks.size());
    for (std::size_t i = 0; i < blocks.size(); ++i) { firstRec[i] = total; total += blocks[i].second; }
    // 2) the records the converter must have written: the selection minus bad source records, at most --max
    const std::uint64_t sel = selection_size(in.n, o);
    std::vector<std::uint64_t> srcOfRec;
    srcOfRec.reserve(static_cast<std::size_t>(std::min<std::uint64_t>(sel, o.maxN)));
    std::uint64_t badSrc = 0;
    {
        Expect x;
        for (std::uint64_t s = 0; s < sel && srcOfRec.size() < o.maxN; ++s) {
            const std::uint64_t src = o.skip + s * o.stride;
            if (!expected(boards + src * 32, scores[src], metas[src], o, x)) { ++badSrc; continue; }
            srcOfRec.push_back(src);
        }
    }
    // 3) decode every output record with the loader's decoder and compare it square by square (parallel by block)
    const int T = std::max(1, o.threads);
    std::vector<std::uint64_t> mism(static_cast<std::size_t>(T), 0);
    std::vector<int> masks(static_cast<std::size_t>(T), 0);
    std::atomic<std::size_t> nextBlock{0};
    auto worker = [&](int t) {
        Expect x;
        for (;;) {
            const std::size_t bi = nextBlock.fetch_add(1);
            if (bi >= blocks.size()) break;
            const auto [off, recs] = blocks[bi];
            for (std::uint64_t r = 0; r < recs; ++r) {
                const std::uint64_t gi = firstRec[bi] + r;
                if (gi >= srcOfRec.size()) { ++mism[t]; masks[t] |= 64; continue; }  // more output records than expected
                const std::uint64_t src = srcOfRec[gi];
                expected(boards + src * 32, scores[src], metas[src], o, x);
                binpack::TrainingDataEntry e;
                if (binpackIn) {
                    const char* rec = data.data() + off + r * ENTRY_BYTES;
                    binpack::PackedTrainingDataEntry packed;
                    std::memcpy(&packed, rec, sizeof(packed));
                    e = binpack::unpackEntry(packed);
                    if (rec[32] != 0 || rec[33] != 0) { ++mism[t]; masks[t] |= 128; continue; }  // move count must be 0
                } else {
                    binpack::nodchip::PackedSfenValue psv;
                    std::memcpy(&psv, data.data() + off + r * sizeof(psv), sizeof(psv));
                    e = binpack::packedSfenValueToTrainingDataEntry(psv);
                }
                const int d = compare(e, x, o);
                if (d) { ++mism[t]; masks[t] |= d; }
            }
        }
    };
    {
        std::vector<std::thread> pool;
        for (int t = 1; t < T; ++t) pool.emplace_back(worker, t);
        worker(0);
        for (auto& th : pool) th.join();
    }
    std::uint64_t mismatches = 0; int mask = 0;
    for (int t = 0; t < T; ++t) { mismatches += mism[static_cast<std::size_t>(t)]; mask |= masks[static_cast<std::size_t>(t)]; }
    const std::uint64_t missing = srcOfRec.size() > total ? srcOfRec.size() - total : 0;
    // 4) the training loader's own sequential reader over the whole .binpack
    std::uint64_t readerRecs = 0, readerMism = 0;
    if (binpackIn && o.readerCheck) {
        binpack::CompressedTrainingDataEntryReader reader(dataPath);
        Expect x;
        while (reader.hasNext()) {
            const auto e = reader.next();
            if (readerRecs >= srcOfRec.size()) { ++readerMism; ++readerRecs; continue; }
            const std::uint64_t src = srcOfRec[readerRecs];
            expected(boards + src * 32, scores[src], metas[src], o, x);
            if (compare(e, x, o)) ++readerMism;
            ++readerRecs;
        }
    }
    const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    std::printf("verify in=%s data=%s records=%llu expected=%llu bad_source_records=%llu format_errors=%llu "
                "mismatches=%llu mask=%d missing=%llu reader_records=%llu reader_mismatches=%llu threads=%d seconds=%.2f\n",
                inPath.c_str(), dataPath.c_str(), (unsigned long long)total, (unsigned long long)srcOfRec.size(),
                (unsigned long long)badSrc, (unsigned long long)formatErrors, (unsigned long long)mismatches, mask,
                (unsigned long long)missing, (unsigned long long)readerRecs, (unsigned long long)readerMism, T, secs);
    const bool ok = formatErrors == 0 && mismatches == 0 && missing == 0 && total > 0 &&
                    (!binpackIn || !o.readerCheck || (readerMism == 0 && readerRecs == total));
    std::printf("%s\n", ok ? "VERIFY OK" : "VERIFY FAILED");
    return ok ? 0 : 1;
}

}  // namespace

int main(int argc, char** argv) {
    const bool verify = argc > 1 && std::string(argv[1]) == "--verify";
    const int base = verify ? 2 : 1;
    if (argc < base + 2) {
        std::fprintf(stderr, "usage: fpos2sf_mt [--verify] <in.pos> <out.bin|out.binpack> [--max N] [--skip N] [--stride K] [--ply P] "
                             "[--score-mult M] [--threads T] [--fen-out f] [--reader-check 0|1]\n");
        return 2;
    }
    const std::string in = argv[base], out = argv[base + 1];
    Options o;
    for (int i = base + 2; i + 1 < argc; i += 2) {
        const std::string k = argv[i], v = argv[i + 1];
        if (k == "--max") o.maxN = std::stoull(v);
        else if (k == "--skip") o.skip = std::stoull(v);
        else if (k == "--stride") o.stride = std::max<std::uint64_t>(1, std::stoull(v));
        else if (k == "--ply") o.ply = std::stoi(v);
        else if (k == "--score-mult") o.mult = std::stod(v);
        else if (k == "--threads") o.threads = std::max(1, std::stoi(v));
        else if (k == "--fen-out") o.fenOut = v;
        else if (k == "--reader-check") o.readerCheck = std::stoi(v) != 0;
        else { std::fprintf(stderr, "unknown option %s\n", k.c_str()); return 2; }
    }
    return verify ? run_verify(in, out, o) : run_convert(in, out, o);
}
