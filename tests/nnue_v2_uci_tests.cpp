// UCI-level tests of the fail-loud NNUE v2 rule (C4 review fix, C5 output buckets; rule in
// forge/search_options.hpp).
// Runs the real engine (argv[1]) with scripted stdin and checks its output and exit status:
//   - defaults: nothing NNUE-v2 related is printed, readyok, bestmove, exit 0;
//   - a requested v2 net that cannot be used (missing file, truncated file, bad checksum, wrong king
//     bucket count, NNUEKingBuckets without NNUEFile, NNUEFile with NNUEKingBuckets 0, a failed reload after
//     a good net): `info string ERROR NNUE v2: <reason>` at once and again at the next isready / go / bench,
//     then exit status 2 without readyok / bestmove / bench output;
//   - a valid net: `info string NNUE v2: active: <file> king buckets N output buckets M hidden H ...` once
//     when it becomes active and at every isready, then readyok and bestmove, exit 0;
//   - UseNNUE false is not an error, NNUEFile <empty> clears the request, option order does not matter;
//   - C5: NNUEOutputBuckets is a request too (without a file, with a net of another head count, a net with
//     heads loaded but the count left 0, king + output buckets with only one of the two options: exit 2);
//     nets with 8 output heads (alone and with king buckets) become active with both counts set.
// Writes its net files and engine transcripts into the working directory (removed at the end).
// usage: forge_nnue_v2_uci_tests <forge executable>
#include "forge/nnue.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#if !defined(_WIN32)
#include <sys/wait.h>
#endif

namespace {

int checks = 0;
int failures = 0;
void report(bool okay, const std::string& label) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << label << '\n';
}

const std::string Prefix = "nnue_v2_uci_";
std::vector<std::string> temporary_files;

void write_file(const std::string& path, const std::string& bytes) {
    std::ofstream out(path, std::ios::binary);
    out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    temporary_files.push_back(path);
}

std::string read_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream text;
    text << in.rdbuf();
    return text.str();
}

// ---- a v2 net file (format in forge/nnue_v2.hpp), small random weights
void put32(std::string& s, std::uint32_t v) {
    for (int i = 0; i < 4; ++i) s.push_back(static_cast<char>((v >> (8 * i)) & 0xFFU));
}
void putf(std::string& s, float f) {
    std::uint32_t v = 0;
    std::memcpy(&v, &f, 4);
    put32(s, v);
}
void put16(std::string& s, std::int16_t v) {
    const auto u = static_cast<std::uint16_t>(v);
    s.push_back(static_cast<char>(u & 0xFFU));
    s.push_back(static_cast<char>(u >> 8U));
}
std::uint64_t fnv(const std::string& data) {
    std::uint64_t h = 0xcbf29ce484222325ULL;
    for (const unsigned char c : data) {
        h ^= c;
        h *= 0x100000001b3ULL;
    }
    return h;
}
std::string net_file(int king_buckets, std::uint64_t seed, int output_buckets = 1) {
    const int hidden = forge::nnue::HiddenSize;
    std::string s = "FORGENN2";
    put32(s, 2); put32(s, 160); put32(s, 0); put32(s, 768); put32(s, static_cast<std::uint32_t>(hidden));
    put32(s, static_cast<std::uint32_t>(king_buckets)); put32(s, static_cast<std::uint32_t>(output_buckets));
    put32(s, 1);   // residual
    putf(s, 4096.0F); putf(s, 4096.0F); putf(s, 2.25F);
    for (int square = 0; square < 64; ++square) s.push_back(static_cast<char>((square & 7) * king_buckets / 8));
    // Output bucket map by piece count (the trainer's default: n = pieces - 2 -> min(N - 1, n * N / 32)).
    for (int pieces = 0; pieces <= 32; ++pieces) {
        const int n = pieces > 2 ? pieces - 2 : 0;
        s.push_back(static_cast<char>(n * output_buckets / 32 < output_buckets - 1 ? n * output_buckets / 32 : output_buckets - 1));
    }
    s.append(160 - s.size(), '\0');
    std::uint64_t x = seed;
    auto value = [&x](int range) {
        x ^= x >> 12U; x ^= x << 25U; x ^= x >> 27U;
        return static_cast<std::int16_t>(static_cast<int>((x * 2685821657736338717ULL) % static_cast<std::uint64_t>(2 * range + 1)) - range);
    };
    for (long i = 0; i < static_cast<long>(king_buckets) * 768 * hidden; ++i) put16(s, value(60));
    for (int i = 0; i < hidden; ++i) put16(s, value(400));
    for (int i = 0; i < output_buckets * 2 * hidden; ++i) put16(s, value(300));
    for (int i = 0; i < output_buckets; ++i) put16(s, value(100));
    const std::uint64_t h = fnv(s);
    for (int i = 0; i < 8; ++i) s.push_back(static_cast<char>((h >> (8 * i)) & 0xFFU));
    return s;
}

