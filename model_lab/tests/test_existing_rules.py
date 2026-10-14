"""Independent rule tests: hand-worked fixtures, no policy/solver dependencies.

Run: python -m unittest discover -s reports/fpl_simulator_2026_10_13 -p test_engine_independent.py -v
Rule source provenance is recorded under vendor/fpl_rules_v1/PROVENANCE.json. Tests intentionally exercise the
public engine API, not private implementation helpers.
"""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("independent_engine_under_test", HERE.parent / "vendor/fpl_rules_v1/engine.py")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


def fixture():
    positions = {1: 1, 2: 1, **{i: 2 for i in range(3, 8)},
                 **{i: 3 for i in range(8, 13)}, **{i: 4 for i in range(13, 16)}}
    pool = {i: {"pos": positions[i], "club": (i - 1) % 5, "market": 50, "can_buy": True}
            for i in range(1, 16)}
    choice = {"squad": list(range(1, 16)), "starters": [1, 3, 4, 5, 8, 9, 10, 11, 13, 14, 15],
              "bench": [2, 12, 6, 7], "captain": 13, "vice": 8}
    return pool, choice


def outcomes(points=2):
    return {i: {"points": points, "active": True} for i in range(1, 16)}


class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.pool, self.choice = fixture()
        self.points = {i: 2 for i in range(1, 16)}
        self.active = {i: True for i in range(1, 16)}

    def settle(self, chip=None):
        c = self.choice
        return engine.settle(c["starters"], c["bench"], c["captain"], c["vice"],
                             {i: p["pos"] for i, p in self.pool.items()}, self.points, self.active, chip)

    def test_ordinary_total_is_24_and_bench_ignored(self):
        self.points[12] = 99
        self.assertEqual(self.settle()["gross"], 24)

    def test_negative_captain_points_are_doubled(self):
        self.points[13] = -2
        self.assertEqual(self.settle()["gross"], 16)

    def test_zero_point_appearance_keeps_armband(self):
        self.points[13] = 0
        self.points[8] = 10
        result = self.settle()
        self.assertEqual(result["effective_captain"], 13)
        self.assertEqual(result["captain_bonus"], 0)

    def test_goalkeeper_replaced_only_by_reserve_goalkeeper(self):
        self.active[1] = False
        self.points[1], self.points[2] = 0, 7
        result = self.settle()
        self.assertEqual(result["gross"], 29)
        self.assertIn(2, result["counted"])
        self.assertNotIn(1, result["counted"])

    def test_minimum_defenders_skips_high_priority_midfielder(self):
        self.active[3], self.points[3] = False, 0
        self.points[12], self.points[6], self.points[7] = 99, -1, 50
        result = self.settle()
        self.assertEqual(result["gross"], 21)
        self.assertIn(6, result["counted"])
        self.assertNotIn(12, result["counted"])
        self.assertNotIn(7, result["counted"])

    def test_multiple_absences_preserve_formation_and_bench_priority(self):
        for pid in [3, 8]:
            self.active[pid], self.points[pid] = False, 0
        self.points[12], self.points[6], self.points[7] = 1, 3, 99
        result = self.settle()
        self.assertEqual(result["gross"], 24)
        self.assertTrue({12, 6}.issubset(result["counted"]))
        self.assertNotIn(7, result["counted"])

    def test_unavailable_first_bench_does_not_block_second(self):
        for pid in [8, 12]:
            self.active[pid], self.points[pid] = False, 0
        self.points[6] = 4
        self.assertEqual(self.settle()["gross"], 26)

    def test_vice_captain_fallback_and_triple_bonus(self):
        self.active[13], self.points[13] = False, 0
        self.points[8] = 7
        result = self.settle("triple_captain")
        self.assertEqual(result["effective_captain"], 8)
        self.assertEqual(result["base"], 27)
        self.assertEqual(result["gross"], 41)

    def test_no_captain_played_means_no_bonus(self):
        for pid in [13, 8]:
            self.active[pid], self.points[pid] = False, 0
        self.assertEqual(self.settle("triple_captain")["captain_bonus"], 0)

    def test_bench_boost_scores_all_fifteen_once_plus_captain(self):
        self.assertEqual(self.settle("bench_boost")["gross"], 32)

    def test_missing_counted_points_never_become_zero(self):
        del self.points[13]
        with self.assertRaises(ValueError):
            self.settle()

    def test_unknown_participation_never_becomes_dnp(self):
        del self.active[13]
        with self.assertRaises(ValueError):
            self.settle()

    def test_nonfinite_points_rejected(self):
        for bad in [None, float("nan"), float("inf")]:
            with self.subTest(bad=bad):
                self.points[13] = bad
                with self.assertRaises(ValueError):
                    self.settle()

    def test_card_without_minutes_is_appearance_and_negative_points_count(self):
        self.assertTrue(engine.appearance(0, yellow_cards=1))
        self.assertTrue(engine.appearance(0, red_cards=1))
        self.assertFalse(engine.appearance(0, 0, 0))
        self.active[13] = engine.appearance(0, red_cards=1)
        self.points[13] = -3
        self.assertEqual(self.settle()["gross"], 14)


