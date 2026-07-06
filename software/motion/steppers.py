"""28BYJ-48 half-step driver for the desk-pi neck (pan + tilt).

Design constraints (see repo CLAUDE.md):
- Pan carries the Pi power cable as a SERVICE LOOP through the neck column.
  It must NEVER over-wind, so pan has a hard software clamp (default +/-88 deg,
  2 deg margin inside the +/-90 mechanical target). The clamp is enforced in
  move_to() and cannot be bypassed by relative moves.
- Tilt is a self-locking worm drive, +/-30 deg mechanical. Software clamp
  matches (default +/-30). The worm holds position de-energized, so we
  release the coils after every move (no idle current / heat).
- GPIO is via lgpio (python3-lgpio, in Raspberry Pi OS / Debian trixie repos).
  lgpio is imported LAZILY so this module imports and unit-tests on any
  machine (dry_run=True needs no GPIO at all).

Pins are parameterized with NO defaults: the robot is not built yet, nothing
is wired, and a wrong default silently energizing the wrong pins is worse
than an explicit error.

Usage (on the Pi, once wired):

    from steppers import PanStepper
    pan = PanStepper(pins=(17, 18, 27, 22))   # IN1..IN4 on the ULN2003
    pan.move_to(45.0)                          # degrees, clamped to +/-88
    pan.release()

Dry-run (any machine):

    pan = PanStepper(pins=(1, 2, 3, 4), dry_run=True)
    pan.move_to(120)      # -> moves to +88, returns 88.0
"""

import time

# 28BYJ-48 half-step sequence, applied to (IN1, IN2, IN3, IN4) on the ULN2003.
# 8 half-steps per electrical cycle; going forward = walking this list in order.
HALF_STEP_SEQUENCE = (
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
)

# Nominal 28BYJ-48: 32 steps/rev rotor, ~1:64 gearbox, half-stepping doubles it.
# The true ratio is 63.68395:1 (4075.77 half-steps/rev); 4096 is the usual
# nominal figure and fine for a face robot. Override per-instance if the
# accumulated error ever matters.
HALF_STEPS_PER_REV = 4096

# Datasheet max response frequency ~ 1000 pps at 5 V. 1.2 ms/half-step (~830 pps)
# is a safe default with load.
DEFAULT_STEP_DELAY_S = 0.0012


