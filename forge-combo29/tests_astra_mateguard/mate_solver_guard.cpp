#include "forge/search.hpp"
#define main unchanged_mate_solver_main
#include "../tests_t23/mate_solver_test.cpp"
#undef main
int main() {
    forge::tune::MateAlphaGuard = true;
    return unchanged_mate_solver_main();
}
