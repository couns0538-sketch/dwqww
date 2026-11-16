#include <cstdio>
#include <cstdint>
struct TTEntry { std::uint32_t key32; std::uint32_t move; std::int16_t score; std::int16_t eval;
                 std::uint8_t depth, gen_bound, rule50, padding; };
int main(){ std::printf("sizeof(TTEntry)=%zu ; one __m128i = 16 bytes covers %zu entries\n",
                        sizeof(TTEntry), 16/sizeof(TTEntry)); }
