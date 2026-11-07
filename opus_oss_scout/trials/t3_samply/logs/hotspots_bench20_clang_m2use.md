process forge_m2use_lsx.exe: 4 threads, 4872 samples (interval 1.0 ms)

| Module | Self samples | % |
|---|---|---|
| forge_m2use_lsx.exe | 4811 | 98.7 |
| ntoskrnl.exe | 28 | 0.6 |
| ucrtbase.dll | 28 | 0.6 |
| ntdll.dll | 4 | 0.1 |
| (no module) | 1 | 0.0 |

### Self samples by innermost (inlined) function (top 25)

| # | Function | Samples | % of process |
|---|---|---|---|
| 1 | `forge::Worker::search` | 409 | 8.4 |
| 2 | `forge::`anonymous namespace'::evaluate_pieces` | 313 | 6.4 |
| 3 | `forge::nnue::update` | 250 | 5.1 |
| 4 | `forge::MovePicker::pick_best` | 207 | 4.2 |
| 5 | `forge::nnue::evaluate(forge::Board const&, forge::nnue::Accumulator const&)` | 202 | 4.1 |
| 6 | `forge::Move::operator==` | 165 | 3.4 |
| 7 | `forge::Board::generate_pseudo_legal(forge::MoveList&, forge::Board::GenMode) const` | 139 | 2.9 |
| 8 | `forge::Board::see_ge(forge::Move const&, int) const` | 134 | 2.8 |
| 9 | `forge::`anonymous namespace'::evaluate_king` | 126 | 2.6 |
| 10 | `std::__countr_zero` | 105 | 2.2 |
| 11 | `forge::Worker::corrected_eval` | 103 | 2.1 |
| 12 | `forge::`anonymous namespace'::Accumulator<0>::add` | 102 | 2.1 |
| 13 | `forge::MovePicker::next` | 97 | 2.0 |
| 14 | `forge::`anonymous namespace'::quiet_history_sum` | 85 | 1.7 |
| 15 | `forge::Worker::qsearch` | 84 | 1.7 |
| 16 | `forge::Board::gives_check` | 75 | 1.5 |
| 17 | `std::__unguarded_linear_insert` | 71 | 1.5 |
| 18 | `forge::Evaluator::update_runtime_psqt` | 68 | 1.4 |
| 19 | `forge::Worker::static_evaluate` | 67 | 1.4 |
| 20 | `forge::MovePicker::pick_best::<lambda1>::operator()` | 64 | 1.3 |
| 21 | `std::array<forge::attacks::Magic,64>::operator[]` | 57 | 1.2 |
| 22 | `forge::Board::generate_pseudo_legal::<lambda0>::operator()` | 56 | 1.1 |
| 23 | `int forge::(anonymous namespace)::evaluate_position<false>(forge::Board const&, forge::Evaluator::PawnEntry...` | 54 | 1.1 |
| 24 | `forge::TranspositionTable::probe_body` | 54 | 1.1 |
| 25 | `forge::Board::key_after` | 53 | 1.1 |

### Self samples by outermost (physical) function (top 25)

