#include <array>
#include <cstddef>
#include <tuple>
struct E { };
struct C4 { std::array<E,4> entries{}; };
struct C5 { std::array<E,5> entries{}; };
int main() {
    C4 a; C5 b;
    static_assert(std::tuple_size_v<decltype(a.entries)> == 4, "4-lane compare covers exactly this many slots");
    static_assert(std::tuple_size_v<decltype(b.entries)> == 4, "PLANTED: this one should fail");
    return 0;
}
