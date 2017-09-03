# -*- coding: utf-8 -*-
"""Some basic test for the blender_tesing module
"""

import blender_testing

@blender_testing.blender_fixture()
def essai_2():
    return "result_2"