class LimitedStepper:
    """A 28BYJ-48 on a ULN2003 with a hard software travel clamp.

    Angle convention: 0.0 deg is the pose at power-on (the caller is
    responsible for physically homing/centering before construction, or for
    calling `zero_here()` after a manual home). Positive = forward walk of
    HALF_STEP_SEQUENCE; flip `invert=True` if the mechanism runs backwards.
    """

    def __init__(
        self,
        pins,
        limit_deg,
        steps_per_rev=HALF_STEPS_PER_REV,
        gear_ratio=1.0,
        step_delay_s=DEFAULT_STEP_DELAY_S,
        invert=False,
        dry_run=False,
    ):
        """
        pins:          (IN1, IN2, IN3, IN4) BCM GPIO numbers. Required, no default.
        limit_deg:     symmetric clamp; the axis will never be commanded past
                       +/-limit_deg from zero. Required.
        steps_per_rev: half-steps per revolution of the MOTOR OUTPUT shaft.
        gear_ratio:    extra reduction between motor shaft and the axis
                       (e.g. the 12T worm wheel on tilt). axis_deg =
                       shaft_deg / gear_ratio.
        step_delay_s:  seconds between half-steps.
        invert:        reverse the electrical direction for positive angles.
        dry_run:       no GPIO; pin writes are recorded in self.trace.
        """
        pins = tuple(pins)
        if len(pins) != 4:
            raise ValueError("pins must be exactly 4 GPIO numbers (IN1..IN4)")
        if len(set(pins)) != 4:
            raise ValueError("pins must be distinct")
        if limit_deg <= 0:
            raise ValueError("limit_deg must be positive")

        self.pins = pins
        self.limit_deg = float(limit_deg)
        self.steps_per_rev = int(steps_per_rev)
        self.gear_ratio = float(gear_ratio)
        self.step_delay_s = float(step_delay_s)
        self.invert = bool(invert)
        self.dry_run = bool(dry_run)

        # Position in half-steps of the AXIS (post-gearbox), 0 = home.
        self._pos_steps = 0
        # Index into HALF_STEP_SEQUENCE for the coil pattern.
        self._seq_idx = 0

        self.trace = []  # dry-run: list of (IN1, IN2, IN3, IN4) tuples written
        self._gpio = None
        self._gpio_handle = None
        if not self.dry_run:
            self._init_gpio()

    # ---------------------------------------------------------------- GPIO

    def _init_gpio(self):
        import lgpio  # lazy: only touched on real hardware

        self._gpio = lgpio
        self._gpio_handle = lgpio.gpiochip_open(0)
        for p in self.pins:
            lgpio.gpio_claim_output(self._gpio_handle, p, 0)

    def _write_pattern(self, pattern):
        if self.dry_run:
            self.trace.append(tuple(pattern))
            return
        for pin, level in zip(self.pins, pattern):
            self._gpio.gpio_write(self._gpio_handle, pin, level)

    def release(self):
        """De-energize all coils (0000). Always safe; on tilt the worm holds."""
        self._write_pattern((0, 0, 0, 0))

    def close(self):
        """Release coils and free the GPIO chip handle."""
        self.release()
        if self._gpio_handle is not None:
            self._gpio.gpiochip_close(self._gpio_handle)
            self._gpio_handle = None

    # ------------------------------------------------------------ geometry

    @property
    def steps_per_axis_rev(self):
        return self.steps_per_rev * self.gear_ratio

    def angle_to_steps(self, deg):
        return int(round(deg / 360.0 * self.steps_per_axis_rev))

    def steps_to_angle(self, steps):
        return steps * 360.0 / self.steps_per_axis_rev

    @property
    def position_deg(self):
        return self.steps_to_angle(self._pos_steps)

    def clamp(self, deg):
        """The hard limit. Every commanded target passes through here."""
        return max(-self.limit_deg, min(self.limit_deg, float(deg)))

    def zero_here(self):
        """Declare the current physical pose to be 0 deg (after manual homing)."""
        self._pos_steps = 0

    # -------------------------------------------------------------- motion

    def _step_once(self, direction):
        """One half-step. direction: +1 forward, -1 backward (axis frame)."""
        electrical = -direction if self.invert else direction
        self._seq_idx = (self._seq_idx + electrical) % len(HALF_STEP_SEQUENCE)
        self._write_pattern(HALF_STEP_SEQUENCE[self._seq_idx])
        self._pos_steps += direction

    def move_to(self, deg, hold=False):
        """Move to an absolute angle. Target is clamped to +/-limit_deg.

        Returns the actual angle reached (post-clamp, quantized to steps).
        hold=False releases the coils afterwards (default: tilt's worm and
        pan's friction don't need holding torque, and 28BYJ coils cook if
        left energized).
        """
        target = self.clamp(deg)
        target_steps = self.angle_to_steps(target)
        # Belt & braces: clamp in step space too, so rounding can't overshoot.
        limit_steps = self.angle_to_steps(self.limit_deg)
        target_steps = max(-limit_steps, min(limit_steps, target_steps))

        delta = target_steps - self._pos_steps
        direction = 1 if delta > 0 else -1
        for _ in range(abs(delta)):
            self._step_once(direction)
            if not self.dry_run:
                time.sleep(self.step_delay_s)
        if not hold:
            self.release()
        return self.position_deg

    def move_by(self, delta_deg, hold=False):
        """Relative move. Still clamped: cannot walk past the limit."""
        return self.move_to(self.position_deg + delta_deg, hold=hold)


class PanStepper(LimitedStepper):
    """Neck pan (yaw). Direct D-hub drive, 1:1 to the platform.

    Default clamp +/-88 deg: the mechanical target is +/-90 and the Pi power
    service loop in the neck must never over-wind, so we keep a 2 deg margin.
    Do not raise this above 90 without redesigning the cable path.
    """

    DEFAULT_LIMIT_DEG = 88.0

    def __init__(self, pins, limit_deg=DEFAULT_LIMIT_DEG, **kwargs):
        super().__init__(pins=pins, limit_deg=limit_deg, **kwargs)


class TiltStepper(LimitedStepper):
    """Head tilt (pitch) via the self-locking worm. +/-30 deg mechanical.

    gear_ratio defaults to 12.0 (single-start worm into the 12T wheel:
    one worm rev = one tooth = 1/12 axle rev). The worm self-locks, so
    hold=False (the default) is always safe.
    """

    DEFAULT_LIMIT_DEG = 30.0
    DEFAULT_GEAR_RATIO = 12.0

    def __init__(self, pins, limit_deg=DEFAULT_LIMIT_DEG,
                 gear_ratio=DEFAULT_GEAR_RATIO, **kwargs):
        super().__init__(pins=pins, limit_deg=limit_deg,
                         gear_ratio=gear_ratio, **kwargs)


if __name__ == "__main__":
    # Smoke demo, dry-run only (safe anywhere).
    pan = PanStepper(pins=(17, 18, 27, 22), dry_run=True)
    print("pan  move_to(120) ->", pan.move_to(120), "deg (clamped)")
    tilt = TiltStepper(pins=(5, 6, 13, 19), dry_run=True)
    print("tilt move_to(-45) ->", tilt.move_to(-45), "deg (clamped)")
    print("pan trace length:", len(pan.trace), "coil writes")
