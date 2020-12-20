from glob import glob
import json


def create_table_for_schema_in_directory(directory):
    from dynamo_db_resource.create_table import (
        create_dynamo_db_table_from_schema,
    )

    schemas = glob(directory)

    for schema_file in schemas:
        with open(schema_file, "r") as f:
            schema = json.load(f)
        create_dynamo_db_table_from_schema(schema)


if __name__ == "__main__":
    from os import environ as os_environ
    from argparse import ArgumentParser

    __parser = ArgumentParser()
    __parser.add_argument(
        "--stage",
        "-s",
        choices=["test", "dev", "prod"],
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
    __vars = vars(__parser.parse_args())
    os_environ["ENV"] = __vars["environment"]
    os_environ["STAGE"] = __vars["stage"].upper()
    os_environ["WRAPPER_CONFIG_FILE"] = "../dynamodb_wrapper_config.json"

    create_table_for_schema_in_directory("../test_data/tables/*.json")
