process forge_ltopgo_x_al1s198_trial_w6.exe: 31 threads, 14941 samples (interval 1.0 ms)

| Module | Self samples | % |
|---|---|---|
| forge_ltopgo_x_al1s198_trial_w6.exe | 14777 | 98.9 |
| ntdll.dll | 66 | 0.4 |
| ucrtbase.dll | 62 | 0.4 |
| ntoskrnl.exe | 32 | 0.2 |
| kernel32.dll | 2 | 0.0 |
| msvcrt.dll | 1 | 0.0 |
| rt640x64.sys | 1 | 0.0 |

### Self samples by innermost (inlined) function (top 25)

| # | Function | Samples | % of process |
|---|---|---|---|
| 1 | `forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)` | 3439 | 23.0 |
| 2 | `int forge::(anonymous namespace)::evaluate_position<false>(forge::Board const&, forge::Evaluator::PawnEntry...` | 2782 | 18.6 |
| 3 | `forge::Worker::static_evaluate(forge::Board const&, forge::SearchStack*)` | 2279 | 15.3 |
| 4 | `forge::MovePicker::next(bool)` | 1743 | 11.7 |
| 5 | `forge::Worker::qsearch(forge::Board&, forge::SearchStack*, int, int)` | 1670 | 11.2 |
| 6 | `forge::Board::generate_pseudo_legal(forge::MoveList&, forge::Board::GenMode) const` | 1021 | 6.8 |
| 7 | `forge::Board::see_ge(forge::Move const&, int) const` | 654 | 4.4 |
| 8 | `forge::Board::make_move(forge::Move const&, forge::Undo&) (.isra.0)` | 317 | 2.1 |
| 9 | `void std::__introsort_loop<forge::MovePicker::Scored*, long long, __gnu_cxx::__ops::_Iter_comp_iter<forge::...` | 312 | 2.1 |
| 10 | `void std::__insertion_sort<forge::MovePicker::Scored*, __gnu_cxx::__ops::_Iter_comp_iter<forge::MovePicker:...` | 225 | 1.5 |
| 11 | `forge::Board::is_pseudo_legal(forge::Move const&) const (.isra.0)` | 84 | 0.6 |
| 12 | `___chkstk_ms` | 54 | 0.4 |
| 13 | `forge::Worker::record_move(forge::SearchStack*, forge::Board const&, forge::Move const&) (.isra.0)` | 37 | 0.2 |
| 14 | `forge::Board::is_legal(forge::Move const&) const (.isra.0)` | 37 | 0.2 |
| 15 | `forge::MovePicker::init_check_squares()` | 30 | 0.2 |
| 16 | `forge::Board::unmake_move(forge::Move const&, forge::Undo const&) (.isra.0)` | 25 | 0.2 |
| 17 | `forge::Worker::update_continuation(forge::SearchStack*, forge::Piece, int, int) (.isra.0)` | 24 | 0.2 |
| 18 | `forge::MovePicker::is_valid_quiet(forge::Move) const` | 14 | 0.1 |
| 19 | `forge::MovePicker::MovePicker(forge::Board const&, forge::Worker const&, forge::SearchStack const*, forge::...` | 12 | 0.1 |
| 20 | `forge::Board::square_attacked_with_occupancy(int, forge::Color, unsigned long long, unsigned long long) const` | 6 | 0.0 |
| 21 | `pthread_spin_lock` | 5 | 0.0 |
| 22 | `forge::Worker::should_stop()` | 1 | 0.0 |
| 23 | `forge::Board::has_legal_en_passant_capture() const` | 1 | 0.0 |
| 24 | `std::basic_istream<char, std::char_traits<char>>& std::getline<char, std::char_traits<char>, std::allocator...` | 1 | 0.0 |
| 25 | `forge::Move* std::copy_n<forge::Move*, int, forge::Move*>(forge::Move*, int, forge::Move*) (.isra.0)` | 1 | 0.0 |

### Self samples by outermost (physical) function (top 25)

