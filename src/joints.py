"""Reviewed joint inventory for desk-pi.

Coordinates are world-space datums from the same PARAMS used by the builders.  Add a
contract here in the same change that adds a structural interface.  The required set is
kept separate so deleting a declaration cannot make the completeness gate green.
"""
import math

from jointspec import Fastener, Fit, Insertion, Joint, Locator, Probe
from params import P

LOCATING = Fit("locating", 0.10, 0.35)
SLIDING = Fit("sliding", 0.15, 0.50)
ROTATING = Fit("rotating", 0.10, 0.40)


def ring(part, point, axis=(0, 0, 1), radius=3.0):
    return Probe(part, "material_ring", point, axis, radius=radius)


def solid(part, point):
    return Probe(part, "solid", point, radius=0.45)


def m3(qty, length, axis, stack, capture="hex_nut", capture_t=2.4,
       bores=(), blockers=(), access=8.0):
    return Fastener("M3", qty, length, axis, stack, capture, capture_t,
                    head_access=access, bore_probes=bores,
                    tool_blockers=blockers)


REQUIRED_STRUCTURAL_JOINTS = (
    "neck_to_pan", "pan_retainer_to_chassis", "lower_tub_front_seam",
    "lower_tub_tail_seam", "deck_strip_front_seam", "deck_strip_rear_seam",
    "side_panel_splice", "side_panel_feet", "belly_plate_to_chassis",
    "chassis_base_to_chassis", "head_bezel_to_back", "head_back_panel_to_frames",
    "head_back_frame_seam", "head_bezel_seam", "screen_tray_to_head_back",
    "ant_bracket_to_head_back", "tilt_carrier_to_neck", "track_master_to_loop",
)


_neck_pin_pts = ((-18.0, -32.0, P["base_h"] + 1.2),
                 (18.0, -32.0, P["base_h"] + 1.2))
_neck_bores = []
for az in (270.0, 30.0, 150.0):
    a = math.radians(az)
    _neck_bores.append(ring("neck_clevis",
                            (16.5 * math.cos(a), P["neck_y"] + 16.5 * math.sin(a), 72.0)))

_retainer_bores = []
_retainer_captures = []
_retainer_lip = []
for az, _width, _r0, _r1, screw_r, _run in P["pan_retainer_lobes"]:
    a = math.radians(az)
    _retainer_bores.append(ring("pan_retainer",
                                (screw_r * math.cos(a), screw_r * math.sin(a),
                                 P["base_h"] - 5.0)))
    _retainer_captures.append(Probe("chassis_deck_center", "void",
                                    (screw_r * math.cos(a), screw_r * math.sin(a),
                                     P["pan_retainer_nut_z"])))
for az in range(0, 360, 30):
    a = math.radians(az)
    _retainer_lip.append(solid("pan_retainer",
                               (46.7 * math.cos(a), 46.7 * math.sin(a),
                                P["base_h"] - 2.0)))


