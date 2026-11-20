"""Hidden reference for Volta Citrus Soda 20 fl oz: a contoured PET bottle (rounded heel, a grip
waist, a straight label panel, a tapered shoulder, support ring and neck finish) and a plain cap.
Outer solid about 655 mL against 591 mL net contents. Sizes in mm; never shown to the agent."""
from geom import MM, lathe

BOTTLE = [(0, 0), (26, 0), (31, 3), (33.5, 8), (34, 14), (34, 60), (32, 72), (30.5, 85), (32, 98),
          (34, 110), (34, 150), (33, 160), (29, 175), (22, 190), (16, 200), (14, 203), (16.5, 203),
          (16.5, 205.5), (13.5, 205.5), (13.5, 220), (0, 220)]
CAP = [(0, 206.5), (15, 206.5), (15, 223), (0, 223)]

lathe("Bottle", [(r * MM, z * MM) for r, z in BOTTLE])
lathe("Cap", [(r * MM, z * MM) for r, z in CAP])
