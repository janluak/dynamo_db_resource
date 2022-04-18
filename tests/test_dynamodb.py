from unittest import TestCase, skip, mock
from os import environ as os_environ
from pathlib import Path
from os import chdir, getcwd
import json
import sys
from copy import deepcopy
from moto import mock_dynamodb2
from pytest import fixture

with open(Path(Path(__file__).parent, "test_data/items/test_item.json")) as fi:
    test_item = json.load(fi)
test_item_primary = {"primary_partition_key": "some_identification_string"}


@fixture
def set_stack_os_environ():
    os_environ["DYNAMO_DB_RESOURCE_STAGE_NAME"] = "TEST"
    os_environ["DYNAMO_DB_RESOURCE_STACK_NAME"] = "someStack"
    yield
    del os_environ["DYNAMO_DB_RESOURCE_STAGE_NAME"]
    del os_environ["DYNAMO_DB_RESOURCE_STACK_NAME"]


@fixture
def set_stage_os_environ():
    os_environ["DYNAMO_DB_RESOURCE_STAGE_NAME"] = "TEST"
    yield
    del os_environ["DYNAMO_DB_RESOURCE_STAGE_NAME"]


@mock_dynamodb2
def test_stack_name_in_table_name(set_stack_os_environ):
    from dynamo_db_resource.dynamo_db_table import _cast_table_name
    assert _cast_table_name("TableName") == "TEST-someStack-TableName"


@mock_dynamodb2
def test_stage_name_in_table_name(set_stage_os_environ):
    from dynamo_db_resource.dynamo_db_table import _cast_table_name
    assert _cast_table_name("TableName") == "TEST-TableName"


@mock_dynamodb2
def test_no_additional_name_in_table_name():
    from dynamo_db_resource.dynamo_db_table import _cast_table_name
    assert _cast_table_name("TableName") == "TableName"


@mock_dynamodb2
class TestDynamoDBBase(TestCase):
    table_name = "TableForTests"
    actual_cwd = str()

    def setUp(self) -> None:
        for key in list(sys.modules.keys()):
            if any(key.startswith(i) for i in ["dynamo_db_resource", "test"]):
                del sys.modules[key]
        os_environ["STAGE"] = "TEST"
        os_environ["AWS_REGION"] = "eu-central-1"
        os_environ["DYNAMO_DB_RESOURCE_SCHEMA_ORIGIN"] = "file"
        os_environ["DYNAMO_DB_RESOURCE_SCHEMA_DIRECTORY"] = "test_data/tables/"

        self.actual_cwd = getcwd()
        chdir(Path(__file__).parent)

        from dynamo_db_resource.table_existence import (
            create_dynamo_db_table_from_schema,
        )

        with open(Path(Path(__file__).parent, f"test_data/tables/{self.table_name}.json")) as f:
            self.raw_schema = json.load(f)
        create_dynamo_db_table_from_schema(self.raw_schema)

    def tearDown(self) -> None:
        from dynamo_db_resource.table_existence import delete_dynamo_db_table
        delete_dynamo_db_table(self.table_name, require_confirmation=False)
        chdir(self.actual_cwd)


class TestDynamoDBQuery(TestDynamoDBBase):
    pass


class TestDynamoDBQueryWithUpdateDictionaries(TestDynamoDBQuery):
    def test_update_query_with_string_attributes(self):
        expected_expression = "set #AA = :aa, #AB = :ab"
        expected_expression_name_mapping = {"#AA": "attribute1", "#AB": "attribute2"}

        update_data = {
            "attribute1": "new_value1",
            "attribute2": "new_value2",
        }
        expected_update_values = {":aa": "new_value1", ":ab": "new_value2"}

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(update_data)
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    def test_update_query_with_number_attributes(self):
        expected_expression = "set #AA = :aa, #AB = :ab"
        expected_expression_name_mapping = {"#AA": "attribute1", "#AB": "attribute2"}

        update_data = {
            "attribute1": 2943,
            "attribute2": 1.2443,
        }

        from decimal import Decimal

        expected_update_values = {":aa": 2943, ":ab": Decimal("1.2443")}

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(update_data)
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    def test_update_query_with_dicts(self):
        expected_expression = "set #AA.#AB = :aa, " "#AA.#AC = :ab, " "#AD.#AE = :ac"
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1",
            "#AC": "child2",
            "#AD": "parent2",
            "#AE": "child3",
        }

        update_data = {
            "parent1": {"child1": "new_child1", "child2": "new_child2"},
            "parent2": {"child3": "new_child3"},
        }

        expected_update_values = {
            ":aa": "new_child1",
            ":ab": "new_child2",
            ":ac": "new_child3",
        }

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(update_data)
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    def test_update_query_with_nested_dicts(self):
        expected_expression = (
            "set #AA.#AB.#AC = :aa, " "#AA.#AD = :ab, " "#AE.#AF = :ac"
        )
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1",
            "#AC": "grandchild1",
            "#AD": "child2",
            "#AE": "parent2",
            "#AF": "child3",
        }

        update_data = {
            "parent1": {
                "child1": {"grandchild1": "new_child1"},
                "child2": "new_child2",
            },
            "parent2": {"child3": "new_child3"},
        }

        expected_update_values = {
            ":aa": "new_child1",
            ":ab": "new_child2",
            ":ac": "new_child3",
        }

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(update_data)
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    # def test_update_query_add_attribute(self):
    #     expected_expression = "add attribute1 = :attribute1, " \
    #                           "attribute2 = :attribute2"
    #     update_data = {
    #         "attribute1": "new_value1",
    #         "attribute2": "new_value2",
    #     }
    #
    #     from aws_serverless_wrapper.database.dynamo_db import Table
    #     t = Table(self.table_name)
    #
    #     calculated_expression, _ = t._create_update_replace_expression(update_data, add_instead_of_replacement=True)
    #     self.assertEqual(expected_expression, calculated_expression)
    #
    # def test_update_add_attribute(self):
    #     new_attribute = {"additional_key": "additional_value"}
    #     from aws_serverless_wrapper.database.dynamo_db import Table
    #     t = Table(self.table_name)
    #
    #     t.put(test_item)
    #
    #     t.update_add_new_attribute(test_item_primary, new_attribute)
    #
    #     self.assertEqual(new_attribute["additional_key"], t.get(**test_item_primary)["additional_key"])
    #

    def test_append_list_with_item(self):
        expected_expression = (
            "set #AA.#AB = list_append(#AA.#AB, :aa), "
            "#AC.#AD = list_append(#AC.#AD, :ab)"
        )
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1",
            "#AC": "parent2",
            "#AD": "child3",
        }

        update_data = {
            "parent1": {"child1": ["new_child1", "new_child2"]},
            "parent2": {"child3": ["new_child3"]},
        }

        expected_update_values = {
            ":aa": ["new_child1", "new_child2"],
            ":ab": ["new_child3"],
        }

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(update_data, list_operation=True)
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    def test_add_set_with_item(self):
        expected_expression = (
            "add #AA.#AB :aa"
        )
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1"
        }

        update_data = {
            "parent1": {"child1": {"2", "3"}}
        }

        expected_update_values = {
            ":aa": {"2", "3"}
        }

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(update_data, set_operation=True)
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    def test_remove_from_set(self):
        expected_expression = (
            "delete #AA.#AB :aa"
        )
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1"
        }

        path_to_attribute = [["parent1", "child1"]]

        expected_update_values = {
            ":aa": {"2", "3"}
        }

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
        ) = t._create_remove_expression(path_to_attribute, set_items_if_set=[{"2", "3"}])
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)


