// Isolated original lock-API probe; deliberately violates UCI's serial bootstrap.
#include "forge/board.hpp"
#include <barrier>
#include <thread>
#include <vector>
int main(){std::barrier start(4);std::vector<std::thread> ts;for(int n=0;n<4;++n)ts.emplace_back([&]{start.arrive_and_wait();forge::Board b;(void)b.perft(1);});for(auto&t:ts)t.join();}
