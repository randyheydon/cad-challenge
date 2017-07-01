"""Data structures to examine the topological connectivity of shapes."""

from __future__ import absolute_import

import FreeCAD
import Part


def is_close(a, b, tol=1e-13):
    "Helper function for inexact floating point comparison."
    return abs(a - b) < tol


class HashShape(object):
    """Decorator for Part.Shape, that can be used as key in dicts. Based on isSame method.
    
    Copied in from current development version of FreeCAD, commit 7c8b9a4.
    
    """
    def __init__(self, shape):
        self.Shape = shape
        self.hash = shape.hashCode()

    def __eq__(self, other):
        return self.Shape.isSame(other.Shape)

    def __hash__(self):
        return self.hash


def is_concave(face):
    """Determine if a cylindrical or conical face is concave.

    Given a face, will return True if that face is an inside corner (concave),
    False otherwise.

    """
    u, _, v, _ = face.ParameterRange
    loc = face.valueAt(u, v)
    norm = face.normalAt(u, v)
    center = face.Surface.Center
    # Check that the vector from center to point on surface is opposite to the
    # normal vector at that point.
    return (loc - center).dot(norm) < 0
