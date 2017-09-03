# -*- coding: utf-8 -*-
"""Module for facilitating the testing of Blender scripts or addons
"""

import inspect
import subprocess
import contextlib
import tempfile
import os
import pickle

from unittest import TestCase
import importlib.util

INSIDE_BLENDER = bool(importlib.util.find_spec("bpy") is not None)


BLENDER_FAILURE_CODE = 1
BEGIN_LINE = "==========BlenderTestingBegin=========="
END_LINE = "==========BlenderTestingEnd=========="
ERROR_BEGIN_LINE = "==========BlenderTestingErrorBegin=========="
ERROR_END_LINE = "==========BlenderTestingErrorEnd=========="


def composed(*decs):
    """Compose several operators together

    Code written by Jochen Ritzel here :
    https://stackoverflow.com/questions/5409450/...
    can-i-combine-two-decorators-into-a-single-one-in-python

    """

    def deco(func):
        """Custom-function returned bu the composed decorator
        """

        for dec in reversed(decs):
            func = dec(func)
        return func
    return deco


class BlenderNotFound(Exception):
    """Exception Raised when the path to blender is not found
    """

@contextlib.contextmanager
def _closable_named_tempfile():
    """Context manager for providing a temp file

    This file can be closed to read within Blender or any other process.
    The temp file is deleted at the end of the context manager ('with' keyword)
    """
    try:
        file = tempfile.NamedTemporaryFile("w+t", delete=False)
        yield file
    finally:
        file.close()
        os.remove(file.name)


def _check_no_blender_error(code, erreur):
    import pytest

    if code == BLENDER_FAILURE_CODE:
        pytest.fail(erreur, pytrace=False)


def run_inside_blender(blender_path=None, import_paths=None):
    """Decorator Factory for running functions into Blender

    If run outside of Blender, it opens Blender and run the function into
    Blender.

    Args:
        blender_path: If None, it searches for the environment variable
        "BLENDER_PATH". If not defined, it assumes blender is aleady in
        system's path by just calling "blender"
        imports_paths: List of paths to add to system's path for blender to
        be able to find python libs of your project (or any other path you
        may want to use)
    """

    if import_paths is None:
        import_paths = []

    if INSIDE_BLENDER:
        def wrapper(func):
            """Custom-made decorator for running functions into Blender
            """
            return func

    else:
        import decorator

        if blender_path is None:
            if "BLENDER_PATH" in os.environ:

                blender_path = os.environ.get("BLENDER_PATH")

                # Remove quotes
                for char in ("'", '"'):
                    if (
                            blender_path.startswith(char) and
                            blender_path.endswith(char)
                    ):
                        blender_path = blender_path[1:-1]

            else:
                blender_path = "blender"

        @decorator.decorator
        def wrapper(func, *args, **kwargs):
            """Custom-made decorator for running functions into Blender
            """

            print("We are not inside Blender")

            f_name, m_name = _get_func_name_and_module(func)

            modules, args_strings = FunctionCallExpression.aggregate_args(
                args, kwargs
                )

            modules.update(set([m_name, "pickle"]))

            print("Function to run : {}".format(f_name))
            print("Module of the function : {}".format(m_name))

            call_string = r"{}.{}({})".format(
                m_name, f_name,
                ", ".join(args_strings)
                )

            script = "\n".join([
                r"import traceback,sys",
                r"print('{}')".format(BEGIN_LINE),
                r"try:",
                r"    import sys",
                r"    sys.path.extend({})".format(import_paths),
                r"    import {}".format(", ".join(modules)),
                r"    print('Import OK')",
                r"    {}".format(call_string),
                r"    print('{}')".format(END_LINE),
                r"except Exception as e:",
                r"    print('{}')".format(END_LINE),
                r"    print('{}')".format(ERROR_BEGIN_LINE),
                r"    print(e)",
                r"    traceback.print_exc(file=sys.stdout)",
                r"    print('{}')".format(ERROR_END_LINE),
                r"    exit({})".format(BLENDER_FAILURE_CODE),
                ])

            print(script)
            print()

            with _closable_named_tempfile() as file:
                file.write(script)
                file.close()

                call_args = [
                    blender_path, "-b",
                    "--python-exit-code", str(BLENDER_FAILURE_CODE),
                    "--python", file.name
                    ]

                print(call_args)

                try:
                    process_return = subprocess.run(
                        call_args, stdout=subprocess.PIPE,
                        stderr=None
                        )
                except FileNotFoundError:
                    raise BlenderNotFound(
                        "Blender not found (called with '{}')".format(
                            blender_path))


            stdout = process_return.stdout.decode()

            print(process_return.returncode)
            print(stdout)

            _check_no_blender_error(
                process_return.returncode,
                "Error in Blender !!!\n" + str(stdout))

    return wrapper


