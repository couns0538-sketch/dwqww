#include "forge/a.hpp"
int forge::answer() { return 42; }
int main() { return forge::answer() == 42 ? 0 : 1; }
