from pytest import mark, raises
from jsonschema import ValidationError


@mark.parametrize(
    ("item", "raised"),
    (
            ({
                 "primary_partition_key": "ab",
                 "some_string": "3",
                 "some_string_set": {"2", "3"},
                 "some_number_set": {2, 3, 4}
             }, None),
            ({
                 "primary_partition_key": "ab",
                 "some_string": "3",
                 "some_string_set": {"2", 3},
             }, ValidationError),
            ({
                 "primary_partition_key": "ab",
                 "some_string": "3",
                 "some_number_set": {2, 3},
             }, ValidationError),
    )
)
def test_ddb_validator(item, raised):
    from dynamo_db_resource._schema import DynamoDBValidator

    schema = {
        "properties": {
            "primary_partition_key": {
                "description": "the primary partition key of the dynamo db",
                "type": "string"
            },
            "some_string": {
                "description": "some key containing any kind of strings",
                "type": "string"
            },
            "some_string_set": {
                "type": "stringSet",
                "$comment": "only strings allowed"
            },
            "some_number_set": {
                "type": "numberSet",
                "minItems": 3
            }
        }
    }

    validator = DynamoDBValidator(schema)

    if raised:
        with raises(raised):
            validator.validate(
                item
            )
    else:
        validator.validate(
            item
        )
