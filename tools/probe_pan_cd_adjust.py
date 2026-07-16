#!/usr/bin/env python3
"""Probe the complete pan pedestal adjustment against fixed assembly geometry."""
import os
import sys

import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import geo
from params import P

MOVING = {"chassis_pedestal", "motor_pan", "pan_gears"}
# The platform pinion is the gear being adjusted against, so tooth contact is not
# a surrounding-structure collision. Its backlash is set by the documented feeler.
EXCLUDE = {"pan_platform"}
EPS = 0.01


def world_meshes(path):
    scene = trimesh.load(path, force="scene")
    out = {}
    for node in scene.graph.nodes_geometry:
        tf, geom = scene.graph.get(node)
        mesh = scene.geometry[geom].copy()
        mesh.apply_transform(tf)
        out[node] = mesh
    return out


def bounds_overlap(a, b):
    return bool(np.all(a.bounds[0] <= b.bounds[1]) and np.all(b.bounds[0] <= a.bounds[1]))


def overlap(a, b):
    if not bounds_overlap(a, b):
        return 0.0
    try:
        return float(geo.inter(a, b).volume)
    except Exception:
        return float("inf")


def main():
    meshes = world_meshes(os.path.join(ROOT, "web", "assembly.glb"))
    fixed = {n: m for n, m in meshes.items() if n not in MOVING and n not in EXCLUDE}
    baseline = {(mn, fn): overlap(meshes[mn], fm)
                for mn in MOVING for fn, fm in fixed.items()}
    failed = False
    travel = P["pan_cd_adjust"]
    print("pan CD adjust interference probe: moving pedestal + motor + 32T gear")
    for dx in (-travel, travel):
        new_contacts = []
        candidates = 0
        for mn in sorted(MOVING):
            moved = meshes[mn].copy()
            moved.apply_translation((dx, 0.0, 0.0))
            for fn, fm in fixed.items():
                if not bounds_overlap(moved, fm):
                    continue
                candidates += 1
                vol = overlap(moved, fm)
                if baseline[(mn, fn)] <= EPS and vol > EPS:
                    new_contacts.append((mn, fn, vol))
        print("  X=%+.3f mm: %d broad-phase pairs, %d new contacts" %
              (dx, candidates, len(new_contacts)))
        for mn, fn, vol in new_contacts:
            print("    FAIL %s vs %s: %.4f mm3" % (mn, fn, vol))
        failed = failed or bool(new_contacts)
    if failed:
        print("FAIL: adjustment creates surrounding-structure contact")
        return 1
    print("PASS: no new contact at either adjustment extreme")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
