import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from params import P
from standins import STANDINS
from standins import f688_bushing, foot_pin, m4_bolt, m4_nut, m8_bolt, m8_nut
from standins import m8_washer, pan_ring, seam_dowel, tilt_axle


class HardwareStandinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meshes = {name: build() for name, (build, _count) in STANDINS.items()}

    def test_every_export_is_one_watertight_printable_body(self):
        for name, mesh in self.meshes.items():
            with self.subTest(name=name):
                self.assertTrue(mesh.is_watertight)
                self.assertTrue(mesh.is_volume)
                self.assertEqual(mesh.body_count, 1)

    def test_counts_match_functional_stack(self):
        self.assertEqual(m4_bolt.COUNT, 10)
        self.assertEqual(m4_nut.COUNT, 10)
        self.assertEqual(m8_bolt.COUNT, 4)
        self.assertEqual(m8_nut.COUNT, 8)  # inner + outboard jam nut per end axle
        self.assertEqual(m8_washer.COUNT, 4)
        self.assertEqual(f688_bushing.COUNT, 8)
        self.assertEqual(pan_ring.COUNT, P["pan_race_n"] + 2)

    def test_m8_thread_spans_both_nuts_and_tower(self):
        self.assertAlmostEqual(m8_bolt.JOURNAL_L, 40.4, places=6)
        self.assertAlmostEqual(m8_bolt.THREAD_L, 29.6, places=6)
        self.assertAlmostEqual(m8_bolt.JOURNAL_L + m8_bolt.THREAD_L, 70.0, places=6)
        self.assertGreaterEqual(m8_bolt.THREAD_L,
                                m8_nut.H * 2 + 8.0 + m8_washer.T)

    def test_rolling_and_locating_interfaces_are_compensated(self):
        self.assertGreater(f688_bushing.BORE_D, m8_bolt.SHANK_D)
        self.assertLess(tilt_axle.AXLE_PRINT_D, P["axle_d"])
        self.assertLess(seam_dowel.D, 4.0)
        self.assertEqual(foot_pin.D, 3.0)
        self.assertLess(pan_ring.CROWN_D, P["pan_race_ball_d"])

    def test_nuts_match_captive_wrench_dimensions(self):
        self.assertEqual(m4_nut.AF, 7.0)
        self.assertEqual(m8_nut.AF, 13.0)
        self.assertEqual(m8_washer.AF, 13.0)


if __name__ == "__main__":
    unittest.main()
