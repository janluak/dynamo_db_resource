import boto3
from os import environ as os_environ
from .dynamo_db_table import _cast_table_name
from ._schema import _json_schema_2_dynamo_db_type_switch

__all__ = ["create_dynamo_db_table_from_schema", "delete_dynamo_db_table", "convert_schema_to_infrastructure_code"]


def create_dynamo_db_table_from_schema(json_schema, **resource_config):
    if not resource_config:
        resource_config = {"region_name": os_environ["AWS_REGION"]}

    ddb = boto3.resource("dynamodb", **resource_config)
    infrastructure = convert_schema_to_infrastructure_code(json_schema)
    infrastructure["TableName"] = _cast_table_name(infrastructure["TableName"])
    try:
        ddb.create_table(
            **infrastructure
        )

        print(f"successfully created table {infrastructure['TableName']}")
    except Exception as e:
        print(f"not created table {infrastructure['TableName']}")
        print(e)
        pass


def delete_dynamo_db_table(table_name: str, require_confirmation: bool = True, **resource_config):
    if not resource_config:
        resource_config = {"region_name": os_environ["AWS_REGION"]}
    if require_confirmation:
        decision = input(f"Are you sure to delete Dynamo DB table {table_name}\ny/n: ")
        if decision != "y":
            return

    table_name = _cast_table_name(table_name)

    ddb = boto3.client("dynamodb", **resource_config)
    ddb.delete_table(TableName=table_name)


def _create_attribute_definition(schema, attribute_name):
    return {
        "AttributeName": attribute_name,
        "AttributeType": _json_schema_2_dynamo_db_type_switch[
            schema["properties"][attribute_name]["type"]
        ]
    }


def convert_schema_to_infrastructure_code(schema: dict) -> dict:
    infrastructure_code = schema["$infrastructure"]
    infrastructure_code["TableName"] = schema["title"]
    infrastructure_code["AttributeDefinitions"] = list()

    keys_to_define = set([key_schema["AttributeName"] for key_schema in infrastructure_code["KeySchema"]])
    for index_type in ["LocalSecondaryIndexes", "GlobalSecondaryIndexes"]:
        for index_schema in infrastructure_code.get(index_type, list()):
            keys_to_define.update(set([key_schema["AttributeName"] for key_schema in index_schema["KeySchema"]]))

    infrastructure_code["AttributeDefinitions"] = [
        _create_attribute_definition(schema, key) for key in keys_to_define
    ]
    return infrastructure_code
