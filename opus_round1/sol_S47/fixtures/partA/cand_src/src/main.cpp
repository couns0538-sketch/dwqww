#include "forge/a.hpp"
int forge::answer() { return 43; }
int main() { return forge::answer() == 43 ? 0 : 1; }
