import os
import sys
import torch
from torch.testing._internal.jit_utils import JitTestCase
from torch.jit._monkeytype_config import _IS_MONKEYTYPE_INSTALLED
from typing import List, Dict, Tuple  # noqa F401

# Make the helper files in test/ importable
pytorch_test_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(pytorch_test_dir)

if not _IS_MONKEYTYPE_INSTALLED:
    print("monkeytype is not installed. Skipping tests for Profile-Directed Typing ", file=sys.stderr)
    JitTestCase = object  # type: ignore[misc, assignment] # noqa: F811

if __name__ == "__main__":
    raise RuntimeError(
        "This test file is not meant to be run directly, use:\n\n"
        "\tpython test/test_jit.py TESTNAME\n\n"
        "instead."
    )

def test_sum(a, b):
    return a + b

def test_sub(a, b):
    return a - b

def test_mul(a, b):
    return a * b

def test_args_complex(real, img):
    return torch.complex(real, img)

def test_bool(a):
    if a:
        return -1
    else:
        return 0

def test_str(a):
    if a == "":
        return False
    else:
        return True

def test_list_and_tuple(a):
    return sum(a)

def test_dict(a):
    return a['foo']

def test_dict_int_list(a):
    return a[1]

def test_multiple_types(a):
    assert not isinstance(a, bool)
    return a

def test_multiple_types_2(a):
    assert a is not None
    return a

class TestPDT(JitTestCase):
    """
    A suite of tests for profile directed typing in TorchScript.
    """
    def setUp(self):
        super(TestPDT, self).setUp()

    def tearDown(self):
        super(TestPDT, self).tearDown()

    def test_pdt(self):
        scripted_fn_add = torch.jit._script_pdt(test_sum, example_inputs=[(3, 4)])
        scripted_fn_sub = torch.jit._script_pdt(test_sub, example_inputs=[(3.9, 4.10)])
        scripted_fn_mul = torch.jit._script_pdt(test_mul, example_inputs=[(-10, 9)])
        scripted_fn_bool = torch.jit._script_pdt(test_bool, example_inputs=[(True,)])
        scripted_fn_str = torch.jit._script_pdt(test_str, example_inputs=[("",)])
        scripted_fn_complex = torch.jit._script_pdt(test_args_complex, example_inputs=[(torch.rand(3, 4), torch.rand(3, 4))])

        self.assertEqual(scripted_fn_add(10, 2), test_sum(10, 2))
        self.assertEqual(scripted_fn_sub(6.5, 2.9), test_sub(6.5, 2.9))
        self.assertEqual(scripted_fn_mul(-1, 3), test_mul(-1, 3))
        self.assertEqual(scripted_fn_bool(True), test_bool(True))
        self.assertEqual(scripted_fn_str("abc"), test_str("abc"))

        arg1, arg2 = torch.rand(3, 4), torch.rand(3, 4)
        self.assertEqual(scripted_fn_complex(arg1, arg2), test_args_complex(arg1, arg2))

    def test_pdt_list(self):
        scripted_fn_float = torch.jit._script_pdt(test_list_and_tuple, example_inputs=[([4.9, 8.9],)])
        self.assertEqual(scripted_fn_float([11.9, 7.6]), test_list_and_tuple([11.9, 7.6]))

        scripted_fn_bool = torch.jit._script_pdt(test_list_and_tuple, example_inputs=[([True, False, True],)])
        self.assertEqual(scripted_fn_bool([True, True, True]), test_list_and_tuple([True, True, True]))

        scripted_fn_int = torch.jit._script_pdt(test_list_and_tuple, example_inputs=[([3, 4, 5], )])
        self.assertEqual(scripted_fn_int([1, 2, 3]), test_list_and_tuple([1, 2, 3]))

    def test_pdt_tuple(self):
        scripted_fn_float = torch.jit._script_pdt(test_list_and_tuple, example_inputs=[((4.9, 8.9),)])
        self.assertEqual(scripted_fn_float((11.9, 7.6)), test_list_and_tuple((11.9, 7.6)))

        scripted_fn_bool = torch.jit._script_pdt(test_list_and_tuple, example_inputs=[((True, False, True),)])
        self.assertEqual(scripted_fn_bool((True, True, True)), test_list_and_tuple((True, True, True)))

        scripted_fn_int = torch.jit._script_pdt(test_list_and_tuple, example_inputs=[((3, 4, 5), )])
        self.assertEqual(scripted_fn_int((1, 2, 3)), test_list_and_tuple((1, 2, 3)))

    def test_pdt_dict(self):
        _input = {'foo' : True, 'bar': False}
        scripted_fn = torch.jit._script_pdt(test_dict, example_inputs=[(_input,)])
        self.assertEqual(scripted_fn({'foo' : False, 'bar': True}, ), test_dict({'foo' : False, 'bar': True}, ))

    def test_pdt_dict_1(self):
        _input = {0 : [True, False], 1: [False, True]}
        scripted_fn = torch.jit._script_pdt(test_dict_int_list, example_inputs=[(_input,)])
        self.assertEqual(scripted_fn({0 : [False, False], 1: [True, True]}, ),
                         test_dict_int_list({0 : [False, False], 1: [True, True]}, ))

    def test_any(self):
        scripted_fn = torch.jit._script_pdt(test_multiple_types, example_inputs=[(1,), ("abc", ), (8.9,), ([3, 4, 5], )])
        self.assertEqual(scripted_fn(10), test_multiple_types(10))
        self.assertEqual(scripted_fn("def"), test_multiple_types("def"))
        self.assertEqual(scripted_fn(7.89999), test_multiple_types(7.89999))
        self.assertEqual(scripted_fn([10, 11, 14]), test_multiple_types([10, 11, 14]))

        scripted_fn_2 = torch.jit._script_pdt(test_multiple_types_2, example_inputs=[(1,), ("abc", ), (8.9,),
                                              ([3, 4, 5],), (True, ), ({"a": True}, ), ])
        self.assertEqual(scripted_fn_2(10), test_multiple_types_2(10))
        self.assertEqual(scripted_fn_2("def"), test_multiple_types_2("def"))
        self.assertEqual(scripted_fn_2(7.89999), test_multiple_types_2(7.89999))
        self.assertEqual(scripted_fn_2([10, 11, 14]), test_multiple_types_2([10, 11, 14]))
        self.assertEqual(scripted_fn_2(False), test_multiple_types_2(False))
        self.assertEqual(scripted_fn_2({"abc" : True, "def": False}), test_multiple_types_2({"abc" : True, "def": False}))