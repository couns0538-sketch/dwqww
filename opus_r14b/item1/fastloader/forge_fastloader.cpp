// forge_fastloader.cpp - Opus R14-B fast training-data loader for the npt trainer (own code, 2026-11-02).
//
// Produces the batches of the npt loader DLL run with one decode worker, byte for byte (behaviour in
// ../LOADER_SPEC.md; nnue-pytorch is GPL-3.0 and was read for behaviour only, no code taken).
// Speed comes from (1) filtering on the packed record fields without building a board, (2) shuffling a 4-byte
// index permutation instead of 224-byte entries, (3) building feature batches on several threads, each batch
// into its own slot, so the output does not depend on the thread count.
// Build: build_fastloader.sh (MinGW g++ 15.2 = the libstdc++ of the old DLL, so std::shuffle matches).

#include <algorithm>
#include <atomic>
#include <bit>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <exception>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#ifdef _WIN32
#define FFL_API extern "C" __declspec(dllexport)
#else
#define FFL_API extern "C" __attribute__((visibility("default")))
#endif

namespace {

constexpr int kMaxActive = 32;                       // K32H3: one feature per piece and perspective
constexpr int kInputs = 768 * 32 * 3;                // planes x king buckets x states
constexpr int kValueNone = 32002;
constexpr std::size_t kScratchEntries = 1u << 14;    // kept records per bulk append (spec 4)
constexpr std::size_t kDefaultWindow = 1u << 20;
constexpr std::size_t kRecordBytes = 34;             // 32-byte packed entry + 2-byte chain length
constexpr std::uint32_t kMaxChunkBytes = 100u << 20;
constexpr double kTwo64 = static_cast<double>(~0ULL);

// The trainer's SparseBatch header as its ctypes structure reads it.
struct BatchView {
    int num_inputs;
    int size;
    float* is_white;
    float* outcome;
    float* score;
    int num_active_white_features;
    int num_active_black_features;
    int max_active_features;
    int* white;
    int* black;
    int* piece_count;
    int* queen_bucket;
};
static_assert(offsetof(BatchView, is_white) == 8 && offsetof(BatchView, num_active_white_features) == 32
              && offsetof(BatchView, white) == 48 && sizeof(BatchView) == 80, "SparseBatch ctypes layout");

}  // namespace

// C configuration filled by forge_fastloader.py (field order is part of the ABI).
struct FflConfig {
    int batch_size;
    int threads;                  // feature-builder threads
    int cyclic;
    int window_entries;           // shuffle_buffer_entries; <= 0 = 1,048,576
    int random_fen_skipping;
    int early_fen_skipping;
    int soft_early_fen_skipping;
    int filtered;                 // must be 0
    int wld_filtered;             // must be 0
    int simple_eval_skipping;     // must be <= 0
    int max_live_windows;         // <= 0 = 3
    int ring_batches;             // <= 0 = threads + 4
    double pc_y[5];
    double ply_x[4];
    double ply_y[4];
};