class StateAndRulesTests(unittest.TestCase):
    def setUp(self):
        self.pool, self.choice = fixture()

    def established(self):
        state, _ = engine.apply_decision(engine.initial_state(), self.choice, self.pool, gw=1)
        return state

    def replacement(self, choice=None, old=3, new=16, market=50):
        choice = copy.deepcopy(choice or self.choice)
        self.pool[new] = dict(self.pool[old], market=market)
        for key in ["squad", "starters", "bench"]:
            choice[key] = [new if i == old else i for i in choice[key]]
        return choice

    def test_initial_purchase_and_bank_and_inputs_not_mutated(self):
        state = engine.initial_state()
        original = copy.deepcopy((state, self.choice, self.pool))
        after, _ = engine.apply_decision(state, self.choice, self.pool, gw=1)
        self.assertEqual(after["bank"], 250)
        self.assertEqual(after["ft"], 1)
        self.assertEqual(after["owned"], {i: 50 for i in range(1, 16)})
        self.assertEqual((state, self.choice, self.pool), original)

    def test_roll_free_transfers_caps_at_five(self):
        state = self.established()
        for gw in range(2, 9):
            state, _ = engine.apply_decision(state, self.choice, self.pool, gw=gw)
            self.assertEqual(state["ft"], min(gw, 5))

    def test_half_profit_rounds_down_and_loss_is_full(self):
        for market, expected_bank in [(53, 251), (54, 252), (47, 247)]:
            with self.subTest(market=market):
                self.pool, self.choice = fixture()
                state = self.established()
                self.pool[3]["market"] = market
                changed = self.replacement()
                state, decision = engine.apply_decision(state, changed, self.pool, gw=2)
                self.assertEqual(state["bank"], expected_bank)
                self.assertEqual(state["owned"][16], 50)
                self.assertEqual(decision["paid"], 0)

    def test_paid_transfer_cost_four_and_net_score(self):
        state = self.established()
        changed = self.replacement()
        changed = self.replacement(changed, old=4, new=17)
        out = outcomes()
        out[16] = out[17] = {"points": 2, "active": True}
        after, log = engine.play_round(state, changed, self.pool, out, gw=2)
        self.assertEqual(after["ft"], 1)
        self.assertEqual(log["net_points"], 20)

    def test_wildcard_preserves_ft_and_changes_squad_permanently(self):
        state = self.established()
        state["ft"] = 4
        changed = self.replacement()
        after, decision = engine.apply_decision(state, changed, self.pool, gw=2, chip="wildcard")
        self.assertEqual(after["ft"], 4)
        self.assertIn(16, after["owned"])
        self.assertNotIn(3, after["owned"])
        self.assertEqual(decision["paid"], 0)

    def test_free_hit_restores_bank_purchase_prices_and_squad(self):
        state = self.established()
        state["ft"] = 4
        original = copy.deepcopy(state)
        self.pool[3]["market"] = 57
        changed = self.replacement(market=60)
        out = outcomes()
        out[16] = {"points": 10, "active": True}
        after, log = engine.play_round(state, changed, self.pool, out, gw=2, chip="free_hit")
        self.assertEqual(after["owned"], original["owned"])
        self.assertEqual(after["bank"], original["bank"])
        self.assertEqual(after["ft"], 4)
        self.assertEqual(log["net_points"], 32)
        # Next ordinary sale realizes original purchase basis with current market.
        normal, _ = engine.apply_decision(after, changed, self.pool, gw=3)
        self.assertEqual(normal["bank"], 243)

    def test_bench_boost_and_triple_captain_allowed_initially(self):
        for chip, expected in [("bench_boost", 32), ("triple_captain", 26)]:
            with self.subTest(chip=chip):
                state, log = engine.play_round(engine.initial_state(), self.choice, self.pool,
                                               outcomes(), gw=1, chip=chip)
                self.assertEqual(log["net_points"], expected)
                self.assertIn(chip, state["used_chips"]["1"])

    def test_club_transfer_exception_requires_proof_and_next_transfer_repairs_it(self):
        state = self.established()
        self.pool[2]["club"] = self.pool[1]["club"]
        after, _ = engine.apply_decision(state, self.choice, self.pool, gw=2)
        after, _ = engine.apply_decision(after, self.choice, self.pool, gw=3)
        changed = self.replacement()
        with self.assertRaises(ValueError):
            engine.apply_decision(after, changed, self.pool, gw=4)
        changed = self.replacement(old=2, new=18)
        self.pool[18]["club"] = 1
        repaired, _ = engine.apply_decision(after, changed, self.pool, gw=4)
        self.assertIn(18, repaired["owned"])
        state.pop("ownership_clubs")
        with self.assertRaises(ValueError):
            engine.apply_decision(state, self.choice, self.pool, gw=2)

    def test_retaining_unbuyable_owned_player_is_allowed(self):
        state = self.established()
        self.pool[1]["can_buy"] = False
        after, _ = engine.apply_decision(state, self.choice, self.pool, gw=2)
        self.assertIn(1, after["owned"])

    def test_missing_bench_outcome_prevents_unqualified_complete_score(self):
        out = outcomes()
        del out[12]
        with self.assertRaises(ValueError):
            engine.play_round(engine.initial_state(), self.choice, self.pool, out, gw=1)

    def test_reject_invalid_squad_lineup_bench_and_captains(self):
        variants = []
        for key, value in [("squad", list(range(1, 15))), ("starters", self.choice["starters"][:-1]),
                           ("bench", [2, 12, 6, 6]), ("captain", 12), ("vice", 13)]:
            c = copy.deepcopy(self.choice)
            c[key] = value
            variants.append(c)
        c = copy.deepcopy(self.choice)
        c["starters"] = [12 if i == 3 else i for i in c["starters"]]
        c["bench"] = [3 if i == 12 else i for i in c["bench"]]
        variants.append(c)
        for c in variants:
            with self.subTest(choice=c):
                with self.assertRaises(ValueError):
                    engine.validate_decision(engine.initial_state(), c, self.pool, gw=1)

    def test_budget_club_limit_and_unbuyable_enforced(self):
        for mode in ["budget", "club", "unbuyable"]:
            pool = copy.deepcopy(self.pool)
            if mode == "budget":
                for player in pool.values(): player["market"] = 100
            elif mode == "club": pool[2]["club"] = pool[1]["club"]
            else: pool[1]["can_buy"] = False
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):
                    engine.validate_decision(engine.initial_state(), self.choice, pool, gw=1)

    def test_reject_stale_round_and_false_accounting_claims(self):
        state = self.established()
        with self.assertRaises(ValueError):
            engine.apply_decision(state, self.choice, self.pool, gw=1)
        changed = self.replacement()
        changed["paid"] = 99
        with self.assertRaises(ValueError):
            engine.apply_decision(state, changed, self.pool, gw=2)

    def test_chips_gw1_expiry_repeat_and_consecutive_free_hit(self):
        for chip in ["wildcard", "free_hit"]:
            with self.subTest(chip=chip):
                with self.assertRaises(ValueError):
                    engine.apply_decision(engine.initial_state(), self.choice, self.pool, gw=1, chip=chip)
        state = self.established()
        state, _ = engine.apply_decision(state, self.choice, self.pool, gw=2, chip="triple_captain")
        with self.assertRaises(ValueError):
            engine.apply_decision(state, self.choice, self.pool, gw=3, chip="triple_captain")
        state["next_gw"] = 20
        after, _ = engine.apply_decision(state, self.choice, self.pool, gw=20, chip="triple_captain")
        self.assertIn("triple_captain", after["used_chips"]["2"])
        state = self.established()
        state["next_gw"] = 19
        state, _ = engine.apply_decision(state, self.choice, self.pool, gw=19, chip="free_hit")
        with self.assertRaises(ValueError):
            engine.apply_decision(state, self.choice, self.pool, gw=20, chip="free_hit")

    def test_unknown_chip_rejected(self):
        with self.assertRaises(ValueError):
            engine.apply_decision(self.established(), self.choice, self.pool, gw=2, chip="mystery")

    def test_unknown_outcomes_abort_without_state_mutation(self):
        state = self.established()
        original = copy.deepcopy(state)
        out = outcomes()
        del out[13]
        with self.assertRaises(ValueError):
            engine.play_round(state, self.choice, self.pool, out, gw=2)
        self.assertEqual(state, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
