from pytest import fixture
from os.path import dirname, realpath
from os import environ as os_environ


@fixture
def os_env():

    os_environ["ENV"] = "cloud"
    os_environ["STAGE"] = "TEST"
    os_environ["AWS_REGION"] = "eu-central-1"
    os_environ["DYNAMO_DB_RESOURCE_SCHEMA_ORIGIN"] = "file"
    os_environ["DYNAMO_DB_RESOURCE_SCHEMA_DIRECTORY"] = "test_data/tables/"


def test_resource_config_unittest(os_env):
    from dynamo_db_resource.resource_config import create_resource_config

    config = create_resource_config("local", True)

    assert config == {
        'aws_access_key_id': 'dummy',
        'aws_secret_access_key': 'dummy',
        'endpoint_url': 'http://localhost:8000',
        'region_name': 'dummy'
    }


def test_resource_config_aws_sam(os_env):
    from dynamo_db_resource.resource_config import create_resource_config

    config = create_resource_config("local", aws_sam=True)

    assert config == {
        'aws_access_key_id': 'dummy',
        'aws_secret_access_key': 'dummy',
        'endpoint_url': 'http://docker.for.mac.localhost:8000',
        'region_name': 'dummy'
    }


def test_resource_config_cloud(os_env):
    from dynamo_db_resource.resource_config import create_resource_config

    config = create_resource_config(os_environ["AWS_REGION"])

    assert config == {
        'region_name': os_environ["AWS_REGION"]
    }

