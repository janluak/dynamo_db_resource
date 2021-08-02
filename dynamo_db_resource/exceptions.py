from jsonschema.exceptions import ValidationError

__all__ = [
    "ConditionalCheckFailedException",
    "AttributeExistsException",
    "AttributeNotExistsException",
    "ValidationError"
]


class ConditionalCheckFailedException(Exception):
    pass


class AttributeExistsException(AttributeError):
    pass


class AttributeNotExistsException(AttributeError):
    pass


class CustomExceptionRaiser:
    def __init__(self, table):
        self.table = table

    def not_found_message(self, not_found_item):
        raise FileNotFoundError(
            {
                "statusCode": 404,
                "body": f"{not_found_item} not found in {self.table.name}",
                "headers": {"Content-Type": "text/plain"},
            }
        )

    def _primary_key_rudimentary_message(self, provided_message):
        raise LookupError(
            {
                "statusCode": 400,
                "body": f"Wrong primary for {self.table.name}: "
                f"required for table is {self.table.pk}; {provided_message}",
                "headers": {"Content-Type": "text/plain"},
            }
        )

    def missing_primary_key(self, missing):
        raise self._primary_key_rudimentary_message(f"missing {missing}")

    def wrong_primary_key(self, given):
        raise self._primary_key_rudimentary_message(f"given {given}")

    def wrong_data_type(self, error: ValidationError):
        if error.validator == "type":
            response = {
                "statusCode": 415,
                "body": f"Wrong value type in {self.table.name} for key={'/'.join(error.absolute_path)}:\n"
                f"{error.message}.",
                "headers": {"Content-Type": "text/plain"},
            }
            if "enum" in error.schema and error.schema["enum"]:
                response["body"] += f"\nenum: {error.schema['enum']}"
            raise TypeError(response)
        elif error.validator == "required":
            response = {
                "statusCode": 400,
                "body": f"{error.message} for table {self.table.name} and is missing",
                "headers": {"Content-Type": "text/plain"},
            }
        elif error.validator == "additionalProperties":
            response = {
                "statusCode": 400,
                "body": f"{error.message} for table {self.table.name}\n"
                f"path to unexpected property: {list(error.relative_path)}",
                "headers": {"Content-Type": "text/plain"},
            }
        else:
            response = {
                "statusCode": 500,
                "body": f"unexpected database validation error for table {self.table.name}: {error.message}",
                "headers": {"Content-Type": "text/plain"},
            }

        raise ValidationError(response)

    def item_already_existing(self, item):
        raise FileExistsError(
            {
                "statusCode": 409,
                "body": f"Item is already existing.\nTable: {self.table.name}\nItem: {item}",
                "headers": {"Content-Type": "text/plain"},
            }
        )

    def removing_required_attribute(self, attribute, path):
        raise ValidationError(
            {
                "statusCode": 400,
                "body": f"{attribute} is a required attribute in {path} for table {self.table.name} and cannot be removed",
                "headers": {"Content-Type": "text/plain"},
            }
        )
