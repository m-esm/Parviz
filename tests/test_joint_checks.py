import os
import sys
import unittest
from unittest import mock

import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from joint_checks import MeshStore, analytic_results, fastener_results, inventory_results, mesh_results, probe_result
from jointspec import Fastener, Fit, Insertion, Joint, Locator, Probe

FIT = Fit("locating", 0.1, 0.3)


def good_joint(**changes):
    values = dict(name="fixture_joint", parts=("moving", "fixed"), structural=True,
                  assembly_axis=(0, 0, -1),
                  locator=Locator("pin_pair", 2, 4.0, FIT, True),
                  fasteners=(Fastener("M3", 2, 12.0, (0, 0, 1), 7.0,
                                      "hex_nut", 2.4, 1.0, 5.0, 8.0, 7.0, 30.0),),
                  supporting_probes=(Probe("fixed", "solid", (0, 0, 0)),))
    values.update(changes)
    return Joint(**values)


def failed_codes(results):
    return {r.gate for r in results if not r.ok}


class DictStore(MeshStore):
    def __init__(self, meshes):
        self.cache = meshes


class ContractMutationTests(unittest.TestCase):
    def test_baseline_contract_passes(self):
        self.assertFalse(failed_codes(analytic_results(good_joint())))

    def test_missing_locator_fails(self):
        codes = failed_codes(analytic_results(good_joint(locator=None)))
        self.assertIn("self-location", codes)
        self.assertIn("pre-fastener-stability", codes)

    def test_single_round_pin_leaves_rotation_free(self):
        loc = Locator("pin", 1, 4.0, FIT, False)
        self.assertIn("locator-constraints", failed_codes(analytic_results(good_joint(locator=loc))))

    def test_bad_fit_classes_fail(self):
        for fit in (Fit("magic", 0.1, 0.3), Fit("sliding", 0.4, 0.1)):
            loc = Locator("rail", 1, 4.0, fit, True)
            self.assertIn("fit-class", failed_codes(analytic_results(good_joint(locator=loc))))

    def test_bad_screw_lengths_fail_stack(self):
        for length in (8.0, 30.0):
            f = Fastener("M3", 1, length, (0, 0, 1), 7.0, "hex_nut", 2.4)
            self.assertIn("fastener-1-stack", failed_codes(fastener_results("j", 0, f)))

    def test_blocked_driver_envelope_fails(self):
        f = Fastener("M3", 1, 12.0, (0, 0, 1), 7.0, "hex_nut", 2.4,
                     head_access=5.0, driver_diameter=7.0)
        self.assertIn("fastener-1-tool-envelope", failed_codes(fastener_results("j", 0, f)))

    def test_missing_load_path_probe_fails(self):
        self.assertIn("load-path", failed_codes(analytic_results(good_joint(supporting_probes=()))))

    def test_inventory_deletion_and_duplicates_fail(self):
        with mock.patch("joint_checks.REQUIRED_STRUCTURAL_JOINTS", ("a", "b")):
            self.assertIn("structural-inventory-complete",
                          failed_codes(inventory_results((good_joint(name="a"),))))
        j = good_joint(name="a")
        with mock.patch("joint_checks.REQUIRED_STRUCTURAL_JOINTS", ("a",)):
            self.assertIn("unique-joint-ids", failed_codes(inventory_results((j, j))))


class MeshMutationTests(unittest.TestCase):
    def setUp(self):
        self.store = DictStore({"block": trimesh.creation.box((10, 10, 10))})

    def test_solid_void_and_sealed_pocket(self):
        self.assertTrue(probe_result("j", Probe("block", "solid", (0, 0, 0)), self.store, "s").ok)
        self.assertTrue(probe_result("j", Probe("block", "void", (20, 0, 0)), self.store, "v").ok)
        self.assertFalse(probe_result("j", Probe("block", "void", (0, 0, 0)), self.store, "sealed").ok)

    def test_material_ring_detects_bore_through_air(self):
        self.assertTrue(probe_result("j", Probe("block", "material_ring", (0, 0, 0), radius=3), self.store, "r").ok)
        self.assertFalse(probe_result("j", Probe("block", "material_ring", (20, 0, 0), radius=3), self.store, "r").ok)

    def test_open_path_detects_obstruction(self):
        self.assertTrue(probe_result("j", Probe("block", "open_path", (0, 0, 8), length=10), self.store, "p").ok)
        self.assertFalse(probe_result("j", Probe("block", "open_path", (0, 0, 0), length=3), self.store, "p").ok)

    def test_insertion_sweep_detects_mid_path_wall(self):
        moving = trimesh.creation.box((2, 2, 2))
        wall = trimesh.creation.box((10, 10, 1)); wall.apply_translation((0, 0, 5))
        store = DictStore({"moving": moving, "wall": wall,
                           "fixed": trimesh.creation.box((20, 20, 1))})
        j = good_joint(insertion=Insertion("moving", ("wall",), (0, 0, 1), 10.0, 11))
        self.assertIn("insertion-path", failed_codes(mesh_results(j, store)))


if __name__ == "__main__":
    unittest.main()
