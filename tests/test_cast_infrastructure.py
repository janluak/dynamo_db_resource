from pathlib import Path
import json

with open(Path(Path(__file__).parent, "test_data/tables/TableForInfrastructureTest.json")) as f:
    DATABASE_SCHEMA = json.load(f)


def test_to_infrastructure_code():
    from dynamo_db_resource.table_existence import convert_schema_to_infrastructure_code
    converted_schema = convert_schema_to_infrastructure_code(DATABASE_SCHEMA)

    assert json.dumps(converted_schema, sort_keys=True) == json.dumps(
        {
            'AttributeDefinitions': [
                {
                    'AttributeName': 'some_string',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'primary_partition_key',
                    'AttributeType': 'S'
                }
            ],
            'KeySchema': [
                {
                    'AttributeName': 'primary_partition_key',
                    'KeyType': 'HASH'
                }
            ],
            'LocalSecondaryIndexes': [
                {
                    'IndexName': 'some_string_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'some_string',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            },
            'StreamSpecification': {
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            },
            'TableName': 'TableForInfrastructureTest',
            'Tags': [
                {
                    'Key': 'tag-Key',
                    'Value': 'tag-Value'
                }
            ]
        },
        sort_keys=True
    )
