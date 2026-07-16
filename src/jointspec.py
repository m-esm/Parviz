"""Typed contracts for printed-part joints.

The contract is deliberately independent of trimesh.  Part modules may import these
dataclasses without creating a geometry dependency; :mod:`joint_checks` supplies the
analytic and mesh-backed validators.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Vec3 = Tuple[float, float, float]


@dataclass(frozen=True)
class Fit:
    kind: str
    clearance_min: float
    clearance_max: float


@dataclass(frozen=True)
class Probe:
    """A generated-mesh assertion at a world-coordinate datum."""
    part: str
    kind: str                 # solid, void, material_ring, open_path
    point: Vec3
    axis: Vec3 = (0.0, 0.0, 1.0)
    length: float = 0.0
    radius: float = 0.4
    minimum_hits: int = 4
    samples: int = 12


@dataclass(frozen=True)
class Locator:
    kind: str                 # pin_pair, tongue, rail, rebate, spigot, keyed
    count: int
    engagement: float
    fit: Fit
    prevents_rotation: bool = True
    male_probes: Tuple[Probe, ...] = ()
    female_probes: Tuple[Probe, ...] = ()


@dataclass(frozen=True)
class Fastener:
    size: str
    quantity: int
    length: float
    axis: Vec3
    clamp_stack: float
    capture: str              # hex_nut, nyloc, heat_set, factory_thread, pin
    capture_thickness: float
    thread_protrusion_min: float = 1.0
    thread_protrusion_max: float = 5.0
    head_access: float = 8.0
    driver_diameter: float = 7.0
    driver_length: float = 35.0
    bore_probes: Tuple[Probe, ...] = ()
    capture_probes: Tuple[Probe, ...] = ()
    tool_blockers: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Insertion:
    moving_part: str
    fixed_parts: Tuple[str, ...]
    axis: Vec3
    distance: float
    steps: int = 12
    allowed_final_overlap: float = 0.0


@dataclass(frozen=True)
class Joint:
    name: str
    parts: Tuple[str, ...]
    structural: bool
    assembly_axis: Vec3
    locator: Optional[Locator]
    fasteners: Tuple[Fastener, ...]
    insertion: Optional[Insertion] = None
    seating_probes: Tuple[Probe, ...] = ()
    supporting_probes: Tuple[Probe, ...] = ()
    allowed_dof: Tuple[str, ...] = ()
    assembly_step: int = 0
    notes: str = ""


@dataclass
class GateResult:
    joint: str
    gate: str
    ok: bool
    detail: str = ""
    measurements: Dict[str, float] = field(default_factory=dict)


M3 = {"diameter": 3.0, "nut": 2.4}
M2 = {"diameter": 2.0, "nut": 1.6}
FASTENER_SPECS = {"M2": M2, "M3": M3, "M4": {"diameter": 4.0, "nut": 3.2},
                  "M8": {"diameter": 8.0, "nut": 6.5}}

