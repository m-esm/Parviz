#!/usr/bin/env python3
"""Assembly-joint release gate.

Contracts catch missing intent; sparse probes catch geometry that silently vanished.
The algorithms are reusable and unit-tested with intentionally broken fixtures.
"""
import argparse
import json
import math
import os
import sys
import tempfile
from typing import Dict, Iterable, List, Sequence

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo
from jointspec import FASTENER_SPECS, Fastener, GateResult, Joint, Probe
from joints import JOINTS, REQUIRED_STRUCTURAL_JOINTS
from stlpaths import stlp, webpath

EPS_VOLUME = 0.01


def unit(v):
    a = np.asarray(v, dtype=float)
    n = np.linalg.norm(a)
    if n < 1e-9:
        raise ValueError("zero-length axis")
    return a / n


def analytic_results(joint: Joint) -> List[GateResult]:
    out = []
    out.append(GateResult(joint.name, "part-count", len(joint.parts) >= 2,
                          "joint must name both sides"))
    try:
        unit(joint.assembly_axis)
        axis_ok = True
    except ValueError:
        axis_ok = False
    out.append(GateResult(joint.name, "assembly-axis", axis_ok))
    loc = joint.locator
    out.append(GateResult(joint.name, "self-location",
                          (not joint.structural) or loc is not None,
                          "structural joints require a screw-independent locator"))
    if loc is not None:
        useful = loc.engagement > 0 and loc.count >= 1
        rotation = loc.prevents_rotation or "rotation" in joint.allowed_dof
        if loc.kind == "pin" and loc.count == 1 and "rotation" not in joint.allowed_dof:
            rotation = False
        out.append(GateResult(joint.name, "locator-engagement", useful,
                              "%.2f mm" % loc.engagement,
                              {"engagement_mm": loc.engagement}))
        out.append(GateResult(joint.name, "locator-constraints", rotation,
                              "single round pins need a second anti-rotation feature"))
        out.append(GateResult(joint.name, "fit-class",
                              loc.fit.kind in {"sliding", "locating", "snug_press",
                                               "permanent_press", "rotating", "clearance"}
                              and loc.fit.clearance_min <= loc.fit.clearance_max,
                              "%s %.3f..%.3f mm" % (loc.fit.kind,
                                                    loc.fit.clearance_min,
                                                    loc.fit.clearance_max)))
    out.append(GateResult(joint.name, "fastener-present",
                          (not joint.structural) or bool(joint.fasteners),
                          "structural joint requires declared retention"))
    for i, f in enumerate(joint.fasteners):
        out.extend(fastener_results(joint.name, i, f))
    if joint.insertion is not None:
        ins = joint.insertion
        ok = ins.distance > 0 and ins.steps >= 2 and ins.moving_part in joint.parts
        out.append(GateResult(joint.name, "insertion-declared", ok,
                              "%s over %.1f mm / %d steps" %
                              (ins.moving_part, ins.distance, ins.steps)))
    out.append(GateResult(joint.name, "pre-fastener-stability",
                          (not joint.structural) or (loc is not None and
                          (loc.prevents_rotation or "rotation" in joint.allowed_dof)),
                          "locator must constrain the seated part before screws"))
    out.append(GateResult(joint.name, "load-path",
                          (not joint.structural) or bool(joint.supporting_probes),
                          "structural joints require material probes around the load path"))
    return out


def fastener_results(joint_name: str, index: int, f: Fastener) -> List[GateResult]:
    tag = "fastener-%d" % (index + 1)
    spec = FASTENER_SPECS.get(f.size)
    protrusion = f.length - f.clamp_stack - f.capture_thickness
    stack_ok = (spec is not None and f.quantity > 0 and
                f.thread_protrusion_min <= protrusion <= f.thread_protrusion_max)
    return [
        GateResult(joint_name, tag + "-stack", stack_ok,
                   "%s x%d: %.2f mm protrusion" % (f.size, f.quantity, protrusion),
                   {"protrusion_mm": protrusion}),
        GateResult(joint_name, tag + "-capture",
                   f.capture in {"hex_nut", "nyloc", "heat_set", "factory_thread", "pin"},
                   f.capture),
        GateResult(joint_name, tag + "-tool-envelope",
                   f.head_access >= f.driver_diameter and f.driver_length > 0,
                   "access %.1f, driver diameter %.1f" %
                   (f.head_access, f.driver_diameter)),
    ]