namespace {

// x * 2^64 thresholds of the skip filter as u64. x = 2^64 exactly (acceptance 0) is out of range for a plain cast;
// it saturates to 2^64 - 1 ("always reject"), which is what the AVX-512 conversion of both DLLs returns on this CPU.
inline std::uint64_t to_threshold(double x) {
    if (!(x < kTwo64))
        return ~0ULL;
    if (x <= 0.0)
        return 0;
    return static_cast<std::uint64_t>(x);
}

inline std::uint16_t be16(const unsigned char* p) { return static_cast<std::uint16_t>((p[0] << 8) | p[1]); }

inline std::uint64_t be64(const unsigned char* p) {
    std::uint64_t v = 0;
    for (int i = 0; i < 8; ++i)
        v = (v << 8) | p[i];
    return v;
}

// 16-bit zig-zag style code of the packed entry (spec 2).
inline int unzig16(std::uint16_t u) {
    std::uint16_t r = static_cast<std::uint16_t>((u << 15) | (u >> 1));
    if (r & 0x8000)
        r ^= 0x7FFF;
    return static_cast<std::int16_t>(r);
}

// One kept record: everything the batch builder needs, 32 bytes.
struct Kept {
    std::uint64_t occ;
    std::uint8_t nib[16];
    std::int16_t score;
    std::int16_t result;
    std::uint32_t pad;
};
static_assert(sizeof(Kept) == 32, "compact record");

// Skip filter of spec 3. One instance per stream, used by one thread, in file order.
class SkipFilter {
public:
    explicit SkipFilter(const FflConfig& c) : cfg_(c) {
        // The old loader installs no filter at all when no skip option is active: keep everything, no draws.
        active_ = c.filtered || c.wld_filtered || c.random_fen_skipping > 0 || c.early_fen_skipping >= 0
               || c.soft_early_fen_skipping > 0;
        if (c.random_fen_skipping > 0) {
            const double p = double(c.random_fen_skipping) / (c.random_fen_skipping + 1);
            random_threshold_ = to_threshold(p * kTwo64);
        }
        double total = 0.0;
        for (int pc = 0; pc <= 32; ++pc) {
            weight_[pc] = spline_weight(pc);
            total += weight_[pc];
        }
        if (total <= 0.0) {
            for (double& w : weight_)
                w = 1.0;
            total = 33.0;
        }
        weight_total_ = total;
        if (c.soft_early_fen_skipping > 0) {
            ply_accept_.resize(static_cast<std::size_t>(c.soft_early_fen_skipping) + 1);
            for (std::size_t i = 0; i < ply_accept_.size(); ++i)
                ply_accept_[i] = std::clamp(ply_curve(static_cast<double>(i)), 0.0, 1.0);
        }
    }

    // True = keep the record.
    bool keep(int ply, int score, int result, int pc, std::mt19937_64& rng) {
        if (!active_)
            return true;
        const bool placeholder = ply > last_ply_ && last_score_ != kValueNone && std::abs(last_score_) > 100
                              && result != 0 && score == 0;
        last_ply_ = ply;
        if (score == kValueNone || placeholder)
            return false;
        last_score_ = score;
        if (ply <= cfg_.early_fen_skipping)
            return false;
        if (cfg_.random_fen_skipping && rng() < random_threshold_)
            return false;
        if (cfg_.soft_early_fen_skipping > 0 && ply < cfg_.soft_early_fen_skipping) {
            const auto reject = to_threshold((1.0 - ply_accept_[ply]) * kTwo64);
            if (rng() < reject)
                return false;
        }
        if (pc < 0 || pc > 32)
            return false;
        seen_[pc] += 1.0;
        seen_total_ += 1.0;
        ++steps_;
        if (steps_ == 100 || steps_ == 500 || steps_ == 1000 || steps_ == 2500 || steps_ == 5000
            || (steps_ > 5000 && steps_ % 10000 == 0)) {
            double lowest = std::numeric_limits<double>::infinity();
            bool found = false;
            for (int i = 0; i <= 32; ++i)
                if (weight_[i] > 0.0 && seen_[i] > 0.0) {
                    const double r = (seen_total_ * weight_[i]) / (weight_total_ * seen_[i]);
                    if (r < lowest) {
                        lowest = r;
                        found = true;
                    }
                }
            if (found && lowest > 0.0)
                alpha_ = (1.0 - kMaxPcSkip) / lowest;
            if (steps_ >= 10000 && steps_ % 10000 == 0) {
                for (double& s : seen_)
                    s *= 0.5;
                seen_total_ *= 0.5;
            }
        }
        double accept = 0.0;
        if (weight_[pc] > 0.0 && seen_[pc] > 0.0)
            accept = alpha_ * ((seen_total_ * weight_[pc]) / (weight_total_ * seen_[pc]));
        accept = std::clamp(accept, 0.0, 1.0);
        const auto reject = to_threshold((1.0 - accept) * kTwo64);
        return !(rng() < reject);
    }

private:
    static constexpr double kMaxPcSkip = 0.975;

