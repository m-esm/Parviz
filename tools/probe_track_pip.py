#!/usr/bin/env python3
"""Numeric verification for the 2026-07-12 print-in-place track strips.

1. ARTICULATION SWEEP: every adjacency variant pair (mid|first|last|master) is swung
   -35..+35 deg about the shared pin (loop max is ~33.8 deg at the ramp tangents; the
   loop only ever bends the +theta way, but the strips get handled/flexed at assembly
   so both signs must be clean). Boolean-intersection volume must be 0 at every step.
2. SPROCKET vs the Ø2.0 INTEGRAL PIN (re-run of the task-15 metrics after the envelope
   regen 1.15 -> 1.275): conjugate-action penetration across a full mesh cycle, trap
   window / contact ratio, NUMERIC skip barrier (rigid chain lifted h, slid one full
   pitch over the stalled sprocket -- min h with no contact), analytic tip cap, and
   the Ø1.75 boundary-filament-pin seating depth vs the Ø2.0 pin.
3. 3D MESH SWEEP: sprocket disc rolled through 1.5 tooth pitches against 5 conjugately
   advancing ground-run links (keels + integral pins included): 0 overlap required,
   plus the keel-band vs tooth-band x-gap.

Exit 1 on any failure. Run after any track/sprocket geometry change.
"""
import os
import sys

import numpy as np
import shapely.geometry as sg
import trimesh
from trimesh.transformations import rotation_matrix as RM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import tracks                                     # noqa: E402
from params import P                              # noqa: E402

FAIL = []


def ivol(a, b):
    if not (a.bounds[1] >= b.bounds[0]).all() or not (b.bounds[1] >= a.bounds[0]).all():
        return 0.0
    m = trimesh.boolean.intersection([a, b], engine="manifold")
    if m is None or m.is_empty or len(m.faces) == 0:
        return 0.0
    return abs(float(m.volume))


def articulation_sweep():
    print("== 1. articulation sweep (-35..+35 deg about the shared pin) ==")
    pitch = P["track_pitch"]
    mid = tracks._track_link()
    first = tracks._track_link(open_a=True)
    last = tracks._track_link(open_b=True)
    mbody, mkeep = tracks._track_master_link()
    master = trimesh.util.concatenate([mbody] + mkeep)
    pairs = [                                     # (A = link i, B = link i+1): B's own
        ("mid", mid, "mid", mid),                 # pin end meets A's far end
        ("first", first, "mid", mid),
        ("mid", mid, "last", last),
        ("last", last, "first", first),           # strip-to-strip filament boundary
        ("master", master, "first", first),       # master far end -> strip 1 first
        ("last", last, "master", master),         # strip 4 last -> master jaw end
    ]
    worst = None
    for na, ma, nb, mb, in pairs:
        for th in list(np.arange(-35.0, 35.01, 2.5)) + [-33.8, 33.8]:
            b = mb.copy()
            b.apply_translation((0, pitch, 0))
            b.apply_transform(RM(np.radians(th), (1, 0, 0), (0, pitch, 0)))
            v = ivol(ma, b)
            if v > 1e-6:
                FAIL.append(f"articulation: {na}->{nb} overlap {v:.3f} mm3 at {th:+.1f} deg")
        # quote a min clearance at the extremes for the standard pair
        if (na, nb) == ("mid", "mid"):
            for th in (-35.0, 0.0, 35.0):
                b = mb.copy(); b.apply_translation((0, pitch, 0))
                b.apply_transform(RM(np.radians(th), (1, 0, 0), (0, pitch, 0)))
                pts = b.sample(3000)
                d = trimesh.proximity.signed_distance(ma, pts)
                mn = float(-d.max()) if d.max() < 0 else 0.0
                mn = float(np.abs(d).min())
                print(f"   mid->mid at {th:+5.1f} deg: min surface distance {mn:.3f} mm")
                worst = mn if worst is None else min(worst, mn)
    print(f"   all {len(pairs)} variant pairs x 30 angles: "
          f"{'CLEAN' if not FAIL else 'OVERLAPS FOUND'}")
    return worst


def _profile():
    poly = tracks._sprocket_profile()
    return poly


def _pen(poly, c, r):
    """Penetration depth of a disk (c, r) into the polygon (<=0 = clearance)."""
    p = sg.Point(c)
    if poly.contains(p):
        return r + p.distance(poly.exterior)
    return r - p.distance(poly)


