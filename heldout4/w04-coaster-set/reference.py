"""Reference layout for w04 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

An open rounded-square holder with a thumb notch, two square coasters stacked inside it (0.5 mm
clear of the floor and of each other), and two more beside it: one on the ground, one resting on
that one turned 45 degrees. VARIANT selects deliberately broken layouts.
"""
from geom_wb import coaster_holder, rr_slab

VARIANT = globals().get("VARIANT", "good")
n = 6 if VARIANT == "coarse" else 16           # coarse: 24 segments per full circle (must pass)
half = 50 if VARIANT == "big_coasters" else 48  # big_coasters: 100 mm coasters that cannot fit
T = 6.0                                         # coaster thickness

coaster_holder(n=n, notch=VARIANT != "no_notch")

z1 = 3.0 if VARIANT == "on_floor" else 3.5      # on_floor: resting on the holder floor, no clearance
z2 = z1 + T + (0.0 if VARIANT == "touching_stack" else 0.5)
z4 = T + (0.0 if VARIANT == "c4_touching" else 0.5)
turn = 0.0 if VARIANT == "c4_square" else 45.0  # c4_square: top coaster left square to the one below

rr_slab("Coaster_1", half, 8, z1, z1 + T, n=n)
rr_slab("Coaster_2", half, 8, z2, z2 + T, n=n)
rr_slab("Coaster_3", half, 8, 0.0, T, cx=140, n=n)
rr_slab("Coaster_4", half, 8, z4, z4 + T, cx=140, angle_deg=turn, n=n)