    // Target piece-count weight: cubic Hermite through (8i, pc_y[i]) with central-difference slopes.
    double spline_weight(int pc) const {
        const double x = static_cast<double>(pc);
        const double* y = cfg_.pc_y;
        if (x <= 0)
            return y[0];
        if (x >= 32)
            return y[4];
        int i = static_cast<int>(x / 8.0);
        if (i > 3)
            i = 3;
        const double t = (x - i * 8.0) / 8.0;
        auto slope = [y](int k) {
            if (k == 0)
                return (y[1] - y[0]);
            if (k == 4)
                return (y[4] - y[3]);
            return (y[k + 1] - y[k - 1]) / 2.0;
        };
        const double m0 = slope(i);
        const double m1 = slope(i + 1);
        const double t2 = t * t;
        const double t3 = t2 * t;
        const double h00 = 2 * t3 - 3 * t2 + 1;
        const double h10 = t3 - 2 * t2 + t;
        const double h01 = -2 * t3 + 3 * t2;
        const double h11 = t3 - t2;
        const double v = h00 * y[i] + h10 * m0 + h01 * y[i + 1] + h11 * m1;
        return std::max(0.0, v);
    }

    // Early-ply acceptance: piecewise linear through the four (ply_x, ply_y) points and (S, 1).
    double ply_curve(double ply) const {
        const double xs[5] = {cfg_.ply_x[0], cfg_.ply_x[1], cfg_.ply_x[2], cfg_.ply_x[3],
                              static_cast<double>(cfg_.soft_early_fen_skipping)};
        const double ys[5] = {cfg_.ply_y[0], cfg_.ply_y[1], cfg_.ply_y[2], cfg_.ply_y[3], 1.0};
        if (ply <= xs[0])
            return ys[0];
        if (ply >= xs[4])
            return ys[4];
        for (int i = 0; i < 4; ++i)
            if (ply >= xs[i] && ply <= xs[i + 1]) {
                if (xs[i + 1] == xs[i])
                    return ys[i];
                const double t = (ply - xs[i]) / (xs[i + 1] - xs[i]);
                return ys[i] + t * (ys[i + 1] - ys[i]);
            }
        return 1.0;
    }

    FflConfig cfg_;
    bool active_ = true;
    std::uint64_t random_threshold_ = 0;
    double weight_[33] = {};
    double weight_total_ = 0.0;
    std::vector<double> ply_accept_;
    int last_ply_ = -1;
    int last_score_ = kValueNone;
    double alpha_ = 1.0;
    double seen_[33] = {};
    double seen_total_ = 0.0;
    std::uint64_t steps_ = 0;
};

class Loader;

// A sealed shuffle window: kept records in arrival order plus the shuffled index order.
struct Window {
    std::vector<Kept> recs;
    std::vector<std::uint32_t> order;
    Loader* owner = nullptr;
    ~Window();
};

struct Segment {
    std::shared_ptr<Window> win;
    std::uint32_t begin = 0;
    std::uint32_t count = 0;
};

struct Task {
    std::int64_t index = 0;
    int size = 0;
    std::vector<Segment> segs;
};

struct BatchBuf {
    BatchView view{};               // handed out to the consumer; release() maps it back
    bool handed_out = false;        // guarded by the loader mutex
    std::vector<float> floats;
    std::vector<int> ints;
};

class Loader {
public:
    Loader(const FflConfig& cfg, std::string path) : cfg_(cfg), path_(std::move(path)) {
        if (cfg_.batch_size <= 0)
            throw std::runtime_error("batch_size must be positive");
        if (cfg_.filtered || cfg_.wld_filtered || cfg_.simple_eval_skipping > 0)
            throw std::runtime_error("--fast-loader supports only --no-filtered --no-wld-filtered and no simple-eval skipping");
        window_ = cfg_.window_entries <= 0 ? kDefaultWindow
                                           : static_cast<std::size_t>(std::clamp(cfg_.window_entries, 1024, 1 << 24));
        threads_ = std::max(1, cfg_.threads);
        // Windows alive at once: the ones whose entries still wait for a whole batch (at most ceil(B / W)), the open
        // one and one spare. With fewer, a window much smaller than the batch would block the filter forever.
        const std::size_t per_batch = (static_cast<std::size_t>(cfg_.batch_size) + window_ - 1) / window_;
        max_live_ = std::max({3, static_cast<int>(std::min<std::size_t>(per_batch + 2, 1u << 20)), cfg_.max_live_windows});
        const int ring = cfg_.ring_batches > 0 ? cfg_.ring_batches : threads_ + 4;
        bufs_.resize(static_cast<std::size_t>(ring));
        for (auto& b : bufs_) {
            b = std::make_unique<BatchBuf>();
            b->floats.resize(static_cast<std::size_t>(cfg_.batch_size) * 3);
            b->ints.resize(static_cast<std::size_t>(cfg_.batch_size) * (2 * kMaxActive + 2));
            free_.push_back(b.get());
        }
        std::FILE* probe = std::fopen(path_.c_str(), "rb");
        if (!probe)
            throw std::runtime_error("cannot open " + path_);
        std::fclose(probe);
    }

