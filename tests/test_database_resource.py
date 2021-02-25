from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from copy import deepcopy
from fil_io.json import load_single
from moto import mock_dynamodb2


@mock_dynamodb2
class TestDynamoDBResource(TestCase):
    actual_cwd = str()
    table = object

    @classmethod
    def setUpClass(cls) -> None:
        os_environ["STAGE"] = "TEST"
        os_environ["AWS_REGION"] = "eu-central-1"
        os_environ[
            "WRAPPER_CONFIG_FILE"
        ] = f"{dirname(realpath(__file__))}/dynamodb_wrapper_config.json"

        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)

        del os_environ["WRAPPER_CONFIG_FILE"]

    def setUp(self) -> None:
        from dynamo_db_resource.table_existence import (
            create_dynamo_db_table_from_schema,
        )
        create_dynamo_db_table_from_schema(
            load_single(
                f"{dirname(realpath(__file__))}/test_data/tables/{self.table_name}.json"
            )
        )

        from dynamo_db_resource import Table
        self.table = Table(self.table_name)
        self.table.put(self.test_item, overwrite=True)

    def tearDown(self) -> None:
        from dynamo_db_resource.table_existence import delete_dynamo_db_table
        delete_dynamo_db_table(self.table_name, require_confirmation=False)


class TestSimpleDynamoDBResource(TestDynamoDBResource):
    table_name = "TableForTests"
    test_item = load_single(
        f"{dirname(realpath(__file__))}/test_data/items/test_item.json"
    )
    test_item_primary = {"primary_partition_key": "some_identification_string"}

    def test_get_item_from_resource(self):
        from dynamo_db_resource.resource import (
            DatabaseResourceController,
        )

        database_resource = DatabaseResourceController()

        loaded_item = database_resource[self.table_name].get(**self.test_item_primary)

        self.assertEqual(self.test_item, loaded_item)

    def test_resource_returns_table(self):
        from dynamo_db_resource.resource import (
            DatabaseResourceController,
        )
        from dynamo_db_resource import Table

        database_resource = DatabaseResourceController()

        self.assertEqual(
            type(Table(self.table_name)), type(database_resource[self.table_name])
        )


class TestReusedDynamoDBResource(TestDynamoDBResource):
    # ToDo check re-usage of connection -> only one entry if accessing table twice
    pass


class TestCachedDynamoDBResource(TestDynamoDBResource):
    table_name = "CachedTableForTests"
    test_item = load_single(
        f"{dirname(realpath(__file__))}/test_data/items/test_cache_item.json"
    )
    test_item_primary = {"primary_partition_key": "cache_identification_string"}

    def test_get_item_from_resource(self):
        from dynamo_db_resource.resource import (
            DatabaseResourceController,
        )

        database_resource = DatabaseResourceController()

        loaded_item = database_resource[self.table_name].get(**self.test_item_primary)

        self.assertEqual(self.test_item, loaded_item)

    def test_get_item_from_resource_direct_import(self):
        from dynamo_db_resource import database_resource

        loaded_item = database_resource[self.table_name].get(**self.test_item_primary)

        self.assertEqual(self.test_item, loaded_item)

    def test_get_item_from_cache_with_hash(self):
        from dynamo_db_resource.resource import (
            DatabaseResourceController,
        )

        database_resource = DatabaseResourceController()

        database_resource[self.table_name].get(**self.test_item_primary)
        self.table.delete(**self.test_item_primary)

        from aws_environ_helper import hash_dict

        item_hash = hash_dict(self.test_item)

        loaded_item = database_resource[self.table_name].get(
            **self.test_item_primary, hash=item_hash
        )

        self.assertEqual(self.test_item, loaded_item)

    def test_get_changed_item_with_outdated_hash(self):
        from dynamo_db_resource.resource import (
            DatabaseResourceController,
        )

        database_resource = DatabaseResourceController()

        database_resource[self.table_name].get(**self.test_item_primary)
        original_hash = database_resource[self.table_name]._hash_of(
            **self.test_item_primary
        )
        changed_item = deepcopy(self.test_item)
        changed_item["some_float"] = 300281.382
        self.table.put(changed_item, overwrite=True)

        from aws_environ_helper import hash_dict

        changed_hash = hash_dict(changed_item)

        self.assertNotEqual(original_hash, changed_hash)

        loaded_item = database_resource[self.table_name].get(
            **self.test_item_primary, hash=changed_hash
        )

        self.assertEqual(changed_item, loaded_item)

    def test_put_item(self):
        from dynamo_db_resource.resource import (
            DatabaseResourceController,
        )

        database_resource = DatabaseResourceController()

        database_resource[self.table_name].put(self.test_item, overwrite=True)

    def test_update_item_and_check_for_new_hash(self):
        self.skipTest("solution not implemented")
