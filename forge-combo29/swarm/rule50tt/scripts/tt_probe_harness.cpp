// Store -> probe -> score_usable, through the real TranspositionTable, using the
// same store() the search calls. This is the level at which the function lives.
//
// The plan (label, stored, probe, depth, score, expect) is read from a CSV that
// make_plan.py generates from an INDEPENDENT Python model of the documented rule.
// The C++ does not contain any hand-written expectation: two seats of arithmetic
// in this one were wrong, and a table of expectations typed by the same person who
// wrote the harness is not a check.
//
// Every planted entry is written with a TTProbe obtained from a real probe(), so
// the owner/epoch/key/slot checks in store_body() pass and the entry really lands.
// `landed` is reported per row: a silently-rejected store would turn every
// "refused" row into a counterfeit pass.
//
// usage: tt_probe_harness <plan.csv> <out.json>
#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct Planting {
    std::string label;
    int stored_clock;
    int probe_clock;
    int depth;
    int score;
    bool expect_usable;
};

constexpr const char* kFen = "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 10 8";

std::vector<Planting> read_plan(const char* path) {
    std::vector<Planting> plan;
    std::ifstream in(path);
    std::string line;
    std::getline(in, line);  // header
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string field;
        std::vector<std::string> fields;
        while (std::getline(ss, field, ',')) fields.push_back(field);
        if (fields.size() != 6) continue;
        plan.push_back({fields[0], std::stoi(fields[1]), std::stoi(fields[2]), std::stoi(fields[3]),
                        std::stoi(fields[4]), std::stoi(fields[5]) != 0});
    }
    return plan;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::fprintf(stderr, "usage: %s <plan.csv> <out.json>\n", argv[0]);
        return 2;
    }
    const std::vector<Planting> plan = read_plan(argv[1]);
    if (plan.empty()) {
        std::fprintf(stderr, "empty plan\n");
        return 2;
    }

    forge::TranspositionTable tt(16);
    forge::Board board;
    std::string err;
    if (!board.set_fen(kFen, &err)) {
        std::fprintf(stderr, "fixture refused by the engine: %s\n", err.c_str());
        return 2;
    }
    const std::uint64_t key = board.key();

    std::FILE* f = std::fopen(argv[2], "w");
    if (f == nullptr) return 1;
    std::fprintf(f, "{\n  \"fixture\": \"%s\",\n  \"rows\": [\n", kFen);
    int failures = 0, landed_count = 0;
    for (std::size_t i = 0; i < plan.size(); ++i) {
        const Planting& p = plan[i];
        tt.clear();
        const forge::TTProbe probe = tt.probe(key);
        // The score goes through the same clamp the search applies, so a mate
        // score is not silently altered between plan and observation.
        tt.store(probe, key, p.score, 0, forge::Move::none(), p.depth, forge::BoundExact, false,
                 static_cast<std::uint16_t>(p.stored_clock));
        const forge::TTProbe after = tt.probe(key);
        const bool landed = after.hit && after.entry.score == static_cast<std::int16_t>(p.score) &&
                            after.entry.rule50_clock == p.stored_clock && after.entry.depth == p.depth;
        if (landed) ++landed_count;
        const bool usable = landed && after.entry.score_usable(static_cast<std::uint16_t>(p.probe_clock));
        const bool ok = landed && (usable == p.expect_usable);
        if (!ok) ++failures;
        std::fprintf(f,
                     "    {\"label\": \"%s\", \"stored\": %d, \"probe\": %d, \"depth\": %d, "
                     "\"score\": %d, \"landed\": %s, \"usable\": %s, \"expect\": %s, \"pass\": %s}%s\n",
                     p.label.c_str(), p.stored_clock, p.probe_clock, p.depth, p.score,
                     landed ? "true" : "false", usable ? "true" : "false",
                     p.expect_usable ? "true" : "false", ok ? "true" : "false",
                     i + 1 == plan.size() ? "" : ",");
        std::printf("%-30s stored=%3d probe=%3d d=%2d score=%6d landed=%d usable=%d expect=%d %s\n",
                    p.label.c_str(), p.stored_clock, p.probe_clock, p.depth, p.score,
                    landed ? 1 : 0, usable ? 1 : 0, p.expect_usable ? 1 : 0, ok ? "PASS" : "MISMATCH");
    }

    // Control that the comparator fires. Without this, "0 failures" could mean the
    // comparison never ran (brief rule 3).
    int control_fired = 0;
    {
        tt.clear();
        const forge::TTProbe probe = tt.probe(key);
        tt.store(probe, key, 120, 0, forge::Move::none(), 8, forge::BoundExact, false, 95);
        const forge::TTProbe after = tt.probe(key);
        const bool usable = after.hit && after.entry.score_usable(10);
        control_fired = usable ? 0 : 1;
        std::printf("\ncontrol (store 95, probe 10, want refused): usable=%d -> %s\n",
                    usable ? 1 : 0, control_fired ? "control fires" : "CONTROL DID NOT FIRE");
    }
    // Second control: plant the opposite fault, so the comparator is shown to
    // detect a false refusal as well as a false acceptance.
    {
        tt.clear();
        const forge::TTProbe probe = tt.probe(key);
        tt.store(probe, key, 120, 0, forge::Move::none(), 8, forge::BoundExact, false, 10);
        const forge::TTProbe after = tt.probe(key);
        const bool usable = after.hit && after.entry.score_usable(10);
        std::printf("control (store 10, probe 10, want usable): usable=%d -> %s\n",
                    usable ? 1 : 0, usable ? "control fires" : "CONTROL DID NOT FIRE");
        if (!usable) control_fired = 0;
    }

    std::fprintf(f, "  ],\n  \"failures\": %d,\n  \"landed\": %d,\n  \"rows\": %zu,\n  "
                    "  \"control_fired\": %s\n}\n",
                 failures, landed_count, plan.size(), control_fired ? "true" : "false");
    std::fclose(f);
    std::printf("\nrows %zu, landed %d, mismatches %d\n", plan.size(), landed_count, failures);
    return (failures == 0 && control_fired && landed_count == static_cast<int>(plan.size())) ? 0 : 1;
}
