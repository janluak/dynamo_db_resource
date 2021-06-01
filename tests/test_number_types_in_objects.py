from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from copy import deepcopy
from decimal import Decimal


float_dict = {
    "some_string": "abcdef",
    "some_int": 42,
    "some_float": 13.42,
    "some_dict": {"key1": "value1", "key2": 2},
    "some_nested_dict": {"KEY1": {"subKEY1": "subVALUE1", "subKEY2": 42.24}},
    "some_array": [
        "array_string",
        13,
        {"KEY1": {"arraySubKEY1": "subVALUE1", "arraySubKEY2": 21.12}},
    ],
}

decimal_dict = {
    "some_string": "abcdef",
    "some_int": 42,
    "some_float": Decimal("13.42"),
    "some_dict": {"key1": "value1", "key2": 2},
    "some_nested_dict": {"KEY1": {"subKEY1": "subVALUE1", "subKEY2": Decimal("42.24")}},
    "some_array": [
        "array_string",
        13,
        {"KEY1": {"arraySubKEY1": "subVALUE1", "arraySubKEY2": Decimal("21.12")}},
    ],
}


class TestTraverseDict(TestCase):
    actual_cwd = str()

    @classmethod
    def setUpClass(cls) -> None:
        os_environ["STAGE"] = "TEST"
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config_empty.json"

        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)

    def setUp(self) -> None:
        self._float_dict = deepcopy(float_dict)
        self._decimal_dict = deepcopy(decimal_dict)

    def tearDown(self) -> None:
        global float_dict
        float_dict = self._float_dict

        global decimal_dict
        decimal_dict = self._decimal_dict

    def test_float_to_decimal(self):
        from dynamo_db_resource._number_types_in_objects import (
            object_with_float_to_decimal,
        )

        self.assertEqual(decimal_dict, object_with_float_to_decimal(float_dict))

    def test_decimal_to_float(self):
        from dynamo_db_resource._number_types_in_objects import (
            object_with_decimal_to_float,
        )

        self.assertEqual(float_dict, object_with_decimal_to_float(decimal_dict))

    def test_string_input(self):
        from dynamo_db_resource._number_types_in_objects import (
            object_with_float_to_decimal,
            object_with_decimal_to_float,
        )

        self.assertEqual("abc", object_with_decimal_to_float("abc"))
        self.assertEqual("abc", object_with_float_to_decimal("abc"))

    def test_number_input(self):
        from dynamo_db_resource._number_types_in_objects import (
            object_with_float_to_decimal,
            object_with_decimal_to_float,
        )

        self.assertEqual(3, object_with_decimal_to_float(3))
        self.assertEqual(3, object_with_float_to_decimal(3))

        self.assertEqual(3.5, object_with_decimal_to_float(3.5))
        self.assertEqual(Decimal(3.5), object_with_float_to_decimal(3.5))

    def test_list_input(self):
        from dynamo_db_resource._number_types_in_objects import (
            object_with_float_to_decimal,
            object_with_decimal_to_float,
        )

        self.assertEqual(
            ["abc", 1, {"number": 3.5}],
            object_with_decimal_to_float(["abc", 1, {"number": Decimal(3.5)}]),
        )
        self.assertEqual(
            ["abc", 1, {"number": Decimal(3.5)}],
            object_with_float_to_decimal(["abc", 1, {"number": 3.5}]),
        )
