"""hw_m4_bolt plastic stand-in. See the package docstring for rationale + LOAD LIMITS.

M4x40 ROAD-WHEEL BOLT-AXLE, as a real SHOULDER BOLT (2026-07-16, user: "as functional
and as close to reality of their metal counterparts as possible").

Was `_bolt(1.95, 40.0, 3.5, 3.5)`: a plain Ø3.9 rod with a Ø7 button, no thread. The
owned steel M4 nut -- and the printed hw_m4_nut in its slide-up slot -- threaded onto
nothing, so the "bolt" was a push-in pin that gravity and friction held.

WHY PARTIALLY THREADED (docs/ASSEMBLY.md hard M4x40 shank spec): the road wheel
ROTATES on this axle. Thread under the wheel means the wheel rides on 60-deg crests
-- a 5-point line contact that machines its own Ø4.2 PLA bore into a spiral. Full-
thread kits and stock DIN 931 M4x40 (plain shank ~20 mm) are REJECTED. So the shank
is a PLAIN Ø3.9 JOURNAL where the wheel runs, and the thread is confined to the tail
that reaches the captive nut.

THE SHOULDER IS THE AXIAL STOP -- this is the part that makes the joint work, and it
falls out of the two diameters for free:

    journal Ø3.900   >   nut thread minor Ø3.204  (threads.py internal form, M4/1.0/0.25)

The journal physically cannot enter the nut, so it BOTTOMS on the nut's outboard face.
That matters because the nut here is CAPTIVE in the beam's slide-up slot (chassis.py):
there is no "tighten until snug" -- without a shoulder, screwing the bolt home would
drag the head down onto the wheel and clamp it against the beam, and the wheel would
stop turning. With the shoulder, torque is reacted shoulder -> nut -> slot inner wall,
entirely inboard of the wheel, and the wheel stays free NO MATTER HOW HARD IT IS DONE
UP. Run it in until it stops; that is the design.

VERIFIED STACK (2026-07-16 K1 re-probe; R side world x from tracks.py axle_hw +
chassis.py beam; under-head = distance from head underside toward tip):
    head underside at x 111.4; tip at x 71.4; total under-head length 40.0
    0.00..30.00  ROAD WHEEL hub, 30.0 wide, Ø4.2 bore   <- MUST stay plain journal
   30.00..31.00  1.0 running gap beam outer face (x 80.4) -> wheel inner face
   29.70..41.70  beam bore Ø4.4 (cut center x 75.7, len 12; teardrop in chassis.py)
   33.95..37.15  M4 nut t=3.2 seated in slide-up slot (outboard face = shoulder seat)
   40.00         tip (2.85 past nut inboard face)

Local z from head OUTER face (local z = 114.9 - x_world, head-down print frame):
    0.00.. 3.50  head
    3.50..33.50  ROAD WHEEL, Ø4.2 bore          <- journal, must stay plain
   33.20..45.20  beam bore Ø4.4                 <- journal, then thread
   37.40..41.00  nut slide-up slot, 3.6 wide (a 3.2 nut has 0.4 of axial play)
The nut is pushed inboard onto the slot's inner wall (local 41.00), so its outboard
face -- the shoulder seat -- sits at 41.00 - t_nut.

METAL PURCHASE plain-shank range under head (M4x40, 40 mm under-head total):
    MIN 34.0 mm  covers full wheel + gap + beam path to the nut outboard face;
                 thread never enters the Ø4.2 wheel bore
    MAX 35.5 mm  leaves >= 4.5 mm threaded tail; with tip at 40 and nut inboard at
                 37.15, engagement >= 1.65 mm = more than 2 full turns of M4x0.7
                 (1.4 mm). At the printed 1.0 pitch this part uses, 2 turns = 2.0 mm
                 and engagement at JOURNAL_L=34.7 is 2.45 mm.
Stand-in values (unchanged after K1 verify; no drift):
    JOURNAL_L = 34.7   plain Ø3.9 (inside 34.0..35.5)
    THREAD_L  =  5.3   M4x1.0 printed form

REJECT: full-thread M4x40 kits; stock DIN 931 / ISO 4014 M4x40 (nominal plain shank
~18..20 mm starts thread inside the wheel). REJECT Ø5 shoulder screws: wheel bore is
Ø4.2 and beam bore is Ø4.4, neither accepts a Ø5 shoulder.

JOURNAL LENGTH is picked so the head can NEVER reach the wheel, across the whole range
of nut thickness the 3.6 slot admits (hw_m4_nut is a sibling module; we coordinate only
through threads.py defaults, so its thickness is not ours to assume):
    t_nut 3.00..3.55  ->  shoulder seat local 37.45..38.00
    head underside     =  seat - 34.70  =  local 2.75..3.30   (wheel face is at 3.50)
i.e. 0.20..0.75 of head-to-wheel gap, never negative. Wheel axial float goes 1.00 ->
1.20..1.75, which is rattle, not a fault. Erring the other way (a journal 0.3 short)
locks the wheel, so the asymmetry is deliberate.

SHOULDER BEARING is small by construction -- the seat annulus is nut-minor r1.602 to
journal r1.950 = 3.9 mm2 -- because anything wider than Ø4.4 could not pass the beam
bore to reach the nut. Hand-tight on the Ø10.4 knurl (~0.1 Nm -> ~150 N) puts ~38 MPa
there, near PLA yield: expect the shoulder to bed in ~0.1 mm on first assembly and then
stop. Self-limiting (seating deeper only opens the head gap further), but do not put a
driver on it and lean.

HEAD: Ø10.4 knurled thumb head + a flat-blade slot, NOT the real M4's AF7 hex. Reasons:
(1) Ø10.4 is exactly the wheel's hub-boss OD -- probed solid r2.1..5.2 at the outer
face, with the dish void r5.2..7.8 outside it -- so the head caps the boss it bears on
and its rim dies into the dish wall; (2) AF7 in PLA needs a 7 mm spanner on a fastener
that wants ~0.1 Nm, and the corners round off after a few cycles; (3) probed clear:
nothing is within r6.5 of the axle outboard of the wheel at any of the 5 stations, so
the head is free to be grippable. The slot is the break-loose path if the knurl is
greasy. This is a deliberate departure from the metal part's head -- the shank, which
is what the assembly actually constrains, is faithful.
"""
import numpy as np

