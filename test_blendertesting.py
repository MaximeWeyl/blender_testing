# -*- coding: utf-8 -*-
"""Some basic tests for the blender_testing module
"""

# pylint: disable=w0621

import os
import blender_testing

# pylint: disable=c0103
run_blender = blender_testing.run_inside_blender(
    import_paths=[os.getcwd()]
    )

# pylint: disable=c0103
blender_fixture = blender_testing.blender_fixture()


@blender_fixture
def essai(essai_2):
    return "Coucou <{}>".format(essai_2)


@run_blender
def test_function():
    import bpy  # pylint: disable=import-error
    scene = bpy.data.scenes[0]
    objects = list(scene.objects)
    assert len(objects) == 3


@run_blender
def test_function_2(essai):
    print(essai)
    import bpy  # pylint: disable=import-error
    scene = bpy.data.scenes[0]
    assert scene.name == "Scene"

