// r11_pos2binpack: Forge FPOS v1 (.pos) + an R11 destination map -> nnue-pytorch .binpack files (train and
// holdout) plus aligned FHCE side-cars, and an independent verify mode. R11 (2026-10-30).
//
// Licence: GPL-3.0. Built against nnue-pytorch's data-loader headers (data_loader/cpp/lib/binpack.h, GPL-3.0) from
// the R6 clone; tool tree only (tools/nnue_pytorch_amd/), never copied into Forge sources.
//
// Conversion rule = R7 J2 fpos2sf_mt (itself byte-identical to Grok Bot's fpos2sf): FEN text from the FPOS board,
// castling "-", en passant "-", halfmove 0, fullmove 1 -> chess::Position::tryFromFen; move = the side to move's
// king square to itself (stored by binpack as Move::null()); ply = --ply (constant, so entries never chain);
// score = stored side-to-move cp clipped to +-32000; result = White's result from the side to move's view.
// Every entry is the 32-byte packed entry + a 2-byte zero move count; a chunk ("BINP" + u32 size) is flushed before
// an entry is added once it holds >= 1 MiB (30,841 entries), exactly like the sequential writer. With an all-train
// destination map the output is therefore byte-identical to fpos2sf_mt.
//
// Destination map (.dest2, written by r11_data.py): 2 bits per source row, row i in byte i >> 2 at bits 2 * (i & 3):
// 0 drop (duplicate), 1 train, 2 holdout, 3 bad (rejected by the cheap row checks).
//
// usage:
//   r11_pos2binpack convert --pos P --dest D [--hce H] [--train T.binpack] [--hold O.binpack]
//                   [--hce-train T.hce] [--hce-hold O.hce] [--ply 40]
//   r11_pos2binpack verify --pos P --dest D --code 1|2 --file F.binpack [--hce H --hce-file F.hce] [--ply 40]
// Both modes print one JSON summary line on stdout. convert never overwrites an existing output file. verify streams the .binpack through the training loader's
// own CompressedTrainingDataEntryReader, checks the chunk structure independently, and compares every record with
// the source row square by square; exit 0 only with 0 mismatches.
#include "lib/binpack.h"

#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#ifdef _WIN32
// kernel32, declared by hand (<windows.h> pulls in names that clash with the loader headers in a static MinGW link)
extern "C" __declspec(dllimport) void* __stdcall GetCurrentProcess();
extern "C" __declspec(dllimport) int __stdcall SetPriorityClass(void*, unsigned long);
#endif

