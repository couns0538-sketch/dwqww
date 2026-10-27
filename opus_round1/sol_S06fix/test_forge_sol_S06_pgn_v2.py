"""SYNTHETIC PGNs only. No fixture is evidence of an engine match."""
import json
import unittest

try:
    from forge_sol_S06_pgn_v2 import mine_pgn
except ImportError:
    mine_pgn = None


FEN = "8/8/8/8/8/8/K7/7k w - - 0 1"
FEN2 = "8/8/8/8/8/8/K7/7k b - - 0 1"


def game(round_="1", white="Candidate", result="1-0", *, fen=FEN,
         termination="normal", phase="endgame", extra=None, moves=None):
    """Generate clearly synthetic PGN without relying on the miner's helpers."""
    tags = {"Event": "SYNTHETIC", "Site": "fixture", "Round": round_,
            "White": white, "Black": "Baseline" if white == "Candidate" else "Candidate",
            "Result": result, "TimeControl": "1+0.01", "Threads": "1", "Hash": "16",
            "Concurrency": "1", "Seed": "17", "Gate": "synthetic-A"}
    if fen is not None:
        tags["FEN"] = fen
    if termination is not None:
        tags["Termination"] = termination
    if phase is not None:
        tags["Phase"] = phase
    tags.update(extra or {})
    header = "\n".join('[%s "%s"]' % (key, str(value).replace('\\', '\\\\').replace('"', '\\"'))
                       for key, value in tags.items())
    return header + "\n\n" + (moves if moves is not None else "1. Ka3 " + result) + "\n\n"


class SyntheticPGNTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(mine_pgn), "PGN miner implementation is missing")

    def mine(self, text, **kwargs):
        return mine_pgn(text, "Candidate", "Baseline", **kwargs)

    def test_valid_out_of_order_same_round_pair_preserves_raw_outcomes(self):
        report = self.mine(game("2", result="1/2-1/2") + game("1", result="1-0") +
                           game("2", "Baseline", "1-0", fen=FEN.replace("0 1", "7 9")) +
                           game("1", "Baseline", "0-1"))
        self.assertEqual((report["raw"]["W"], report["raw"]["D"], report["raw"]["L"]), (2, 1, 1))
        self.assertEqual(report["paired"]["valid_pairs"], 2)
        self.assertEqual(report["paired"]["six_bins"], {"WW": 1, "WD": 0, "WL": 0, "DD": 0, "LD": 1, "LL": 0})
        self.assertEqual(report["paired"]["pentabins"], [0, 1, 0, 0, 1])
        self.assertEqual(report["per_phase"]["endgame"]["games"], 4)
        self.assertEqual(report["per_phase"]["endgame"]["paired"]["valid_pairs"], 2)
        self.assertEqual(len(report["pools"]), 1)
        self.assertEqual(report["pools"][0]["raw"]["games"], 4)
        json.dumps(report, allow_nan=False)

    def test_all_six_pair_bins_are_distinct_even_when_penta_score_equal(self):
        text = ""
        # Scores are independent hand-derived candidate half-point units.
        examples = [("1-0", "0-1"), ("1-0", "1/2-1/2"), ("1-0", "1-0"),
                    ("1/2-1/2", "1/2-1/2"), ("0-1", "1/2-1/2"), ("0-1", "1-0")]
        for i, (first, second) in enumerate(examples, 1):
            fen = FEN.replace("w - -", "w - %s3" % chr(ord('a') + i - 1))
            text += game(str(i), result=first, fen=fen) + game(str(i), "Baseline", second, fen=fen)
        result = self.mine(text)
        self.assertEqual(result["paired"]["six_bins"], dict.fromkeys(["WW", "WD", "WL", "DD", "LD", "LL"], 1))
        self.assertEqual(result["paired"]["pentabins"], [1, 1, 2, 1, 1])

    def test_result_tokens_in_comments_nested_variations_and_semicolon_are_ignored(self):
        moves = '1. Ka3 {SYNTHETIC 0-1 [Result "0-1"]} (1. Kb3 0-1 (1... Kh2 1/2-1/2)) ; 0-1\n2. Ka4 $1 1-0'
        result = self.mine(game(moves=moves))
        self.assertEqual(result["raw"]["W"], 1)
        self.assertEqual(result["games"][0]["mainline_result"], "1-0")
        self.assertEqual(result["games"][0]["issues"], [])

    def test_escaped_quotes_backslashes_and_same_line_headers(self):
        text = game(extra={"Annotator": 'SYNTHETIC "quote" \\path'})
        text = text.replace('[Event "SYNTHETIC"]\n[Site "fixture"]', '[Event "SYNTHETIC"] [Site "fixture"]')
        report = self.mine(text)
        self.assertEqual(report["games"][0]["tags"]["Annotator"], 'SYNTHETIC "quote" \\path')
        self.assertEqual(report["raw"]["W"], 1)

    def test_conflicting_result_is_unknown_and_never_scored_from_either_claim(self):
        report = self.mine(game(moves="1. Ka3 0-1"))
        record = report["games"][0]
        self.assertEqual(record["header_result"], "1-0")
        self.assertEqual(record["mainline_result"], "0-1")
        self.assertIsNone(record["score"])
        self.assertEqual((report["raw"]["W"], report["raw"]["L"], report["raw"]["unknown"]), (0, 0, 1))
        self.assertIn("result_mismatch", record["issues"])

    def test_unfinished_and_missing_terminal_result_are_retained(self):
        report = self.mine(game("1", result="*", termination="Black crashed") +
                           game("2", moves="1. Ka3 {1-0}", termination=None))
        self.assertEqual(report["raw"]["games"], 2)
        self.assertEqual(report["raw"]["unknown"], 2)
        self.assertEqual(report["raw"]["faults"]["crash"], 1)
        self.assertEqual(report["raw"]["faults"]["baseline"], 1)
        self.assertEqual(report["raw"]["termination_unknown"], 1)
        self.assertEqual(report["raw"]["fault_status"], "observed_faults")
        self.assertIn("missing_mainline_result", report["games"][1]["issues"])

    def test_unrecognized_termination_is_preserved_but_not_eligible(self):
        for label in ["abandoned", "unterminated", "weird mystery", "?"]:
            with self.subTest(label=label):
                report = self.mine(game(termination=label) + game("1", "Baseline", "0-1"))
                self.assertEqual(report["games"][0]["tags"]["Termination"], label)
                self.assertEqual(report["paired"]["valid_pairs"], 1)
                self.assertEqual(report["paired"]["eligible_pairs"], 0)
                self.assertEqual(report["raw"]["termination_unknown"], 1)
                self.assertEqual(report["raw"]["fault_status"], "unknown")
        report = self.mine(game(termination=" Normal ") + game("1", "Baseline", "0-1"))
        self.assertTrue(report["paired"]["aggregate_eligible"])

    def test_malformed_and_duplicate_tags_block_without_dropping_game(self):
        bad = game().replace('[Round "1"]', '[Round "1"]\n[Round "9"]\n[Broken "unterminated]')
        report = self.mine(bad + game("1", "Baseline", "0-1"))
        self.assertEqual(report["raw"]["games"], 2)
        self.assertEqual(report["raw"]["W"], 2)
        self.assertIn("duplicate_tag:Round", report["games"][0]["issues"])
        self.assertIn("malformed_tag", report["games"][0]["issues"])
        self.assertEqual(report["paired"]["valid_pairs"], 0)

    def test_unclosed_comment_or_variation_blocks_even_if_result_was_seen(self):
        for tail, issue in [("{ unfinished", "unclosed_comment"), ("( 1... Kh2", "unclosed_variation")]:
            with self.subTest(tail=tail):
                report = self.mine(game(moves="1. Ka3 1-0 " + tail))
                self.assertEqual(report["raw"]["games"], 1)
                self.assertIn(issue, report["games"][0]["issues"])
                self.assertEqual(report["paired"]["valid_pairs"], 0)

    def test_missing_termination_is_unknown_and_not_zero_fault_guarantee(self):
        report = self.mine(game(termination=None) + game("1", "Baseline", "0-1", termination=None))
        self.assertEqual(report["paired"]["valid_pairs"], 1)
        self.assertEqual(report["paired"]["eligible_pairs"], 0)
        self.assertFalse(report["paired"]["aggregate_eligible"])
        self.assertEqual(report["raw"]["fault_status"], "unknown")
        self.assertEqual(report["raw"]["faults"]["total"], 0)
        self.assertEqual(report["raw"]["termination_unknown"], 2)

    def test_faulted_complete_pairs_keep_descriptive_bins_and_attribution(self):
        report = self.mine(game(termination="Black loses on time") +
                           game("1", "Baseline", "0-1", termination="Baseline crash; Candidate illegal move"))
        self.assertEqual(report["paired"]["pentabins"], [0, 0, 0, 0, 1])
        self.assertEqual(report["paired"]["fault_count"], 3)
        self.assertEqual(report["pairs"][0]["fault_count"], 3)
        self.assertEqual(report["paired"]["eligible_pairs"], 0)
        faults = report["raw"]["faults"]
        self.assertEqual((faults["time_loss"], faults["crash"], faults["illegal"]), (1, 1, 1))
        self.assertEqual((faults["candidate"], faults["baseline"]), (1, 2))

    def test_unknown_attribution_does_not_invent_a_loser(self):
        report = self.mine(game(result="*", termination="engine crashed"))
        self.assertEqual(report["raw"]["faults"]["unknown"], 1)

    def test_missing_termination_with_explicit_comment_fault_remains_unknown_termination(self):
        report = self.mine(game(termination=None, moves="1. Ka3 {Black crashed} 1-0"))
        self.assertEqual(report["raw"]["termination_unknown"], 1)
        self.assertEqual(report["raw"]["faults"]["baseline"], 1)
        self.assertEqual(report["raw"]["fault_status"], "observed_faults")

    def test_strict_engine_names_and_distinct_api_arguments(self):
        report = self.mine(game(white="Candidate suffix"))
        self.assertEqual(report["raw"]["unknown"], 1)
        self.assertIn("engine_names_mismatch", report["games"][0]["issues"])
        for candidate, baseline in [("", "B"), ("C", "C"), (" C", "B"), (None, "B")]:
            with self.subTest(candidate=candidate, baseline=baseline):
                with self.assertRaises(ValueError):
                    mine_pgn("", candidate, baseline)

    def test_duplicate_incomplete_wrong_colors_and_opening_mismatch_keep_raw_wdl(self):
        examples = [game(), game() + game("1", result="0-1"),
                    game() + game("1", "Baseline", "0-1", fen=FEN2),
                    game() + game("1", "Baseline", "0-1") + game("1", result="1-0")]
        for text in examples:
            with self.subTest(text=text):
                report = self.mine(text)
                self.assertGreater(report["raw"]["W"] + report["raw"]["L"], 0)
                self.assertEqual(report["paired"]["valid_pairs"], 0)
                self.assertEqual(report["paired"]["invalid_pairs"], 1)

    def test_absent_fen_is_opening_unknown_not_assumed_start_position(self):
        report = self.mine(game(fen=None) + game("1", "Baseline", "0-1", fen=None))
        self.assertEqual(report["raw"]["W"], 2)
        self.assertEqual(report["paired"]["valid_pairs"], 0)
        self.assertIn("opening_unknown", report["pairs"][0]["issues"])
        self.assertEqual(report["per_opening"]["unknown"]["games"], 2)

    def test_openingfen_supported_but_conflicting_fen_is_blocked(self):
        report = self.mine(game(fen=None, extra={"OpeningFEN": FEN}) +
                           game("1", "Baseline", "0-1", fen=None, extra={"OpeningFEN": FEN}))
        self.assertEqual(report["paired"]["valid_pairs"], 1)
        report = self.mine(game(extra={"OpeningFEN": FEN2}) + game("1", "Baseline", "0-1"))
        self.assertIn("conflicting_opening_fen", report["games"][0]["issues"])
        self.assertEqual(report["paired"]["valid_pairs"], 0)

    def test_malformed_fen_cannot_claim_a_valid_opening_pair(self):
        cases = ["garbage w - -", "8/8/8/8/8/8/K7 w - -", "8/8/8/8/8/8/K7/6k w - -",
                 "8/8/8/8/8/8/K7/7x w - -", "8/8/8/8/8/8/K7/07k w - -",
                 FEN.replace(' w ', ' x '), FEN.replace(' - - ', ' KK - '),
                 FEN.replace(' - - ', ' Kx - '), FEN.replace(' - - ', ' - a4 '),
                 FEN.replace('0 1', '-1 1'), FEN.replace('0 1', 'a 1'),
                 FEN.replace('0 1', '0 0'), FEN.rsplit(' ', 1)[0], FEN + ' extra']
        for fen in cases:
            with self.subTest(fen=fen):
                report = self.mine(game(fen=fen) + game('1', 'Baseline', '0-1', fen=fen))
                self.assertEqual(report['raw']['W'], 2)
                self.assertIn('invalid_opening_fen', report['games'][0]['issues'])
                self.assertEqual(report['paired']['valid_pairs'], 0)
                self.assertFalse(report['paired']['aggregate_eligible'])

    def test_four_and_six_field_fen_share_normalized_opening_identity(self):
        first_four = '8/8/8/8/8/8/K7/7k w Kq a3'
        report = self.mine(game(fen=first_four) + game('1', 'Baseline', '0-1', fen=first_four + ' 999 12'))
        self.assertEqual(report['games'][0]['opening_key'], first_four)
        self.assertEqual(report['paired']['valid_pairs'], 1)
        self.assertTrue(report['paired']['aggregate_eligible'])

    def test_variation_comments_remain_observations_without_actual_fault_attribution(self):
        text = game(moves='1. Ka3 (1. Kb3 {Black crashed} (1... Kh2 {Candidate loses on time})) 1-0')
        report = self.mine(text)
        self.assertEqual(report['raw']['faults']['total'], 0)
        self.assertEqual(report['games'][0]['comment_observations'], [
            {'text': 'Black crashed', 'variation_depth': 1},
            {'text': 'Candidate loses on time', 'variation_depth': 2}])

    def test_explicit_match_run_attempt_and_supported_option_tags_split_pools(self):
        for tag in ['Match', 'Run', 'Attempt', 'Srand', 'Variant', 'Options', 'EngineOptions',
                    'WhiteOptions', 'BlackOptions', 'Ponder', 'UCI_Chess960', 'SyzygyPath']:
            with self.subTest(tag=tag):
                text = game(extra={tag: 'A'}) + game('1', 'Baseline', '0-1', extra={tag: 'A'})
                text += game('2', extra={tag: 'B'}) + game('2', 'Baseline', '0-1', extra={tag: 'B'})
                report = self.mine(text)
                self.assertEqual(len(report['pools']), 2)
                self.assertIsNone(report['paired']['pentabins'])
                self.assertIn(tag, report.get('supported_identity_tags', []))
        report = self.mine(game(extra={'Date': '2026.10.25'}) +
                           game('1', 'Baseline', '0-1', extra={'Date': '2026.10.26'}))
        self.assertEqual(len(report['pools']), 1)
        self.assertTrue(report['paired']['aggregate_eligible'])
        self.assertNotIn('Date', report.get('supported_identity_tags', []))

    def test_pairing_policies_are_explicit_and_do_not_infer_adjacent_rounds(self):
        text = game("1") + game("2", "Baseline", "0-1")
        self.assertEqual(self.mine(text)["paired"]["valid_pairs"], 0)
        self.assertEqual(self.mine(text, pairing="adjacent-rounds")["paired"]["valid_pairs"], 1)
        text = game("17.1") + game("17.2", "Baseline", "0-1")
        self.assertEqual(self.mine(text)["paired"]["valid_pairs"], 0)
        self.assertEqual(self.mine(text, pairing="round-prefix")["paired"]["valid_pairs"], 1)
        for mode, rounds in [("adjacent-rounds", ("2", "3")), ("round-prefix", ("1.1", "1.1"))]:
            report = self.mine(game(rounds[0]) + game(rounds[1], "Baseline", "0-1"), pairing=mode)
            self.assertEqual(report["paired"]["valid_pairs"], 0)
        with self.assertRaises(ValueError):
            self.mine(text, pairing="guess")

    def test_metadata_identity_changes_create_separate_pools_without_combined_penta(self):
        for tag in ["Event", "Site", "TimeControl", "Threads", "Hash", "Concurrency", "Seed", "Gate"]:
            with self.subTest(tag=tag):
                text = game() + game("1", "Baseline", "0-1")
                text += game("2", extra={tag: "changed"}) + game("2", "Baseline", "0-1", extra={tag: "changed"})
                report = self.mine(text)
                self.assertEqual(report["raw"]["W"], 4)
                self.assertEqual(len(report["pools"]), 2)
                self.assertIsNone(report["paired"]["pentabins"])
                self.assertIsNone(report["paired"]["six_bins"])
                self.assertFalse(report["paired"]["aggregate_eligible"])
                self.assertEqual([pool["paired"]["pentabins"] for pool in report["pools"]], [[0, 0, 0, 0, 1]] * 2)
                self.assertEqual([pool["raw"]["W"] for pool in report["pools"]], [2, 2])
                self.assertTrue(any(issue["code"] == "metadata_variation" for issue in report["issues"]))

    def test_changed_settings_with_same_round_cannot_form_pair(self):
        report = self.mine(game() + game("1", "Baseline", "0-1", extra={"Gate": "B"}))
        self.assertEqual(report["paired"]["valid_pairs"], 0)
        self.assertEqual(report["paired"]["invalid_pairs"], 2)

    def test_repeated_opening_pairs_flag_without_removing_outcomes(self):
        report = self.mine(game("1") + game("1", "Baseline", "0-1") +
                           game("2") + game("2", "Baseline", "0-1"))
        self.assertEqual(report["raw"]["W"], 4)
        self.assertEqual(report["paired"]["valid_pairs"], 2)
        self.assertTrue(any(issue["code"] == "repeated_opening_pairs" for issue in report["issues"]))

    def test_phase_is_explicit_categorical_tag_only_and_missing_is_unknown(self):
        report = self.mine(game(phase=None) + game("1", "Baseline", "0-1", phase=None) +
                           game("2", phase="opening") + game("2", "Baseline", "0-1", phase="middlegame"))
        self.assertEqual(report["per_phase"]["unknown"]["games"], 2)
        self.assertEqual(report["per_phase"]["opening"]["W"], 1)
        self.assertEqual(report["per_phase"]["middlegame"]["W"], 1)
        self.assertEqual(report["per_phase"]["opening"]["paired"]["valid_pairs"], 0)
        self.assertEqual(report["per_phase"]["middlegame"]["paired"]["valid_pairs"], 0)
        self.assertIsNone(report["pairs"][1]["phase"])
        report = self.mine(game(extra={"Stage": "custom"}, phase=None), phase_tag="Stage")
        self.assertEqual(report["per_phase"]["custom"]["games"], 1)

    def test_empty_input_is_explicitly_ineligible(self):
        report = self.mine("")
        self.assertEqual(report["raw"]["games"], 0)
        self.assertEqual(report["paired"]["pentabins"], [0, 0, 0, 0, 0])
        self.assertFalse(report["paired"]["aggregate_eligible"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
