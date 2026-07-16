#!/usr/bin/env python3
"""Focused mutation and crush-clearance checks for geo.nut_slot nibs."""
import math
import os
import sys
import unittest

import numpy as np
from trimesh.transformations import rotation_matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import checks  # noqa: E402
import geo  # noqa: E402


def coupon(size, nib):
    af, nut_t = geo.NUT[size]
    ac = geo.nut_ac(size)
    length = ac + geo.NUT_NIB_MIN_EXTRA
    seat_y = -ac / 2.0
    mouth_y = length - ac / 2.0
    lo = seat_y - 2.0
    hi = mouth_y - 0.15
    body = geo.box(af + 4.2, hi - lo, nut_t + 4.2)
    body.apply_translation((0, (lo + hi) / 2.0, 0))
    slot = geo.nut_slot((0, 0, 0), screw_axis="z", open_dir=(0, 1, 0),
                        size=size, length=length, nib=nib)
    return geo.sub(body, slot), length


class NutSlotNibTests(unittest.TestCase):
    def test_nibless_mutation_fails_and_nibbed_coupon_passes(self):
        plain, length = coupon("M3", False)
        retained, _ = coupon("M3", True)
        self.assertFalse(checks.nib_retention(
            plain, (0, 0, 0), "z", (0, 1, 0), "M3", length)[0])
        self.assertTrue(checks.nib_retention(
            retained, (0, 0, 0), "z", (0, 1, 0), "M3", length)[0])

    def test_m3_and_m4_nuts_crush_past_without_seated_interference(self):
        for size in ("M3", "M4"):
            with self.subTest(size=size):
                part, length = coupon(size, True)
                af, nut_t = geo.NUT[size]
                nut = geo.hex_prism(af, nut_t)
                nut.apply_transform(rotation_matrix(math.radians(30.0), (0, 0, 1)))
                mouth = length - geo.nut_ac(size) / 2.0
                overlaps = []
                for y in np.linspace(mouth, 0.0, 25):
                    moving = nut.copy()
                    moving.apply_translation((0, y, 0))
                    overlaps.append(float(geo.inter(part, moving).volume))
                self.assertGreater(max(overlaps), 0.01)
                self.assertLessEqual(geo.NUT_NIB_PROUD, 0.3)
                self.assertLessEqual(overlaps[-1], 0.05)


if __name__ == "__main__":
    unittest.main()