// ---- running the engine
struct Run {
    std::string out;
    int status = -1;
};

std::string quote(const std::string& text) { return "\"" + text + "\""; }

Run run_engine(const std::string& engine, const std::string& name, const std::string& script) {
    const std::string in = Prefix + name + ".in";
    const std::string out = Prefix + name + ".out";
    const std::string err = Prefix + name + ".err";
    write_file(in, script);
    temporary_files.push_back(out);
    temporary_files.push_back(err);
    std::string command = quote(engine) + " < " + quote(in) + " > " + quote(out) + " 2> " + quote(err);
#if defined(_WIN32)
    command = "\"" + command + "\"";   // cmd.exe /c strips one pair of outer quotes
#endif
    std::fflush(nullptr);
    const int raw = std::system(command.c_str());
    Run run;
#if defined(_WIN32)
    run.status = raw;
#else
    run.status = WIFEXITED(raw) ? WEXITSTATUS(raw) : 128 + (WIFSIGNALED(raw) ? WTERMSIG(raw) : 0);
#endif
    run.out = read_file(out);
    const std::string errors = read_file(err);
    if (!errors.empty()) std::cout << "  [" << name << " stderr] " << errors.substr(0, 400) << '\n';
    return run;
}

int count(const std::string& text, const std::string& what) {
    int n = 0;
    for (std::size_t at = text.find(what); at != std::string::npos; at = text.find(what, at + what.size())) ++n;
    return n;
}
bool has(const std::string& text, const std::string& what) { return text.find(what) != std::string::npos; }
bool has_line(const std::string& text, const std::string& prefix) {
    std::istringstream lines(text);
    for (std::string line; std::getline(lines, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind(prefix, 0) == 0) return true;
    }
    return false;
}
// The last ERROR line of a transcript (the one printed at the trigger command), for the checks and the log.
std::string errors_of(const std::string& text) {
    std::istringstream lines(text);
    std::string last = "(no ERROR line)";
    for (std::string line; std::getline(lines, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind("info string ERROR NNUE v2:", 0) == 0) last = line;
    }
    return last;
}

const std::string Head = "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n";
std::string set(const std::string& name, const std::string& value) { return "setoption name " + name + " value " + value + "\n"; }

// A request that cannot be honoured: an ERROR at once and again at `trigger`, then exit status 2 without
// the trigger's normal answer.
void expect_failure(const std::string& engine, const std::string& name, const std::string& options,
                    const std::string& trigger, const std::string& reason_phrase) {
    const Run r = run_engine(engine, name, Head + options + trigger + "\nquit\n");
    const int errors = count(r.out, "info string ERROR NNUE v2: ");
    const bool no_answer = !has_line(r.out, "readyok") && !has_line(r.out, "bestmove") && !has(r.out, "bench depth");
    report(r.status == 2 && errors >= 2 && no_answer && has(errors_of(r.out), reason_phrase),
           name + ": exit status " + std::to_string(r.status) + " at " + trigger + ", " + std::to_string(errors) +
               " ERROR lines, " + (no_answer ? "no answer" : "ANSWERED (readyok / bestmove / bench)") + ": " + errors_of(r.out));
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: forge_nnue_v2_uci_tests <forge executable>\n";
        return 2;
    }
    std::string engine = argv[1];
#if defined(_WIN32)
    for (char& c : engine) if (c == '/') c = '\\';
