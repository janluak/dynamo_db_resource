from jsonschema.validators import Draft7Validator as BaseValidator, extend
from jsonschema.exceptions import ValidationError
from jsonschema._types import is_number

_json_schema_2_dynamo_db_type_switch = {
    "string": "S",
    "number": "N",
    "integer": "N",
    "bytes": "B",
    "array": "L",
    "object": "M",
    "boolean": "BOOL",
    "null": "NULL",
    "stringSet": "SS",
    "numberSet": "NS",
    "bytesSet": "BS"
}
_array_types = ["array", "stringSet", "numberSet", "bytesSet"]


def _is_bytes(checker, instance):
    return isinstance(instance, bytes)


def _is_string_set(checker, instance):
    return isinstance(instance, set) and all([isinstance(i, str) for i in instance])


def _is_number_set(checker, instance):
    return isinstance(instance, set) and all([is_number(checker, i) for i in instance])


def _is_bytes_set(checker, instance):
    return isinstance(instance, set) and all([_is_bytes(checker, i) for i in instance])


def _min_items(validator, mi, instance, schema):
    if any([validator.is_type(instance, i) for i in _array_types]) and len(instance) < mi:
        yield ValidationError("%r is too short" % (instance,))


def _max_items(validator, mi, instance, schema):
    if any([validator.is_type(instance, i) for i in _array_types]) and len(instance) > mi:
        yield ValidationError("%r is too long" % (instance,))


DynamoDBValidator = extend(
    BaseValidator,
    validators={
        u"maxItems": _max_items,
        u"minItems": _min_items,
    },
    type_checker=BaseValidator.TYPE_CHECKER.redefine_many(
            {
                u"bytes": _is_bytes,
                u"stringSet": _is_string_set,
                u"numberSet": _is_number_set,
                u"bytesSet": _is_bytes_set,
            }
        )
)