JOINTS = (
    Joint("neck_to_pan", ("neck_clevis", "pan_platform"), True, (0, 0, -1),
          Locator("pin_pair", 2, 4.5, LOCATING, True,
                  tuple(solid("pan_platform", p) for p in _neck_pin_pts)),
          (m3(3, 14.0, (0, 0, 1), 10.0),),
          supporting_probes=(solid("pan_platform", (0, P["neck_y"], P["base_h"] + 0.5)),),
          assembly_step=1),

    Joint("pan_retainer_to_chassis", ("pan_retainer", "chassis_deck_center"), True,
          (0, 0, -1), Locator("continuous_rebate", 1, 2.6, LOCATING, True),
          (Fastener("M3", 6, 10.0, (0, 0, -1), 6.0, "hex_nut", 2.4,
                    head_access=8.0, bore_probes=tuple(_retainer_bores),
                    capture_probes=tuple(_retainer_captures)),),
          insertion=Insertion("pan_retainer", ("pan_platform",), (0, 0, 1), 12.0, 13),
          seating_probes=tuple(_retainer_lip),
          supporting_probes=(solid("pan_retainer", (0, 46.7, P["base_h"] - 2.0)),),
          allowed_dof=("yaw",), assembly_step=8,
          notes="Drops vertically over the seated platform: lip ID 90.8, top-band OD 90.0. Race, cage, balls, and platform are installed first."),

    Joint("lower_tub_front_seam", ("chassis_lower_front", "chassis_lower_rear"), True,
          (0, -1, 0), Locator("pin_pair", 2, 8.0, LOCATING, True),
          (m3(2, 20.0, (0, -1, 0), 15.0),),
          supporting_probes=(solid("chassis_lower_front", (54.0, 26.0, 18.0)),),
          assembly_step=2),

    Joint("lower_tub_tail_seam", ("chassis_lower_rear", "chassis_lower_tail"), True,
          (0, 1, 0), Locator("tongue", 1, 6.0, SLIDING, True),
          (m3(2, 16.0, (0, 1, 0), 11.0),),
          supporting_probes=(solid("chassis_lower_tail",
                                   (P["tail_pad_x"], P["lower_seam2_y"] - 9.0, 20.0)),),
          assembly_step=3),

    Joint("deck_strip_front_seam", ("chassis_deck_front", "chassis_deck_center"), True,
          (0, 0, -1), Locator("half_lap", 1, 4.0, LOCATING, True),
          (m3(2, 12.0, (0, 0, -1), 7.0),),
          supporting_probes=(solid("chassis_deck_center", (40.0, 66.0, 49.0)),),
          assembly_step=5),

    Joint("deck_strip_rear_seam", ("chassis_deck_center", "chassis_deck_rear"), True,
          (0, 0, -1), Locator("half_lap", 1, 4.0, LOCATING, True),
          (m3(2, 12.0, (0, 0, -1), 7.0),),
          supporting_probes=(solid("chassis_deck_center", (40.0, -52.0, 49.0)),),
          assembly_step=5),

    Joint("side_panel_splice", ("chassis_side_R_front", "chassis_side_R_rear"), True,
          (0, 1, 0), Locator("half_lap", 2, 5.0, LOCATING, True),
          (m3(2, 10.0, (0, 0, -1), 5.5),),
          supporting_probes=(solid("chassis_side_R_rear", (75.4, -18.5, 22.0)),),
          assembly_step=4, notes="Mirrored contract covers left and right panel pairs."),

    Joint("side_panel_feet", ("chassis_side_R_front", "chassis_lower_front"), True,
          (0, 0, -1), Locator("rebate", 4, 4.0, LOCATING, True),
          (m3(4, 12.0, (0, 0, 1), 7.0),),
          supporting_probes=(solid("chassis_side_R_front", (62.9, 4.0, 19.0)),),
          assembly_step=4, notes="Mirrored/repeated contract: front nut, rear insert."),

    Joint("belly_plate_to_chassis", ("belly_plate", "chassis_lower_rear"), True,
          (0, 0, 1), Locator("perimeter_rebate", 1, 1.5, LOCATING, True),
          (m3(6, 10.0, (0, 0, 1), 5.5),),
          supporting_probes=(solid("belly_plate", (0, 0, 7.0)),), assembly_step=7),

    Joint("chassis_base_to_chassis", ("chassis_base", "chassis_lower_rear"), True,
          (0, 0, -1), Locator("pin_pair", 2, 5.0, LOCATING, True),
          (m3(4, 12.0, (0, 0, 1), 7.0),),
          supporting_probes=(solid("chassis_base", (0, 0, 0)),
                             solid("chassis_lower_rear", (0, 0, 0))), assembly_step=6),

    Joint("head_bezel_to_back", ("head_bezel_L", "head_bezel_R",
                                  "head_back_L", "head_back_R"), True, (0, -1, 0),
          Locator("pin_pair", 2, P["bez_dowel_len"], LOCATING, True),
          (m3(8, 35.0, (0, -1, 0), 29.0),),
          supporting_probes=tuple(solid("head_bezel_L" if x < 0 else "head_bezel_R",
                                       (x, 2.0, z)) for x, z in P["bez_dowel_pts"]),
          assembly_step=15),

    Joint("head_back_panel_to_frames", ("head_back_panel_L", "head_back_panel_R",
                                         "head_back_frame_L", "head_back_frame_R"), True,
          (0, -1, 0), Locator("tab_rebates", 6, P["rim_pad"][1], LOCATING, True),
          (m3(6, 10.0, (0, -1, 0), 5.0),),
          supporting_probes=(solid("head_back_panel_L", (-91.0, -66.0, 120.0)),
                             solid("head_back_frame_R", (91.0, -66.0, 120.0))), assembly_step=12),

    Joint("head_back_frame_seam", ("head_back_frame_L", "head_back_frame_R"), True,
          (-1, 0, 0), Locator("keyed_pin_and_flange", 1, 6.0, LOCATING, True),
          (m3(2, 16.0, (-1, 0, 0), 11.0),),
          supporting_probes=(solid("head_back_frame_L", (-2.0, P["flange_dowel_y"], 238.0)),),
          assembly_step=11),

    Joint("head_bezel_seam", ("head_bezel_L", "head_bezel_R"), True,
          (-1, 0, 0), Locator("pin_pair", 2, 5.0, LOCATING, True),
          (m3(2, 16.0, (-1, 0, 0), 11.0),),
          supporting_probes=(solid("head_bezel_L", (22.0, 26.0, 100.0)),), assembly_step=10),

    Joint("screen_tray_to_head_back", ("screen_tray", "head_back_L", "head_back_R"), True,
          (0, -1, 0), Locator("keyed_pillars", 4, 1.2, LOCATING, True),
          (m3(4, 10.0, (0, 1, 0), 5.0),),
          supporting_probes=(solid("screen_tray", (-63.1, -64.5, 134.0)),
                             solid("screen_tray", (61.6, -64.5, 174.0))), assembly_step=13),

    Joint("ant_bracket_to_head_back", ("ant_bracket", "head_back_L", "head_back_R"), True,
          (0, -1, 0), Locator("spine_rebate", 1, 2.0, LOCATING, True),
          (m3(4, 12.0, (0, -1, 0), 7.0),),
          supporting_probes=(solid("ant_bracket", (P["ant_mount_x"][0], -58.0,
                                                    P["ant_mount_z"])),), assembly_step=14),

    Joint("tilt_carrier_to_neck", ("tilt_carrier", "neck_clevis"), True,
          (0, 1, 0), Locator("boss_rebate", 4, 2.0, LOCATING, True),
          (m3(4, 16.0, (0, 1, 0), 11.0),),
          supporting_probes=(solid("tilt_carrier", (12.0, -39.0, 133.0)),), assembly_step=9),

    Joint("track_master_to_loop", ("track_L", "track_R"), True,
          (1, 0, 0), Locator("hinge_and_c_jaw", 2, P["track_width"], ROTATING, True),
          (Fastener("M2", 4, 8.0, (1, 0, 0), 4.0, "heat_set", 1.6,
                    head_access=6.0, driver_diameter=5.0),),
          supporting_probes=(solid("track_L", (-P["track_width"] / 2.0, 0.0, 25.0)),),
          allowed_dof=("hinge",), assembly_step=16),
)
