from .dynamo_db_table import Table


__all__ = ["database_resource"]


class DatabaseResourceController:
    def __init__(self):
        self.__tables = dict()

    def __getitem__(self, table_name: str) -> (Table):
        if table_name not in self.__tables:
            self.__create_table_connection(table_name)

        return self.__tables[table_name]

    def __create_table_connection(self, table_name: str):
        self.__tables[table_name] = Table(table_name)


database_resource = DatabaseResourceController()