from geo import box, cyl, frustum, inter, sub, uni
from threads import coarse_pitch, thread_solid

from ._common import _bolt, _hex_nut, _ring, _zmin0

COUNT = 10
NAME = "hw_m4_bolt"

D_NOM = 4.0                  # M4, threads.py coarsens the pitch 0.7 -> 1.0 to print
SHANK_R = 1.95               # Ø3.9 journal: 0.30 running clearance in the wheel's Ø4.2
SHANK_L = 40.0               # "M4x40" = 40 under the head; swaps 1:1 with the metal
HEAD_R = 5.2                 # = the wheel hub-boss OD/2 (probed)
HEAD_H = 3.5
JOURNAL_L = 34.7             # head underside -> shoulder (see the docstring's stack)
THREAD_L = SHANK_L - JOURNAL_L      # 5.3 = 5.3 turns; a 3.2 nut engages 3.2 of them


def _knurl(mesh, r, z0, z1, n=18, depth=0.35):
    """Vertical flutes round the head. The bolt prints head-down with the thread axis
    vertical (threads.py's hard requirement), which makes these flutes vertical too --
    they cut as plain wall detail, no overhang anywhere."""
    for i in range(n):
        a = 2.0 * np.pi * i / n
        f = cyl(0.5, (z1 - z0) + 0.2, sections=12)
        f.apply_translation(((r + 0.5 - depth) * np.cos(a),
                             (r + 0.5 - depth) * np.sin(a),
                             (z0 + z1) / 2.0))
        mesh = sub(mesh, f)
    return mesh


def build():
    # --- head: knurled thumb cap, outer face on the bed at z=0 -------------------
    hd = cyl(HEAD_R, HEAD_H, sections=96)
    hd.apply_translation((0, 0, HEAD_H / 2.0))
    hd = _knurl(hd, HEAD_R, 0.0, HEAD_H)
    # Flat-blade slot in the OUTER face (the bed face). Head-down means this is a
    # 1.8-wide gap in the first 1.5 mm of the print with a flat roof at z=1.5 -- a
    # bridge that short needs no support. Costs ~20% of the bed footprint, which the
    # brim (package docstring: bolts stand head-down on a brim) already covers.
    sl = box(1.8, 2 * HEAD_R + 2, 1.5)
    sl.apply_translation((0, 0, 1.5 / 2.0))
    hd = sub(hd, sl)

    # --- plain journal: the wheel and the beam bore both run on this -------------
    jo = cyl(SHANK_R, JOURNAL_L, sections=64)
    jo.apply_translation((0, 0, HEAD_H + JOURNAL_L / 2.0))

    # --- threaded tail ----------------------------------------------------------
    th = thread_solid(D_NOM, THREAD_L, clear=0.25)
    th.apply_translation((0, 0, HEAD_H + JOURNAL_L))

    bolt = uni([hd, jo, th])

    # Tip lead-in: a 45-deg chamfer so the first thread finds the nut instead of
    # butting its crest against the nut face. Cut as (slab minus cone) at the tip.
    tip = HEAD_H + SHANK_L
    ch = 1.0
    slab = cyl(HEAD_R + 2, ch, sections=64)
    slab.apply_translation((0, 0, tip - ch / 2.0))
    keep = frustum(SHANK_R + 0.1, SHANK_R + 0.1 - ch, ch, sections=64)
    keep.apply_translation((0, 0, tip - ch))
    bolt = sub(bolt, sub(slab, keep))
    return _zmin0(bolt)
