from .dynamo_db_table import Table


__all__ = ["database_resource", "DatabaseResourceController"]


class DatabaseResourceController:
    def __init__(self, config: dict = None):
        self.__tables = dict()
        self._config = config if config else {}

    def __getitem__(self, table_name: str) -> Table:
        if table_name not in self.__tables:
            self.__create_table_connection(table_name)

        return self.__tables[table_name]

    def __create_table_connection(self, table_name: str):
        self.__tables[table_name] = Table(table_name, config=self._config)


database_resource = DatabaseResourceController()
