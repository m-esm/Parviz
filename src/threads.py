"""REAL ISO METRIC THREADS for the plastic hardware stand-ins (2026-07-16, user:
"as functional and as close to reality of their metal counterparts as possible").

The 2026-07-15 stand-ins were all THREADLESS push/press fits, which made them
locators, not fasteners: the M8 press nut could not hold tension preload at all
(PLA creeps on a 0.2 interference), so the dry track ran slack ON PURPOSE. A real
printed 60-degree V-thread turns a push-on into an actual screw: it can be
tightened, it holds preload through form (not friction), and it assembles exactly
like the metal part it stands in for -- which is the whole point of a dry build.

GEOMETRY: ISO 68-1 60-deg V-profile, truncated H/8 at the crest and H/4 at the
root (H = sqrt(3)/2 * pitch = the sharp-V height). Swept as a polygon helix, so
the flanks are real ruled surfaces, not a stack of discs. Internal threads get the
same profile grown by `clear` (radial), which is what makes a printed pair
actually spin together.

PRINTABILITY (why the numbers are what they are):
  * Thread axis MUST print VERTICAL. A vertical thread is a series of ~30-deg
    overhangs spiralling up -- self-supporting, no support material. Printed
    horizontally the flanks become unsupported ledges and the profile smears.
  * Pitch >= ~0.8 mm survives a 0.4 nozzle: at 0.7 (stock M4) the flank is barely
    two extrusions tall and the crest rounds off into a smooth cone. So M4 uses a
    COARSENED 1.0 mm pitch (see coarse_pitch) -- it is no longer a standards M4,
    but it is a working screw, and these mate ONLY with each other (the printed
    nut ships with the printed bolt). M8's stock 1.25 prints as-is.
  * `clear` 0.25 radial is the FDM reality gap: bores print under, pegs print
    over, and a 60-deg flank turns any radial error into ~2x that along the
    flank normal. 0.25 spins freely after a wire-brush of the first thread;
    0.15 binds on a fresh nozzle.

LIMITS: PLA threads strip long before steel. These hold hand-tight preload (a few
N-m at M8), which is enough to tension a dry track and to keep a wheel from
wandering -- they are NOT a substitute for the real M8x60 + NYLOC under load.
"""
import numpy as np
import trimesh

from geo import _from_man, _to_man, cyl, sub, uni

SQ3 = np.sqrt(3.0)


def coarse_pitch(nominal_d):
    """Printable pitch for a nominal diameter. Stock ISO coarse where it prints
    (M8 1.25, M5 0.8), COARSENED where stock is too fine for a 0.4 nozzle (M4
    0.7 -> 1.0, M3 0.5 -> 0.8). Printed pairs only ever mate with each other."""
    return {3.0: 0.8, 4.0: 1.0, 5.0: 0.8, 6.0: 1.0, 8.0: 1.25}[float(nominal_d)]


def _profile(d_nom, pitch, internal, clear):
    """One thread turn as a CLOSED (r, z) polygon, ISO 68-1 truncation, crest
    centred on z=0 and spanning exactly one pitch.

    The right boundary is the real thread surface; the left boundary is a plain
    back face at r_back, sunk inside the core so the swept tube overlaps the core
    cylinder and their union is a solid. Keeping the back OFF the root radius is
    what makes this polygon simple -- the first cut of this helper put collinear
    points on the back edge and the degenerate fan collapsed the sweep.

    ISO geometry (H = sqrt(3)/2*p is the sharp-V height): flank rises 5H/8 over
    5p/16 of z (= 30 deg half-angle), crest flat p/8, root flat p/4. Those four
    add back to exactly one pitch, which is the identity this profile is built on.
    """
    H = SQ3 / 2.0 * pitch
    r_maj = d_nom / 2.0
    # BOTH cases are the same MALE form and the same topology -- an internal
    # thread is just that form grown by `clear` and used as a cutter. (The first
    # cut of this helper flipped the internal back face OUTSIDE the crest, so the
    # cutter ate the nut's thread instead of forming it: a printed pair that could
    # never mate.) tip = crest (max r), val = root (min r), back = sunk inside.
    if internal:
        r_tip = r_maj + clear / 2.0
        r_val = r_maj - 5.0 * H / 8.0 + clear / 2.0
    else:
        r_tip = r_maj - clear / 2.0
        r_val = r_maj - 5.0 * H / 8.0 - clear / 2.0
    r_back = max(0.05, r_val - 0.6 * pitch)
    fc = pitch / 8.0                            # crest flat
    zf = 5.0 * pitch / 16.0                     # flank z-run (30 deg half-angle)
    surf = [(r_val, -pitch / 2.0),              # mid root flat
            (r_val, -fc / 2.0 - zf),            # root -> flank start
            (r_tip, -fc / 2.0),                 # crest flat
            (r_tip, +fc / 2.0),
            (r_val, +fc / 2.0 + zf),
            (r_val, +pitch / 2.0)]
    poly = [(r_back, -pitch / 2.0)] + surf + [(r_back, +pitch / 2.0)]
    return np.array(poly), r_tip, r_val, r_back


