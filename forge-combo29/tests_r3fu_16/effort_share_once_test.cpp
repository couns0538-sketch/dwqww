#include "forge/tm_node_share.hpp"

#include <cmath>
#include <iostream>

namespace {

int g_failed = 0;
int g_checked = 0;

void expect(const char* name, double got, double want) {
    ++g_checked;
    if (std::fabs(got - want) <= 1e-12) return;
    std::cerr << name << " got " << got << " want " << want << '\n';
    ++g_failed;
}

double older_clamp(double effort, int base_percent) {
    const double raw = static_cast<double>(base_percent) / 100.0 - effort;
    if (raw < 0.6) return 0.6;
    if (raw > 1.4) return 1.4;
    return raw;
}

}  // namespace

int main() {
    static_assert(forge::effort_share_factor(0.0, 155, true) == 1.0);
    static_assert(forge::effort_share_factor(0.55, 155, true) == 1.0);
    static_assert(forge::effort_share_factor(1.0, 155, true) == 1.0);
    static_assert(forge::effort_share_factor(0.0, 100, true) == 1.0);
    static_assert(forge::effort_share_factor(0.9, 200, true) == 1.0);

    const double efforts[] = {0.0, 0.1, 0.15, 0.25, 0.5, 0.55, 0.75, 0.9, 0.95, 1.0};
    for (double effort : efforts) {
        const double on = forge::effort_share_factor(effort, 155, true);
        expect("on stays 1", on, 1.0);
        expect("on ignores effort", on, forge::effort_share_factor(0.0, 155, true));
        expect("off keeps older clamp", forge::effort_share_factor(effort, 155, false), older_clamp(effort, 155));
    }
    expect("off base 100 effort 0", forge::effort_share_factor(0.0, 100, false), 1.0);
    expect("off base 100 effort 0.5", forge::effort_share_factor(0.5, 100, false), 0.6);
    expect("off base 200 effort 0", forge::effort_share_factor(0.0, 200, false), 1.4);
    expect("off base 155 effort 0.2", forge::effort_share_factor(0.2, 155, false), older_clamp(0.2, 155));
    expect("on differs from a scaling off value", forge::effort_share_factor(0.0, 155, true), 1.0);
    if (forge::effort_share_factor(0.0, 155, false) == 1.0) {
        std::cerr << "off path collapsed to 1\n";
        ++g_failed;
    }
    ++g_checked;

    if (g_failed != 0) {
        std::cerr << g_failed << " failed of " << g_checked << '\n';
        return 1;
    }
    std::cout << "effort share once checks " << g_checked << '\n';
    return 0;
}
