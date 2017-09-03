# -*- coding: utf-8 -*-
"""Test the fixture inside Blender
"""

# pylint: disable=w0621
# pylint: disable=e1101

import os
import blender_testing

if blender_testing.INSIDE_BLENDER:
    import bpy # pylint: disable=e0401

# pylint: disable=c0103
run_blender = blender_testing.run_inside_blender(
    import_paths=[os.getcwd()]
    )

# pylint: disable=c0103
blender_fixture = blender_testing.blender_fixture()


def build_fixture_1():
    """Builder for the fixture_1

    fixture_1 uses a closure for returning a new, incremented int, each time
    """
    counter = [0]

    @blender_fixture
    def fixture_1():
        """Fixture that returns an int, which is incremented at each call
        """
        counter[0] = counter[0] + 1
        return counter[0]

    return fixture_1

fixture_1 = build_fixture_1()


@blender_fixture
def fixture_2(fixture_1):
    """Fixture that just calls fixture_1 and returns the same
    """

    return fixture_1


@run_blender
def test_fixtures(fixture_1, fixture_2):
    """Test that must proove that a fixture is always called once
    """

    blender_testing.assertEquals(fixture_1, fixture_2)


@blender_fixture
def scene():
    """Returns a default scene, which is empty, except if other used fixtures
    add something to it
    """

    scene = bpy.data.scenes.new("SceneDeTest")
    return scene


@blender_fixture
def mesh_object(scene):
    """Adds a default empty mesh object to the default scene
    """

    mesh = bpy.data.meshes.new("TestMesh")
    mesh_o = bpy.data.objects.new("TestMeshO", mesh)
    scene.objects.link(mesh_o)
    return mesh_o


@run_blender
def test_function(scene, mesh_object):
    """Test to see if mesh_object is really in scene

    It means that the scene fixture should be called only once, and not 2 (
    one for this test and one for the mesh_object fixture)
    """

    blender_testing.assertIn(mesh_object, scene.objects.values())
