#include "/workspace/work/parity-softnodes-depth64-preparation/softnodes_labels.hpp"
#include <iostream>
int main() {
    for (const std::string field : {"64", "64junk", "-64", "999999999999999999999999999999", "63 depth 64", "64 depth 63", "64 depth 64"}) {
        const auto r = check_labels({"info depth " + field + " score cp 0 nodes 100 pv e2e4", "info string softnodes nodes 200", "bestmove e2e4"}, true);
        std::cout << "depth_field=" << field << " parsed=" << r.depth << " has_depth=" << r.has_depth << " exact=" << r.exact << " item4=" << r.item4 << " error=" << r.error << '\n';
    }
}
