// Search module: worker lifecycle (construction and clearing of the per-thread
// state in forge/thread_data.hpp).
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {

Worker::Worker(SharedSearchState& shared, int id) : ThreadData(shared, id) {
    clear();
}

ThreadData::~ThreadData() = default;

Worker::~Worker() = default;

void Worker::clear() {
    evaluator_.clear();
    histories_.clear();
    *correction_history_ = CorrectionHistory{};
    *material_correction_ = CorrectionHistory{};
    correction_plus_.reset();  // CorrHistPlus tables, reallocated (zeroed) by the next update
    for (SearchStack& ss : stack_) ss = SearchStack{};
}

} // namespace forge