def _helix_solid(prof, lead, turns, seg):
    """Sweep a closed (r, z) polygon along a helix and CAP both ends -> watertight.

    Explicit indexing (no fill_holes): fill_holes cannot cap a helical ribbon, and
    a non-watertight input makes manifold3d return an EMPTY solid, which silently
    turns the union into just the core cylinder (the first cut of this helper
    printed threads whose max radius was the ROOT -- the band had vanished).
    """
    k = len(prof)
    n = max(16, int(round(seg * turns)))
    th = np.linspace(0.0, turns * 2.0 * np.pi, n)
    verts = np.empty((n * k, 3))
    for i, a in enumerate(th):
        z0 = lead * a / (2.0 * np.pi)
        c, s = np.cos(a), np.sin(a)
        verts[i * k:(i + 1) * k, 0] = prof[:, 0] * c
        verts[i * k:(i + 1) * k, 1] = prof[:, 0] * s
        verts[i * k:(i + 1) * k, 2] = prof[:, 1] + z0
    faces = []
    for i in range(n - 1):
        for j in range(k):
            a0, b0 = i * k + j, i * k + (j + 1) % k
            a1, b1 = (i + 1) * k + j, (i + 1) * k + (j + 1) % k
            faces.append((a0, b0, b1))
            faces.append((a0, b1, a1))
    fan = [(0, j, j + 1) for j in range(1, k - 1)]           # start cap (reversed)
    faces += [(f[0], f[2], f[1]) for f in fan]
    off = (n - 1) * k                                        # end cap
    faces += [(off + f[0], off + f[1], off + f[2]) for f in fan]
    m = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=False)
    m.fix_normals()
    return m


def thread_solid(d_nom, length, pitch=None, internal=False, clear=0.25,
                 starts=1, seg=64):
    """A threaded SOLID (external) or the CUTTER for an internal thread, axis +Z,
    z 0..length. Real ruled flanks swept along a helix, not stacked discs.

    external: the threaded rod -- union it onto a head/shank.
    internal: the NEGATIVE -- sub() it from a nut blank to tap it.
    """
    pitch = pitch or coarse_pitch(d_nom)
    prof, r_tip, r_val, r_back = _profile(d_nom, pitch, internal, clear)
    lead = pitch * starts
    turns = length / lead + 2.0                  # over-run, trimmed back to length
    band = _helix_solid(prof, lead, turns, seg)
    band.apply_translation((0, 0, -pitch))       # start below z=0
    # Same in both cases: the helical tooth + a core column at its root radius.
    # External -> a threaded rod. Internal -> the male form + its bore column,
    # i.e. exactly the negative that leaves a mating nut thread behind.
    core = cyl(r_val + 0.02, length + 6.0 * pitch)
    core.apply_translation((0, 0, length / 2.0))
    solid = uni([band, core])
    lo = cyl(d_nom * 2.0 + 4.0, 6.0 * pitch)
    lo.apply_translation((0, 0, -3.0 * pitch))
    hi = cyl(d_nom * 2.0 + 4.0, 6.0 * pitch)
    hi.apply_translation((0, 0, length + 3.0 * pitch))
    return sub(sub(solid, lo), hi)


def tap(mesh, d_nom, at, length, pitch=None, clear=0.25, axis="z"):
    """Cut a real internal thread into `mesh` at `at`, along `axis`, `length` deep."""
    cut = thread_solid(d_nom, length, pitch=pitch, internal=True, clear=clear)
    if axis == "y":
        cut.apply_transform(trimesh.transformations.rotation_matrix(
            -np.pi / 2.0, (1, 0, 0)))
    elif axis == "x":
        cut.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi / 2.0, (0, 1, 0)))
    cut.apply_translation(at)
    return sub(mesh, cut)