def sprocket_metrics():
    print("== 2. sprocket 2D metrics (integral Ø%.1f pin, envelope r %.3f) ==" %
          (P["track_pin_print_d"], P["track_pin_print_d"] / 2 + 0.275))
    rp = P["track_wheel_r"]
    tip = P["sprocket_outer_d"] / 2
    pin_r = P["track_pin_print_d"] / 2
    pitch = P["track_pitch"]
    poly = _profile()
    # analytic numbers
    skip_cap = tip + pin_r - rp
    trap_half = np.sqrt(tip * tip - rp * rp)
    print(f"   analytic skip barrier (tip+pin-rp): {skip_cap:.3f} mm "
          f"(was 2.055 on the Ø1.75 filament pin)")
    print(f"   tip-circle trap window {2*trap_half:.2f} mm -> contact ratio "
          f"{2*trap_half/pitch:.2f} (pin-diameter independent)")
    # conjugate action across a full mesh cycle
    worst = -9e9
    for s in np.arange(0.0, pitch + 1e-9, 0.1):
        th = s / rp
        cth, sth = np.cos(-th), np.sin(-th)
        for k in range(-3, 4):
            y = k * pitch + s                     # rack coords: the generator's pin
            if abs(y) > 12:                       # rides (rp, +rp*theta)
                continue
            u, v = rp, y
            c = (cth * u - sth * v, sth * u + cth * v)
            worst = max(worst, _pen(poly, c, pin_r))
    print(f"   conjugate-action max penetration: {worst:+.3f} mm "
          f"({'CLEARANCE, zero-lift action' if worst <= 0 else 'INTERFERENCE'})")
    if worst > 0:
        FAIL.append(f"sprocket: conjugate interference {worst:.3f}")
    # numeric skip barrier: rigid chain (pins every pitch) lifted h, slid a full
    # pitch across the stalled sprocket at the worst phase
    def slide_clean(h, phase):
        for s in np.arange(0.0, pitch + 1e-9, 0.1):
            for k in range(-3, 4):
                y = phase + k * pitch + s
                if abs(y) > tip + pin_r + 1:
                    continue
                # rack = the straight line x = rp+h in profile coords (+x = BDC
                # direction, +y = track +y); pins every pitch along it
                if _pen(poly, (rp + h, y), pin_r) > 0:
                    return False
        return True
    barrier = None
    for phase in np.arange(0.0, pitch, 1.0):
        h = 0.0
        while h <= skip_cap + 0.2:
            if slide_clean(h, phase):
                break
            h += 0.02
        barrier = h if barrier is None else min(barrier, h)
    print(f"   numeric skip barrier (rigid-chain lift to slide a pitch): {barrier:.2f} mm "
          f"({barrier/0.2:.0f}x the FDM +-0.2 tolerance)")
    if barrier < 1.0:
        FAIL.append(f"sprocket: numeric skip barrier {barrier:.2f} < 1.0")
    # best-pin escape lift per phase (most-caged pin: tip circle cage depth)
    mins = []
    for s in np.arange(0.0, pitch, 0.1):
        cages = []
        for k in range(-2, 3):
            y = k * pitch + s
            r_c = np.hypot(rp, y)
            cages.append(tip + pin_r - r_c)       # lift to clear the tip circle
        mins.append(max(cages))
    print(f"   best-pin tip-cage depth: min over phase {min(mins):.2f} mm "
          f"(BDC {skip_cap:.2f})")
    # Ø1.75 boundary filament pin seating depth at BDC vs the Ø2.0 pin
    def rest_radius(r_pin):
        r = rp - 1.0
        while _pen(poly, (r, 0.0), r_pin) > 0:
            r += 0.005
        return r
    r20, r175 = rest_radius(1.0), rest_radius(0.875)
    print(f"   BDC rest radius: Ø2.0 pin {r20:.3f}  Ø1.75 pin {r175:.3f}  "
          f"delta {r20-r175:.3f} mm (chain pitch line unaffected: pins hang in the")
    print(f"   links, the delta only adds to the boundary joints' existing "
          f"{(P['track_pin_bore_d']-1.75)/2:.3f} bore slop)")
    return worst, barrier


def mesh_sweep_3d():
    print("== 3. 3D sweep: sprocket disc vs conjugately advancing keeled links ==")
    rp = P["track_wheel_r"]
    pitch = P["track_pitch"]
    zc = tracks._track_zc()
    mid = tracks._track_link()
    disc0 = tracks._sprocket_disc(8.0)
    worst_v = 0.0
    for s in np.arange(0.0, 1.5 * pitch + 1e-9, 0.75):
        th = s / rp
        disc = disc0.copy()
        disc.apply_transform(RM(th, (1, 0, 0)))
        disc.apply_translation((0, 0, zc))
        links = []
        for k in range(-2, 3):
            lk = mid.copy()
            lk.apply_translation((0, k * pitch + s, zc - rp))   # pin line z = zc - rp
            links.append(lk)
        chain = trimesh.util.concatenate(links)
        v = ivol(disc, chain)
        worst_v = max(worst_v, v)
        if v > 1e-6:
            FAIL.append(f"3D sweep: sprocket/link overlap {v:.3f} mm3 at s={s:.2f}")
    print(f"   18 phases x 5 links (keels + integral pins): max overlap {worst_v:.4f} mm3")
    ka, kb = tracks._KNUCKLES(P["track_width"])
    print(f"   tooth band |x|<=4.0 vs keel bands |x|>= {kb[1][0]:.1f}: "
          f"gap {kb[1][0]-4.0:.2f} mm (keels never see the teeth)")


if __name__ == "__main__":
    w = articulation_sweep()
    sprocket_metrics()
    mesh_sweep_3d()
    if FAIL:
        print("\nPROBE FAILURES:")
        for f in FAIL:
            print("  " + f)
        sys.exit(1)
    print("\nPROBE PASS: articulation clean, conjugate action clear, skip barrier ok, "
          "3D sweep clean")
