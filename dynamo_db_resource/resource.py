from aws_environ_helper import environ, hash_dict
from .dynamo_db_table import Table


__all__ = ["database_resource"]


class _CachedDatabaseResource(Table):
    # ToDo delete hash/update cache on every operation manipulating the object
    def __init__(self, table_name):
        self.__table = Table(table_name)
        self.__storage = dict()
        self.__hashes = dict()
        self.__current_lookup_key = str()

        super().__init__(table_name)

    def __calculate_lookup_key(self, kwargs):
        self.__current_lookup_key = str(dict(sorted(kwargs.items())))

    def __update_item_from_db(self, **kwargs):
        response = self.__table.get(**kwargs)
        self.__storage[self.__current_lookup_key] = response
        self.__hashes[self.__current_lookup_key] = hash_dict(response)

    def get(self, hash=None, **kwargs):
        self.__calculate_lookup_key(kwargs)
        if (
            self.__current_lookup_key not in self.__storage
            or hash != self.__hashes[self.__current_lookup_key]
        ):
            self.__update_item_from_db(**kwargs)
        return self.__storage[self.__current_lookup_key]

    def _hash_of(self, **kwargs):
        self.__calculate_lookup_key(kwargs)
        return self.__hashes[self.__current_lookup_key]


class DatabaseResourceController:
    def __init__(self):
        self.__tables = dict()

    def __getitem__(self, table_name: str) -> (Table, _CachedDatabaseResource):
        if table_name not in self.__tables:
            self.__create_table_connection(table_name)

        return self.__tables[table_name]

    def __create_table_connection(self, table_name: str):
        if table_name in environ["WRAPPER_DATABASE"]["noSQL"]["CACHED_TABLES"]:
            self.__tables[table_name] = _CachedDatabaseResource(table_name)
        else:
            self.__tables[table_name] = Table(table_name)


database_resource = DatabaseResourceController()
