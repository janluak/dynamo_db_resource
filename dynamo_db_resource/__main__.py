from pathlib import Path
from fil_io.select import get_file_list_from_directory
import json


def create_table(schema_file):
    from dynamo_db_resource.table_existence import (
        create_dynamo_db_table_from_schema,
    )

    with open(schema_file, "r") as f:
        schema = json.load(f)
    create_dynamo_db_table_from_schema(schema)


def create_table_for_schema_in_directory(directory, tables=None):
    schemas = get_file_list_from_directory(directory, file_ending=".json")

    for schema_file in schemas:
        if not tables:
            create_table(schema_file)
        else:
            schema_file = Path(schema_file)
            if any(f"{i}.json" == schema_file.name for i in tables):
                create_table(schema_file)


if __name__ == "__main__":
    from os import environ as os_environ
    from argparse import ArgumentParser

    __parser = ArgumentParser()
    __parser.add_argument(
        "--stage",
        "-s",
        help="stage name",
        default="test",
    )
    __parser.add_argument(
        "--environment",
        "-e",
        choices=["local", "cloud"],
        help="environment names",
        default="local",
    )

    __parser.add_argument(
        "--tables",
        "-t",
        help="which tables to create",
        nargs="*",
    )

    __parser.add_argument(
        "--directory",
        "-d",
        help="directory of schema files",
        default="../test_data/tables/",
    )

    __vars = vars(__parser.parse_args())
    os_environ["ENV"] = __vars["environment"]
    os_environ["STAGE"] = __vars["stage"].upper()
    os_environ["WRAPPER_CONFIG_FILE"] = "../dynamodb_wrapper_config.json"

    if not __vars["tables"]:
        create_table_for_schema_in_directory(__vars["directory"])
    else:
        create_table_for_schema_in_directory(__vars["directory"], __vars["tables"])