    // Separate from the constructor so that a failed thread start still runs the destructor (joins).
    void start() {
        reader_ = std::thread([this] { guarded([this] { reader_main(); }); });
        filter_ = std::thread([this] { guarded([this] { filter_main(); }); });
        for (int i = 0; i < threads_; ++i)
            builders_.emplace_back([this] { guarded([this] { builder_main(); }); });
    }

    ~Loader() {
        {
            std::lock_guard lk(m_);
            stop_ = true;
        }
        notify_all();
        if (reader_.joinable())
            reader_.join();
        if (filter_.joinable())
            filter_.join();
        for (auto& t : builders_)
            if (t.joinable())
                t.join();
        tasks_.clear();
        pending_.clear();
    }

    BatchView* next() {
        std::unique_lock lk(m_);
        cv_out_.wait(lk, [&] {
            return stop_ || !error_.empty() || done_.count(next_out_) != 0 || (filter_done_ && next_out_ == tasks_made_);
        });
        if (!error_.empty() || stop_)
            return nullptr;
        auto it = done_.find(next_out_);
        if (it == done_.end())
            return nullptr;              // end of a finite stream
        BatchBuf* b = it->second;
        done_.erase(it);
        ++next_out_;
        b->handed_out = true;
        return &b->view;
    }

    // Gives a batch buffer back. A pointer that is not a handed-out batch (double release, foreign pointer) stops
    // the stream with an error instead of letting two builders share one buffer.
    void release(BatchView* v) {
        if (!v)
            return;
        bool bad = true;
        {
            std::lock_guard lk(m_);
            for (auto& b : bufs_)
                if (&b->view == v && b->handed_out) {
                    b->handed_out = false;
                    free_.push_back(b.get());
                    bad = false;
                    break;
                }
            if (bad && error_.empty())
                error_ = "release of a batch that is not handed out (double release?)";
        }
        if (bad)
            notify_all();
        else
            cv_build_.notify_all();
    }

    void stats(std::uint64_t* preskip, std::uint64_t* total, std::uint64_t* batches) const {
        if (preskip)
            *preskip = preskip_.load(std::memory_order_relaxed);
        if (total)
            *total = total_.load(std::memory_order_relaxed);
        if (batches)
            *batches = static_cast<std::uint64_t>(batches_out_.load(std::memory_order_relaxed));
    }

    std::string error() {
        std::lock_guard lk(m_);
        return error_;
    }

    void window_freed() {
        {
            std::lock_guard lk(m_);
            --live_windows_;
        }
        cv_win_.notify_all();
    }

private:
    template <class F>
    void guarded(F&& f) {
        try {
            f();
        } catch (const std::exception& e) {
            fail(e.what());
        } catch (...) {
            fail("unknown error");
        }
    }

