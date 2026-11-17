"""Build a scratch instrumented copy of the PATCHED source that counts and times the
per-move scan, so the cost question is answered by measurement rather than by reading.

The instrumentation is added only to a throwaway copy under $HOME; nothing of it is
committed. It prints one stderr line when the engine exits:
    SCANPROBE roots=<n> scanned_roots=<n> scan_iterations=<n> scan_ns=<n>
"""
import re
import sys

SRC = sys.argv[1]
DST = sys.argv[2]

text = open(SRC + "/search.cpp").read()

old = """    if (root_draw_adjudicated) {
        for (const Move move : legal) {
            Board child = board;
            Undo undo;
            (void)child.make_move(move, undo);
            if (child.legal_moves().empty() && child.in_check()) {
                root_draw_adjudicated = false;      // a mate on the board outranks the claim
                break;
            }
        }
    }"""
assert old in text, "patched scan block not found verbatim; refusing to instrument blind"

new = """    {
        extern std::uint64_t g_scan_roots, g_scan_scanned_roots, g_scan_iters, g_scan_ns;
        g_scan_roots += 1;
        if (root_draw_adjudicated) {
            g_scan_scanned_roots += 1;
            const auto t0 = std::chrono::steady_clock::now();
            for (const Move move : legal) {
                g_scan_iters += 1;
                Board child = board;
                Undo undo;
                (void)child.make_move(move, undo);
                if (child.legal_moves().empty() && child.in_check()) {
                    root_draw_adjudicated = false;      // a mate on the board outranks the claim
                    break;
                }
            }
            g_scan_ns += static_cast<std::uint64_t>(
                std::chrono::duration_cast<std::chrono::nanoseconds>(
                    std::chrono::steady_clock::now() - t0).count());
        }
    }"""
text = text.replace(old, new, 1)
open(DST + "/search.cpp", "w").write(text)

# globals + atexit reporter in main.cpp
main_path = DST + "/uci.cpp"
main_text = open(main_path).read()
defs = """
#include <cstdint>
#include <cstdio>
#include <cstdlib>
std::uint64_t g_scan_roots = 0, g_scan_scanned_roots = 0, g_scan_iters = 0, g_scan_ns = 0;
namespace {
struct ScanProbeReporter {
    ~ScanProbeReporter() {
        const char* on = std::getenv("SCANPROBE");
        if (!on) return;
        std::fprintf(stderr,
            "SCANPROBE roots=%llu scanned_roots=%llu scan_iterations=%llu scan_ns=%llu\\n",
            (unsigned long long)g_scan_roots, (unsigned long long)g_scan_scanned_roots,
            (unsigned long long)g_scan_iters, (unsigned long long)g_scan_ns);
    }
} g_scan_probe_reporter;
}
"""
# insert right after the last #include line block at the top
lines = main_text.split("\n")
last_inc = 0
for i, l in enumerate(lines[:80]):
    if l.startswith("#include"):
        last_inc = i
lines.insert(last_inc + 1, defs)
open(main_path, "w").write("\n".join(lines))
print("instrumented", DST)
