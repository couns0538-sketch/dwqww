#!/usr/bin/env python3
"""Apply the planted-race patches to a COPY of the engine tree.

Two independent plants, because they prove two different things:

  plant A  (`plantrace` UCI command)  -- two threads, one global, no
            synchronisation, not on any search path. Proves the runner binary
            can print a TSan report at all.

  plant B  (search.cpp hot path)     -- an unsynchronised increment inside
            Worker::should_stop(), reached by the main worker AND every helper
            during a normal `go`. Proves the runner observes the ENGINE'S
            ACTUAL SEARCH THREADS, not merely a thread pair we created.

Plant B is the one that matters for the clean negative: without it, a silent
run would only show that TSan was linked in.
"""
import shutil
import sys
from pathlib import Path

PLANT_A = """
// PLANTED RACE A (audit self-test only): two threads bump this without any
// synchronisation. Present only in the planted build; never in the engine
// under test.
unsigned long g_planted_counter = 0;
"""

HANDLER_A = '''        } else if (command == "plantrace") {
            // PLANTED RACE A: two threads, one global, no synchronisation.
            std::thread a([] { for (int i = 0; i < 200000; ++i) ++g_planted_counter; });
            std::thread b([] { for (int i = 0; i < 200000; ++i) ++g_planted_counter; });
            a.join();
            b.join();
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
              std::cout << "info string plantrace done " << g_planted_counter << std::endl; }
'''

PLANT_B = """// PLANTED RACE B (audit self-test only): touched from every search thread on
// the hot should_stop path, with no synchronisation.
static unsigned long g_planted_hot = 0;
"""


def patch_a(src: Path) -> None:
    p = src / "src" / "uci.cpp"
    s = p.read_text()
    anchor = "namespace {\n\nvoid apply_position"
    if anchor not in s:
        raise SystemExit("patch A: anchor not found in uci.cpp")
    s = s.replace(anchor, "namespace {\n" + PLANT_A + "\nvoid apply_position", 1)

    anchor2 = '        } else if (command == "eval") {'
    if anchor2 not in s:
        raise SystemExit("patch A: handler anchor not found")
    s = s.replace(anchor2, HANDLER_A + anchor2, 1)
    p.write_text(s)


def patch_b(src: Path) -> None:
    p = src / "src" / "search.cpp"
    s = p.read_text()
    anchor = """bool Worker::should_stop() {
    // Publish this thread's node count for the others at the same cadence."""
    if anchor not in s:
        raise SystemExit("patch B: anchor not found in search.cpp")
    s = s.replace(anchor, PLANT_B + """
bool Worker::should_stop() {
    // PLANTED RACE B: unsynchronised increment reached by main + helpers.
    ++g_planted_hot;
    // Publish this thread's node count for the others at the same cadence.""", 1)

    anchor2 = "bool Worker::is_draw(const Board& board, int ply) const {"
    s = s.replace(anchor2, "unsigned long planted_hot_read() { return g_planted_hot; }\n\n" + anchor2, 1)
    p.write_text(s)


def main():
    src = Path(sys.argv[1]).resolve()
    dest = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path("/home/ubuntu/work/planted2")
    which = sys.argv[3] if len(sys.argv) > 3 else "B"

    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    if which in ("A", "AB"):
        patch_a(dest)
    if which in ("B", "AB"):
        patch_b(dest)
    print("planted %s into %s" % (which, dest))


if __name__ == "__main__":
    main()
