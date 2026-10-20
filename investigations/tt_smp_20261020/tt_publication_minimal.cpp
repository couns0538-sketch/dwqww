// Structural reproducer for Forge 6.4 TT store's field write ordering.
// Not an end-to-end engine test; forced scheduling makes the partial write visible.
#include <atomic>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <thread>
struct Entry { std::uint32_t key; int score; int bound; };
int main() {
 Entry e{1,320,3};
 std::atomic<bool> key_ready{false},reader_done{false};
 bool false_hit=false;
 std::thread writer([&] {
   e.key=2; // production store writes new key before new score/bound
   key_ready.store(true,std::memory_order_release);
   while(!reader_done.load(std::memory_order_acquire)) std::this_thread::yield();
   e.score=-120;
 });
 std::thread reader([&] {
   while(!key_ready.load(std::memory_order_acquire)) std::this_thread::yield();
   false_hit=(e.key==2 && e.bound==3 && e.score==320);
   reader_done.store(true,std::memory_order_release);
 });
 writer.join();reader.join();
 std::cout << (false_hit?"PASS: wrong-key score accepted":"FAIL") << '\n';
 assert(false_hit);
}
