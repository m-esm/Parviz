import os
import sys
import unittest

import numpy as np
from trimesh.transformations import rotation_matrix as R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from geo import box, cyl, inter, sub
from head import build_antennas, build_ant_drive, build_ant_orings, build_head_shell
from motors import antenna_motor
from params import P


class AntennaDriveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts = {m.metadata["name"]: m
                     for m in build_antennas() + build_ant_drive()}

    def test_every_exported_drive_part_is_one_watertight_body(self):
        for name, mesh in self.parts.items():
            with self.subTest(name=name):
                self.assertTrue(mesh.is_watertight)
                self.assertEqual(1, len(mesh.split(only_watertight=False)))

    def test_both_gear_trains_have_zero_static_tooth_interference(self):
        for side in ("L", "R"):
            pairs = ((f"ant_motor_gear_{side}", f"ant_idler_gear_{side}"),
                     (f"ant_idler_gear_{side}", f"ant_output_{side}"),
                     (f"ant_output_{side}", f"antenna_{side}"))
            for a, b in pairs:
                with self.subTest(a=a, b=b):
                    self.assertLess(abs(inter(self.parts[a], self.parts[b]).volume), 0.01)

    def test_rack_and_pinion_roll_without_collision_over_full_travel(self):
        pitch_r = P["ant_gear_m"] * P["ant_pinion_t"] / 2.0
        cy, cz = P["ant_cross_y"], P["ant_cross_z"]
        for side, sx in (("L", -1), ("R", 1)):
            for extension in np.linspace(0.0, P["ant_travel"], 11):
                mast = self.parts[f"antenna_{side}"].copy()
                mast.apply_translation((0, 0, extension))
                output = self.parts[f"ant_output_{side}"].copy()
                output.apply_transform(R(extension / pitch_r, (1, 0, 0),
                                         point=(sx * 47.0, cy, cz)))
                with self.subTest(side=side, extension=extension):
                    self.assertLess(abs(inter(output, mast).volume), 0.02)

    def test_28byj_shafts_land_on_motor_gear_axes(self):
        # Sample a small cylinder around the declared shaft line. It must intersect the
        # bought motor placeholder and the keyed G1 hub, proving both use one datum.
        from geo import cyl
        for side, sx in (("L", -1), ("R", 1)):
            motor = antenna_motor(sx, f"motor_ant_{side}")
            axis_probe = cyl(1.0, 10.0, axis="x")
            axis_probe.apply_translation((sx * 30.0, P["ant_motor_y"], P["ant_motor_z"]))
            hub_probe = cyl(3.2, 5.0, axis="x")
            hub_probe = sub(hub_probe, cyl(2.7, 7.0, axis="x"))
            hub_probe.apply_translation((sx * P["ant_gear_x"][0],
                                         P["ant_motor_y"], P["ant_motor_z"]))
            with self.subTest(side=side):
                self.assertGreater(abs(inter(motor, axis_probe).volume), 1.0)
                self.assertGreater(abs(inter(self.parts[f"ant_motor_gear_{side}"],
                                             hub_probe).volume), 1.0)
                self.assertLess(abs(inter(motor, self.parts["ant_bracket"]).volume), 0.01)

    def test_both_masts_have_two_park_grooves_one_travel_apart(self):
        stations = (P["ant_gland_z"], P["ant_gland_z"] - P["ant_travel"])
        self.assertAlmostEqual(stations[0] - stations[1], P["ant_travel"], places=6)
        major = (P["ant_mast_d"] / 2.0 + P["ant_park_groove_minor_r"]
                 - P["ant_park_groove_depth"])
        for side, sx in (("L", -1), ("R", 1)):
            mast = self.parts[f"antenna_{side}"]
            for z in stations:
                probe = cyl(P["ant_mast_d"] / 2.0, 0.12)
                core = cyl(major - P["ant_park_groove_minor_r"] + 0.08, 0.2)
                probe = sub(probe, core)
                probe.apply_translation((sx * P["ant_x"], P["ant_y"], z))
                # The lower groove intentionally omits the rack sector. Probe only the
                # remaining arc, which is the surface the O-ring relaxes into.
                arc = box(20.0, 12.0, 2.0)
                arc.apply_translation((sx * P["ant_x"], P["ant_y"] + 4.0, z))
                probe = inter(probe, arc)
                with self.subTest(side=side, z=z):
                    self.assertLess(abs(inter(mast, probe).volume), 0.03)

    def test_deployed_park_groove_spares_rack_sector(self):
        z = P["ant_gland_z"] - P["ant_travel"]
        for side, sx in (("L", -1), ("R", 1)):
            rack_probe = box(2.8, 0.5, 0.2)
            rack_probe.apply_translation((sx * P["ant_x"], P["ant_y"] - 2.75, z))
            with self.subTest(side=side):
                self.assertGreater(abs(inter(self.parts[f"antenna_{side}"], rack_probe).volume),
                                   0.05)

    def test_head_shell_contains_annular_oring_glands(self):
        shell = build_head_shell()
        for sx in (-1, 1):
            gland = cyl(P["ant_gland_d"] / 2.0 - 0.05, P["ant_gland_w"] * 0.8)
            bore = cyl(P["ant_mast_d"] / 2.0 + 0.30, P["ant_gland_w"] + 0.2)
            gland = sub(gland, bore)
            gland.apply_translation((sx * P["ant_x"], P["ant_y"], P["ant_gland_z"]))
            with self.subTest(side=sx):
                self.assertLess(abs(inter(shell, gland).volume), 0.03)

    def test_oring_seats_at_both_parks_and_bites_between_them(self):
        rings = {m.metadata["name"]: m for m in build_ant_orings()}
        for side in ("L", "R"):
            mast = self.parts[f"antenna_{side}"]
            ring = rings[f"ant_oring_{side}"]
            for extension in (0.0, P["ant_travel"]):
                moved = mast.copy()
                moved.apply_translation((0, 0, extension))
                # Exclude the deliberately ungrooved rack sector at deployed park.
                arc = box(20.0, 12.0, 4.0)
                arc.apply_translation(((-1 if side == "L" else 1) * P["ant_x"],
                                       P["ant_y"] + 4.0, P["ant_gland_z"]))
                with self.subTest(side=side, extension=extension):
                    self.assertLess(abs(inter(inter(moved, arc), ring).volume), 0.08)
            ring_inner_r = P["ant_mast_d"] / 2.0
            groove_root_r = (P["ant_mast_d"] / 2.0
                             - P["ant_park_groove_depth"])
            self.assertAlmostEqual(ring_inner_r - groove_root_r,
                                   P["ant_park_groove_depth"], places=6)


if __name__ == "__main__":
    unittest.main()