    void fail(const std::string& what) {
        {
            std::lock_guard lk(m_);
            if (error_.empty())
                error_ = what;
        }
        notify_all();
    }

    void notify_all() {
        cv_chunk_.notify_all();
        cv_space_.notify_all();
        cv_win_.notify_all();
        cv_build_.notify_all();
        cv_out_.notify_all();
    }

    bool halted() {
        std::lock_guard lk(m_);
        return stop_ || !error_.empty();
    }

    // ---- reader thread: chunks in file order (cyclic restarts at the first chunk) ----
    void reader_main() {
        std::unique_ptr<std::FILE, int (*)(std::FILE*)> f(std::fopen(path_.c_str(), "rb"), &std::fclose);
        if (!f)
            throw std::runtime_error("cannot open " + path_);
        std::setvbuf(f.get(), nullptr, _IOFBF, 1 << 22);
        bool chunk_in_pass = false;
        for (;;) {
            if (halted())
                return;
            unsigned char hdr[8];
            const std::size_t got = std::fread(hdr, 1, 8, f.get());
            if (got == 0 && std::feof(f.get())) {
                if (!chunk_in_pass)
                    throw std::runtime_error("binpack file has no chunk: " + path_);
                if (!cfg_.cyclic) {
                    push_chunk(nullptr);
                    return;
                }
#ifdef _WIN32
                _fseeki64(f.get(), 0, SEEK_SET);
#else
                fseeko(f.get(), 0, SEEK_SET);
#endif
                std::clearerr(f.get());
                chunk_in_pass = false;
                continue;
            }
            if (got != 8 || std::memcmp(hdr, "BINP", 4) != 0)
                throw std::runtime_error("bad binpack chunk header in " + path_);
            const std::uint32_t size = std::uint32_t(hdr[4]) | (std::uint32_t(hdr[5]) << 8)
                                     | (std::uint32_t(hdr[6]) << 16) | (std::uint32_t(hdr[7]) << 24);
            if (size > kMaxChunkBytes)
                throw std::runtime_error("binpack chunk larger than 100 MiB in " + path_);
            auto chunk = std::make_unique<std::vector<unsigned char>>(size);
            if (std::fread(chunk->data(), 1, size, f.get()) != size)
                throw std::runtime_error("truncated binpack chunk in " + path_);
            chunk_in_pass = true;
            if (!push_chunk(std::move(chunk)))
                return;
        }
    }

    bool push_chunk(std::unique_ptr<std::vector<unsigned char>> c) {
        std::unique_lock lk(m_);
        cv_space_.wait(lk, [&] { return stop_ || !error_.empty() || chunks_.size() < kChunkQueue; });
        if (stop_ || !error_.empty())
            return false;
        if (c)
            chunks_.push_back(std::move(c));
        else
            reader_done_ = true;
        lk.unlock();
        cv_chunk_.notify_all();
        return true;
    }

    std::unique_ptr<std::vector<unsigned char>> pop_chunk() {
        std::unique_lock lk(m_);
        cv_chunk_.wait(lk, [&] { return stop_ || !error_.empty() || !chunks_.empty() || reader_done_; });
        if (stop_ || !error_.empty() || chunks_.empty())
            return nullptr;
        auto c = std::move(chunks_.front());
        chunks_.pop_front();
        lk.unlock();
        cv_space_.notify_all();
        return c;
    }

