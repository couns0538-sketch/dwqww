#include "forge/profile.hpp"

#ifdef FORGE_PROF
#include <ostream>

namespace forge::prof {
thread_local constinit Bank* current_bank=nullptr;

namespace {
struct Description {const char* name;Counter denominator;};
constexpr std::array<Description,CounterCount> descriptions{{
    {"nodes",Counter::Nodes},{"main_nodes",Counter::Nodes},{"qs_nodes",Counter::Nodes},
    {"eval_requests",Counter::Nodes},{"hce_computations",Counter::EvalRequests},
    {"nnue_forward",Counter::EvalRequests},{"nnue_refresh",Counter::NnueForward},
    {"tt_probes",Counter::Nodes},{"tt_hits",Counter::TtProbes},{"tt_misses",Counter::TtProbes},
    {"picker_visits",Counter::Nodes},
    {"picker_main_tt",Counter::PickerVisits},{"picker_generate_captures",Counter::PickerVisits},
    {"picker_good_captures",Counter::PickerVisits},{"picker_killer1",Counter::PickerVisits},
    {"picker_killer2",Counter::PickerVisits},{"picker_counter_move",Counter::PickerVisits},
    {"picker_generate_quiets",Counter::PickerVisits},{"picker_quiet_moves",Counter::PickerVisits},
    {"picker_bad_captures",Counter::PickerVisits},{"picker_qs_tt",Counter::PickerVisits},
    {"picker_qs_generate",Counter::PickerVisits},{"picker_qs_captures",Counter::PickerVisits},
    {"picker_evasion_tt",Counter::PickerVisits},{"picker_evasion_generate",Counter::PickerVisits},
    {"picker_evasions",Counter::PickerVisits},
    {"razor_checks",Counter::MainNodes},{"razor_searches",Counter::RazorChecks},
    {"razor_cutoffs",Counter::RazorSearches},
    {"probcut_checks",Counter::MainNodes},{"probcut_searches",Counter::ProbCutChecks},
    {"probcut_cutoffs",Counter::ProbCutSearches},
    {"iir_checks",Counter::MainNodes},{"iir_reductions",Counter::IirChecks},
    {"lmp_checks",Counter::MainNodes},{"lmp_activations",Counter::LmpChecks},
    {"futility_checks",Counter::MainNodes},{"futility_prunes",Counter::FutilityChecks},
    {"capture_futility_checks",Counter::MainNodes},{"capture_futility_prunes",Counter::CaptureFutilityChecks},
    {"history_checks",Counter::MainNodes},{"history_prunes",Counter::HistoryChecks},
    {"quiet_see_checks",Counter::MainNodes},{"quiet_see_prunes",Counter::QuietSeeChecks},
    {"noisy_see_checks",Counter::MainNodes},{"noisy_see_prunes",Counter::NoisySeeChecks},
    {"qs_futility_checks",Counter::QsNodes},{"qs_futility_prunes",Counter::QsFutilityChecks},
    {"qs_see_checks",Counter::QsNodes},{"qs_see_prunes",Counter::QsSeeChecks},
    {"singular_checks",Counter::MainNodes},{"singular_searches",Counter::SingularChecks},
    {"singular_extensions",Counter::SingularSearches},{"singular_double_extensions",Counter::SingularSearches},
    {"singular_cutoffs",Counter::SingularSearches}
}};
}

void merge(Snapshot& total,const Snapshot& delta) noexcept {
    total.overflow=total.overflow || delta.overflow;
    for (std::size_t i=0;i<CounterCount;++i) {
        const auto previous=total.values[i];total.values[i]+=delta.values[i];
        total.overflow=total.overflow || total.values[i]<previous;
    }
}

void write_snapshot(std::ostream& output,const Snapshot& snapshot) {
    output << "info string prof schema 1 scope search_only setup_excluded 1 overflow " << snapshot.overflow << '\n';
    for (std::size_t i=0;i<CounterCount;++i) {
        const auto& description=descriptions[i];
        const auto d=static_cast<std::size_t>(description.denominator);
        output << "info string prof " << description.name << " count " << snapshot.values[i]
               << " denominator " << descriptions[d].name << " opportunities " << snapshot.values[d];
        if (snapshot.values[d]!=0 && !snapshot.overflow) {
            output << " pct " << (100.0*static_cast<double>(snapshot.values[i])/static_cast<double>(snapshot.values[d]));
        } else output << " pct unknown";
        output << '\n';
    }
}
} // namespace forge::prof
#endif