#endif
    const std::string valid = Prefix + "valid.fnn2";       // 2 king buckets (files a-d / e-h), 1 output bucket
    const std::string truncated = Prefix + "truncated.fnn2";
    const std::string damaged = Prefix + "damaged.fnn2";
    const std::string missing = Prefix + "missing.fnn2";   // never written
    const std::string bytes = net_file(2, 20261027);
    write_file(valid, bytes);
    write_file(truncated, bytes.substr(0, bytes.size() - 2));
    std::string flipped = bytes;
    flipped[5000] = static_cast<char>(flipped[5000] ^ 0x10);
    write_file(damaged, flipped);
    const std::string active_line = "info string NNUE v2: active: " + valid + " king buckets 2 output buckets 1 hidden " +
                                    std::to_string(forge::nnue::HiddenSize);

    // Defaults: nothing new.
    {
        const Run r = run_engine(engine, "defaults", Head + "isready\ngo depth 1\nisready\nquit\n");
        report(r.status == 0 && count(r.out, "readyok") == 2 && has_line(r.out, "bestmove") && !has(r.out, "NNUE v2") &&
                   has(r.out, "option name NNUEFile type string default <empty>"),
               "defaults: exit 0, readyok, bestmove, no NNUE v2 line");
    }
    // Requests that cannot be honoured.
    expect_failure(engine, "missing_file_isready", set("NNUEFile", missing) + set("NNUEKingBuckets", "2"), "isready", "cannot open");
    expect_failure(engine, "missing_file_go", set("NNUEFile", missing) + set("NNUEKingBuckets", "2"), "go depth 1", "cannot open");
    expect_failure(engine, "missing_file_bench", set("NNUEFile", missing) + set("NNUEKingBuckets", "2"), "bench 2", "cannot open");
    expect_failure(engine, "truncated_file", set("NNUEFile", truncated) + set("NNUEKingBuckets", "2"), "isready",
                   "the weights were not read");
    expect_failure(engine, "damaged_file", set("NNUEFile", damaged) + set("NNUEKingBuckets", "2"), "isready", "checksum mismatch");
    expect_failure(engine, "wrong_bucket_count", set("NNUEFile", valid) + set("NNUEKingBuckets", "4"), "isready", "does not match");
    expect_failure(engine, "buckets_without_file", set("NNUEKingBuckets", "2"), "go depth 1", "no v2 net is loaded");
    expect_failure(engine, "file_with_buckets_0", set("NNUEFile", valid), "isready", "NNUEKingBuckets is 0");
    expect_failure(engine, "failed_reload_after_good_net",
                   set("NNUEFile", valid) + set("NNUEKingBuckets", "2") + set("NNUEFile", missing), "isready", "cannot open");
    expect_failure(engine, "usennue_true_again", set("UseNNUE", "false") + set("NNUEFile", missing) + set("NNUEKingBuckets", "2") +
                   set("UseNNUE", "true"), "isready", "cannot open");
    // A valid net: active line once when it becomes active and at every isready.
    {
        const Run r = run_engine(engine, "valid_net", Head + set("NNUEFile", valid) + set("NNUEKingBuckets", "2") +
                                                          "isready\ngo depth 1\nisready\nquit\n");
        report(r.status == 0 && count(r.out, active_line) == 3 && count(r.out, "readyok") == 2 && has_line(r.out, "bestmove") &&
                   has(r.out, "info string NNUE v2: loaded " + valid),
               "valid net: exit 0, \"" + active_line + " ...\" printed 3 times (activation + 2 isready), readyok, bestmove");
        report(count(r.out, "ERROR NNUE v2") == 1, "valid net: NNUEFile before NNUEKingBuckets reports the half-set request once (" +
                                                        errors_of(r.out) + "), resolved by NNUEKingBuckets 2");
    }
    {
        const Run r = run_engine(engine, "order_buckets_first", Head + set("NNUEKingBuckets", "2") + set("NNUEFile", valid) +
                                                                   "isready\nquit\n");
        report(r.status == 0 && count(r.out, active_line) == 2 && has_line(r.out, "readyok"),
               "NNUEKingBuckets before NNUEFile: active, readyok, exit 0");
    }
    {
        const Run r = run_engine(engine, "bench_active", Head + set("NNUEFile", valid) + set("NNUEKingBuckets", "2") + "bench 3\nquit\n");
        report(r.status == 0 && has(r.out, "bench depth 3 nodes"), "valid net: bench runs, exit 0");
    }
    // Not errors.
    {
        const Run r = run_engine(engine, "usennue_false", Head + set("UseNNUE", "false") + set("NNUEKingBuckets", "2") +
                                                             set("NNUEFile", missing) + "isready\ngo depth 1\nquit\n");
        report(r.status == 0 && has_line(r.out, "readyok") && has_line(r.out, "bestmove") && !has(r.out, "ERROR") &&
                   has(r.out, "UseNNUE is false"),
               "UseNNUE false with a v2 request: not an error (exit 0, readyok, bestmove)");
    }
    {
        const Run r = run_engine(engine, "cleared", Head + set("NNUEFile", valid) + set("NNUEKingBuckets", "2") +
                                                       set("NNUEKingBuckets", "0") + set("NNUEFile", "<empty>") + "isready\ngo depth 1\nquit\n");
        report(r.status == 0 && has_line(r.out, "readyok") && has_line(r.out, "bestmove") && has(r.out, "info string NNUE v2: off") &&
                   count(r.out, active_line) == 1,
               "NNUEKingBuckets 0 + NNUEFile <empty>: request cleared, compiled-in net, exit 0");
    }
    // C5: output buckets.
    const std::string heads = Prefix + "heads.fnn2";         // 1 king bucket, 8 output heads
    const std::string both = Prefix + "kb2_heads.fnn2";      // 2 king buckets, 8 output heads
    write_file(heads, net_file(1, 20261028, 8));
    write_file(both, net_file(2, 20261029, 8));
    expect_failure(engine, "output_buckets_without_file", set("NNUEOutputBuckets", "8"), "isready", "no v2 net is loaded");
    expect_failure(engine, "output_buckets_vs_1_head", set("NNUEFile", valid) + set("NNUEKingBuckets", "2") + set("NNUEOutputBuckets", "8"),
                   "isready", "does not match");
    expect_failure(engine, "heads_net_counts_0", set("NNUEFile", heads), "go depth 1", "NNUEOutputBuckets is 0");
    expect_failure(engine, "heads_net_wrong_count", set("NNUEFile", heads) + set("NNUEOutputBuckets", "4"), "isready", "does not match");
    expect_failure(engine, "king_and_heads_net_king_option_only", set("NNUEFile", both) + set("NNUEKingBuckets", "2"), "isready",
                   "set NNUEKingBuckets 2, NNUEOutputBuckets 8");
    expect_failure(engine, "king_and_heads_net_output_option_only", set("NNUEFile", both) + set("NNUEOutputBuckets", "8"), "bench 2",
                   "does not match");
    {
        const std::string line = "info string NNUE v2: active: " + heads + " king buckets 1 output buckets 8 hidden " +
                                 std::to_string(forge::nnue::HiddenSize);
        const Run r = run_engine(engine, "heads_net", Head + set("NNUEFile", heads) + set("NNUEOutputBuckets", "8") +
                                                         "isready\ngo depth 1\nisready\nquit\n");
        report(r.status == 0 && count(r.out, line) == 3 && count(r.out, "readyok") == 2 && has_line(r.out, "bestmove"),
               "8-head net with NNUEOutputBuckets 8: \"" + line + " ...\" 3 times, readyok, bestmove, exit 0");
    }
    {
        const std::string line = "info string NNUE v2: active: " + both + " king buckets 2 output buckets 8 hidden " +
                                 std::to_string(forge::nnue::HiddenSize);
        const Run r = run_engine(engine, "king_and_heads_net", Head + set("NNUEOutputBuckets", "8") + set("NNUEFile", both) +
                                                                  set("NNUEKingBuckets", "2") + "isready\nbench 3\nquit\n");
        report(r.status == 0 && count(r.out, line) == 2 && has_line(r.out, "readyok") && has(r.out, "bench depth 3 nodes"),
               "2 king buckets + 8 heads with both options (any order): active, readyok, bench, exit 0");
    }
    {
        const Run r = run_engine(engine, "usennue_false_output_buckets", Head + set("UseNNUE", "false") + set("NNUEOutputBuckets", "8") +
                                                                            "isready\nquit\n");
        report(r.status == 0 && has_line(r.out, "readyok") && !has(r.out, "ERROR"), "UseNNUE false with NNUEOutputBuckets 8: not an error");
    }
    for (const std::string& file : temporary_files) std::remove(file.c_str());
    std::cout << checks - failures << "/" << checks << " checks passed\n";
    return failures == 0 ? 0 : 1;
}