    // ---- filter thread: spec 3 + spec 4, the only user of the random engine ----
    void filter_main() {
        std::mt19937_64 rng;
        SkipFilter filter(cfg_);
        std::vector<Kept> scratch;
        scratch.reserve(kScratchEntries);
        std::shared_ptr<Window> open;
        for (;;) {
            auto chunk = pop_chunk();
            if (!chunk)
                break;
            const unsigned char* p = chunk->data();
            const std::size_t n = chunk->size();
            if (n < kRecordBytes)
                throw std::runtime_error("binpack chunk smaller than one record");
            std::uint64_t pre = 0, kept = 0;
            for (std::size_t off = 0; off + kRecordBytes <= n; off += kRecordBytes) {
                const unsigned char* r = p + off;
                if (be16(r + 32) != 0)
                    throw std::runtime_error("chained binpack records are not supported by --fast-loader");
                const std::uint64_t occ = be64(r);
                const int pc = std::popcount(occ);
                if (pc > 32)
                    throw std::runtime_error("binpack record with more than 32 pieces");
                const int score = unzig16(be16(r + 26));
                const std::uint16_t pr = be16(r + 28);
                const int ply = pr & 0x3FFF;
                const int result = unzig16(static_cast<std::uint16_t>(pr >> 14));
                ++pre;
                if (!filter.keep(ply, score, result, pc, rng))
                    continue;
                ++kept;
                Kept& k = scratch.emplace_back();
                k.occ = occ;
                std::memcpy(k.nib, r + 8, 16);
                k.score = static_cast<std::int16_t>(score);
                k.result = static_cast<std::int16_t>(result);
                k.pad = 0;
                if (scratch.size() >= kScratchEntries && !append(scratch, open, rng))
                    return;
            }
            preskip_.fetch_add(pre, std::memory_order_relaxed);
            total_.fetch_add(kept, std::memory_order_relaxed);
        }
        if (halted())
            return;
        // Finite stream: last scratch, then the partial window (spec 4), then the short last batch.
        if (!scratch.empty() && !append(scratch, open, rng))
            return;
        if (open && !open->recs.empty())
            seal(open, rng);
        open.reset();
        {
            std::lock_guard lk(m_);
            if (pending_count_ > 0)
                make_task_locked(static_cast<int>(pending_count_));
            filter_done_ = true;
        }
        cv_build_.notify_all();
        cv_out_.notify_all();
    }

    bool append(std::vector<Kept>& scratch, std::shared_ptr<Window>& open, std::mt19937_64& rng) {
        std::size_t off = 0;
        while (off < scratch.size()) {
            if (!open) {
                std::unique_lock lk(m_);
                cv_win_.wait(lk, [&] { return stop_ || !error_.empty() || live_windows_ < max_live_; });
                if (stop_ || !error_.empty())
                    return false;
                ++live_windows_;
                lk.unlock();
                open = std::make_shared<Window>();
                open->owner = this;
                open->recs.reserve(window_);
            }
            const std::size_t take = std::min(window_ - open->recs.size(), scratch.size() - off);
            open->recs.insert(open->recs.end(), scratch.begin() + static_cast<std::ptrdiff_t>(off),
                              scratch.begin() + static_cast<std::ptrdiff_t>(off + take));
            off += take;
            if (open->recs.size() >= window_) {
                seal(open, rng);
                open.reset();
            }
        }
        scratch.clear();
        return true;
    }

    // Shuffle the window's index order with the filter's engine, then cut it into batch tasks.
    void seal(const std::shared_ptr<Window>& w, std::mt19937_64& rng) {
        w->order.resize(w->recs.size());
        std::iota(w->order.begin(), w->order.end(), 0u);
        std::shuffle(w->order.begin(), w->order.end(), rng);
        {
            std::lock_guard lk(m_);
            pending_.push_back(Segment{w, 0, static_cast<std::uint32_t>(w->recs.size())});
            pending_count_ += w->recs.size();
            while (pending_count_ >= static_cast<std::size_t>(cfg_.batch_size))
                make_task_locked(cfg_.batch_size);
        }
        cv_build_.notify_all();
    }

    void make_task_locked(int size) {
        Task t;
        t.index = tasks_made_++;
        t.size = size;
        int need = size;
        while (need > 0) {
            Segment& s = pending_.front();
            const auto take = static_cast<std::uint32_t>(std::min<std::size_t>(need, s.count));
            t.segs.push_back(Segment{s.win, s.begin, take});
            s.begin += take;
            s.count -= take;
            need -= static_cast<int>(take);
            if (s.count == 0)
                pending_.pop_front();
        }
        pending_count_ -= static_cast<std::size_t>(size);
        tasks_.push_back(std::move(t));
    }