namespace {

// CR fix 2: background mode (very low I/O and memory priority) and the Idle class for the writer itself (the R11
// driver that starts it is already Idle + background on 3 cores; the 3-core mask is inherited). Background mode resets
// the class to Normal, so Idle is set again after it (measured 2026-10-30).
void enter_background_mode() {
#ifdef _WIN32
    SetPriorityClass(GetCurrentProcess(), 0x00100000UL);  // PROCESS_MODE_BACKGROUND_BEGIN
    SetPriorityClass(GetCurrentProcess(), 0x00000040UL);  // IDLE_PRIORITY_CLASS
#endif
}

const char* PIECE_CH = ".PNBRQKpnbrqk";
constexpr std::uint64_t ENTRY_BYTES = sizeof(binpack::PackedTrainingDataEntry) + 2;
static_assert(ENTRY_BYTES == 34, "binpack entry layout changed");

struct Args {
    std::string mode, pos, dest, hce, train, hold, hceTrain, hceHold, json, file, hceFile;
    int ply = 40;
    int code = 0;
    std::uint64_t chunkRows = 1u << 20;
};

[[noreturn]] void die(const std::string& msg) {
    std::fprintf(stderr, "r11_pos2binpack: %s\n", msg.c_str());
    std::exit(1);
}

bool file_exists(const std::string& p) {
    std::ifstream f(p, std::ios::binary);
    return static_cast<bool>(f);
}

struct Fpos {
    std::ifstream f;
    std::uint64_t n = 0;
    void open(const std::string& path) {
        f.open(path, std::ios::binary);
        if (!f) die("cannot open " + path);
        char magic[4];
        std::uint32_t ver = 0;
        f.read(magic, 4);
        f.read(reinterpret_cast<char*>(&ver), 4);
        f.read(reinterpret_cast<char*>(&n), 8);
        if (!f || std::memcmp(magic, "FPOS", 4) != 0 || ver != 1) die("not FPOS v1: " + path);
        f.seekg(0, std::ios::end);
        const auto size = static_cast<std::uint64_t>(f.tellg());
        if (size != 16 + 35 * n) die("FPOS size mismatch: " + path);
    }
    void read(std::uint64_t first, std::uint64_t count, std::vector<std::uint8_t>& boards, std::vector<std::int16_t>& scores,
              std::vector<std::uint8_t>& metas) {
        boards.resize(count * 32);
        scores.resize(count);
        metas.resize(count);
        f.seekg(static_cast<std::streamoff>(16 + first * 32));
        f.read(reinterpret_cast<char*>(boards.data()), static_cast<std::streamsize>(count * 32));
        f.seekg(static_cast<std::streamoff>(16 + n * 32 + first * 2));
        f.read(reinterpret_cast<char*>(scores.data()), static_cast<std::streamsize>(count * 2));
        f.seekg(static_cast<std::streamoff>(16 + n * 34 + first));
        f.read(reinterpret_cast<char*>(metas.data()), static_cast<std::streamsize>(count));
        if (!f) die("read error in FPOS");
    }
};

struct Fhce {
    std::ifstream f;
    std::uint64_t n = 0;
    void open(const std::string& path) {
        f.open(path, std::ios::binary);
        if (!f) die("cannot open " + path);
        char magic[4];
        std::uint32_t ver = 0;
        f.read(magic, 4);
        f.read(reinterpret_cast<char*>(&ver), 4);
        f.read(reinterpret_cast<char*>(&n), 8);
        if (!f || std::memcmp(magic, "FHCE", 4) != 0) die("not FHCE: " + path);
        f.seekg(0, std::ios::end);
        if (static_cast<std::uint64_t>(f.tellg()) != 16 + 2 * n) die("FHCE size mismatch: " + path);
    }
    void read(std::uint64_t first, std::uint64_t count, std::vector<std::int16_t>& v) {
        v.resize(count);
        f.seekg(static_cast<std::streamoff>(16 + first * 2));
        f.read(reinterpret_cast<char*>(v.data()), static_cast<std::streamsize>(count * 2));
        if (!f) die("read error in FHCE");
    }
};

std::vector<std::uint8_t> read_dest(const std::string& path, std::uint64_t n) {
    std::ifstream f(path, std::ios::binary);
    if (!f) die("cannot open " + path);
    std::vector<std::uint8_t> d((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    if (d.size() != (n + 3) / 4) die("dest map size " + std::to_string(d.size()) + " != ceil(rows / 4)");
    return d;
}

inline int dest_at(const std::vector<std::uint8_t>& d, std::uint64_t i) { return (d[i >> 2] >> (2 * (i & 3))) & 3; }

inline int code_at(const std::uint8_t* b, int s) { return (s & 1) ? (b[s >> 1] >> 4) : (b[s >> 1] & 15); }

// The fpos2sf / fpos2sf_mt conversion rule, unchanged.
bool convert(const std::uint8_t* b, std::int16_t score, std::uint8_t meta, int ply, binpack::TrainingDataEntry& e,
             std::string& fen, bool& clipped) {
    fen.clear();
    clipped = false;
    int wk = 0, bk = 0;
    bool okp = true;
    for (int r = 7; r >= 0; --r) {
        int empty = 0;
        for (int fi = 0; fi < 8; ++fi) {
            const int code = code_at(b, r * 8 + fi);
            if (code > 12) okp = false;
            if (code == 0 || code > 12) {
                ++empty;
                continue;
            }
            if (empty) {
                fen += char('0' + empty);
                empty = 0;
            }
            if (code == 6) ++wk;
            if (code == 12) ++bk;
            fen += PIECE_CH[code];
        }
        if (empty) fen += char('0' + empty);
        if (r) fen += '/';
    }
    const bool blackToMove = meta & 1;
    const int wr2 = (meta >> 1) & 3;
    if (!okp || wk != 1 || bk != 1 || wr2 > 2) return false;
    fen += blackToMove ? " b - - 0 1" : " w - - 0 1";
    auto pos = chess::Position::tryFromFen(fen);
    if (!pos) return false;
    e.pos = *pos;
    const chess::Square ksq = e.pos.kingSquare(e.pos.sideToMove());
    e.move = chess::Move{ksq, ksq};
    double sc = score;
    if (sc > 32000) { sc = 32000; clipped = true; }
    if (sc < -32000) { sc = -32000; clipped = true; }
    e.score = static_cast<std::int16_t>(sc);
    e.ply = static_cast<std::uint16_t>(ply);
    const int whiteRes = wr2 - 1;
    e.result = static_cast<std::int16_t>(blackToMove ? -whiteRes : whiteRes);
    return true;
}

struct BinpackOut {
    std::string path;
    std::ofstream f;
    std::vector<char> pending;
    std::uint64_t records = 0, bytes = 0, chunks = 0;
    bool active = false;
    void open(const std::string& p) {
        if (p.empty()) return;
        if (file_exists(p)) die("output exists, refusing to overwrite: " + p);
        path = p;
        f.open(p, std::ios::binary | std::ios::trunc);
        if (!f) die("cannot create " + p);
        pending.reserve(binpack::suggestedChunkSize + 64);
        active = true;
    }
    void flush() {
        if (pending.empty()) return;
        const auto size = static_cast<std::uint32_t>(pending.size());
        const unsigned char header[8] = {'B', 'I', 'N', 'P', static_cast<unsigned char>(size), static_cast<unsigned char>(size >> 8),
                                         static_cast<unsigned char>(size >> 16), static_cast<unsigned char>(size >> 24)};
        f.write(reinterpret_cast<const char*>(header), 8);
        f.write(pending.data(), size);
        if (!f) die("write error on " + path);
        bytes += 8 + size;
        ++chunks;
        pending.clear();
    }
    void add(const binpack::TrainingDataEntry& e) {
        if (pending.size() >= binpack::suggestedChunkSize) flush();
        const auto packed = binpack::packEntry(e);
        const char* p = reinterpret_cast<const char*>(&packed);
        pending.insert(pending.end(), p, p + sizeof(packed));
        pending.push_back(0);  // movetext numPlies = 0 (big-endian u16)
        pending.push_back(0);
        ++records;
    }
    void close() {
        if (!active) return;
        flush();
        f.close();
        if (f.fail()) die("close error on " + path);
    }
};

struct HceOut {
    std::string path;
    std::ofstream f;
    std::vector<std::int16_t> buf;
    std::uint64_t n = 0;
    bool active = false;
    void open(const std::string& p) {
        if (p.empty()) return;
        if (file_exists(p)) die("output exists, refusing to overwrite: " + p);
        path = p;
        f.open(p, std::ios::binary | std::ios::trunc);
        if (!f) die("cannot create " + p);
        const char head[16] = {'F', 'H', 'C', 'E', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
        f.write(head, 16);
        active = true;
    }
    void add(std::int16_t v) {
        buf.push_back(v);
        ++n;
        if (buf.size() >= (1u << 20)) flush();
    }
    void flush() {
        if (buf.empty()) return;
        f.write(reinterpret_cast<const char*>(buf.data()), static_cast<std::streamsize>(buf.size() * 2));
        if (!f) die("write error on " + path);
        buf.clear();
    }
    void close() {
        if (!active) return;
        flush();
        f.seekp(8);
        f.write(reinterpret_cast<const char*>(&n), 8);
        f.close();
        if (f.fail()) die("close error on " + path);
    }
};

std::string json_escape(const std::string& in) {
    std::string out;
    for (const char c : in) {
        if (c == '\\' || c == '"') out += '\\';
        if (static_cast<unsigned char>(c) < 0x20) continue;
        out += c;
    }
    return out;
}

// The JSON summary goes to stdout as one line starting with '{'; the Python driver stores it.
void emit_json(const Args&, const std::string& body) {
    std::printf("%s\n", body.c_str());
    std::fflush(stdout);
}

// Sequential reader of an FHCE file in blocks (verify reads the side-car once, front to back).
struct FhceSeq {
    Fhce f;
    std::vector<std::int16_t> buf;
    std::uint64_t bufStart = 0;
    bool get(std::uint64_t idx, std::int16_t& v) {
        if (idx >= f.n) return false;
        if (idx < bufStart || idx >= bufStart + buf.size()) {
            bufStart = idx;
            f.read(idx, std::min<std::uint64_t>(1u << 20, f.n - idx), buf);
        }
        v = buf[idx - bufStart];
        return true;
    }
};

int run_convert(const Args& a) {
    const auto t0 = std::chrono::steady_clock::now();
    Fpos in;
    in.open(a.pos);
    const auto dest = read_dest(a.dest, in.n);
    Fhce hce;
    const bool withHce = !a.hce.empty();
    if (withHce) {
        hce.open(a.hce);
        if (hce.n != in.n) die("hce rows != pos rows");
    } else if (!a.hceTrain.empty() || !a.hceHold.empty()) {
        die("--hce-train / --hce-hold need --hce");
    }
    std::uint64_t cnt[4] = {0, 0, 0, 0};
    for (std::uint64_t i = 0; i < in.n; ++i) ++cnt[dest_at(dest, i)];
    if (cnt[1] && a.train.empty()) die("rows marked train but no --train output");
    if (cnt[2] && a.hold.empty()) die("rows marked holdout but no --hold output");
    BinpackOut outT, outH;
    HceOut hT, hH;
    if (cnt[1]) { outT.open(a.train); hT.open(a.hceTrain); }
    if (cnt[2]) { outH.open(a.hold); hH.open(a.hceHold); }
    std::vector<std::uint8_t> boards, metas;
    std::vector<std::int16_t> scores, hv;
    binpack::TrainingDataEntry e;
    std::string fen;
    std::uint64_t writerBad = 0, clippedN = 0;
    for (std::uint64_t first = 0; first < in.n; first += a.chunkRows) {
        const std::uint64_t count = std::min<std::uint64_t>(a.chunkRows, in.n - first);
        in.read(first, count, boards, scores, metas);
        if (withHce) hce.read(first, count, hv);
        for (std::uint64_t j = 0; j < count; ++j) {
            const int d = dest_at(dest, first + j);
            if (d != 1 && d != 2) continue;
            bool clipped = false;
            if (!convert(boards.data() + j * 32, scores[j], metas[j], a.ply, e, fen, clipped)) {
                ++writerBad;
                continue;
            }
            clippedN += clipped;
            if (d == 1) {
                outT.add(e);
                if (hT.active) hT.add(hv[j]);
            } else {
                outH.add(e);
                if (hH.active) hH.add(hv[j]);
            }
        }
    }
    outT.close();
    outH.close();
    hT.close();
    hH.close();
    const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    char buf[1024];
    std::snprintf(buf, sizeof buf,
                  "{\"mode\": \"convert\", \"rows\": %llu, \"dest_drop\": %llu, \"dest_train\": %llu, \"dest_hold\": %llu, "
                  "\"dest_bad\": %llu, \"train_records\": %llu, \"hold_records\": %llu, \"writer_bad\": %llu, \"clipped\": %llu, "
                  "\"train_bytes\": %llu, \"hold_bytes\": %llu, \"train_chunks\": %llu, \"hold_chunks\": %llu, "
                  "\"hce_train\": %llu, \"hce_hold\": %llu, \"ply\": %d, \"seconds\": %.2f}",
                  (unsigned long long)in.n, (unsigned long long)cnt[0], (unsigned long long)cnt[1], (unsigned long long)cnt[2],
                  (unsigned long long)cnt[3], (unsigned long long)outT.records, (unsigned long long)outH.records,
                  (unsigned long long)writerBad, (unsigned long long)clippedN, (unsigned long long)outT.bytes,
                  (unsigned long long)outH.bytes, (unsigned long long)outT.chunks, (unsigned long long)outH.chunks,
                  (unsigned long long)hT.n, (unsigned long long)hH.n, a.ply, secs);
    emit_json(a, buf);
    return 0;
}

// ------------------------------------------------------------------------------------------------ verify
// 0 = equal; otherwise a bit mask: 1 board, 2 side, 4 score, 8 result, 16 ply, 32 move
int compare(const binpack::TrainingDataEntry& e, const std::uint8_t* b, std::int16_t score, std::uint8_t meta, int ply) {
    int diff = 0;
    for (int s = 0; s < 64; ++s) {
        const chess::Piece p = e.pos.pieceAt(chess::fromOrdinal<chess::Square>(s));
        int code = 0;
        if (p.type() != chess::PieceType::None) code = 1 + chess::ordinal(p.type()) + 6 * chess::ordinal(p.color());
        if (code != code_at(b, s)) {
            diff |= 1;
            break;
        }
    }
    const bool blackToMove = meta & 1;
    if ((e.pos.sideToMove() == chess::Color::Black) != blackToMove) diff |= 2;
    const int clipped = score > 32000 ? 32000 : (score < -32000 ? -32000 : score);
    if (e.score != clipped) diff |= 4;
    const int whiteRes = ((meta >> 1) & 3) - 1;
    if (e.result != (blackToMove ? -whiteRes : whiteRes)) diff |= 8;
    if (e.ply != ply) diff |= 16;
    if (!(e.move == chess::Move::null())) {
        const chess::Square ksq = e.pos.kingSquare(e.pos.sideToMove());
        if (!(e.move.from == ksq && e.move.to == ksq)) diff |= 32;
    }
    return diff;
}

int run_verify(const Args& a) {
    const auto t0 = std::chrono::steady_clock::now();
    if (a.code != 1 && a.code != 2) die("--code must be 1 (train) or 2 (holdout)");
    Fpos in;
    in.open(a.pos);
    const auto dest = read_dest(a.dest, in.n);
    // 1) independent structure check: BINP chunks, sizes multiple of 34, zero move counts, exact file size
    std::uint64_t formatErrors = 0, structRecords = 0;
    {
        std::ifstream f(a.file, std::ios::binary);
        if (!f) die("cannot open " + a.file);
        f.seekg(0, std::ios::end);
        const auto fsize = static_cast<std::uint64_t>(f.tellg());
        f.seekg(0);
        std::uint64_t off = 0;
        std::vector<char> chunk;
        while (off + 8 <= fsize) {
            char head[8];
            f.read(head, 8);
            if (!f || std::memcmp(head, "BINP", 4) != 0) { ++formatErrors; break; }
            const std::uint32_t size = static_cast<unsigned char>(head[4]) | (static_cast<unsigned char>(head[5]) << 8) |
                                       (static_cast<unsigned char>(head[6]) << 16) |
                                       (static_cast<std::uint32_t>(static_cast<unsigned char>(head[7])) << 24);
            if (size % ENTRY_BYTES != 0 || off + 8 + size > fsize) { ++formatErrors; break; }
            chunk.resize(size);
            f.read(chunk.data(), size);
            for (std::uint64_t r = 0; r < size / ENTRY_BYTES; ++r)
                if (chunk[r * ENTRY_BYTES + 32] != 0 || chunk[r * ENTRY_BYTES + 33] != 0) ++formatErrors;
            structRecords += size / ENTRY_BYTES;
            off += 8 + size;
        }
        if (off != fsize) ++formatErrors;
    }
    // 2) the loader's own sequential reader against the selected source rows
    Fhce hce;
    FhceSeq hceOut;
    const bool withHce = !a.hceFile.empty();
    if (withHce) {
        if (a.hce.empty()) die("--hce-file needs --hce");
        hce.open(a.hce);
        hceOut.f.open(a.hceFile);
    }
    binpack::CompressedTrainingDataEntryReader reader(a.file);
    std::vector<std::uint8_t> boards, metas;
    std::vector<std::int16_t> scores, hv, ho;
    binpack::TrainingDataEntry e;
    std::string fen;
    std::uint64_t expected = 0, readerRecords = 0, mismatches = 0, writerBad = 0, hceMism = 0, hceIdx = 0;
    int mask = 0;
    for (std::uint64_t first = 0; first < in.n; first += a.chunkRows) {
        const std::uint64_t count = std::min<std::uint64_t>(a.chunkRows, in.n - first);
        in.read(first, count, boards, scores, metas);
        if (withHce) hce.read(first, count, hv);
        for (std::uint64_t j = 0; j < count; ++j) {
            if (dest_at(dest, first + j) != a.code) continue;
            bool clipped = false;
            if (!convert(boards.data() + j * 32, scores[j], metas[j], a.ply, e, fen, clipped)) {
                ++writerBad;
                continue;
            }
            ++expected;
            if (!reader.hasNext()) {
                ++mismatches;
                mask |= 64;
                continue;
            }
            const auto got = reader.next();
            ++readerRecords;
            const int d = compare(got, boards.data() + j * 32, scores[j], metas[j], a.ply);
            if (d) {
                ++mismatches;
                mask |= d;
            }
            if (withHce) {
                std::int16_t v = 0;
                if (!hceOut.get(hceIdx, v) || v != hv[j]) ++hceMism;
                ++hceIdx;
            }
        }
    }
    while (reader.hasNext()) {
        (void)reader.next();
        ++readerRecords;
        ++mismatches;
        mask |= 128;
    }
    if (withHce && hceOut.f.n != expected) ++hceMism;
    const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    const bool ok = formatErrors == 0 && mismatches == 0 && hceMism == 0 && structRecords == expected &&
                    readerRecords == expected && expected > 0;
    char buf[4096];
    std::snprintf(buf, sizeof buf,
                  "{\"mode\": \"verify\", \"file\": \"%s\", \"code\": %d, \"expected\": %llu, \"struct_records\": %llu, "
                  "\"reader_records\": %llu, \"format_errors\": %llu, \"mismatches\": %llu, \"mask\": %d, \"writer_bad\": %llu, "
                  "\"hce_checked\": %s, \"hce_mismatches\": %llu, \"seconds\": %.2f, \"ok\": %s}",
                  json_escape(a.file).c_str(), a.code, (unsigned long long)expected, (unsigned long long)structRecords,
                  (unsigned long long)readerRecords, (unsigned long long)formatErrors, (unsigned long long)mismatches, mask,
                  (unsigned long long)writerBad, withHce ? "true" : "false", (unsigned long long)hceMism, secs,
                  ok ? "true" : "false");
    emit_json(a, buf);
    std::printf("%s\n", ok ? "VERIFY OK" : "VERIFY FAILED");
    return ok ? 0 : 1;
}

Args parse(int argc, char** argv) {
    Args a;
    if (argc < 2) die("usage: r11_pos2binpack convert|verify --pos P --dest D ... (see the source header)");
    a.mode = argv[1];
    for (int i = 2; i < argc; ++i) {
        const std::string k = argv[i];
        auto val = [&]() -> std::string {
            if (i + 1 >= argc) die("missing value for " + k);
            return argv[++i];
        };
        if (k == "--pos") a.pos = val();
        else if (k == "--dest") a.dest = val();
        else if (k == "--hce") a.hce = val();
        else if (k == "--train") a.train = val();
        else if (k == "--hold") a.hold = val();
        else if (k == "--hce-train") a.hceTrain = val();
        else if (k == "--hce-hold") a.hceHold = val();
        else if (k == "--json") a.json = val();
        else if (k == "--file") a.file = val();
        else if (k == "--hce-file") a.hceFile = val();
        else if (k == "--ply") a.ply = std::stoi(val());
        else if (k == "--code") a.code = std::stoi(val());
        else if (k == "--chunk-rows") a.chunkRows = std::stoull(val());
        else die("unknown option " + k);
    }
    if (a.pos.empty() || a.dest.empty()) die("--pos and --dest are required");
    if (a.ply < 0 || a.ply > 65535) die("--ply out of range");
    if (a.chunkRows == 0) die("--chunk-rows must be > 0");
    return a;
}

}  // namespace

int main(int argc, char** argv) {
    enter_background_mode();
    const Args a = parse(argc, argv);
    if (a.mode == "convert") return run_convert(a);
    if (a.mode == "verify") return run_verify(a);
    die("unknown mode " + a.mode);
}
