The blender_testing module was created to help you test your Blender tests/addons.
From your favorite python IDE, you can run a function inside Blender. 


# Run a function inside Blender

`blender_testing` offers a `run_inside_blender` decorator for running a function into Blender and not in your current python environment.



```

import os
import blender_testing

run_blender = blender_testing.run_inside_blender(
    import_paths=[os.getcwd()],
    blender_path=r"C:\Program Files\Blender Foundation\Blender\blender.exe"
    )


@run_blender
def my_function(hello):
    import bpy  # pylint: disable=import-error
    scene = bpy.data.scenes[0]
    objects = list(scene.objects)
    print(objects)
    print(hello)

if __name__ == "__main__":
    my_function('Hello world')
```

As you can see, we used the arguments `import_paths` for letting Blender know from where it can import modules. 
We also use the `blender_path` argument. It is not required if "blender" is accessible within your PATH, or if you have set the `BLENDER_PATH` environment variable. 


In order to work, this decorator invoke it's own blender instance, loads the necessary modules and calls the correct function. If we had forgotten the `if __name__ == "__main__"`, the my_function would have been run twice (at loading the module, and then at running the function). So be careful !


# Use within py.test

You can use it within py.test. The rule for finding tests has not changed, just let the test function names begin with "test_".

As usual with py.test, all arguments are considered as fixtures. 

If you use normal `pytest.fixture` for your fictures, they will be run before entering Blender. If you want to use fixtures INSIDE Blender, you have to use another decorator `blender_testing.blender_fixture` : 


```
import os
import blender_testing

if blender_testing.INSIDE_BLENDER:
    import bpy 


run_blender = blender_testing.run_inside_blender(
    import_paths=[os.getcwd()]
    )


blender_fixture = blender_testing.blender_fixture()


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
```


Blender testing's fixture do not have a scope. It's always a 'function' scope, because eachtest  function runs into it's own Blender instance. 

As you can see, blender_testing comes with a set of `assert*` functions. It simply copies all the `assert*` methods from `unittest.TestCase`. For documentation, please see the one for unittest.

# Limitations

blender_testing does not offer a 'tear down functionnality' for it's internal Blender fixtures, as py.test does (with the `yield` instruction). It could be an improvement, but for now, I had no need for it. 

You cannot use any magical stuff from py.test like the special `request` fixture argument. 