    // ---- builder threads: batch k into its own buffer (spec 5) ----
    void builder_main() {
        for (;;) {
            Task t;
            BatchBuf* b = nullptr;
            {
                std::unique_lock lk(m_);
                cv_build_.wait(lk, [&] {
                    return stop_ || !error_.empty() || (!tasks_.empty() && !free_.empty())
                        || (tasks_.empty() && filter_done_);
                });
                if (stop_ || !error_.empty() || tasks_.empty())
                    return;
                t = std::move(tasks_.front());
                tasks_.pop_front();
                b = free_.back();
                free_.pop_back();
            }
            build(t, *b);
            t.segs.clear();  // drops window references (a fully used window is freed here)
            {
                std::lock_guard lk(m_);
                done_[t.index] = b;
                batches_out_.fetch_add(1, std::memory_order_relaxed);
            }
            cv_out_.notify_all();
            cv_build_.notify_all();
        }
    }

    static void build(const Task& t, BatchBuf& b) {
        const int n = t.size;
        BatchView& v = b.view;
        float* fl = b.floats.data();
        int* in = b.ints.data();
        v.num_inputs = kInputs;
        v.size = n;
        v.max_active_features = kMaxActive;
        v.is_white = fl;
        v.outcome = fl + n;
        v.score = fl + 2 * n;
        v.white = in;
        v.black = in + static_cast<std::size_t>(n) * kMaxActive;
        v.piece_count = in + static_cast<std::size_t>(n) * kMaxActive * 2;
        v.queen_bucket = v.piece_count + n;
        std::fill(in, in + static_cast<std::size_t>(n) * kMaxActive * 2, -1);
        int row = 0;
        int active = 0;
        for (const Segment& s : t.segs)
            for (std::uint32_t i = 0; i < s.count; ++i)
                active += fill_row(s.win->recs[s.win->order[s.begin + i]], row++, v);
        v.num_active_white_features = active;
        v.num_active_black_features = active;
    }

    // Returns the number of pieces (= features per perspective).
    static int fill_row(const Kept& k, int row, BatchView& v) {
        int sq_of[32];
        int code_of[32];
        int cnt = 0;
        int stm = 0;
        int king[2] = {-1, -1};
        bool queen[2] = {false, false};
        bool rook_or_queen = false;
        std::uint64_t occ = k.occ;
        while (occ) {
            const int sq = std::countr_zero(occ);
            occ &= occ - 1;
            const int nib = (cnt & 1) ? (k.nib[cnt >> 1] >> 4) : (k.nib[cnt >> 1] & 0xF);
            int code = nib;
            if (nib == 12)
                code = (sq >> 3) == 3 ? 0 : 1;   // pawn with an en-passant square behind it
            else if (nib == 13)
                code = 6;                        // white rook with a castling right
            else if (nib == 14)
                code = 7;                        // black rook with a castling right
            else if (nib == 15) {
                code = 11;                       // black king, black to move
                stm = 1;
            }
            const int type = code >> 1;
            const int colour = code & 1;
            if (type == 5 && king[colour] < 0)
                king[colour] = sq;
            if (type == 4) {
                queen[colour] = true;
                rook_or_queen = true;
            }
            if (type == 3)
                rook_or_queen = true;
            sq_of[cnt] = sq;
            code_of[cnt] = code;
            ++cnt;
        }
        if (king[0] < 0 || king[1] < 0)
            throw std::runtime_error("binpack record without both kings");
        v.is_white[row] = stm == 0 ? 1.0f : 0.0f;
        v.outcome[row] = (k.result + 1.0f) / 2.0f;
        v.score[row] = static_cast<float>(k.score);
        v.piece_count[row] = cnt;
        v.queen_bucket[row] = (queen[stm] ? 2 : 0) | (queen[stm ^ 1] ? 1 : 0);
        for (int c = 0; c < 2; ++c) {
            const int flip = (c == 1 ? 56 : 0) ^ ((king[c] & 7) < 4 ? 7 : 0);
            const int ok = king[c] ^ flip;
            const int bucket = 31 - (4 * (ok >> 3) + (ok & 7) - 4);
            const int state = queen[c ^ 1] ? 2 : (rook_or_queen ? 1 : 0);
            const int base = 768 * (32 * state + bucket);
            int* out = (c == 0 ? v.white : v.black) + static_cast<std::size_t>(row) * kMaxActive;
            for (int i = 0; i < cnt; ++i) {
                const int code = code_of[i];
                out[i] = (sq_of[i] ^ flip) + 64 * (2 * (code >> 1) + ((code & 1) != c)) + base;
            }
        }
        return cnt;
    }

