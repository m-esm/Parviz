"""Unit tests for steppers.py (dry-run, no GPIO, runs anywhere).

Run:  python3 -m unittest software/motion/test_steppers.py -v
  or: cd software/motion && python3 -m unittest test_steppers -v
"""

import unittest

from steppers import (
    HALF_STEP_SEQUENCE,
    LimitedStepper,
    PanStepper,
    TiltStepper,
)

PINS = (17, 18, 27, 22)


def mk(limit=88.0, **kw):
    kw.setdefault("dry_run", True)
    return LimitedStepper(pins=PINS, limit_deg=limit, **kw)


class TestSequence(unittest.TestCase):
    def test_half_step_table_shape(self):
        self.assertEqual(len(HALF_STEP_SEQUENCE), 8)
        for pat in HALF_STEP_SEQUENCE:
            self.assertEqual(len(pat), 4)
            self.assertIn(sum(pat), (1, 2))  # alternates 1-coil / 2-coil

    def test_adjacent_patterns_differ_by_one_coil(self):
        # Half-stepping toggles exactly one coil between neighbors (cyclically).
        for i in range(8):
            a = HALF_STEP_SEQUENCE[i]
            b = HALF_STEP_SEQUENCE[(i + 1) % 8]
            diff = sum(x != y for x, y in zip(a, b))
            self.assertEqual(diff, 1, f"patterns {i}->{(i + 1) % 8}")

    def test_forward_walks_sequence_in_order(self):
        s = mk()
        s.move_to(s.steps_to_angle(8))  # exactly 8 half-steps forward
        # trace = 8 step patterns + final release(0,0,0,0)
        self.assertEqual(len(s.trace), 9)
        expected = [HALF_STEP_SEQUENCE[(1 + i) % 8] for i in range(8)]
        self.assertEqual(s.trace[:8], expected)
        self.assertEqual(s.trace[-1], (0, 0, 0, 0))

    def test_backward_walks_sequence_in_reverse(self):
        s = mk()
        s.move_to(s.steps_to_angle(-3), hold=True)
        expected = [HALF_STEP_SEQUENCE[(-1 - i) % 8] for i in range(3)]
        self.assertEqual(s.trace, expected)

    def test_invert_flips_electrical_direction(self):
        s = mk(invert=True)
        s.move_to(s.steps_to_angle(2), hold=True)
        # Positive axis motion, inverted electrics: sequence walks backward.
        self.assertEqual(
            s.trace, [HALF_STEP_SEQUENCE[-1 % 8], HALF_STEP_SEQUENCE[-2 % 8]]
        )
        self.assertEqual(s._pos_steps, 2)  # axis position still +2

    def test_there_and_back_returns_to_start_pattern_index(self):
        s = mk()
        s.move_to(10, hold=True)
        s.move_to(0, hold=True)
        self.assertEqual(s._seq_idx, 0)
        self.assertEqual(s._pos_steps, 0)


class TestClamping(unittest.TestCase):
    def test_move_to_clamps_high(self):
        s = mk(limit=88)
        reached = s.move_to(120)
        self.assertAlmostEqual(reached, 88.0, delta=0.1)

    def test_move_to_clamps_low(self):
        s = mk(limit=88)
        reached = s.move_to(-500)
        self.assertAlmostEqual(reached, -88.0, delta=0.1)

    def test_relative_moves_cannot_creep_past_limit(self):
        s = mk(limit=88)
        for _ in range(10):
            s.move_by(30)
        self.assertLessEqual(s.position_deg, 88.0 + 1e-9)
        self.assertAlmostEqual(s.position_deg, 88.0, delta=0.1)

    def test_step_count_never_exceeds_limit_steps(self):
        s = mk(limit=88)
        s.move_to(10000)
        self.assertLessEqual(abs(s._pos_steps), s.angle_to_steps(88.0))

    def test_in_range_target_untouched(self):
        s = mk(limit=88)
        reached = s.move_to(45)
        self.assertAlmostEqual(reached, 45.0, delta=0.1)

    def test_pan_default_limit_is_88(self):
        p = PanStepper(pins=PINS, dry_run=True)
        self.assertEqual(p.limit_deg, 88.0)
        self.assertAlmostEqual(p.move_to(90), 88.0, delta=0.1)

    def test_tilt_default_limit_is_30(self):
        t = TiltStepper(pins=PINS, dry_run=True)
        self.assertEqual(t.limit_deg, 30.0)
        self.assertAlmostEqual(t.move_to(-90), -30.0, delta=0.1)

    def test_limit_is_constructor_param(self):
        p = PanStepper(pins=PINS, limit_deg=45, dry_run=True)
        self.assertAlmostEqual(p.move_to(60), 45.0, delta=0.1)


class TestGearing(unittest.TestCase):
    def test_tilt_gear_ratio_multiplies_steps(self):
        t = TiltStepper(pins=PINS, dry_run=True)  # ratio 12
        flat = LimitedStepper(pins=PINS, limit_deg=30, dry_run=True)
        self.assertEqual(t.steps_per_axis_rev, 12 * flat.steps_per_axis_rev)
        # A full axis rev is exact (no rounding): 4096 * 12 half-steps.
        self.assertEqual(t.angle_to_steps(360), 49152)

    def test_round_trip_angle_steps(self):
        s = mk()
        for deg in (0, 1, -1, 45.5, -88, 88):
            self.assertAlmostEqual(
                s.steps_to_angle(s.angle_to_steps(deg)), deg, delta=0.05
            )


class TestConstruction(unittest.TestCase):
    def test_pins_required_and_validated(self):
        with self.assertRaises(ValueError):
            LimitedStepper(pins=(1, 2, 3), limit_deg=88, dry_run=True)
        with self.assertRaises(ValueError):
            LimitedStepper(pins=(1, 1, 2, 3), limit_deg=88, dry_run=True)
        with self.assertRaises(ValueError):
            LimitedStepper(pins=PINS, limit_deg=0, dry_run=True)

    def test_dry_run_never_imports_lgpio(self):
        import sys
        self.assertNotIn("lgpio", sys.modules)
        s = mk()
        s.move_to(5)
        self.assertNotIn("lgpio", sys.modules)

    def test_release_writes_all_zero(self):
        s = mk()
        s.release()
        self.assertEqual(s.trace[-1], (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