| # | Function | Samples | % of process |
|---|---|---|---|
| 1 | `forge::Worker::search` | 1784 | 36.6 |
| 2 | `int forge::(anonymous namespace)::evaluate_position<false>(forge::Board const&, forge::Evaluator::PawnEntry...` | 994 | 20.4 |
| 3 | `forge::Worker::qsearch` | 627 | 12.9 |
| 4 | `forge::Board::generate_pseudo_legal(forge::MoveList&, forge::Board::GenMode) const` | 306 | 6.3 |
| 5 | `forge::nnue::evaluate(forge::Board const&, forge::nnue::Accumulator const&)` | 226 | 4.6 |
| 6 | `forge::Board::see_ge(forge::Move const&, int) const` | 203 | 4.2 |
| 7 | `forge::TranspositionTable::probe_owned` | 151 | 3.1 |
| 8 | `std::__final_insertion_sort<forge::MovePicker::Scored *,__gnu_cxx::__ops::_Iter_comp_iter<`lambda at C:/opu...` | 128 | 2.6 |
| 9 | `std::__introsort_loop<forge::MovePicker::Scored *,long long,__gnu_cxx::__ops::_Iter_comp_iter<`lambda at C:...` | 106 | 2.2 |
| 10 | `forge::MovePicker::generate_quiets` | 81 | 1.7 |
| 11 | `forge::MovePicker::generate_evasions` | 60 | 1.2 |
| 12 | `forge::Board::has_legal_move() const` | 58 | 1.2 |
| 13 | `forge::Board::make_move(forge::Move const&, forge::Undo&)` | 35 | 0.7 |
| 14 | `forge::Board::is_pseudo_legal(forge::Move const&) const` | 24 | 0.5 |
| 15 | `___chkstk_ms` | 11 | 0.2 |
| 16 | `forge::MovePicker::next` | 7 | 0.1 |
| 17 | `forge::Board::has_legal_en_passant_capture() const` | 4 | 0.1 |
| 18 | `std::istream::sentry::sentry(std::istream&, bool)` | 1 | 0.0 |
| 19 | `forge::book::Book::load_embedded()` | 1 | 0.0 |
| 20 | `forge::Searcher::clear()` | 1 | 0.0 |
| 21 | `pthread_mutex_unlock` | 1 | 0.0 |
| 22 | `forge::Board::is_legal(forge::Move const&) const` | 1 | 0.0 |
| 23 | `forge::Board::make_null_move(forge::NullUndo&)` | 1 | 0.0 |

### Inclusive samples by outermost function (top 25)

| # | Function | Samples | % of process |
|---|---|---|---|
| 1 | `forge::Evaluator::Evaluator()` | 4841 | 99.4 |
| 2 | `mainCRTStartup` | 4841 | 99.4 |
| 3 | `main` | 4838 | 99.3 |
| 4 | `forge::Worker::search` | 4825 | 99.0 |
| 5 | `forge::Searcher::search(forge::Board, forge::SearchLimits const&, bool, forge::Searcher::TTAccess)` | 4822 | 99.0 |
| 6 | `forge::Worker::qsearch` | 1605 | 32.9 |
| 7 | `int forge::(anonymous namespace)::evaluate_position<false>(forge::Board const&, forge::Evaluator::PawnEntry...` | 995 | 20.4 |
| 8 | `forge::Board::generate_pseudo_legal(forge::MoveList&, forge::Board::GenMode) const` | 306 | 6.3 |
| 9 | `forge::nnue::evaluate(forge::Board const&, forge::nnue::Accumulator const&)` | 226 | 4.6 |
| 10 | `forge::Board::see_ge(forge::Move const&, int) const` | 204 | 4.2 |
| 11 | `forge::MovePicker::generate_quiets` | 156 | 3.2 |
| 12 | `forge::TranspositionTable::probe_owned` | 152 | 3.1 |
| 13 | `std::__final_insertion_sort<forge::MovePicker::Scored *,__gnu_cxx::__ops::_Iter_comp_iter<`lambda at C:/opu...` | 142 | 2.9 |
| 14 | `std::__introsort_loop<forge::MovePicker::Scored *,long long,__gnu_cxx::__ops::_Iter_comp_iter<`lambda at C:...` | 106 | 2.2 |
| 15 | `forge::MovePicker::generate_evasions` | 102 | 2.1 |
| 16 | `forge::Board::has_legal_move() const` | 70 | 1.4 |
| 17 | `forge::Board::make_move(forge::Move const&, forge::Undo&)` | 35 | 0.7 |
| 18 | `forge::Board::is_pseudo_legal(forge::Move const&) const` | 24 | 0.5 |
| 19 | `forge::MovePicker::next` | 14 | 0.3 |
| 20 | `___chkstk_ms` | 11 | 0.2 |
| 21 | `forge::Searcher::Searcher(unsigned long long, int)` | 10 | 0.2 |
| 22 | `forge::TranspositionTable::resize` | 9 | 0.2 |
| 23 | `forge::TranspositionTable::TranspositionTable` | 9 | 0.2 |
| 24 | `forge::Board::has_legal_en_passant_capture() const` | 4 | 0.1 |
| 25 | `forge::Board::Board()` | 2 | 0.0 |
