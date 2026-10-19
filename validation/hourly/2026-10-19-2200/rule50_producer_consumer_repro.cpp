// Forge 6.4 22:00 audit: policy model only, not a full engine test.
#include <cassert>
#include <iostream>
#include <string_view>
struct Entry { std::string_view key; int score; int origin_clock; bool occupied; };
constexpr bool reusable(int clock) { return clock < 90; }
bool receiver_only(const Entry& e, std::string_view key, int clock) {
  return e.occupied && e.key == key && reusable(clock);
}
bool origin_aware(const Entry& e, std::string_view key, int clock) {
  return receiver_only(e,key,clock) && e.origin_clock < 90;
}
int main() {
  constexpr std::string_view key="7k/8/8/8/8/8/8/KR6 w - -";
  int tested=0, reverse=0;
  for(int source: {90,95,98,99}) for(int probe: {0,25,89}) {
    const Entry entry{key,0,source,true};
    assert(receiver_only(entry,key,probe));
    assert(!origin_aware(entry,key,probe));
    ++tested; ++reverse;
  }
  for(int source: {0,25,89}) for(int probe: {0,25,89}) {
    const Entry entry{key,123,source,true};
    assert(receiver_only(entry,key,probe) && origin_aware(entry,key,probe));
    ++tested;
  }
  for(int source: {0,89,90,99}) for(int probe: {90,99,100}) {
    const Entry entry{key,123,source,true};
    assert(!receiver_only(entry,key,probe) && !origin_aware(entry,key,probe));
    ++tested;
  }
  std::cout << "MODEL PASS " << tested << " cases, " << reverse << " source-high/probe-low paths\n";
}
