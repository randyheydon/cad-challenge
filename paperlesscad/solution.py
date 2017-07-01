"""
You may create as many additional packages or modules as you needed. Your
solution will be accessed by the test cases by calling the function `dfm_check`
in this module. The function will be a passed a path to a STEP file. We 
strongly suggest using FreeCAD (as shown below), but you may use any 
open-source and freely available library you would like. If the library is not
available via `pip`, please include installation instructions. 
"""

from __future__ import absolute_import, division, print_function

from itertools import chain, combinations, product

from paperlesscad.utils import is_close, HashShape, is_concave

import FreeCAD
import Part


def dfm_check(step_path):
    """Place your solution in this function. Create and call other functions, 
    classes, modules, and packages as required."""
    shape = Part.Shape()
    shape.read(step_path)
    issues = []

    # Break out sets of surfaces for later evaluation.
    faces = shape.Faces
    planes = set(f for f in faces if isinstance(f.Surface, Part.Plane))
    horizontal_planes = set(
        p for p in planes
        if (is_close(p.Surface.Axis.x, 0) and is_close(p.Surface.Axis.y, 0)
            and is_close(abs(p.Surface.Axis.z), 1)))
    angled_planes = set(
        p for p in (planes - horizontal_planes)
        if not is_close(p.Surface.Axis.z, 0))
    cylinders = set(f for f in faces if isinstance(f.Surface, Part.Cylinder))
    vertical_cylinders = set(
        c for c in cylinders
        if (is_close(c.Surface.Axis.x, 0) and is_close(c.Surface.Axis.y, 0)
            and is_close(abs(c.Surface.Axis.z), 1)))
    cones = set(f for f in faces if isinstance(f.Surface, Part.Cone))
    vertical_cones = set(
        c for c in cones
        if (is_close(c.Surface.Axis.x, 0) and is_close(c.Surface.Axis.y, 0)
            and is_close(abs(c.Surface.Axis.z), 1)))
    # TODO There are a bunch of other FreeCAD surface types.  We will assume
    # that none of them are manufacturable in flat parts.  Sphere and Toroid
    # are definitely no good, but the others could maybe use further
    # consideration.  Bezier and BSpline in particular could be manufacturable
    # in certain circumstances (like the BSplines in milled_pocket.STEP).
    leftovers = set(faces) - planes - cylinders - cones

    # Construct map of which faces are connected to a given edge.
    # There is usually two faces per edge, but sometimes only one.  I don't
    # think that more than two is possible, but let's not assume.
    # NOTE FreeCAD 0.17 will have an "ancestorsOfType" method that could
    # simplify or replace this code.  See FreeCAD commit f9bfd775.
    edge_to_faces = {HashShape(e): set() for e in shape.Edges}
    for f in faces:
        for e in f.Edges:
            edge_to_faces[HashShape(e)].add(HashShape(f))

    # Construct map of which faces are adjacent to a given face (i.e. all faces
    # that share an edge with this face).
    face_to_faces = {HashShape(f): set() for f in faces}
    for f in faces:
        for e in f.Edges:
            face_to_faces[HashShape(f)].update(edge_to_faces[HashShape(e)])
    for k, v in face_to_faces.iteritems():
        # Don't consider a face as connected to itself.
        v.remove(k)
        #v.difference_update(horizontal_planes)

    # Start by checking for things that are well outside our problem space.  If
    # a part does not have top and bottom planes or if it has any unhandled
    # surface types, then the rest of the code does not apply.  Just call it
    # "non-uniform" and quit.
    if len(horizontal_planes) < 2 or leftovers:
        issues.append({'issue': 'non-uniform', 'faces': None})
        return {'issues': issues}

    # Check for any cylinders or cones that are not vertical.  These will be
    # considered as radiused edges.
    # NOTE This could also correspond to a bunch of other geometric issues, but
    # none of those are being checked for here, so just call them all "radius".
    if (cylinders - vertical_cylinders) or (cones - vertical_cones):
        issues.append({'issue': 'radius', 'faces': None})

    # Check for countersinks.  This will be anywhere that a cone and a cylinder
    # have the same axis, are connected at an edge, and are both concave.
    # Also track the cones involved here, since any that are not part of
    # countersinks must instead be a draft or a chamfer.
    countersink_cones = set()
    for surfs in edge_to_faces.itervalues():
        s = [surf.Shape for surf in surfs]
        # Sometimes an edge connects to only one face.  Maybe it could connect
        # to more than two faces.  Skip those cases.
        if len(s) != 2:
            continue
        # Check if the surface pair is exactly one cone and one cylinder.
        cone_cyl = ((s[0] in vertical_cones and s[1] in vertical_cylinders)
                    or (s[1] in vertical_cones and s[0] in vertical_cylinders))
        if not cone_cyl:
            continue
        # Check that both cone and cylinder are concave.
        if not (is_concave(s[0]) and is_concave(s[1])):
            continue
        # Check that the axes of the cone and cylinder are aligned.
        aligned = (is_close(s[0].Surface.Center.x, s[1].Surface.Center.x)
                   and is_close(s[0].Surface.Center.y, s[1].Surface.Center.y))
        if not aligned:
            continue
        # If we've made it this far, then we can consider it a countersink.
        issues.append({
            'issue': 'counter-sink',
            'faces': [faces.index(s[0]), faces.index(s[1])]})
        countersink_cones.add(vertical_cones.intersection(s).pop())

    # Check for counterbores.  This will be anywhere that two cylinders of
    # different radii have the same axis and are connected with a horizontal
    # plane.  First find cylinders with aligned centers, then find the surface
    # that is connected to both of them.
    # Also track those connecting planes, since they are otherwise non-uniform.
    # NOTE I'm not really checking connectivity, but I'm faking it by checking
    # that the plane's outer edge is a circle centered on the same axis, and
    # that the center is in the bounding box of each cylinder.  This could fail
    # if the part has some floating point error in it.  This could also
    # potentially misidentify certain pathological cases.
    counterbore_planes = set()
    for c1, c2 in combinations(vertical_cylinders, 2):
        aligned = (is_close(c1.Surface.Center.x, c2.Surface.Center.x)
                   and is_close(c1.Surface.Center.y, c2.Surface.Center.y))
        if aligned:
            for p in horizontal_planes:
                edge = p.OuterWire.Edges[0].Curve
                if not isinstance(edge, Part.Circle):
                    continue
                edge_aligned = (
                    is_close(c1.Surface.Center.x, edge.Center.x)
                    and is_close(c1.Surface.Center.y, edge.Center.y)
                    and c1.BoundBox.isInside(edge.Center)
                    and c2.BoundBox.isInside(edge.Center))
                if edge_aligned:
                    issues.append({
                        'issue': 'counter-bore',
                        'faces': [faces.index(c1), faces.index(c2),
                                  faces.index(p)]})
                    counterbore_planes.add(p)

    # Check for small holes.  These are cylinders with diameters less than the
    # part thickness, or less than 0.125" (3.175 mm).
    # NOTE This code also captures small outside radii; not sure if that is
    # desired.
    # NOTE This must happen after counterbore checks just because of the way
    # that test.py is currently configured.
    min_radius = 0.5 * max(3.175, shape.BoundBox.ZLength)
    small_holes = [
        faces.index(c) for c in vertical_cylinders
        if c.Surface.Radius < min_radius]
    if small_holes:
        issues.append({'issue': 'small-hole', 'faces': small_holes})

    # Check for small cuts.  We'll look for any horizontal edges that are
    # shorter than the part thickness, or shorter than 0.125" (3.175 mm).
    # We'll only look for surfaces that extend through the full thickness of
    # the part, with the short edges at top and/or bottom.
    # NOTE This will also capture small external features; not sure if that is
    # desired.
    min_size = max(3.175, shape.BoundBox.ZLength)
    small_faces = []
    for f in planes - horizontal_planes:
        if not (is_close(f.BoundBox.ZMin, shape.BoundBox.ZMin)
                and is_close(f.BoundBox.ZMax, shape.BoundBox.ZMax)):
            continue
        for e in f.Edges:
            short = (isinstance(e.Curve, Part.Line)
                     and is_close(e.BoundBox.ZLength, 0)
                     and (is_close(e.BoundBox.ZMin, shape.BoundBox.ZMin)
                          or is_close(e.BoundBox.ZMax, shape.BoundBox.ZMax))
                     and e.Curve.length() < min_size)
            if short:
                small_faces.append(faces.index(f))
                break
    if small_faces:
        issues.append({'issue': 'small-cut', 'faces': small_faces})

    # Check for drafts and chamfers.  These will be any planes on an angle and
    # any vertical cones that are not already considered countersinks.  Drafts
    # and chamfers are distinguished by whether they extend through the full
    # thickness of the part.  Each issue will only be added to the list once.
    # NOTE Certain cases of angled planes may be better classified as "non-
    # uniform", but this code does not consider that.
    unhandled_vertical_cones = vertical_cones - countersink_cones
    zmax = shape.BoundBox.ZMax
    zmin = shape.BoundBox.ZMin
    drafted = False
    chamfered = False
    for f in chain(angled_planes, unhandled_vertical_cones):
        if is_close(f.BoundBox.ZMax, zmax) and is_close(f.BoundBox.ZMin, zmin):
            if not drafted:
                issues.append({'issue': 'draft', 'faces': None})
                drafted = True
        else:
            if not chamfered:
                issues.append({'issue': 'chamfer', 'faces': None})
                chamfered = True

    # Check for non-uniform thickness that is not otherwise covered by one of
    # the previous issues.  At this point, the only unhandled geometry still
    # remaining are horizontal surfaces that are not the top and bottom and are
    # not part of counterbores.
    if len(horizontal_planes - counterbore_planes) != 2:
        issues.append({'issue': 'non-uniform', 'faces': None})

    return {'issues': issues}
