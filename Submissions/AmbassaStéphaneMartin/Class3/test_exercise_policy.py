"""Small exact reference decisions, production boundary contracts and path tests."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fractions import Fraction
import math
import unittest

import american_put
import exercise_policy as policy
from test_american_put import ABS_TOL, REL_TOL


class ExerciseNotImplemented(AssertionError):
    """An explicit pending production signal, separate from test errors."""


@dataclass(frozen=True)
class NodeDecision:
    date_index: int
    stock: Fraction
    intrinsic: Fraction
    continuation: Fraction | None
    exercise: bool


@dataclass(frozen=True)
class ReferenceBoundary:
    price: Fraction
    boundary: tuple[Fraction | None, ...]
    nodes: tuple[tuple[NodeDecision, ...], ...]


def exact_full_tree_decisions(S0, K, u, d, R, N):
    """Test-only full binary tree, exact rational arithmetic, no production helpers."""
    S0, K, u, d, R = (Fraction(str(value)) for value in (S0, K, u, d, R))
    q = (R-d) / (u-d)
    nodes = [[] for _ in range(N+1)]

    def visit(stock, t):
        intrinsic = max(K-stock, Fraction(0))
        if t == N:
            continuation = None
            exercise = intrinsic > 0
            value = intrinsic
        else:
            up = visit(stock*u, t+1)
            down = visit(stock*d, t+1)
            continuation = (q*up + (1-q)*down) / R
            exercise = intrinsic > continuation
            value = max(intrinsic, continuation)
        nodes[t].append(NodeDecision(t, stock, intrinsic, continuation, exercise))
        return value

    price = visit(S0, 0)
    boundary = tuple(max((node.stock for node in level if node.exercise), default=None) for level in nodes)
    return ReferenceBoundary(price, boundary, tuple(tuple(level) for level in nodes))


BASE = dict(S0=100, K=100, u=1.2, d=0.8, R=1.05, N=2)
POSITIVE_TIE = dict(S0=80, K=100, u=1.125, d=0.875, R=1, N=1)
ZERO_TIE = dict(S0=120, K=100, u=1.25, d=0.875, R=1, N=1)


class BoundaryReferenceTests(unittest.TestCase):
    def test_two_period_reference_boundaries_and_node_decisions(self):
        result = exact_full_tree_decisions(**BASE)
        self.assertEqual(result.price, Fraction(1175, 147))
        self.assertEqual(result.boundary, (None, Fraction(80), Fraction(96)))
        down = next(node for node in result.nodes[1] if node.stock == 80)
        up = next(node for node in result.nodes[1] if node.stock == 120)
        self.assertEqual((down.intrinsic, down.continuation, down.exercise),
                         (Fraction(20), Fraction(320, 21), True))
        self.assertEqual((up.intrinsic, up.continuation, up.exercise),
                         (Fraction(0), Fraction(10, 7), False))
        self.assertEqual({node.stock for node in result.nodes[2] if node.exercise},
                         {Fraction(64), Fraction(96)})

    def test_three_period_reference_has_independently_checked_date_indices(self):
        # At t=1 only S=80 exercises; at t=2 only S=64 exercises;
        # at t=3 positive-payoff prices are 76.8 and 51.2, so the max is 76.8.
        result = exact_full_tree_decisions(**{**BASE, 'N': 3})
        self.assertEqual(result.boundary, (None, Fraction(80), Fraction(64), Fraction(384, 5)))

    def test_positive_value_tie_continues(self):
        result = exact_full_tree_decisions(**POSITIVE_TIE)
        root = result.nodes[0][0]
        self.assertEqual((root.intrinsic, root.continuation), (20, 20))
        self.assertFalse(root.exercise)
        self.assertEqual(result.boundary, (None, Fraction(90)))

    def test_zero_value_tie_continues(self):
        result = exact_full_tree_decisions(**ZERO_TIE)
        root = result.nodes[0][0]
        self.assertEqual((root.intrinsic, root.continuation), (0, 0))
        self.assertFalse(root.exercise)
        self.assertEqual(result.boundary, (None, None))

    def test_immediate_expiry_has_only_maturity_at_index_zero(self):
        for spot, expected in ((80, Fraction(80)), (100, None), (120, None)):
            with self.subTest(S0=spot):
                result = exact_full_tree_decisions(**{**BASE, 'S0': spot, 'N': 0})
                self.assertEqual(result.boundary, (expected,))


class ExerciseBoundaryTests(unittest.TestCase):
    def call(self, function, **inputs):
        try:
            return function(**inputs)
        except NotImplementedError as exc:
            raise ExerciseNotImplemented(f'PENDING_IMPLEMENTATION: {function.__name__} is pending.') from exc

    def priced(self, tree):
        result = self.call(policy.price_american_put_with_boundary, **tree)
        self.assertIsInstance(result, policy.PutExerciseResult)
        self.assertTrue(math.isfinite(result.price))
        self.assertIsInstance(result.boundary, tuple)
        self.assertEqual(len(result.boundary), tree['N']+1)
        return result

    def assert_boundary(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for t, (value, reference) in enumerate(zip(actual, expected)):
            with self.subTest(t=t):
                if reference is None:
                    self.assertIsNone(value)
                else:
                    self.assertIsNotNone(value)
                    self.assertTrue(math.isfinite(value))
                    self.assertTrue(math.isclose(value, float(reference), rel_tol=REL_TOL, abs_tol=ABS_TOL))

    def test_boundary_is_highest_exercising_node_at_every_date(self):
        for tree in (BASE, {**BASE, 'N': 3}, POSITIVE_TIE, ZERO_TIE):
            with self.subTest(tree=tree):
                reference = exact_full_tree_decisions(**tree)
                actual = self.priced(tree)
                for t, level in enumerate(reference.nodes):
                    classified = [node.stock for node in level if node.exercise]
                    expected = max(classified, default=None)
                    self.assert_boundary((actual.boundary[t],), (expected,))

    def test_root_intermediate_and_maturity_indices(self):
        for periods, expected in ((2, (None, 80, 96)), (3, (None, 80, 64, 76.8))):
            with self.subTest(N=periods):
                self.assert_boundary(self.priced({**BASE, 'N': periods}).boundary, expected)

    def test_no_exercise_region_is_explicit_none(self):
        result = self.priced(ZERO_TIE)
        self.assertEqual(result.boundary, (None, None))

    def test_positive_value_tie_uses_continuation(self):
        result = self.priced(POSITIVE_TIE)
        self.assertIsNone(result.boundary[0])
        self.assert_boundary(result.boundary, (None, 90))

    def test_zero_intrinsic_zero_continuation_is_not_exercise(self):
        result = self.priced(ZERO_TIE)
        self.assertEqual(result.price, 0)
        self.assertIsNone(result.boundary[0])

    def test_maturity_boundary_is_maximum_positive_payoff_stock(self):
        # At expiry 64 and 96 exercise; 144 has zero payoff. A minimum of 64 is wrong.
        result = self.priced(BASE)
        self.assertTrue(math.isclose(result.boundary[2], 96, rel_tol=REL_TOL, abs_tol=ABS_TOL))

    def test_expiry_boundary_has_one_entry_at_date_zero(self):
        for spot, boundary in ((80, 80), (100, None), (120, None)):
            with self.subTest(S0=spot):
                result = self.priced({**BASE, 'S0': spot, 'N': 0})
                self.assert_boundary(result.boundary, (boundary,))

    def test_companion_price_matches_existing_scalar_interface(self):
        for tree in (BASE, POSITIVE_TIE, ZERO_TIE):
            with self.subTest(tree=tree):
                result = self.priced(tree)
                scalar = self.call(american_put.price_american_put, **tree)
                self.assertTrue(math.isclose(result.price, scalar, rel_tol=REL_TOL, abs_tol=ABS_TOL))


class ObservedExerciseTests(unittest.TestCase):
    @staticmethod
    def dates(count):
        start = datetime(2026, 1, 1, 17, tzinfo=timezone.utc)
        return tuple(start + timedelta(hours=i) for i in range(count))

    def observed(self, prices, boundary, K=100, timestamps=None):
        try:
            result = policy.first_observed_exercise(
                prices, boundary, K, timestamps_utc=timestamps if timestamps is not None else self.dates(len(prices)))
        except NotImplementedError as exc:
            raise ExerciseNotImplemented('PENDING_IMPLEMENTATION: first_observed_exercise is pending.') from exc
        self.assertIsInstance(result, policy.ObservedExercise)
        return result

    def assert_decision(self, result, kind, index, payoff, prices, K=100):
        self.assertEqual(result.kind, kind)
        self.assertEqual(result.index, index)
        self.assertEqual(result.timestamp_utc, self.dates(len(prices))[index] if index is not None else None)
        self.assertEqual(result.payoff, payoff)
        if index is not None:
            self.assertEqual(result.payoff, K-prices[index])
        else:
            self.assertEqual(result.payoff, 0)

    def test_first_qualifying_date_is_returned_instead_of_later_larger_payoff(self):
        prices = (105, 95, 80, 60)
        result = self.observed(prices, (None, 96, 90, 75))
        self.assert_decision(result, 'early_exercise', 1, 5, prices)

    def test_price_equal_to_boundary_qualifies(self):
        prices = (105, 90, 120)
        self.assert_decision(self.observed(prices, (None, 90, None)), 'early_exercise', 1, 10, prices)

    def test_none_means_no_early_exercise_even_with_positive_intrinsic(self):
        prices = (80, 75, 120)
        self.assert_decision(self.observed(prices, (None, None, None)), 'never', None, 0, prices)

    def test_never_when_no_crossing_and_expiry_has_no_positive_payoff(self):
        prices = (105, 100, 110)
        self.assert_decision(self.observed(prices, (80, 90, 95)), 'never', None, 0, prices)

    def test_positive_expiry_payoff_is_maturity_settlement(self):
        prices = (110, 105, 90)
        self.assert_decision(self.observed(prices, (None, 80, 96)), 'maturity_settlement', 2, 10, prices)

    def test_off_lattice_positive_expiry_settles_without_a_boundary_crossing(self):
        prices = (110, 105, 95)
        self.assert_decision(self.observed(prices, (None, None, 92)), 'maturity_settlement', 2, 5, prices)

    def test_zero_payoff_at_expiry_is_never(self):
        prices = (110, 110, 100)
        self.assert_decision(self.observed(prices, (None, None, None)), 'never', None, 0, prices)

    def test_time_zero_exercise_is_index_zero_when_periods_remain(self):
        prices = (80, 90)
        self.assert_decision(self.observed(prices, (80, 90)), 'early_exercise', 0, 20, prices)

    def test_immediate_expiry_is_settlement_not_early_exercise(self):
        prices = (80,)
        self.assert_decision(self.observed(prices, (80,)), 'maturity_settlement', 0, 20, prices)

    def test_zero_strike_and_zero_payoffs_never_exercise(self):
        prices = (100, 110)
        self.assert_decision(self.observed(prices, (None, None), K=0), 'never', None, 0, prices, K=0)

    def test_mismatched_date_axes_are_rejected(self):
        for prices, boundary, dates in (
                ((100, 90), (None,), self.dates(2)),
                ((100, 90), (None, 95), self.dates(1)),
                ((), (), ())):
            with self.subTest(prices=prices, boundary=boundary, timestamps=dates):
                with self.assertRaises(ValueError):
                    self.observed(prices, boundary, timestamps=dates)

    def test_unordered_or_naive_dates_are_rejected(self):
        dates = self.dates(2)
        for timestamps in ((dates[1], dates[0]), (dates[0].replace(tzinfo=None), dates[1])):
            with self.subTest(timestamps=timestamps):
                with self.assertRaises(ValueError):
                    self.observed((100, 90), (None, 95), timestamps=timestamps)

    def test_zero_or_nan_is_not_a_missing_region_marker(self):
        for invalid in (0, float('nan')):
            with self.subTest(boundary=invalid):
                with self.assertRaises(ValueError):
                    self.observed((100, 110), (invalid, None))


if __name__ == '__main__':
    unittest.main()