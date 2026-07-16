"""The real (downloaded) 28BYJ mesh must land with its SHAFT on the placeholder's
shaft axis -- the hard datum every gear is keyed to. The old OBB best-fit parked it
~15 mm off (2026-07-16, user: "motors mounted wrongly to the gears"); refparts now
recovers the placeholder's exact pose by Kabsch over the vertex correspondence and
registers the real mesh with a fixed measured native->local transform. This test
poses a pristine placeholder at arbitrary rigid transforms and asserts the real
mesh's shaft tip tracks the placeholder's within the mesh's own 0.125 mm
eccentricity slop (real 8.0 vs spec 7.875) plus fit tolerance."""
import os
import sys
import unittest

import numpy as np
from trimesh.transformations import rotation_matrix as R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import refparts
from motors import motor_28byj
from params import P


def shaft_tip(mesh, axis_dir):
    """Centroid of the extreme vertex cluster along the unit vector axis_dir."""
    v = np.asarray(mesh.vertices)
    c = v @ axis_dir
    return v[c > c.max() - 2.0].mean(axis=0)


class Refparts28byjTests(unittest.TestCase):
    def test_real_shaft_tracks_placeholder_shaft_across_poses(self):
        poses = [
            np.eye(4),
            R(np.radians(90), (0, 0, 1)) @ R(np.radians(-90), (1, 0, 0)),
            R(np.radians(37), (0, 1, 0)) @ R(np.radians(211), (0, 0, 1)),
        ]
        for i, T in enumerate(poses):
            T = T.copy()
            T[:3, 3] = (13.0 * i - 5.0, 7.0 - 2.0 * i, 40.0 + 11.0 * i)
            ph = motor_28byj("motor_probe")
            ph.apply_transform(T)
            real = refparts.fit_real("28byj", ph, "motor_probe")
            axis_dir = T[:3, :3] @ np.array([0.0, 0.0, 1.0])   # local shaft dir +Z
            pt, rt = shaft_tip(ph, axis_dir), shaft_tip(real, axis_dir)
            # compare radially (perpendicular to the shaft axis): the real mesh is
            # deliberately shorter along the axis than the old placeholder was.
            d = (rt - pt) - np.dot(rt - pt, axis_dir) * axis_dir
            with self.subTest(pose=i):
                self.assertLess(float(np.linalg.norm(d)), 0.3)

    def test_pose_recovery_rejects_non_pristine_meshes(self):
        # A mesh that is not a rigidly-transformed motor_28byj must fall back
        # (return None), never a wrong "exact" pose.
        ph = motor_28byj("motor_probe")
        ph = ph.slice_plane((0, 0, 5.0), (0, 0, 1.0), cap=True)
        self.assertIsNone(refparts._pose_28byj(ph))


if __name__ == "__main__":
    unittest.main()
