#include "forge/search.hpp"
#define main unchanged_fifty_move_main
#include "../tests_t23/fifty_move_tt_test.cpp"
#undef main
int main() {
    forge::tune::MateAlphaGuard = true;
    return unchanged_fifty_move_main();
}