class TestDynamoDBQueryDirectProvisionOfPath(TestDynamoDBQuery):
    def test_update_query_direct_provision_of_paths_and_values(self):
        expected_expression = (
            "set #AA.#AB.#AC = :aa, " "#AA.#AD = :ab, " "#AE.#AF = :ac"
        )
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1",
            "#AC": "grandchild1",
            "#AD": "child2",
            "#AE": "parent2",
            "#AF": "child3",
        }

        expected_update_values = {
            ":aa": "new_child1",
            ":ab": "new_child2",
            ":ac": "new_child3",
        }

        update_paths = [
            ["parent1", "child1", "grandchild1"],
            ["parent1", "child2"],
            ["parent2", "child3"],
        ]
        update_values = ["new_child1", "new_child2", "new_child3"]

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(
            paths_to_new_data=update_paths, values_per_path=update_values
        )
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    def test_append_query_direct_provision_of_paths_and_values(self):
        expected_expression = (
            "set #AA.#AB.#AC = list_append(#AA.#AB.#AC, :aa), "
            "#AA.#AD = list_append(#AA.#AD, :ab), "
            "#AE.#AF = list_append(#AE.#AF, :ac)"
        )
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1",
            "#AC": "grandchild1",
            "#AD": "child2",
            "#AE": "parent2",
            "#AF": "child3",
        }

        expected_update_values = {
            ":aa": "new_child1",
            ":ab": "new_child2",
            ":ac": "new_child3",
        }

        update_paths = [
            ["parent1", "child1", "grandchild1"],
            ["parent1", "child2"],
            ["parent2", "child3"],
        ]
        update_values = ["new_child1", "new_child2", "new_child3"]

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(
            paths_to_new_data=update_paths,
            values_per_path=update_values,
            list_operation=True,
        )
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    def test_partly_update_partly_append_query_direct_provision_of_paths_and_values(
        self,
    ):
        expected_expression = (
            "set #AA.#AB.#AC = :aa, "
            "#AA.#AD = list_append(#AA.#AD, :ab), "
            "#AE.#AF = :ac"
        )
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1",
            "#AC": "grandchild1",
            "#AD": "child2",
            "#AE": "parent2",
            "#AF": "child3",
        }

        expected_update_values = {
            ":aa": "new_child1",
            ":ab": "new_child2",
            ":ac": "new_child3",
        }

        update_paths = [
            ["parent1", "child1", "grandchild1"],
            ["parent1", "child2"],
            ["parent2", "child3"],
        ]
        update_values = ["new_child1", "new_child2", "new_child3"]

        update_list_operation = [False, True, False]

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        (
            calculated_expression,
            calculated_values,
            calculated_name_mapping,
            _,
        ) = t._create_update_expression(
            paths_to_new_data=update_paths,
            values_per_path=update_values,
            list_operation=update_list_operation,
        )
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_update_values, calculated_values)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)

    def test_remove_attribute(self):
        expected_expression = "remove #AA.#AB, #AA.#AC"
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1",
            "#AC": "child2"
        }

        remove_paths = [["parent1", "child1"], ["parent1", "child2"]]

        from dynamo_db_resource import Table
        t = Table(self.table_name)

        calculated_expression, _, calculated_name_mapping = t._create_remove_expression(remove_paths)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)
        self.assertEqual(expected_expression, calculated_expression)

    def test_remove_list_entry(self):
        expected_expression = "remove #AA.#AB[0]"
        expected_expression_name_mapping = {
            "#AA": "parent1",
            "#AB": "child1"
        }

        remove_path = [["parent1", "child1"]]

        from dynamo_db_resource import Table
        t = Table(self.table_name)

        calculated_expression, _, calculated_name_mapping = t._create_remove_expression(remove_path, 0)
        self.assertEqual(expected_expression, calculated_expression)
        self.assertEqual(expected_expression_name_mapping, calculated_name_mapping)


