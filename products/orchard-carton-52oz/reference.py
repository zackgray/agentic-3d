"""Hidden reference for Orchard Row Apple Juice 52 fl oz: a gable-top carton, 90 x 90 mm body 190 mm
tall, roof ridge at 225 mm along X, a 2 mm seal fin to 237 mm. Outer solid about 1.68 L against
1.54 L. Sizes in mm; never shown to the agent."""
import bmesh

from geom import MM, boolean, box, rename, to_object


def prism(name, profile_yz, x0, x1):
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in profile_yz]
    b = [bm.verts.new((x1, y, z)) for y, z in profile_yz]
    bm.faces.new(a)
    bm.faces.new(b)
    n = len(profile_yz)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    return to_object(name, bm)


H = 45 * MM
body = prism("Carton", [(-H, 0), (H, 0), (H, 190 * MM), (0, 225 * MM), (-H, 190 * MM)], -H, H)
boolean(body, box("Fin", (-H, -1 * MM, 219 * MM), (H, 1 * MM, 237 * MM)), "UNION")
rename(body, "Carton")
