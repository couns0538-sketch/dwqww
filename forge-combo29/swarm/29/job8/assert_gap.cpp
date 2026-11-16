#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <tuple>
// A future 8-slot cluster of 8-byte entries is STILL 64 bytes, so the pre-existing sizeof==64 assert passes,
// while a 4-lane key compare would silently miss slots 4..7. This is the case my assert covers and theirs does not.
struct E8 { std::uint32_t key32; std::uint32_t pad; };
struct alignas(64) C8 { std::array<E8, 8> entries{}; };
int main() {
    static_assert(sizeof(C8) == 64, "pre-existing assert: PASSES with 8 slots of 8 bytes");
    C8 c;
    static_assert(std::tuple_size_v<decltype(c.entries)> == 4, "my assert: FAILS, which is the point");
    return 0;
}