class TestDynamoDBQueryConditions(TestDynamoDBQuery):
    def test_no_conditions(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        condition = t._build_conditions(False, False, dict())

        self.assertEqual(None, condition)

    def test_item_exists(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        condition = t._item_exists_condition

        self.assertEqual("attribute_exists(primary_partition_key)", condition)

    def test_item_not_exists(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        condition = t._item_not_exists_condition

        self.assertEqual("attribute_not_exists(primary_partition_key)", condition)

    def test_update_attribute_if_exists(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        paths = [["p1", "p2"]]
        name_map = {"#AA": "p1", "#AB": "p2"}
        condition, att_key_map, att_val_map = t._build_conditions(paths, False, name_map)

        self.assertEqual("attribute_exists(#AA.#AB)", condition)
        self.assertEqual(dict(), att_key_map)
        self.assertEqual(dict(), att_val_map)

    def test_update_attribute_if_multiple_exists(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        paths = [["p1", "p2"], ["p1", "p3"]]
        name_map = {"#AA": "p1", "#AB": "p2", "#AC": "p3"}
        condition, att_key_map, att_val_map = t._build_conditions(paths, False, name_map)

        self.assertEqual(
            "attribute_exists(#AA.#AB) and attribute_exists(#AA.#AC)", condition
        )
        self.assertEqual(dict(), att_key_map)
        self.assertEqual(dict(), att_val_map)

    def test_set_attribute_if_not_exists(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        paths = [["p1", "p2"]]
        name_map = {"#AA": "p1", "#AB": "p2"}
        condition, att_key_map, att_val_map = t._build_conditions(False, paths, name_map)

        self.assertEqual("attribute_not_exists(#AA.#AB)", condition)
        self.assertEqual(dict(), att_key_map)
        self.assertEqual(dict(), att_val_map)

    def test_direct_given_condition(self):
        from dynamo_db_resource import Table
        from dynamo_db_resource.conditions import Attr

        t = Table(self.table_name)

        paths = [["p1", "p2"]]
        name_map = {"#AA": "p1", "#AB": "p2"}
        user_condition = Attr("some_attribute").eq("some_value")
        condition, att_key_map, att_val_map = t._build_conditions(False, paths, name_map, user_condition)

        self.assertEqual("attribute_not_exists(#AA.#AB) and #n0 = :v0", condition)
        self.assertEqual({"#n0": "some_attribute"}, att_key_map)
        self.assertEqual({":v0": "some_value"}, att_val_map)


class TestDynamoDB(TestDynamoDBBase):
    def test_cast_primary_key(self):
        from dynamo_db_resource import Table
        t = Table("TableForTests")

        self.assertEqual({"primary_partition_key": "pk"}, t._cast_primary_keys("pk"))
        self.assertEqual({"primary_partition_key": "pk"}, t._cast_primary_keys({"primary_partition_key": "pk"}))
        self.assertEqual(
            [{"primary_partition_key": "pk1"}, {"primary_partition_key": "pk2"}],
            t._cast_primary_keys(["pk1", "pk2"], batch=True)
        )
        self.assertEqual(
            [{"primary_partition_key": "pk1"}, {"primary_partition_key": "pk2"}],
            t._cast_primary_keys([{"primary_partition_key": "pk1"}, {"primary_partition_key": "pk2"}], batch=True)
        )

        tr = Table("TableWithRange")
        expected_primary = {"primary_partition_key": "pk", "range_key": "rk"}
        self.assertEqual(expected_primary, tr._cast_primary_keys("pk", "rk"))
        self.assertEqual(expected_primary, tr._cast_primary_keys({"primary_partition_key": "pk", "range_key": "rk"}))
        self.assertEqual(
            [{"primary_partition_key": "pk1", "range_key": "rk1"}, {"primary_partition_key": "pk1", "range_key": "rk2"}],
            tr._cast_primary_keys([["pk1", "rk1"], ["pk1", "rk2"]], batch=True)
        )
        self.assertEqual(
            [{"primary_partition_key": "pk1", "range_key": "rk1"}, {"primary_partition_key": "pk1", "range_key": "rk2"}],
            tr._cast_primary_keys([{"primary_partition_key": "pk1", "range_key": "rk1"}, {"primary_partition_key": "pk1", "range_key": "rk2"}], batch=True)
        )

    def test_put(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)
        t.put(test_item)

        loaded_item = t.get_and_delete(**test_item_primary)

        self.assertEqual(test_item, loaded_item)

    def test_get_unknown_entry(self):
        get_key = {"primary_partition_key": "abc"}

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        with self.assertRaises(FileNotFoundError) as fnf:
            t.get(**get_key)

        self.assertEqual(
            {
                "statusCode": 404,
                "body": f"{get_key} not found in {t.name}",
                "headers": {"Content-Type": "text/plain"},
            },
            fnf.exception.args[0],
        )

    def test_get_with_wrong_primary(self):
        get_key = {"wrong_key": "some_identification_string"}

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        with self.assertRaises(LookupError) as LE:
            t.get(**get_key)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": f"Wrong primary for {t.name}: required for table is {t.pk}; "
                f"missing {t.pk}",
                "headers": {"Content-Type": "text/plain"},
            },
            LE.exception.args[0],
        )

    def test_projection_expression(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        self.assertEqual(
            ("#AA,#AB", {"#AA": "some_value", "#AB": "primary_partition_key"}),
            t._create_projection_expression("some_value")
        )
        self.assertEqual(
            ("#AA,#AB", {"#AA": "some_value", "#AB": "primary_partition_key"}),
            t._create_projection_expression(["some_value"])
        )
        self.assertEqual(
            ("#AA,#AB,#AC", {"#AA": "some_value", "#AB": "some_int", "#AC": "primary_partition_key"}),
            t._create_projection_expression(["some_value", "some_int"])
        )
        self.assertEqual(
            ("#AA.#AB,#AC", {'#AA': 'some_nested_dict', '#AB': 'KEY1', '#AC': 'primary_partition_key'}),
            t._create_projection_expression([["some_nested_dict", "KEY1"]])
        )
        self.assertEqual(
            ("#AA.[0],#AB", {"#AA": "some_array", "#AB": "primary_partition_key"}),
            t._create_projection_expression([["some_array", 0]])
        )

    @skip("issue in moto: ProjectionExpression not working on get_item (#4370)")
    def test_get_specified_attributes(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.get(
            attributes_to_get=["some_string", ["some_nested_dict", "KEY1", "subKEY1"], ["some_array", 0]],
            **test_item_primary
        )
        self.assertEqual(len(response), 3)

        self.assertEqual(
            1,
            response["some_string"]
        ),
        self.assertNotIn(
            "some_dict",
            response
        )

    def test_put_item_missing_keys(self):
        item = test_item_primary.copy()
        from dynamo_db_resource import Table
        from dynamo_db_resource.exceptions import ValidationError

        t = Table(self.table_name)

        with self.assertRaises(ValidationError) as TE:
            t.put(item)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": f"'some_string' is a required property for table {self.table_name} and is missing",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_put_get_and_delete_item(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)
        result = t.get(**test_item_primary)

        self.assertEqual(test_item, result)

        t.delete(**test_item_primary)

        with self.assertRaises(FileNotFoundError) as FNF:
            t.get(**test_item_primary)

        self.assertEqual(
            {
                "statusCode": 404,
                "body": f"{test_item_primary} not found in {self.table_name}",
                "headers": {"Content-Type": "text/plain"},
            },
            FNF.exception.args[0],
        )

    def test_doubled_put_item_with_same_primary(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)

        with self.assertRaises(FileExistsError) as FEE:
            t.put(test_item)

        self.assertEqual(
            {
                "statusCode": 409,
                "body": f"Item is already existing.\nTable: {self.table_name}\nItem: {test_item}",
                "headers": {"Content-Type": "text/plain"},
            },
            FEE.exception.args[0],
        )

    def test_doubled_put_item_with_same_primary_overwrite(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)

        changed_item = test_item.copy()
        changed_item.update({"some_string": "NewBee"})
        t.put(changed_item, overwrite=True)
        result = t.get(**test_item_primary)
        self.assertEqual(changed_item, result)

    def test_put_item_with_unexpected_property(self):
        from dynamo_db_resource import Table
        from dynamo_db_resource.exceptions import ValidationError

        t = Table(self.table_name)

        changed_item = deepcopy(test_item)
        changed_item["some_dict"].update({"unexpected_key": "unexpected_value"})

        with self.assertRaises(ValidationError) as TE:
            t.put(changed_item)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": f"Additional properties are not allowed ('unexpected_key' was unexpected) for table {self.table_name}\n"
                f"path to unexpected property: ['some_dict']",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_delete_item(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)
        t.put(test_item)
        t.delete(**test_item_primary)

        with self.assertRaises(FileNotFoundError) as FNF:
            t.get(**test_item_primary)

        self.assertEqual(
            {
                "statusCode": 404,
                "body": f"{test_item_primary} not found in {self.table_name}",
                "headers": {"Content-Type": "text/plain"},
            },
            FNF.exception.args[0],
        )

    def test_update_attribute_non_exiting_item(self):
        updated_attribute = {"some_float": 249235.93}
        from dynamo_db_resource import Table

        t = Table(self.table_name)
        with self.assertRaises(FileNotFoundError) as FNF:
            t.update_attribute(updated_attribute, **test_item_primary)

        self.assertEqual(
            {
                "statusCode": 404,
                "body": "{'primary_partition_key': 'some_identification_string'} not found in "
                "TableForTests",
                "headers": {"Content-Type": "text/plain"},
            },
            FNF.exception.args[0],
        )

    def test_update_attribute_non_exiting_item_but_create_it_with_missing_attributes(self):
        updated_attribute = {"some_float": 249235.93}
        from dynamo_db_resource import Table
        from dynamo_db_resource.exceptions import ValidationError

        changed_item = deepcopy(test_item_primary)
        changed_item.update(**updated_attribute)

        t = Table(self.table_name)
        with self.assertRaises(ValidationError) as TE:
            t.update_attribute(
                updated_attribute, create_item_if_non_existent=True, **test_item_primary
            )

        self.assertEqual(
            {
                "statusCode": 400,
                "body": "'some_string' is a required property for table TableForTests and is missing",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_update_nested_attribute_non_exiting_item_but_try_create_it_with_missing_attributes(self):
        updated_attribute = {
            "some_nested_dict": {"KEY1": {"subKEY1": "updated_string"}}
        }
        from dynamo_db_resource import Table
        from dynamo_db_resource.exceptions import ValidationError

        changed_item = deepcopy(test_item_primary)
        changed_item.update(**updated_attribute)

        t = Table(self.table_name)
        with self.assertRaises(ValidationError) as TE:
            t.update_attribute(
                updated_attribute, create_item_if_non_existent=True, **test_item_primary
            )

        self.assertEqual(
            {
                "statusCode": 400,
                "body": "'some_string' is a required property for table TableForTests and is missing",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_update_with_attribute(self):
        updated_attribute = {"some_float": 249235.93}
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)

        t.update_attribute(updated_attribute, **test_item_primary)

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

        t.delete(**test_item_primary)

    def test_update_with_attribute_return_new_item(self):
        updated_attribute = {"some_float": 249235.93}
        from dynamo_db_resource import Table, UpdateReturns

        t = Table(self.table_name)

        t.put(test_item)

        response = t.update_attribute(updated_attribute, returns=UpdateReturns.ALL_NEW, **test_item_primary)

        verification_item = deepcopy(test_item)
        verification_item.update(updated_attribute)

        self.assertEqual(
            verification_item, response
        )

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

        t.delete(**test_item_primary)

    def test_update_with_attribute_return_new_values(self):
        updated_attribute = {"some_float": 249235.93}
        from dynamo_db_resource import Table, UpdateReturns

        t = Table(self.table_name)

        t.put(test_item)

        response = t.update_attribute(updated_attribute, returns=UpdateReturns.UPDATED_NEW, **test_item_primary)

        self.assertEqual(
            {"some_float": 249235.93}, response
        )

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

        t.delete(**test_item_primary)

    def test_update_with_nested_attribute_return_new_values(self):
        updated_attribute = {"some_nested_dict": {"KEY1": {"subKEY2": 342.98}}}
        from dynamo_db_resource import Table, UpdateReturns

        t = Table(self.table_name)

        t.put(test_item)

        response = t.update_attribute(updated_attribute, returns=UpdateReturns.UPDATED_NEW, **test_item_primary)

        self.assertEqual(
            {
                "some_nested_dict": {
                    "KEY1": {
                        "subKEY1": "subVALUE1",
                        "subKEY2": 342.98,
                        "subKEY3": ["first_string"]
                    }
                }
            },
            response
        )

        self.assertEqual(
            updated_attribute["some_nested_dict"]["KEY1"]["subKEY2"],
            t.get(**test_item_primary)["some_nested_dict"]["KEY1"]["subKEY2"],
        )

        t.delete(**test_item_primary)

    def test_update_with_set_attribute_return_new_values(self):
        updated_attribute = {"some_string_set": {"abc"}}
        from dynamo_db_resource import Table, UpdateReturns

        t = Table(self.table_name)

        t.put(test_item)

        response = t.update_attribute(updated_attribute, set_new_attribute_if_not_existent=True, returns=UpdateReturns.UPDATED_NEW, **test_item_primary)

        self.assertEqual(
            {"some_string_set": {"abc"}}, response
        )

        self.assertEqual(
            updated_attribute["some_string_set"], t.get(**test_item_primary)["some_string_set"],
        )

        t.delete(**test_item_primary)

    def test_update_with_attribute_return_old_values(self):
        updated_attribute = {"some_float": 249235.93}
        from dynamo_db_resource import Table, UpdateReturns

        t = Table(self.table_name)

        t.put(test_item)

        response = t.update_attribute(updated_attribute, returns=UpdateReturns.UPDATED_OLD, **test_item_primary)

        self.assertEqual(
            {"some_float": test_item["some_float"]}, response
        )

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

        t.delete(**test_item_primary)

    def test_update_with_attribute_return_old_item(self):
        updated_attribute = {"some_float": 249235.93}
        from dynamo_db_resource import Table, UpdateReturns

        t = Table(self.table_name)

        t.put(test_item)

        response = t.update_attribute(updated_attribute, returns=UpdateReturns.ALL_OLD, **test_item_primary)

        self.assertEqual(
            test_item, response
        )

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

        t.delete(**test_item_primary)

    def test_update_fail_non_existent_attribute(self):
        updated_attribute = {
            "some_nested_dict": {
                "KEY1": {"subKEY4": {"sub4": [{"sub_sub_key": "abc"}]}}
            }
        }
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)

        from dynamo_db_resource.exceptions import AttributeNotExistsException

        with self.assertRaises(AttributeNotExistsException):
            t.update_attribute(updated_attribute, **test_item_primary)

    def test_update_with_attribute_of_false_type(self):
        updated_attribute = {"some_string": False}
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)

        with self.assertRaises(TypeError) as TE:
            t.update_attribute(updated_attribute, **test_item_primary)

        t.delete(**test_item_primary)

        self.assertEqual(
            {
                "statusCode": 415,
                "body": f"Wrong value type in {t.name} for key=some_string:\n"
                f"False is not of type 'string'."
                f"\nenum: ['abcdef', 'ghijkl', 'NewBee']",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_update_with_attribute_in_non_existing_path(self):
        updated_attribute = {
            "some_nested_dict": {
                "KEY1": {"subKEY4": {"sub4": [{"sub_sub_key": "abc"}]}}
            }
        }
        from dynamo_db_resource import Table, UpdateReturns

        t = Table(self.table_name)

        t.put(test_item)

        response = t.update_attribute(
            updated_attribute,
            set_new_attribute_if_not_existent=True,
            returns=UpdateReturns.ALL_NEW,
            **test_item_primary,
        )

        self.assertEqual(
            updated_attribute["some_nested_dict"]["KEY1"]["subKEY4"]["sub4"][0],
            response["some_nested_dict"]["KEY1"]["subKEY4"]["sub4"][0]
        )


        self.assertEqual(
            updated_attribute["some_nested_dict"]["KEY1"]["subKEY4"]["sub4"][0],
            t.get(**test_item_primary)["some_nested_dict"]["KEY1"]["subKEY4"]["sub4"][
                0
            ],
        )

    def test_update_integer_drift(self):
        from dynamo_db_resource import Table, UpdateReturns
        t = Table(self.table_name)
        t.put(test_item)

        new_value = t.update_number_drift({"some_int": -1}, returns=UpdateReturns.UPDATED_NEW, **test_item_primary)
        assert new_value["some_int"] == test_item["some_int"] - 1
        assert t.get(**test_item_primary)["some_int"] == test_item["some_int"] - 1

    def test_update_nested_float_drift(self):
        from dynamo_db_resource import Table, UpdateReturns
        t = Table(self.table_name)
        t.put(test_item)
        new_value = t.update_number_drift(
            {"some_nested_dict": {"KEY1": {"subKEY2": 3.5}}},
            returns=UpdateReturns.UPDATED_NEW,
            **test_item_primary
        )
        assert new_value["some_nested_dict"]["KEY1"]["subKEY2"] == test_item["some_nested_dict"]["KEY1"]["subKEY2"] + 3.5
        assert t.get(
            **test_item_primary
        )["some_nested_dict"]["KEY1"]["subKEY2"] == test_item["some_nested_dict"]["KEY1"]["subKEY2"] +3.5

    def test_add_attribute(self):
        added_attribute = {
            "some_nested_dict": {
                "KEY1": {"subKEY4": {"sub0": [{"sub_sub_key": "abc"}]}}
            }
        }
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)

        t.add_new_attribute(added_attribute, **test_item_primary)

        self.assertEqual(
            {"sub0": [{"sub_sub_key": "abc"}]},
            t.get(**test_item_primary)["some_nested_dict"]["KEY1"]["subKEY4"],
        )

    def test_add_attribute_on_existing_attribute_failure(self):
        added_attribute = {"some_dict": {"key1": "abc"}}
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)

        from dynamo_db_resource.exceptions import AttributeExistsException

        with self.assertRaises(AttributeExistsException):
            t.add_new_attribute(added_attribute, **test_item_primary)

    def test_add_attribute_on_existing_attribute_update(self):
        added_attribute = {"some_dict": {"key1": "abc"}}
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.put(test_item)

        t.add_new_attribute(
            added_attribute, update_if_existent=True, **test_item_primary
        )

        self.assertEqual(
            "abc", t.get(**test_item_primary)["some_dict"]["key1"],
        )

    @skip("issue in moto: item gets created though condition fails (#3729); working on docker test instance")
    def test_add_attribute_on_non_existing_item_with_creation(self):
        added_attribute = deepcopy(test_item)
        added_attribute["some_dict"].update({"key3": {"free_key": "abc"}})
        added_attribute.pop("primary_partition_key")
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        t.add_new_attribute(
            added_attribute, **test_item_primary, create_item_if_non_existent=True
        )

        added_attribute.update(**test_item_primary)
        item = t.get(**test_item_primary)
        self.assertEqual(
            added_attribute,
            item
        )

        scan = t.scan()
        self.assertEqual(
            1,
            len(scan["Items"])
        )

    @skip("issue in moto: item gets created though condition fails (#3729); working on docker test instance")
    def test_add_attribute_on_non_existing_item_with_creation_with_validation_error(self):
        added_attribute = {"some_dict": {"key1": "abc"}}
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        with self.assertRaises(TypeError) as TE:
            t.add_new_attribute(
                added_attribute, **test_item_primary, create_item_if_non_existent=True
            )

        self.assertEqual(
            {
                "statusCode": 400,
                "body": "'some_string' is a required property for table TableForTests and is missing",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )
        scan = t.scan()
        self.assertEqual(
            list(),
            scan["Items"]
        )

    def test_add_attribute_on_non_existing_item_without_creation(self):
        added_attribute = {"some_dict": {"key1": "abc"}}
        from dynamo_db_resource import Table

        t = Table(self.table_name)

        with self.assertRaises(FileNotFoundError) as FNF:
            t.add_new_attribute(
                added_attribute, **test_item_primary
            )

        self.assertEqual(
            {
                "statusCode": 404,
                "body": "{'primary_partition_key': 'some_identification_string'} not found in TableForTests",
                "headers": {"Content-Type": "text/plain"},
            },
            FNF.exception.args[0],
        )
        scan = t.scan()
        self.assertEqual(
            list(),
            scan["Items"]
        )

    def test_append_item(self):
        from dynamo_db_resource import Table

        changed_item = deepcopy(test_item)
        changed_item["some_nested_dict"]["KEY1"]["subKEY3"].append("second_string")

        t = Table(self.table_name)
        t.put(test_item)
        t.update_append_list(
            {"some_nested_dict": {"KEY1": {"subKEY3": ["second_string"]}}},
            **test_item_primary,
        )

        result = t.get(**test_item_primary)

        self.assertEqual(changed_item, result)

    @skip("issue in moto: item gets created though condition fails (#3729); working on docker test instance")
    def test_append_with_attribute_in_non_existing_path(self):
        updated_attribute = {
            "some_nested_dict": {
                "KEY1": {"subKEY4": {"sub4": [{"sub_sub_key": "abc"}]}}
            }
        }

        from dynamo_db_resource import Table

        t = Table(self.table_name)

        changed_item = deepcopy(test_item)
        changed_item["some_nested_dict"]["KEY1"].update({"subKEY4": dict()})
        t.put(changed_item)

        from dynamo_db_resource.exceptions import AttributeNotExistsException

        with self.assertRaises(AttributeNotExistsException):
            t.update_append_list(updated_attribute, **test_item_primary)

        t.update_append_list(
            updated_attribute,
            set_new_attribute_if_not_existent=True,
            **test_item_primary,
        )

        self.assertEqual(
            updated_attribute["some_nested_dict"]["KEY1"]["subKEY4"]["sub4"][0],
            t.get(**test_item_primary)["some_nested_dict"]["KEY1"]["subKEY4"]["sub4"][
                0
            ],
        )

    def test_adding_set_attribute(self):
        from dynamo_db_resource import Table

        t = Table("TableForTests")
        t.put(test_item)

        t.add_new_attribute({"some_string_set": {"2", "3"}}, **test_item_primary)
        self.assertEqual(
            {"2", "3"},
            t.get(**test_item_primary)["some_string_set"]
        )

    def test_adding_to_set(self):
        from dynamo_db_resource import Table

        t = Table("TableForTests")
        t.put(test_item)

        t.add_new_attribute({"some_string_set": {"2", "3"}}, **test_item_primary)
        self.assertEqual(
            {"2", "3"},
            t.get(**test_item_primary)["some_string_set"]
        )
        t.update_add_set(
            {"some_string_set": {"3", "4", "5"}},
            **test_item_primary
        )
        self.assertEqual(
            {"2", "3", "4", "5"},
            t.get(**test_item_primary)["some_string_set"]
        )

    def test_removing_items_from_set(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)
        t.put(test_item)

        t.add_new_attribute({"some_string_set": {"2", "3", "4", "5"}}, **test_item_primary)
        t.remove_from_set(["some_string_set"], {"3", "4"}, **test_item_primary)
        self.assertEqual(
            {"2", "5"},
            t.get(**test_item_primary)["some_string_set"]
        )

    def test_remove_attribute(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)
        t.put(test_item)

        path_to_delete = ["some_dict", "key1"]
        t.remove_attribute(path_to_delete, **test_item_primary)

        item = t.get(**test_item_primary)
        self.assertNotIn("key1", item["some_dict"])

    def test_remove_attribute_with_return_deleted(self):
        from dynamo_db_resource import Table, UpdateReturns
        t = Table(self.table_name)
        t.put(test_item)

        path_to_delete = ["some_dict", "key1"]
        response = t.remove_attribute(path_to_delete, returns=UpdateReturns.DELETED, **test_item_primary)
        self.assertEqual("value1", response)

    def test_remove_attribute_with_return_all_old(self):
        from dynamo_db_resource import Table, UpdateReturns
        t = Table(self.table_name)
        t.put(test_item)

        path_to_delete = ["some_dict", "key1"]
        response = t.remove_attribute(path_to_delete, returns=UpdateReturns.ALL_OLD, **test_item_primary)
        self.assertEqual(test_item, response)
        item = t.get(**test_item_primary)
        self.assertNotIn("key1", item["some_dict"])

    def test_remove_non_existing_attribute(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)
        t.put(test_item)

        path_to_delete = ["some_dict", "non_existing_kex"]

        from dynamo_db_resource.exceptions import AttributeNotExistsException

        with self.assertRaises(AttributeNotExistsException):
            t.remove_attribute(path_to_delete, **test_item_primary)

    def test_remove_list_entry(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)
        t.put(test_item)

        path_to_delete = ["some_array"]
        item_no_to_delete = 2

        t.remove_entry_in_list(path_to_delete, item_no_to_delete, **test_item_primary)

        item = t.get(**test_item_primary)
        self.assertEqual(["simple_string", 13], item["some_array"])

    def test_remove_list_entry_return_deleted(self):
        from dynamo_db_resource import Table, UpdateReturns
        t = Table(self.table_name)
        t.put(test_item)

        path_to_delete = ["some_array"]
        item_no_to_delete = 2

        response = t.remove_entry_in_list(
            path_to_delete,
            item_no_to_delete,
            returns=UpdateReturns.DELETED,
            **test_item_primary
        )

        self.assertEqual(
            {
                "KEY1": {
                    "subKEY1": "subVALUE1",
                    "subKEY2": 42.24
                }
            },
            response
        )

        item = t.get(**test_item_primary)
        self.assertEqual(["simple_string", 13], item["some_array"])

    @skip("not implemented: check on item in lists exists")
    def test_remove_non_existing_list_entry(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)
        t.put(test_item)

        path_to_delete = ["some_array"]
        item_no_to_delete = 5

        with self.assertRaises(IndexError):
            t.remove_entry_in_list(path_to_delete, item_no_to_delete, **test_item_primary)

    def test_remove_required_attribute(self):
        from dynamo_db_resource import Table
        from dynamo_db_resource.exceptions import ValidationError
        t = Table(self.table_name)

        path_to_delete = ["some_int"]
        with self.assertRaises(ValidationError):
            t.remove_attribute(path_to_delete, **test_item_primary)

    def test_update_with_condition(self):
        updated_attribute = {"some_float": 249235.93}
        from dynamo_db_resource import Table
        from dynamo_db_resource.conditions import Attr

        t = Table(self.table_name)

        t.put(test_item)

        t.update_attribute(
            updated_attribute,
            condition=Attr("some_int").eq(42),
            **test_item_primary,
        )

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

        updated_attribute = {"some_float": 34.15}
        t.update_attribute(
            updated_attribute,
            condition=Attr("some_int").lt(45),
            **test_item_primary,
        )

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

    def test_update_condition_exception(self):
        from dynamo_db_resource import Table
        from dynamo_db_resource.exceptions import ConditionalCheckFailedException
        from dynamo_db_resource.conditions import Attr

        t = Table(self.table_name)

        t.put(test_item)

        with self.assertRaises(ConditionalCheckFailedException):
            t.update_attribute(
                {"some_float": 15.15},
                condition=Attr("some_int").eq(0),
                **test_item_primary,
            )
        self.assertEqual(
            test_item,
            t.get(**test_item_primary)
        )

    def test_scan_and_truncate(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)
        t.put(test_item)

        response = t.scan()
        self.assertEqual(test_item, response["Items"][0])
        self.assertEqual(1, response["Count"])

        test_user_copy = test_item.copy()
        for n in range(5):
            test_user_copy.update(
                {"primary_partition_key": f"some_identification_string_{n}"}
            )
            t.put(test_user_copy)

        response = t.scan()
        self.assertEqual(6, response["Count"])

        t.truncate()
        response = t.scan()
        self.assertEqual(list(), response["Items"])

    def test_batch_get_single_primary(self):
        from dynamo_db_resource import Table

        t = Table(self.table_name)
        t.put(test_item)
        second_test_item = deepcopy(test_item)
        second_test_item["primary_partition_key"] = "second_identification_string"
        t.put(second_test_item)

        response = t.batch_get(
            ["some_identification_string", "second_identification_string"],
            return_as_dict_of_primary_keys=True,
        )
        self.assertEqual(
            {"some_identification_string": test_item, "second_identification_string": second_test_item},
            response
        )
        list_response = t.batch_get(
            ["some_identification_string", "second_identification_string"],
        )
        self.assertEqual(
            list(response.values()),
            list_response
        )


class TestDynamoDBRangeNIndex(TestDynamoDBBase):
    table_name = "TableWithRange"

    def setUp(self) -> None:
        super().setUp()
        from dynamo_db_resource import Table

        t = Table(self.table_name)
        file_names = Path(Path(__file__).parent, "test_data/items").iterdir()
        for file_name in file_names:
            if not file_name.stem.startswith("test_range"):
                continue
            with open(Path(Path(__file__).parent, file_name)) as f:
                t.put(json.load(f))

    def test_cast_index_keys(self):
        from dynamo_db_resource import Table

        tr = Table("TableWithRange")
        index_name = "some_string_index"
        expected_index = {"some_string": "some_value"}
        self.assertEqual(expected_index, tr._cast_index_keys(index_name, "some_value"))
        self.assertEqual(expected_index, tr._cast_index_keys(index_name, {"some_string": "some_value"}))

        index_name = "string_n_int_index"
        expected_index = {"some_string": "some_value", "some_int": 2}
        self.assertEqual(expected_index, tr._cast_index_keys(index_name, "some_value", 2))
        self.assertEqual(expected_index, tr._cast_index_keys(
            index_name, {"some_string": "some_value", "some_int": 2})
                         )

    def test_raw_query(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.query(
            primary_partition_key="first_key"
        )
        self.assertEqual(response["Count"], 13)

    def test_get_item_from_index(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.index_get(
            index="some_string_index",
            return_as_dict_of_primary_keys=True,
            **{"some_string": "some_key1"}
        )
        self.assertEqual(
            "first_key",
            response[("first_key", "2020-01-01 12:01")]["primary_partition_key"]
        ),
        self.assertEqual(
            t.get(primary_partition_key="first_key", range_key="2020-01-01 12:01"),
            response[("first_key", "2020-01-01 12:01")]
        )
        list_response = t.index_get(
            index="some_string_index",
            **{"some_string": "some_key1"}
        )
        self.assertEqual(
            list(response.values()),
            list_response
        )

    def test_get_item_parts_from_index(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.index_get(
            index="some_string_index",
            attributes_to_get=["some_int"],
            **{"some_string": "some_key1"}
        )
        self.assertEqual(len(response[0]), 3)

        self.assertEqual(
            1,
            response[0]["some_int"]
        ),
        self.assertNotIn(
            "some_string",
            response[0]
        )

    def test_get_item_from_composite_index(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.index_get(
            index="string_n_int_index",
            return_as_dict_of_primary_keys=True,
            **{"some_string": "some_key2", "some_int": 2}
        )
        self.assertEqual(
            "first_key",
            response[("first_key", "2020-01-01 12:02")]["primary_partition_key"]
        ),
        self.assertEqual(
            t.get(primary_partition_key="first_key", range_key="2020-01-01 12:02"),
            response[("first_key", "2020-01-01 12:02")]
        )

    def test_get_non_existent_item_from_index(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        with self.assertRaises(FileNotFoundError):
            t.index_get(index="some_string_index", **{"some_string": "not existing key"})

    def test_batch_get_with_range_key(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.batch_get([
            ["first_key", "2020-01-01 12:01"],
            {"primary_partition_key": "second_key", "range_key": "range1"}
        ],
            return_as_dict_of_primary_keys=True
        )
        self.assertEqual(
            {
                ('first_key', '2020-01-01 12:01'): {
                    'primary_partition_key': 'first_key',
                    'range_key': '2020-01-01 12:01',
                    'some_int': 1,
                    'some_string': 'some_key1'
                },
                ('second_key', 'range1'): {
                    'primary_partition_key': 'second_key',
                    'range_key': 'range1',
                    'some_int': 1,
                    'some_string': 'some_key3'
                }
             },
            response
        )

    def test_paginate_first(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.query(max_results=3, primary_partition_key="first_key")
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 3,
                "ScannedCount": mock.ANY,
                "LastEvaluatedKey": "2020-01-01 12:03",
                "Items":
                    [
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 12:01",
                            "some_int": 1,
                            "some_string": "some_key1"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 12:02",
                            "some_int": 2,
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 12:03",
                            "some_int": 2,
                            "some_string": "some_key2"
                        }
                    ]
            },
            response
        )

    def test_paginate_second(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.query(
            max_results=3,
            offset_last_key="2020-01-01 12:03",
            primary_partition_key="first_key"
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 3,
                "ScannedCount": mock.ANY,
                "LastEvaluatedKey": "2020-01-01 14:20",
                "Items":
                    [
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 13:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 14:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 14:20",
                            "some_int": 2,
                            "some_string": "some_key2"
                        }
                    ]
            },
            response
        )

    def test_paginate_specific_attributs(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.query(
            attributes_to_get=["some_string"],
            max_results=3,
            offset_last_key="2020-01-01 12:03",
            primary_partition_key="first_key"
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 3,
                "ScannedCount": mock.ANY,
                "LastEvaluatedKey": "2020-01-01 14:20",
                "Items":
                    [
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 13:00",
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 14:00",
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 14:20",
                            "some_string": "some_key2"
                        }
                    ]
            },
            response
        )

    def test_paginate_last(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.query(
            max_results=3,
            offset_last_key="2020-02-03 13:00",
            primary_partition_key="first_key"
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 2,
                "ScannedCount": mock.ANY,
                "Items":
                    [
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-02-04 13:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2021-01-01 12:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        }
                    ]
            },
            response
        )

    def test_query_on_index_with_single_offset_key(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        with self.assertRaises(TypeError) as TE:
            t.query(
                index="string_n_int_index",
                max_results=3,
                some_string="some_key2",
                offset_last_key=2
            )
        self.assertEqual(
            {
                "statusCode": 400,
                "body": "querying on index requires dictionary with last evaluated values",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_query_on_index(self):
        from dynamo_db_resource import Table
        t = Table(self.table_name)

        response = t.query(
            index="string_n_float_index",
            max_results=2,
            some_string="some_key4",
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 2,
                "ScannedCount": mock.ANY,
                "LastEvaluatedKey": {
                    "some_float": 2.2,
                    "primary_partition_key": "third_key",
                    "range_key": "range2",
                    "some_string": "some_key4"
                },
                "Items":
                    [
                        {
                            'primary_partition_key': 'third_key',
                            'range_key': 'range1',
                            'some_int': 1,
                            'some_float': 1.1,
                            'some_string': 'some_key4'
                        },
                        {
                            'primary_partition_key': 'third_key',
                            'range_key': 'range2',
                            'some_int': 2,
                            'some_float': 2.2,
                            'some_string': 'some_key4'
                        }
                    ]
            },
            response
        )

        response = t.query(
            index="string_n_float_index",
            max_results=2,
            offset_last_key=response["LastEvaluatedKey"],
            some_string="some_key4",
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 1,
                "ScannedCount": mock.ANY,
                "Items":
                    [
                        {
                            'primary_partition_key': 'third_key',
                            'range_key': 'range3',
                            'some_int': 3,
                            'some_float': 3.3,
                            'some_string': 'some_key4'
                        }
                    ]
            },
            response
        )

    def test_query_range_condition(self):
        from dynamo_db_resource import Table
        from dynamo_db_resource.conditions import BeginsWith
        t = Table(self.table_name)

        response = t.query(
            range_condition=BeginsWith("2021"),
            primary_partition_key="first_key"
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 1,
                "ScannedCount": mock.ANY,
                "Items":
                    [
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2021-01-01 12:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        }
                    ]
            },
            response
        )

    def test_query_range_condition_page(self):
        from dynamo_db_resource import Table
        from dynamo_db_resource.conditions import BeginsWith
        t = Table(self.table_name)

        response = t.query(
            max_results=3,
            range_condition=BeginsWith("2020-01-01"),
            offset_last_key="2020-01-01 12:02",
            primary_partition_key="first_key"
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 3,
                "ScannedCount": mock.ANY,
                "LastEvaluatedKey": "2020-01-01 14:00",
                "Items":
                    [
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 12:03",
                            "some_int": 2,
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 13:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-01-01 14:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        }
                    ]
            },
            response
        )

    def test_query_range_condition_with_attributes_to_get(self):
        from dynamo_db_resource import Table
        from dynamo_db_resource.conditions import GreaterThan, BeginsWith
        t = Table(self.table_name)

        response = t.query(
            range_condition=GreaterThan("2020-02-03 12:00"),
            attributes_to_get=["some_int"],
            primary_partition_key="first_key"
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 3,
                "ScannedCount": mock.ANY,
                "Items":
                    [
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-02-03 13:00",
                            "some_int": 2,
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-02-04 13:00",
                            "some_int": 2,
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2021-01-01 12:00",
                            "some_int": 2,
                        }
                    ]
            },
            response
        )

    def test_query_range_condition_between(self):
        from dynamo_db_resource import Table
        from dynamo_db_resource.conditions import Between
        t = Table(self.table_name)

        response = t.query(
            range_condition=Between("2020-02-03 12:05", "2020-02-04 13:00"),
            primary_partition_key="first_key"
        )
        response.pop("ResponseMetadata")
        self.assertEqual(
            {
                "Count": 2,
                "ScannedCount": mock.ANY,
                "Items":
                    [
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-02-03 13:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        },
                        {
                            "primary_partition_key": "first_key",
                            "range_key": "2020-02-04 13:00",
                            "some_int": 2,
                            "some_string": "some_key2"
                        }
                    ]
            },
            response
        )