def _get_func_name_and_module(func):
    f_name = func.__name__
    module = inspect.getmodule(func)
    m_name = module.__name__

    if m_name == "__main__":
        m_name = os.path.splitext(
            os.path.basename((inspect.getfile(func))))[0]

    print(m_name)

    return f_name, m_name


class FunctionCallExpression:
    """Class that represents a python expression that can be called later
    inside Blender

    """

    def __init__(self):
        self.modules = set()
        self.call_string = None

    def __repr__(self):
        return (
            "Fixture(modules={},call_string={})".format(
                self.modules, self.call_string)
            )

    @staticmethod
    def aggregate_args(args, kwargs):
        """Aggregate various args and kwargs for using through subprocess

        Args:
            args: List of args that can be either:
                FunctionCallExpression instances
                Any pickable instance
            kwargs: Dict of keywords. Values must be pickelable.

        Returns:
            A modules,args_string tuple:
                modules: Set of modules that should be imported for using this
                expressions.
                args_string: A list of strings that use either calls of
                FunctionCallExpression or serialized strings of pickelable
                objects.
        """

        args_strings = []
        modules = set()

        for arg in args:
            if isinstance(arg, FunctionCallExpression):
                modules.update(arg.modules)
                args_strings.append(arg.call_string)
            else:
                serialized_string = pickle.dumps(
                    arg)
                args_strings.append(
                    "pickle.loads({})".format(
                        serialized_string)
                    )
        args_strings.append("**pickle.loads({})".format(
            pickle.dumps(kwargs)
            ))

        return modules, args_strings


    def build(self, func, args):
        """Builds the object.

        Args:
            func: The function that should be used in this expression
            args: List of FunctionCallExpression that should be used as
                  function arguments
        """

        f_name, m_name = _get_func_name_and_module(func)

        # We update the list of modules that blender should import
        # to be able to use this fixture
        modules = set()
        modules.add(m_name)
        for arg in args:
            modules.update(arg.modules)

        # We build the string that blender should call to run this
        # fixture
        call_string = "{}.{}({})".format(
            m_name,
            f_name,
            ", ".join(a.call_string for a in args)
            )

        self.call_string = call_string
        self.modules = modules


class BadFixtureArgument(Exception):
    """Exception raised when a fixture gets a wrong argument
    """


def blender_fixture():
    """Decorator Factory for using pytest fixtures inside Blender.

    It gives a decorator that behave as folowing.
    When run inside of Blender : it is a simple function
    When run outside of Blender : it is a py.test fixture, which calls all
    other ficture (they MUST be blender_fixture as well). The underlying
    function is not called outside of blender. The scope is always equivalent
    to py.test "function", because the fixture is called each time (because
    we run each test in a new Blender instance, that has no idea about the
    other tests nor py.test"""



    if INSIDE_BLENDER:
        def inside_blender_wrapper(func):
            """Decorator for when we are inside of Blender

            It returns a decorated function which sort of mimics the py.test
            fixtures
            """

            return_values = dict()

            def decorated_function(*args):
                """Decorated function returned by the blender_fixture decorator
                when inside Blender

                It uses the function closure to remember if the function should
                be called or if has already been (and and this cas returns
                the return value directly)
                """

                key = (args)
                if key not in return_values:
                    return_values[key] = func(*args)

                return return_values[key]

            return decorated_function

        return inside_blender_wrapper

    import pytest
    import decorator

    @decorator.decorator
    def outside_blender_wrapper(func, *args):
        """Decorator for when we are outside of Blender.

        It wraps the function for calling it in Blender through command
        line.
        """

        for arg in args:
            if not isinstance(arg, FunctionCallExpression):
                raise BadFixtureArgument("Fixture got non fixture argument !")

        exp = FunctionCallExpression()
        exp.build(func, args)
        return exp

    return composed(pytest.fixture, outside_blender_wrapper)


def _build_assert_functions():
    test_case = TestCase()
    for assert_func_name in dir(test_case):
        if (not assert_func_name.startswith("assert") or
                assert_func_name.endswith("_")):
            continue

        globals()[assert_func_name] = (
            test_case.__getattribute__(assert_func_name)
            )
_build_assert_functions()
