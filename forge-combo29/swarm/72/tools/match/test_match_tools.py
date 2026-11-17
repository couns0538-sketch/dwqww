#!/usr/bin/env python3
"""Focused failure tests for independent paired outcome bookkeeping (MIT)."""
import unittest
from pgn_stats import summarize
from run_match import sprt_decision


def game(round_id, white, black, result, fen, moves="e2e4 e7e5"):
    return (f'[Event "Unit test"]\n[Round "{round_id}"]\n[White "{white}"]\n'
            f'[Black "{black}"]\n[Result "{result}"]\n[FEN "{fen}"]\n'
            f'[Termination "normal"]\n\n{moves} {result}\n\n')


class StatisticsTests(unittest.TestCase):
    def pair(self, result1="1-0", result2="1-0", **kwargs):
        return (game(1, "Candidate", "Baseline", result1, "start", **kwargs) +
                game(1, "Baseline", "Candidate", result2, "start", **kwargs))

    def test_rounded_llr_is_not_acceptance(self):
        self.assertEqual(sprt_decision("LLR: 2.94", 10000, 10000), "inconclusive_at_pair_cap")

    def test_native_h1(self):
        self.assertEqual(sprt_decision("LLR: 2.96\nSPRT ([0,5]) completed - H1 was accepted", 99, 10000), "H1_accepted")

    def test_native_h0(self):
        self.assertEqual(sprt_decision("LLR: -2.96\nSPRT ([0,5]) completed - H0 was accepted", 99, 10000), "H0_accepted")

    def test_premature_stop(self):
        with self.assertRaises(RuntimeError):
            sprt_decision("LLR: 0.01", 99, 10000)

    def test_missing_likelihood(self):
        with self.assertRaises(RuntimeError):
            sprt_decision("LLR: -nan", 10000, 10000)

    def test_aa(self):
        result = summarize(self.pair(), require_identical_pairs=True)
        self.assertEqual(result["pentanomial_0_half_1_1half_2"], [0, 0, 1, 0, 0])
        self.assertEqual(result["candidate_wins_draws_losses"], [1, 0, 1])

    def test_candidate_wins_both(self):
        self.assertEqual(summarize(self.pair("1-0", "0-1"))["pentanomial_0_half_1_1half_2"],
                         [0, 0, 0, 0, 1])

    def test_all_bins(self):
        outcomes = [("0-1", "1-0"), ("1/2-1/2", "1-0"), ("1/2-1/2", "1/2-1/2"),
                    ("1-0", "1/2-1/2"), ("1-0", "0-1")]
        text = "".join(game(i, "Candidate", "Baseline", first, str(i)) +
                       game(i, "Baseline", "Candidate", second, str(i))
                       for i, (first, second) in enumerate(outcomes, 1))
        self.assertEqual(summarize(text)["pentanomial_0_half_1_1half_2"], [1] * 5)

    def test_comments_and_numbers(self):
        summarize(self.pair(moves="1. e2e4 {+0.10/4, n=100} e7e5 {reply}"), require_identical_pairs=True)

    def test_incomplete(self):
        with self.assertRaises(ValueError):
            summarize(game(1, "Candidate", "Baseline", "1-0", "start"))

    def test_colors_not_swapped(self):
        with self.assertRaises(ValueError):
            summarize(game(1, "Candidate", "Baseline", "1-0", "start") * 2)

    def test_duplicate_opening(self):
        with self.assertRaises(ValueError):
            summarize(self.pair() + self.pair().replace('[Round "1"]', '[Round "2"]'))

    def test_mismatch(self):
        with self.assertRaises(ValueError):
            summarize(self.pair().replace("e2e4 e7e5 1-0", "e2e4 e7e5 0-1", 1))

    def test_crash(self):
        with self.assertRaises(ValueError):
            summarize(self.pair().replace('[Termination "normal"]', '[Termination "abandoned"]', 1))

    def test_not_identical_aa(self):
        with self.assertRaises(ValueError):
            summarize(self.pair("1-0", "0-1"), require_identical_pairs=True)


if __name__ == "__main__":
    unittest.main()