    static constexpr std::size_t kChunkQueue = 8;

    FflConfig cfg_;
    std::string path_;
    std::size_t window_ = kDefaultWindow;
    int threads_ = 1;
    int max_live_ = 3;

    std::mutex m_;
    std::condition_variable cv_chunk_, cv_space_, cv_win_, cv_build_, cv_out_;
    bool stop_ = false;
    std::string error_;
    std::deque<std::unique_ptr<std::vector<unsigned char>>> chunks_;
    bool reader_done_ = false;
    int live_windows_ = 0;
    std::deque<Segment> pending_;
    std::size_t pending_count_ = 0;
    std::deque<Task> tasks_;
    std::int64_t tasks_made_ = 0;
    bool filter_done_ = false;
    std::vector<std::unique_ptr<BatchBuf>> bufs_;
    std::vector<BatchBuf*> free_;
    std::map<std::int64_t, BatchBuf*> done_;
    std::int64_t next_out_ = 0;
    std::atomic<std::uint64_t> preskip_{0}, total_{0};
    std::atomic<std::int64_t> batches_out_{0};

    std::thread reader_, filter_;
    std::vector<std::thread> builders_;
};

Window::~Window() {
    if (owner)
        owner->window_freed();
}

thread_local std::string g_create_error;

}  // namespace

FFL_API const char* ffl_version() { return "forge_fastloader 1 (Opus R14-B)"; }

FFL_API int ffl_config_size() { return static_cast<int>(sizeof(FflConfig)); }

FFL_API void* ffl_create(const FflConfig* cfg, const char* path) {
    g_create_error.clear();
    try {
        if (!cfg || !path)
            throw std::runtime_error("null argument");
        auto loader = std::make_unique<Loader>(*cfg, path);
        loader->start();
        return loader.release();
    } catch (const std::exception& e) {
        g_create_error = e.what();
    } catch (...) {
        g_create_error = "unknown error";
    }
    return nullptr;
}

FFL_API const char* ffl_create_error() { return g_create_error.c_str(); }

FFL_API BatchView* ffl_next(void* h) { return h ? static_cast<Loader*>(h)->next() : nullptr; }

FFL_API void ffl_release(void* h, BatchView* b) {
    if (h)
        static_cast<Loader*>(h)->release(b);
}

FFL_API void ffl_stats(void* h, std::uint64_t* preskip, std::uint64_t* total, std::uint64_t* batches) {
    if (h)
        static_cast<Loader*>(h)->stats(preskip, total, batches);
}

// Copies the error text (empty = none) into buf; returns its full length.
FFL_API int ffl_error(void* h, char* buf, int len) {
    if (!h)
        return 0;
    const std::string e = static_cast<Loader*>(h)->error();
    if (buf && len > 0) {
        const int n = std::min<int>(len - 1, static_cast<int>(e.size()));
        std::memcpy(buf, e.data(), static_cast<std::size_t>(n));
        buf[n] = 0;
    }
    return static_cast<int>(e.size());
}

FFL_API void ffl_destroy(void* h) { delete static_cast<Loader*>(h); }
