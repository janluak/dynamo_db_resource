from unittest import TestCase
from os import environ as os_environ
from pathlib import Path
from os import chdir, getcwd
import sys
import json
from moto import mock_dynamodb2


@mock_dynamodb2
class TestDynamoDBResource(TestCase):
    actual_cwd = str()
    table = object

    @classmethod
    def setUpClass(cls) -> None:
        os_environ["STAGE"] = "TEST"
        os_environ["AWS_REGION"] = "eu-central-1"
        os_environ["DYNAMO_DB_RESOURCE_SCHEMA_ORIGIN"] = "file"
        os_environ["DYNAMO_DB_RESOURCE_SCHEMA_DIRECTORY"] = "test_data/tables/"

        cls.actual_cwd = getcwd()
        chdir(Path(__file__).parent)

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)

        del os_environ["DYNAMO_DB_RESOURCE_SCHEMA_ORIGIN"]
        del os_environ["DYNAMO_DB_RESOURCE_SCHEMA_DIRECTORY"]

    def setUp(self) -> None:
        for key in list(sys.modules.keys()):
            if any(key.startswith(i) for i in ["dynamo_db_resource", "test"]):
                del sys.modules[key]

        from dynamo_db_resource.table_existence import (
            create_dynamo_db_table_from_schema,
        )
        with open(Path(Path(__file__).parent, f"test_data/tables/{self.table_name}.json")) as f:
            create_dynamo_db_table_from_schema(
                json.load(f)
            )

        from dynamo_db_resource import Table
        self.table = Table(self.table_name)
        self.table.put(self.test_item, overwrite=True)

    def tearDown(self) -> None:
        from dynamo_db_resource.table_existence import delete_dynamo_db_table
        delete_dynamo_db_table(self.table_name, require_confirmation=False)


class TestSimpleDynamoDBResource(TestDynamoDBResource):
    table_name = "TableForTests"
    with open(Path(Path(__file__).parent, "test_data/items/test_item.json")) as f:
        test_item = json.load(f)
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
