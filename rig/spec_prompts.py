"""Prompt text for the spec-first session on product-page briefs (rig/spec_session.py).

Step 1 asks for a dimensioned spec from the page text and the one product shot, every value marked
with where it came from. Step 2 builds from the spec the owner approved, with the owner's corrections
on top. Corrections go back through the spec writer (REVISE) so the builder only ever sees numbers the
owner approved: a correction riding beside the spec was lost in the first session (2026-11-20). Kept apart from the runner so the wording can change without touching the plumbing.
"""

SPEC = """A client wants this product modelled in 3D for product renders. This is everything they sent: the product page text below and the one product photo attached.

Product page: {page}

Before anything is modelled, write a dimensioned build spec. The client is not a modeller: they will read the spec and approve or correct it in plain words, and then a modeller will build exactly what it says, with no other information.

What the spec must hold:
- Millimetres throughout. The product stands upright with its axis on Z and its base at z = 0.
- Overall height and widest width.
- The outside profile as a table of stations from the base to the top (height, diameter or width), with enough stations to capture every contour, groove, shoulder and neck change you can see in the photo.
- Every separate part (for example a cap or lid) with its own dimensions and where it sits. A closure fits over the container the way the real one does: the neck runs up inside the cap to just below the cap's top, so the cap's height range overlaps the neck's in the station table.
- Features that are part of the shape (ribs, grooves, base feet, threads), not printed graphics. The coloured label band in the photo is printed, not geometry.

The photo has no scale reference. Solve the scale from the net contents: the container's enclosed volume is larger than the net contents, to allow for headspace and wall. Show that calculation in a few lines.

Mark each value with its source: [page] for the page text, [photo] for proportions read from the photo, [standard] for packaging norms (name the norm, e.g. a neck finish), [guess] for anything else.

Keep it short: the spec, not an essay. End with at most three questions, the guesses that most change the result."""

BUILD_HEAD = """Model a hypothetical product in the open Blender scene, following the approved spec below. Units are metres (1 Blender unit = 1 m); the spec's sizes are in millimetres. The product's axis is the world Z axis and its base rests on the ground plane at z = 0. The attached photo is the product shot the spec was written from; use it for shape where the spec leaves room.

Approved spec:

{spec}
{notes}
"""

# The direct arm of the scored comparison: the builder gets the brief itself, with no spec step.
DIRECT_HEAD = """Model a hypothetical product in the open Blender scene for close-up product renders. A client sent only the product page text below and the attached product photo. Units are metres (1 Blender unit = 1 m). The product's axis is the world Z axis and its base rests on the ground plane at z = 0.

Product page: {page}

The photo has no scale reference: work out the real size from the net contents (the container encloses more than its net contents, to allow for headspace and wall) and from packaging standards. Trace the profile, grooves and parts from the photo; the coloured label band is printed, not geometry. A closure fits over the container the way the real one does: the neck runs up inside the cap.
"""

PARTS = """Objects: one mesh object per part, named exactly {names}.
- Each is a single closed (watertight) mesh with consistent outward normals and no self-intersections, suitable for close-up product renders.
- Transforms applied: location at the origin, no rotation, scale 1, so the mesh data holds world coordinates.
- Parts must not touch or intersect each other.
- No other mesh objects in the scene.

Mesh hygiene: no duplicate or coincident vertices, no zero-length edges and no zero-area faces. Merge any coincident vertices before you finish.

Tell me when you're done."""

BUILD, DIRECT = BUILD_HEAD + PARTS, DIRECT_HEAD + "\n" + PARTS

NOTES = """
The client's corrections to the spec (these override the spec where they differ):

{notes}
"""

REVISE = """The client read your spec and replied:

{notes}

Rewrite the full spec with these corrections built into the numbers themselves: every station, part and position they affect must change, not just a note. The modeller will see only the revised spec, never this reply. Keep the same format and source marks ([client] for values the client set). Mark what changed with (changed). No questions unless something the client said is ambiguous."""