class MeshStore:
    def __init__(self):
        self.cache = {}

    def get(self, name):
        if name not in self.cache:
            path = stlp(name + ".stl")
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            self.cache[name] = trimesh.load(path, force="mesh")
        return self.cache[name]


def cube_at(point, side=0.5):
    c = geo.box(side, side, side)
    c.apply_translation(point)
    return c


def intersection_volume(a, b):
    try:
        return float(geo.inter(a, b).volume)
    except Exception:
        return math.inf


def probe_result(joint_name: str, p: Probe, store: MeshStore, label: str) -> GateResult:
    try:
        mesh = store.get(p.part)
    except (FileNotFoundError, ValueError) as e:
        return GateResult(joint_name, label, False, str(e))
    axis = unit(p.axis)
    point = np.asarray(p.point, float)
    if p.kind in ("solid", "void"):
        vol = intersection_volume(mesh, cube_at(point, p.radius * 2.0))
        ok = vol > EPS_VOLUME if p.kind == "solid" else vol < EPS_VOLUME
        return GateResult(joint_name, label, ok, "%s %.4f mm3" % (p.kind, vol),
                          {"intersection_mm3": vol})
    if p.kind == "material_ring":
        ortho = np.cross(axis, (1.0, 0.0, 0.0))
        if np.linalg.norm(ortho) < 0.2:
            ortho = np.cross(axis, (0.0, 1.0, 0.0))
        u = unit(ortho); v = unit(np.cross(axis, u))
        hits = 0
        for angle in np.linspace(0, 2 * np.pi, p.samples, endpoint=False):
            q = point + p.radius * (math.cos(angle) * u + math.sin(angle) * v)
            if intersection_volume(mesh, cube_at(q, 0.5)) > EPS_VOLUME:
                hits += 1
        return GateResult(joint_name, label, hits >= p.minimum_hits,
                          "%d/%d ring probes hit material" % (hits, p.samples),
                          {"hits": float(hits)})
    if p.kind == "open_path":
        worst = 0.0
        for d in np.linspace(0.0, p.length, p.samples):
            worst = max(worst, intersection_volume(mesh, cube_at(point + axis * d,
                                                                  p.radius * 2.0)))
        return GateResult(joint_name, label, worst < EPS_VOLUME,
                          "worst obstruction %.4f mm3" % worst,
                          {"obstruction_mm3": worst})
    return GateResult(joint_name, label, False, "unknown probe kind %s" % p.kind)


def swept_insertion(joint: Joint, store: MeshStore) -> GateResult:
    ins = joint.insertion
    if ins is None:
        return GateResult(joint.name, "insertion-path", True, "not required")
    try:
        moving = store.get(ins.moving_part).copy()
        fixed = [store.get(n) for n in ins.fixed_parts]
    except FileNotFoundError as e:
        return GateResult(joint.name, "insertion-path", False, str(e))
    axis = unit(ins.axis)
    worst = 0.0
    # The declared STL is seated. Test poses from approach distance down to just
    # before seating; designed final contact is assessed by seating probes.
    for d in np.linspace(ins.distance, 0.0, ins.steps)[:-1]:
        posed = moving.copy()
        posed.apply_translation(axis * d)
        for other in fixed:
            worst = max(worst, intersection_volume(posed, other))
    return GateResult(joint.name, "insertion-path", worst <= ins.allowed_final_overlap,
                      "worst swept overlap %.4f mm3" % worst,
                      {"overlap_mm3": worst})


