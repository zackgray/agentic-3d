"""Hidden reference for Northpeak Spring Water 500 mL: a straight 63 mm bottle with five grip grooves
low on the body, a label band above them, a conical shoulder, support ring, short neck finish and a
plain cap. Outer solid about 550 mL. Sizes in mm; never shown to the agent."""
from geom import MM, lathe

R = 31.5
body = [(0, 0), (25, 0), (29.5, 3), (R, 9), (R, 30)]
for k in range(5):  # grooves 1.5 mm deep, 4 mm wide, 14 mm apart
    z = 36 + 14 * k
    body += [(R, z - 2), (R - 1.5, z - 1), (R - 1.5, z + 1), (R, z + 2)]
body += [(R, 135), (26, 155), (18, 170), (13, 177), (15, 177), (15, 179), (12.5, 179), (12.5, 191), (0, 191)]
CAP = [(0, 180), (14, 180), (14, 195), (0, 195)]

lathe("Bottle", [(r * MM, z * MM) for r, z in body])
lathe("Cap", [(r * MM, z * MM) for r, z in CAP])
