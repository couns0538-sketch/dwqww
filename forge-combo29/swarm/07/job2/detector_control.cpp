// detector_control.cpp -- positive control for the debug STL build.
// If this program does NOT abort, then "-D_GLIBCXX_DEBUG" in build-dbg does not
// catch front() on an empty container and any "no abort" result from that build is worthless.
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> empty;
    std::printf("about to read front() of an empty vector\n");
    std::fflush(stdout);
    const int value = empty.front();   // must abort under _GLIBCXX_DEBUG / _GLIBCXX_ASSERTIONS
    std::printf("NO ABORT: read %d -- the detector is blind\n", value);
    return 0;
}