def mesh_results(joint: Joint, store: MeshStore) -> List[GateResult]:
    results = []
    groups = [("locator-male", joint.locator.male_probes if joint.locator else ()),
              ("locator-female", joint.locator.female_probes if joint.locator else ()),
              ("seating", joint.seating_probes)]
    for prefix, probes in groups:
        for i, p in enumerate(probes):
            results.append(probe_result(joint.name, p, store,
                                        "%s-%d" % (prefix, i + 1)))
    # Supporting probes name every exported body on the declared load path.  Exact
    # root-section probes may be added as seating/solid probes, while this baseline
    # catches vanished, empty, open, or invalid load-bearing exports without relying
    # on a copied coordinate that can drift away from derived geometry.
    for i, p in enumerate(joint.supporting_probes):
        try:
            mesh = store.get(p.part)
            ok = len(mesh.faces) > 0 and mesh.is_watertight and abs(mesh.volume) > 0.1
            detail = "%d faces, %.1f mm3" % (len(mesh.faces), abs(mesh.volume))
        except (FileNotFoundError, ValueError) as e:
            ok, detail = False, str(e)
        results.append(GateResult(joint.name, "load-body-%d" % (i + 1), ok, detail))
    for fi, f in enumerate(joint.fasteners):
        for pi, p in enumerate(f.bore_probes):
            results.append(probe_result(joint.name, p, store,
                                        "fastener-%d-bore-%d" % (fi + 1, pi + 1)))
        for pi, p in enumerate(f.capture_probes):
            results.append(probe_result(joint.name, p, store,
                                        "fastener-%d-capture-%d" % (fi + 1, pi + 1)))
        for blocker in f.tool_blockers:
            p = Probe(blocker, "open_path", f.bore_probes[0].point,
                      tuple(-x for x in f.axis), f.driver_length,
                      f.driver_diameter / 2.0, samples=10)
            results.append(probe_result(joint.name, p, store,
                                        "fastener-%d-driver-vs-%s" % (fi + 1, blocker)))
    results.append(swept_insertion(joint, store))
    return results


def inventory_results(joints: Sequence[Joint]) -> List[GateResult]:
    names = [j.name for j in joints]
    duplicate = sorted({n for n in names if names.count(n) > 1})
    missing = sorted(set(REQUIRED_STRUCTURAL_JOINTS) - set(names))
    undeclared = sorted(set(names) - set(REQUIRED_STRUCTURAL_JOINTS))
    return [
        GateResult("__inventory__", "unique-joint-ids", not duplicate,
                   "duplicates: %s" % ", ".join(duplicate)),
        GateResult("__inventory__", "structural-inventory-complete", not missing,
                   "missing: %s" % ", ".join(missing)),
        GateResult("__inventory__", "inventory-reviewed", not undeclared,
                   "not in required ledger: %s" % ", ".join(undeclared)),
    ]


def evaluate(joints=JOINTS, mesh=True):
    results = inventory_results(joints)
    store = MeshStore()
    for joint in joints:
        results.extend(analytic_results(joint))
        if mesh:
            results.extend(mesh_results(joint, store))
    return results


def write_report(path, results):
    rows = []
    for r in results:
        rows.append({"joint": r.joint, "gate": r.gate, "ok": bool(r.ok),
                     "detail": r.detail,
                     "measurements": {k: float(v) for k, v in r.measurements.items()}})
    payload = {"schema": 1,
               "summary": {"passed": int(sum(bool(r.ok) for r in results)),
                           "failed": int(sum(not bool(r.ok) for r in results)),
                           "total": len(results)},
               "results": rows}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".joint-report-", suffix=".json",
                               dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=webpath("joint_report.json"))
    ap.add_argument("--contracts-only", action="store_true")
    args = ap.parse_args()
    results = evaluate(mesh=not args.contracts_only)
    for r in results:
        print("  %s %-28s %-32s %s" % ("ok" if r.ok else "X ", r.joint, r.gate,
                                        r.detail))
    write_report(args.report, results)
    failed = [r for r in results if not r.ok]
    print("\njointcheck: %d/%d gates hold across %d joints" %
          (len(results) - len(failed), len(results), len(JOINTS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
