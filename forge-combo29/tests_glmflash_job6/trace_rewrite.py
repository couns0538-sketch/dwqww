#!/usr/bin/env python3
# Same-tree P1 counters on a freshly applied traced tree (job 6).
path = "/tmp/forge_cm_trace/src/search.cpp"
t = open(path, encoding="utf-8").read()

old_rfp = """        if (++rfp_tested; ++rfp_hist[bucket_of(ss->corr_size)];
        const int corr_term = ss->corr_size * tune::CorrMargin / 64;
        if (depth <= tune::RfpDepth && eval - (tune::RfpMargin * depth - tune::RfpImproving * improving + corr_term) >= beta &&
            eval < MateInMaxPly) {
            ++rfp_cutoff;
            return eval;
        }"""
new_rfp = """        const int corr_term = ss->corr_size * tune::CorrMargin / 64;
        if (depth <= tune::RfpDepth) {
            ++rfp_tested;
            ++rfp_hist[bucket_of(ss->corr_size)];
            const bool off_cut = eval - (tune::RfpMargin * depth - tune::RfpImproving * improving) >= beta && eval < MateInMaxPly;
            const bool on_cut = eval - (tune::RfpMargin * depth - tune::RfpImproving * improving + corr_term) >= beta && eval < MateInMaxPly;
            if (off_cut) ++rfp_off_cut;
            if (on_cut) {
                ++rfp_cutoff;
                return eval;
            }
        }"""
assert old_rfp in t, "RFP traced block not found"
t = t.replace(old_rfp, new_rfp, 1)

old_fut = """                if (!in_check && lmr_depth <= tune::FutilityDepth &&
                    ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth + ss->corr_size * tune::CorrMargin / 64 <= alpha && ++fut_skips) {
                    skip_quiets = true;
                    continue;
                }"""
new_fut = """                if (!in_check && lmr_depth <= tune::FutilityDepth) {
                    if (ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha) {
                        ++fut_off_skip;
                    }
                    if (ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth + ss->corr_size * tune::CorrMargin / 64 <= alpha) {
                        ++fut_skips;
                        skip_quiets = true;
                        continue;
                    }
                }"""
assert old_fut in t, "futility traced block not found"
t = t.replace(old_fut, new_fut, 1)

t = t.replace("static long rfp_tested = 0, rfp_cutoff = 0, fut_skips = 0;",
              "static long rfp_tested = 0, rfp_cutoff = 0, fut_skips = 0, rfp_off_cut = 0, fut_off_skip = 0;", 1)
t = t.replace('"TRACE rfp_tested %ld rfp_cutoff %ld fut_skips %ld hist %ld %ld %ld %ld %ld\\n", rfp_tested, rfp_cutoff, fut_skips, rfp_hist[0], rfp_hist[1], rfp_hist[2], rfp_hist[3], rfp_hist[4]',
              '"TRACE rfp_tested %ld rfp_off_cut %ld rfp_cutoff %ld fut_off_skip %ld fut_skips %ld hist %ld %ld %ld %ld %ld\\n", rfp_tested, rfp_off_cut, rfp_cutoff, fut_off_skip, fut_skips, rfp_hist[0], rfp_hist[1], rfp_hist[2], rfp_hist[3], rfp_hist[4]', 1)
open(path, "w", encoding="utf-8").write(t)
print("same-tree counters installed")
