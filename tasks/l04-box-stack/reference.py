"""Reference layout for l04, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Six 100 x 80 x 60 mm blocks as a 3-2-1 pyramid: 10 mm gaps within a layer, each upper box centred
over the gap below, 0.5 mm clear of the layer beneath. VARIANT selects deliberately broken stacks.
"""
from geom import MM, boolean, box

VARIANT = globals().get("VARIANT", "good")
W, D, H = 100, 80, 60

gap = 0 if VARIANT == "packed" else 10  # packed: neighbours touch, upper boxes over the seams
lift = {"touching_layers": 0, "sunk_layers": -0.5}.get(VARIANT, 0.5)
shift = 10 if VARIANT == "off_centre" else 0
pitch = W + gap
centres = {1: -pitch, 2: 0, 3: pitch, 4: -pitch / 2, 5: pitch / 2, 6: 0}
layer = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 2}

for k in range(1, 7):
    if k == 6 and VARIANT == "missing_top":
        continue
    cx, z0 = centres[k] + shift, layer[k] * (H + lift)
    hx, hy = (D / 2, W / 2) if (k == 6 and VARIANT == "turned_top") else (W / 2, D / 2)
    obj = box(f"Box_{k}", ((cx - hx) * MM, -hy * MM, z0 * MM), ((cx + hx) * MM, hy * MM, (z0 + H) * MM))
    if k == 6 and VARIANT == "open_top":  # modelled as an open carton with 5 mm walls, not a solid block
        boolean(obj, box("Cavity", ((cx - hx + 5) * MM, (-hy + 5) * MM, (z0 + 5) * MM),
                         ((cx + hx - 5) * MM, (hy - 5) * MM, (z0 + H + 1) * MM)), "DIFFERENCE")
