"""Hidden reference for Halden Sparkling Water 12 fl oz: a standard-size beverage can, 66 mm body,
122.2 mm tall, a domed base on a stand ring, a necked top and a recessed lid inside a rolled rim.
Outer solid about 390 mL against 355 mL. Sizes in mm; never shown to the agent."""
from geom import MM, lathe

CAN = [(0, 10), (20, 8), (24, 3), (25, 0), (27.5, 0), (31.5, 4), (33, 10), (33, 110), (30, 116),
       (27.5, 120), (28, 122.2), (26.5, 122.2), (26.5, 120.8), (0, 120.8)]

lathe("Can", [(r * MM, z * MM) for r, z in CAN])