| # | Function | Samples | % of process |
|---|---|---|---|
| 1 | `forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)` | 3439 | 23.0 |
| 2 | `int forge::(anonymous namespace)::evaluate_position<false>(forge::Board const&, forge::Evaluator::PawnEntry...` | 2782 | 18.6 |
| 3 | `forge::Worker::static_evaluate(forge::Board const&, forge::SearchStack*)` | 2279 | 15.3 |
| 4 | `forge::MovePicker::next(bool)` | 1743 | 11.7 |
| 5 | `forge::Worker::qsearch(forge::Board&, forge::SearchStack*, int, int)` | 1670 | 11.2 |
| 6 | `forge::Board::generate_pseudo_legal(forge::MoveList&, forge::Board::GenMode) const` | 1021 | 6.8 |
| 7 | `forge::Board::see_ge(forge::Move const&, int) const` | 654 | 4.4 |
| 8 | `forge::Board::make_move(forge::Move const&, forge::Undo&) (.isra.0)` | 317 | 2.1 |
| 9 | `void std::__introsort_loop<forge::MovePicker::Scored*, long long, __gnu_cxx::__ops::_Iter_comp_iter<forge::...` | 312 | 2.1 |
| 10 | `void std::__insertion_sort<forge::MovePicker::Scored*, __gnu_cxx::__ops::_Iter_comp_iter<forge::MovePicker:...` | 225 | 1.5 |
| 11 | `forge::Board::is_pseudo_legal(forge::Move const&) const (.isra.0)` | 84 | 0.6 |
| 12 | `___chkstk_ms` | 54 | 0.4 |
| 13 | `forge::Worker::record_move(forge::SearchStack*, forge::Board const&, forge::Move const&) (.isra.0)` | 37 | 0.2 |
| 14 | `forge::Board::is_legal(forge::Move const&) const (.isra.0)` | 37 | 0.2 |
| 15 | `forge::MovePicker::init_check_squares()` | 30 | 0.2 |
| 16 | `forge::Board::unmake_move(forge::Move const&, forge::Undo const&) (.isra.0)` | 25 | 0.2 |
| 17 | `forge::Worker::update_continuation(forge::SearchStack*, forge::Piece, int, int) (.isra.0)` | 24 | 0.2 |
| 18 | `forge::MovePicker::is_valid_quiet(forge::Move) const` | 14 | 0.1 |
| 19 | `forge::MovePicker::MovePicker(forge::Board const&, forge::Worker const&, forge::SearchStack const*, forge::...` | 12 | 0.1 |
| 20 | `forge::Board::square_attacked_with_occupancy(int, forge::Color, unsigned long long, unsigned long long) const` | 6 | 0.0 |
| 21 | `pthread_spin_lock` | 5 | 0.0 |
| 22 | `forge::Worker::should_stop()` | 1 | 0.0 |
| 23 | `forge::Board::has_legal_en_passant_capture() const` | 1 | 0.0 |
| 24 | `std::basic_istream<char, std::char_traits<char>>& std::getline<char, std::char_traits<char>, std::allocator...` | 1 | 0.0 |
| 25 | `forge::Move* std::copy_n<forge::Move*, int, forge::Move*>(forge::Move*, int, forge::Move*) (.isra.0)` | 1 | 0.0 |

### Inclusive samples by outermost function (top 25)

| # | Function | Samples | % of process |
|---|---|---|---|
| 1 | `execute_native_thread_routine` | 14822 | 99.2 |
| 2 | `.tl_start` | 14822 | 99.2 |
| 3 | `main::'lambda0'()::operator()()` | 14821 | 99.2 |
| 4 | `forge::Worker::search(forge::Board, forge::SearchLimits const&, bool, std::vector<forge::Worker*, std::allo...` | 14820 | 99.2 |
| 5 | `forge::Searcher::search(forge::Board, forge::SearchLimits const&, bool, forge::Searcher::TTAccess) (.constp...` | 14820 | 99.2 |
| 6 | `forge::Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)` | 14809 | 99.1 |
| 7 | `forge::Worker::static_evaluate(forge::Board const&, forge::SearchStack*)` | 5096 | 34.1 |
| 8 | `forge::Worker::qsearch(forge::Board&, forge::SearchStack*, int, int)` | 4910 | 32.9 |
| 9 | `forge::MovePicker::next(bool)` | 3037 | 20.3 |
| 10 | `int forge::(anonymous namespace)::evaluate_position<false>(forge::Board const&, forge::Evaluator::PawnEntry...` | 2785 | 18.6 |
| 11 | `forge::Board::generate_pseudo_legal(forge::MoveList&, forge::Board::GenMode) const` | 1030 | 6.9 |
| 12 | `forge::Board::see_ge(forge::Move const&, int) const` | 659 | 4.4 |
| 13 | `forge::Board::make_move(forge::Move const&, forge::Undo&) (.isra.0)` | 318 | 2.1 |
| 14 | `void std::__introsort_loop<forge::MovePicker::Scored*, long long, __gnu_cxx::__ops::_Iter_comp_iter<forge::...` | 312 | 2.1 |
| 15 | `void std::__insertion_sort<forge::MovePicker::Scored*, __gnu_cxx::__ops::_Iter_comp_iter<forge::MovePicker:...` | 257 | 1.7 |
| 16 | `forge::Board::is_pseudo_legal(forge::Move const&) const (.isra.0)` | 85 | 0.6 |
| 17 | `main` | 65 | 0.4 |
| 18 | `__tmainCRTStartup` | 65 | 0.4 |
| 19 | `.l_start` | 65 | 0.4 |
| 20 | `std::basic_istream<char, std::char_traits<char>>& std::getline<char, std::char_traits<char>, std::allocator...` | 63 | 0.4 |
| 21 | `__gnu_cxx::stdio_sync_filebuf<char, std::char_traits<char>>::underflow()` | 62 | 0.4 |
| 22 | `___chkstk_ms` | 54 | 0.4 |
| 23 | `forge::MovePicker::is_valid_quiet(forge::Move) const` | 50 | 0.3 |
| 24 | `forge::Worker::record_move(forge::SearchStack*, forge::Board const&, forge::Move const&) (.isra.0)` | 37 | 0.2 |
| 25 | `forge::Board::is_legal(forge::Move const&) const (.isra.0)` | 37 | 0.2 |
