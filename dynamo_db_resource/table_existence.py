import boto3
from os import environ as os_environ
stage = os_environ["STAGE"]
resource_config = {"region_name": os_environ["AWS_REGION"]}

__all__ = ["create_dynamo_db_table_from_schema", "delete_dynamo_db_table"]

_json_schema_2_dynamo_db_type_switch = {
    "string": "S",
    "array": "L",
    "object": "M",
    "boolean": "BOOL",
    "number": "N",
    "integer": "N",
}


def _parse_json_schema_2_dynamo_db_schema(json_schema):
    table_name = json_schema["title"]
    attribute_definitions = [
        {
            "AttributeName": key,
            "AttributeType": _json_schema_2_dynamo_db_type_switch[
                json_schema["properties"][key]["type"]
            ],
        }
        for key in json_schema["default"]
    ]
    key_schemas = [{"AttributeName": json_schema["default"][0], "KeyType": "HASH"}]

    if len(json_schema["default"]) == 2:
        key_schemas.append(
            {"AttributeName": json_schema["default"][1], "KeyType": "RANGE"}
        )

    elif len(json_schema["default"]) > 2:
        raise EnvironmentError(
            f"can't specify more than one PrimaryKey & one SortKey. Given: {json_schema['default']}"
        )

    return table_name, attribute_definitions, key_schemas


def create_dynamo_db_table_from_schema(json_schema, include_stage_in_table_name=True):
    (
        table_name,
        attribute_definitions,
        key_schemas,
    ) = _parse_json_schema_2_dynamo_db_schema(json_schema)

    if include_stage_in_table_name:
        table_name = f"{stage}-{table_name}"

    ddb = boto3.resource("dynamodb", **resource_config)
    try:
        ddb.create_table(
            TableName=table_name,
            AttributeDefinitions=attribute_definitions,
            KeySchema=key_schemas,
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )

        print(f"successfully created table {table_name}")
    except Exception as e:
        print(f"not created table {table_name}")
        print(e)
        pass


def delete_dynamo_db_table(table_name: str, add_stage_to_table_name: bool = True, require_confirmation: bool = True):
    if require_confirmation:
        decision = input(f"Are you sure to delete Dynamo DB table {table_name}\ny/n: ")
        if decision != "y":
            return

    if add_stage_to_table_name:
        table_name = f"{stage}-{table_name}"

    ddb = boto3.client("dynamodb", **resource_config)
    ddb.delete_table(TableName=table_name)
