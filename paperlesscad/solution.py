"""
You may create as many additional packages or modules as you needed. Your
solution will be accessed by the test cases by calling the function `dfm_check`
in this module. The function will be a passed a path to a STEP file. We 
strongly suggest using FreeCAD (as shown below), but you may use any 
open-source and freely available library you would like. If the library is not
available via `pip`, please include installation instructions. 
"""

import FreeCAD
import Part


def dfm_check(step_path):
    """Place your solution in this function. Create and call other functions, 
    classes, modules, and packages as required."""
    shape = Part.Shape()
    shape.read(step_path)
    issues = []
    # analyze shape!
    # return DfM issues!
    # for example:
    # issues.append({'issue': 'chamfer', 'faces': None})
    return {'issues': issues}
