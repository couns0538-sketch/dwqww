// Behavioral fixtures: deliberately not compiled/run until root authorization.
#include "forge/profile.hpp"
#include <array>
#include <cstdint>
#include <iostream>
#include <limits>
#include <thread>

int main() {
    using namespace forge::prof;
    int failures=0;
    auto check=[&](bool value,const char* message) {
        if (!value) {std::cerr << "FAIL " << message << '\n';++failures;}
    };
    Bank outer,inner;
    {
        Scope one(&outer);count(Counter::Nodes);
        {Scope two(&inner);count(Counter::Nodes,2);}
        count(Counter::Nodes,3);
        {Scope disabled(nullptr);count(Counter::Nodes,99);}
        count(Counter::Nodes,4);
    }
    check(outer.snapshot_quiescent().values[0]==8,"nested scope restores previous bank");
    check(inner.snapshot_quiescent().values[0]==2,"independent nested bank");
    count(Counter::Nodes,999);
    check(outer.snapshot_quiescent().values[0]==8,"scope exit disables counting");
    outer.reset_quiescent();
    std::array<std::thread,4> threads;
    for (auto& thread:threads) thread=std::thread([&] {
        Scope scope(&outer);
        for (int i=0;i<1000;++i) count(Counter::Nodes);
    });
    for (auto& thread:threads) thread.join();
    check(outer.snapshot_quiescent().values[0]==4000,"shared atomic counter has no lost updates");
    outer.reset_quiescent();
    outer.add(Counter::Nodes,std::numeric_limits<std::uint64_t>::max());
    outer.add(Counter::Nodes,2);
    auto wrapped=outer.snapshot_quiescent();
    check(wrapped.values[0]==1 && wrapped.overflow,"unsigned wrap marks unusable totals");
    outer.reset_quiescent();
    check(outer.snapshot_quiescent().values[0]==0 && !outer.snapshot_quiescent().overflow,"quiescent reset clears values and overflow");
    Snapshot total;
    total.values[0]=std::numeric_limits<std::uint64_t>::max();
    Snapshot delta;delta.values[0]=2;merge(total,delta);
    check(total.values[0]==1 && total.overflow,"aggregation reports wrap");
    if (!failures) std::cout << "PASS profiling counters and nested TLS\n";
    return failures ? 1 : 0;
}
