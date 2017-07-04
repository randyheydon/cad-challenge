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
from math import pi

from paperlesscad.utils import is_close, HashShape, is_concave

import FreeCAD
import Part


# If desired, a custom kerf width (cut size) can be set here.
# If left as None, a kerf width will be set automatically below.
kerf_width_override = None


def dfm_check(step_path):
    """Place your solution in this function. Create and call other functions, 
    classes, modules, and packages as required."""
    shape = Part.Shape()
    shape.read(step_path)
    issues = []

    # Default kerf width is set as the part thickness, to a minimum of 0.125".
    kerf_width = kerf_width_override
    if kerf_width is None:
        kerf_width = max(3.175, shape.BoundBox.ZLength)

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
    bad_surfaces = set(
        f for f in faces
        if isinstance(f.Surface, (Part.Sphere, Part.Toroid)))
    leftovers = set(faces) - planes - cylinders - cones - bad_surfaces

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

    # Start by checking for things that are well outside our problem space.  If
    # a part does not have top and bottom planes or if it has any known-bad
    # surface types, then the rest of the code does not apply.  Just call it
    # "non-uniform" and quit.
    if len(horizontal_planes) < 2 or bad_surfaces:
        issues.append({'issue': 'non-uniform', 'faces': None})
        return {'issues': issues}

    # If there are any of the more unusual surfaces, use a heuristic to see if
    # they're okay.  Put a grid of points over the surface and check the normal
    # at each point; if all normals have no vertical component, then we can
    # probably assume that the whole surface is like that.  In such a case, the
    # surface should be cuttable; otherwise, it's definitely not.
    # As above, if issues are found, then the rest of the code does not apply.
    n_points = 20
    for f in leftovers:
        u1, u2, v1, v2 = f.ParameterRange
        for a, b in product(range(n_points), repeat=2):
            u = (u2 - u1) * a / n_points + u1
            v = (v2 - v1) * b / n_points + v1
            if not is_close(f.normalAt(u, v).z, 0):
                issues.append({'issue': 'non-uniform', 'faces': None})
                return {'issues': issues}

    # Check for any cylinders or cones that are not vertical.  These will be
    # considered as radiused edges.
    # NOTE This could also correspond to a bunch of other geometric issues, but
    # none of those are being checked for here, so just call them all "radius".
    if (cylinders - vertical_cylinders) or (cones - vertical_cones):
        issues.append({'issue': 'radius', 'faces': None})

    # Check for sharp internal corners.  Look for vertical edges, then evaluate
    # the attached faces to see if they meet at a significant angle, and
    # whether they form a convex or concave corner.
    # NOTE This will not work for an edge that's connected to only one face.
    # If that face connects to itself with a sharp angle, this code will not
    # detect that properly.  An edge connected to more than two faces is also
    # ignored because I don't know what that would look like.
    # The difference between "tight-corner" and "tight-corner-mild" is defined
    # here as being ten degrees.
    shallow_limit = 10 * pi/180
    for e, fs in edge_to_faces.iteritems():
        if len(fs) != 2:
            continue
        fs = list(fs)
        # Check if we have a vertical edge.
        curve = e.Shape.Curve
        if not isinstance(curve, Part.Line):
            continue
        edge_vec = curve.EndPoint - curve.StartPoint
        if not (is_close(edge_vec.x, 0) and is_close(edge_vec.y, 0)):
            continue
        normals = []
        # Calculate the normals of all surfaces meeting at that edge.
        for f in fs:
            params = f.Shape.Surface.parameter(curve.StartPoint)
            normals.append(f.Shape.normalAt(*params))
        # Compare angles between all normals.
        # NOTE Found that tolerance on angles needed loosening so as to not
        # give a spurious error for milled_pocket.STEP.  Should not be an issue
        # since any angle that close to zero is definitely not a problem.
        angle = normals[0].getAngle(normals[1])
        if is_close(angle, 0, tol=1e-6):
            continue
        elif angle > shallow_limit:
            possible_issue = {'issue': 'tight-corner', 'faces': None}
        else:
            possible_issue = {'issue': 'tight-corner-mild', 'faces': None}
        # Check if the corner is internal or external.  This is done by
        # creating a test point slightly away from the edge, in the direction
        # of the average of the surface normals.  This point is then projected
        # onto each surface.  If the projected point is outside of the limits
        # of at least one surface, then it is an external (convex) corner.
        test_point = ((normals[0] + normals[1]).normalize().multiply(0.001)
                      + curve.StartPoint)
        # NOTE This is the rarely used for-else construct.  The else clause
        # will happen only if no break occurs in the for loop.  This therefore
        # checks that the test point is outside all connected surfaces.
        for f in fs:
            ut, vt = f.Shape.Surface.parameter(test_point)
            u1, u2, v1, v2 = f.Shape.ParameterRange
            if not ((u1 <= ut <= u2) and (v1 <= vt <= v2)):
                break
        else:
            issues.append(possible_issue)

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
    # plane.  In each horizontal plane, check all cylinders connected to it to
    # see if they look like counterbores.
    # Also track those connecting planes, since they are otherwise non-uniform.
    counterbore_planes = set()
    for p in horizontal_planes:
        # Get all concave vertical cylinders connected to this plane.
        connected_faces = [f.Shape for f in face_to_faces[HashShape(p)]]
        connected_cyls = vertical_cylinders.intersection(connected_faces)
        concave_cyls = [c for c in connected_cyls if is_concave(c)]
        # Compare these cylinders to each other in pairs.
        for c1, c2 in combinations(concave_cyls, 2):
            # If the cylinders have the same radii or the same vertical limits,
            # then they probably can't be considered counterbores.
            if is_close(c1.Surface.Radius, c2.Surface.Radius):
                continue
            if is_close(c1.BoundBox.ZMax, c2.BoundBox.ZMax):
                continue
            # If the cylinders do not align, then don't call them counterbores.
            aligned = (is_close(c1.Surface.Center.x, c2.Surface.Center.x)
                       and is_close(c1.Surface.Center.y, c2.Surface.Center.y))
            if not aligned:
                continue
            issues.append({
                'issue': 'counter-bore',
                'faces': [faces.index(c1), faces.index(c2), faces.index(p)]})
            counterbore_planes.add(p)

    # Check for small holes and too-small corners.  These are cylinders with
    # diameters less than the kerf width.  Small holes and tight corners are
    # distinguished based on whether that cylinder connects to anything other
    # than cylinders and cones.  Tight corners are further divided into mild
    # and regular, as in the sharp corner code above.
    # NOTE This must happen after counterbore checks just because of the way
    # that test.py is currently configured.
    min_radius = 0.5 * kerf_width
    tight_corner_sets = []
    for c in vertical_cylinders:
        if not (c.Surface.Radius < min_radius and is_concave(c)):
            continue
        connected_fs = {f.Shape for f in face_to_faces[HashShape(c)]}
        interesting_fs = connected_fs - horizontal_planes - cylinders - cones
        if not interesting_fs:
            issues.append({'issue': 'small-hole', 'faces': [faces.index(c)]})
        else:
            # Track faces attached to this corner for us in small cut checks.
            tight_corner_sets.append(interesting_fs)
            u1, u2, v1, v2 = c.ParameterRange
            angle = c.normalAt(u1, v1).getAngle(c.normalAt(u2, v2))
            if angle > shallow_limit:
                issues.append({'issue': 'tight-corner', 'faces': None})
            else:
                issues.append({'issue': 'tight-corner-mild', 'faces': None})

    # Check for small cuts.  Looks for any faces (not counting the horizontal
    # ones) that are not connected to each other, checks the distance between
    # them, then checks whether the space between them is solid or void.
    seen = set()
    for f1 in set(faces) - horizontal_planes:
        seen.add(f1)
        connected_fs = {f2.Shape for f2 in face_to_faces[HashShape(f1)]}
        interesting_fs = set(faces) - connected_fs - horizontal_planes - seen
        for f2 in interesting_fs:
            # A small radius in an internal corner can be confused for a thin
            # cut.  Ignore any face pairs that are part of such a corner.
            is_tight_corner = False
            for tight_corner in tight_corner_sets:
                if tight_corner.issuperset([f1, f2]):
                    is_tight_corner = True
                    break
            if is_tight_corner:
                continue
            # Precise distance checks are expensive, so first check if the
            # bounding boxes of the two surfaces are close enough to even
            # potentially be a concern.
            bound_box1 = f1.BoundBox
            bound_box1.enlarge(0.5 * kerf_width)
            bound_box2 = f2.BoundBox
            bound_box2.enlarge(0.5 * kerf_width)
            if not bound_box1.intersect(bound_box2):
                continue
            # If bounding boxes are close, next check precise distance.
            dist, vecs, info = f1.distToShape(f2)
            if dist > kerf_width:
                continue
            # Check that the vector from one face to the other is in the same
            # general direction as the face normal.  If they are, then this is
            # empty area, and is an issue.  Otherwise, this is a thin solid
            # section that should not be a problem.
            trans1 = vecs[0][1] - vecs[0][0]
            n1 = f1.normalAt(*f1.Surface.parameter(vecs[0][0]))
            if n1.dot(trans1) < 0:
                continue
            trans2 = trans1.multiply(-1)
            n2 = f2.normalAt(*f2.Surface.parameter(vecs[0][1]))
            if n2.dot(trans2) < 0:
                continue
            issues.append({'issue': 'small-cut',
                           'faces': [faces.index(f1), faces.index(f2)]})

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
