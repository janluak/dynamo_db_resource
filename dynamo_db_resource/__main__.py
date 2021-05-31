from pathlib import Path
from fil_io.select import get_file_list_from_directory
import json


def create_table(schema_file, include_stage_name):
    from dynamo_db_resource.table_existence import (
        create_dynamo_db_table_from_schema,
    )

    with open(schema_file, "r") as f:
        schema = json.load(f)
    create_dynamo_db_table_from_schema(schema, include_stage_name)


def create_table_for_schema_in_directory(directory, tables=None, include_stage_name: bool = True):
    schemas = get_file_list_from_directory(directory, file_ending=".json")

    for schema_file in schemas:
        if not tables:
            create_table(schema_file)
        else:
            schema_file = Path(schema_file)
            if any(f"{i}.json" == schema_file.name for i in tables):
                create_table(schema_file, include_stage_name)


if __name__ == "__main__":
    from os import environ as os_environ
    from argparse import ArgumentParser

    __parser = ArgumentParser()
    __parser.add_argument(
        "command",
        help="what shall be done",
        choices=["create_table"]
    )

    __parser.add_argument(
        "--stage",
        "-s",
        help="stage name",
        default="dev",
    )
    __parser.add_argument(
        "--environment",
        "-e",
        choices=["local", "cloud"],
        help="environment names",
        default="cloud",
    )

    __parser.add_argument(
        "--region",
        "-r",
        help="AWS region",
    )

    __parser.add_argument(
        "--no_include_stage_name",
        "-no_stage",
        help="do not include stage_name in table name",
        action="store_false"
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
    os_environ["WRAPPER_CONFIG_FILE"] = __vars["config_file"]
    os_environ["AWS_REGION"] = __vars["region"]

    if __vars["command"] == "create_table":
        if not __vars["tables"]:
            create_table_for_schema_in_directory(__vars["directory"], None, __vars["no_include_stage_name"])
        else:
            create_table_for_schema_in_directory(__vars["directory"], __vars["tables"], __vars["no_include_stage_name"])
