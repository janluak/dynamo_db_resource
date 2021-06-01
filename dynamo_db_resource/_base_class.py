from abc import ABC, abstractmethod
from inspect import stack
from jsonschema.exceptions import ValidationError
from os import environ as os_environ
from aws_schema import SchemaValidator

from .exceptions import CustomExceptionRaiser


class NoSQLTable(ABC):
    @abstractmethod
    def __init__(self, table_name):
        self.__table_name = table_name
        self.__custom_exception_raiser = CustomExceptionRaiser(self)

        self.__schema_validator = SchemaValidator(
            **{
                os_environ["DYNAMO_DB_RESOURCE_SCHEMA_ORIGIN"].lower(): os_environ["DYNAMO_DB_RESOURCE_SCHEMA_DIRECTORY"]
                + self.__table_name
            }
        )

    @property
    def name(self):
        return self.__table_name

    @property
    def pk(self):
        return self.__schema_validator.schema["default"]

    @property
    def schema(self):
        return self.__schema_validator.schema

    @property
    @abstractmethod
    def table(self):
        pass

    @property
    def custom_exception(self):
        return self.__custom_exception_raiser

    def _validate_input(self, given_input):
        if "update" in stack()[1].function:
            try:
                self.__schema_validator.validate_sub_part(given_input)
            except ValidationError as e:
                self.custom_exception.wrong_data_type(e)

        elif "put" == stack()[1].function:
            try:
                self.__schema_validator.validate(given_input)
            except ValidationError as e:
                self.custom_exception.wrong_data_type(e)

        else:
            self._primary_key_checker(given_input)

    def _primary_key_checker(self, given_primaries):
        if not all(pk in given_primaries for pk in self.pk):
            self.custom_exception.missing_primary_key(
                [key for key in self.pk if key not in given_primaries]
            )
        elif len(given_primaries) > len(self.pk):
            self.custom_exception.wrong_primary_key(given_primaries)

    @abstractmethod
    def describe(self) -> dict:
        pass

    @abstractmethod
    def get(self, **primary_dict):
        pass

    @abstractmethod
    def add_new_attribute(
        self,
        new_data: dict,
        update_if_existent=False,
        create_item_if_non_existent=False,
        **primary_dict,
    ):
        pass

    @abstractmethod
    def update_attribute(
        self,
        new_data,
        set_new_attribute_if_not_existent=False,
        create_item_if_non_existent=False,
        **primary_dict,
    ):
        pass

    @abstractmethod
    def update_list_item(self, primary_dict, item_no, new_data):
        pass

    @abstractmethod
    def update_append_list(
        self,
        new_data,
        set_new_attribute_if_not_existent=False,
        create_item_if_non_existent=False,
        **primary_dict,
    ):
        pass

    @abstractmethod
    def update_increment(self, path_of_to_increment: dict, **primary_dict):
        pass

    @abstractmethod
    def put(self, item: dict, overwrite=False):
        pass

    @abstractmethod
    def remove_attribute(self, path_of_attribute: dict, **primary_dict):
        pass

    @abstractmethod
    def remove_entry_in_list(
        self, path_to_list: dict, position_to_delete: int, **primary_dict
    ):
        pass

    @abstractmethod
    def delete(self, **primary_dict) -> None:
        pass

    @abstractmethod
    def get_and_delete(self, **primary_dict) -> dict:
        pass

    @abstractmethod
    def scan(self) -> dict:
        pass

    @abstractmethod
    def truncate(self) -> dict:
        pass
