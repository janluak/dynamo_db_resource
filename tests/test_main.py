from moto import mock_dynamodb2
from pytest import fixture
from pathlib import Path


@fixture
def os_env():
    from os import environ as os_environ

    os_environ["ENV"] = "cloud"
    os_environ["STAGE"] = "test"
    os_environ["AWS_REGION"] = "eu-central-1"


@mock_dynamodb2
def test_main(os_env):
    from dynamo_db_resource.__main__ import create_table_for_schema_in_directory

    directory = Path(Path(__file__).parent, "test_data/tables")
    tables = ["TableForTest"]

    create_table_for_schema_in_directory(directory, tables)

