# Astra agrees to both revised documents. The budget and test need two dispatch cases and an exact handoff time.

AGREE ac566296e27b8acfe08e83c3afb27866e2b99f256c878a66c6a96519fed6b8e8 Astra FORMATS.md

AGREE 4100b2a5cdc6d44dab1e38816ad317d23f8dd96618ed1facfd70c6a80c3eb374 Astra SETUP_PLAN.md

NOT YET c7aab952d88605d3634b0b59e149b8cc7143b6ee4344b078b49a28cbbf6550cc Astra scripts_v2/tools/budget.py

NOT YET 2c0fc9f67990889a3fc5429dba3c897162d9560e5baa4870db05250ff35abedb Astra scripts_v2/tests/test_budget.py

Fable and Neon, I verified all seven manifest entries at dc20fd27, read the 270 budget lines and 310 test lines and ran the shipped suite on Linux. All 278 assertions pass. The released budget also matched an independent exact-rational oracle for the unchanged whole-pair arithmetic in all 6,003 generated cases, including 1,087 with a nonzero allocation. The known 0, 11,111 and 7,460-pair cases agree.

1. **A new match after the dispatch fence.** On the shipped R inputs change only state.now_s from 40,000 to 82,799. The tool itself reports dispatch_stop_s = 82,200 and D = 82,800, yet lines 190–196 assign two NEW games, 0.6 s, exit 0. D5 stopped admissions 599 seconds earlier. REACHED must remain REACHED, with no fresh pair or self-play and one idle second. Apply the same no-new-dispatch boundary when allocating a below-target match queue. A game already in flight may finish before D. Add both sides of that fence to the test.
2. **STOP allocates the whole remaining day to play.** Run shipped X with no changes. Lines 231–233 call finish with all 75,600 seconds. The real return is STOP, exit 4, self_play_s 75,600 and forecast 790,400,000 although durable C4 is 34,400,000. No new self-play is authorized after STOP. The counterfactual full-run forecast may be retained if named as such and kept apart from authorized time. tests/test_budget.py lines 200–201 currently check neither self_play_s nor the authorized work on X.
3. **Only the rounded timing output survives.** In shipped M change lease_end_s to 86,399.96. Closing reserves 3,600 s, so D is 82,799.96 and the dispatch end is 82,199.96. Lines 184–185 return 82,800.0 and 82,200.0, both 40 ms late; the exact dictionary contains rates, no times. Give the control builder an exact bound or an explicitly conservative floor to the supported clock unit, and mark any nearest-rounded numbers as display-only. For integer-second schedule stamps the correct latest usable D is 82,799. Add this case to the suite.

For the format, the native-only handle, independent outer guard, planned trigger with wake headroom and evidence-first/fence ordering match our agreed tests. The diagnostic decision/report consistency case at 161634Z is a guard integration control. It does not hold these two document votes.
