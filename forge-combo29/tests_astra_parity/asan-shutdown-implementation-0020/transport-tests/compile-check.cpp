#include "../uci_process.hpp"

static_assert(uci_diagnostic_shutdown_deadlines(0).natural_ns == 5000000000LL);
static_assert(uci_diagnostic_shutdown_deadlines(0).terminate_ns == 5250000000LL);
static_assert(uci_diagnostic_shutdown_deadlines(0).kill_ns == 5500000000LL);
static_assert(uci_diagnostic_shutdown_deadlines(100000000).natural_ns == 5100000000LL);
static_assert(uci_diagnostic_shutdown_deadlines(100000000).terminate_ns == 5350000000LL);
static_assert(uci_diagnostic_shutdown_deadlines(100000000).kill_ns == 5600000000LL);
static_assert(uci_diagnostic_shutdown_deadlines(175).natural_ns - 175 == 5000000000LL);
// Late observer scheduling is a write-budget fault; never shorten natural grace.
static_assert(uci_diagnostic_shutdown_deadlines(700000000).natural_ns == 5700000000LL);
static_assert(uci_diagnostic_shutdown_deadlines(700000000).terminate_ns == 5700000000LL);
static_assert(uci_diagnostic_shutdown_deadlines(700000000).kill_ns == 5700000000LL);

constexpr UciShutdownResult normal(double delivered, double reaped) {
    UciShutdownResult r;
    r.quit_sent = true; r.reaped = true; r.exit_code = 0; r.signal = 0;
    r.quit_write_end_ms = delivered; r.reap_observed_ms = reaped;
    return r;
}
static_assert(uci_diagnostic_natural_exit(normal(2.0, 5001.999)));
static_assert(uci_diagnostic_natural_exit(normal(2.0, 5002.0)));
static_assert(!uci_diagnostic_natural_exit(normal(2.0, 5002.001)));
static_assert(!uci_diagnostic_natural_exit(normal(2.0, 1.9)));
static_assert(!uci_diagnostic_natural_exit(normal(-1.0, 2.0)));
static_assert([] { auto r = normal(2, 20); r.driver_sigterm = true; return !uci_diagnostic_natural_exit(r); }());
static_assert([] { auto r = normal(2, 20); r.driver_sigkill = true; return !uci_diagnostic_natural_exit(r); }());
static_assert([] { auto r = normal(2, 20); r.quit_sent = false; return !uci_diagnostic_natural_exit(r); }());
static_assert([] { auto r = normal(2, 20); r.reaped = false; return !uci_diagnostic_natural_exit(r); }());
static_assert([] { auto r = normal(2, 20); r.exit_code = 1; return !uci_diagnostic_natural_exit(r); }());
static_assert([] { auto r = normal(2, 20); r.signal = 9; return !uci_diagnostic_natural_exit(r); }());
static_assert([] { auto r = normal(2, 20); r.timed_out = true; return uci_diagnostic_natural_exit(r); }());
// Natural process exit and pipe-EOF timeout are intentionally separate facts.
int main() { return 0; }
