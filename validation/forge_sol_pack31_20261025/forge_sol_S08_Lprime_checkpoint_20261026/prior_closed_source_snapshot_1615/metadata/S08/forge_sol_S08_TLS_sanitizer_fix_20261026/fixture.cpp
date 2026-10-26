#include "forge/profile.hpp"
#include <cstdint>
#include <iostream>
#include <limits>
#include <thread>
using namespace forge::prof;
[[gnu::noinline]] void enter(Bank* bank, std::uint64_t amount) {
    Scope scope(bank);
    count(Counter::Nodes, amount);
}
int main() {
    int failures=0;
    auto check=[&](bool ok,const char* text){if(!ok){std::cerr<<"FAIL "<<text<<'\n';++failures;}};
    // Enter disabled context first, just as normal bench does with Profile off.
    enter(nullptr,99);
    Bank outer,inner;
    {
        Scope first(&outer);count(Counter::Nodes,1);
        enter(&inner,2);
        count(Counter::Nodes,3);
        enter(nullptr,99);
        count(Counter::Nodes,4);
    }
    enter(nullptr,99);
    check(outer.snapshot_quiescent().values[0]==8,"nested and disabled scopes restore bank");
    check(inner.snapshot_quiescent().values[0]==2,"nested scope uses separate bank");
    std::thread a([&]{enter(&outer,5);});
    std::thread b([&]{enter(&inner,7);});
    a.join();b.join();
    check(outer.snapshot_quiescent().values[0]==13,"worker A bank is isolated");
    check(inner.snapshot_quiescent().values[0]==9,"worker B bank is isolated");
    check(current_bank==nullptr,"main context restored after worker joins");
    outer.reset_quiescent();
    outer.add(Counter::Nodes,std::numeric_limits<std::uint64_t>::max());
    outer.add(Counter::Nodes,2);
    auto wrapped=outer.snapshot_quiescent();
    check(wrapped.values[0]==1 && wrapped.overflow,"wrap is flagged");
    outer.reset_quiescent();
    check(outer.snapshot_quiescent().values[0]==0 && !outer.snapshot_quiescent().overflow,"reset clears overflow");
    if(!failures)std::cout<<"PASS disabled-first cross-TU TLS, nested scopes, independent workers, wrap/reset\n";
    return failures?1:0;
}
