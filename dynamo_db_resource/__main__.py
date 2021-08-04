from pathlib import Path
import json


def create_table(schema_file):
    from dynamo_db_resource.table_existence import (
        create_dynamo_db_table_from_schema,
    )

    with open(schema_file, "r") as f:
        schema = json.load(f)
    create_dynamo_db_table_from_schema(schema)


def create_table_for_schema_in_directory(directory, tables=None):
    schemas = [i for i in Path(directory).iterdir() if i.suffix == ".json"]

    for schema_file in schemas:
        if not tables:
            create_table(schema_file)
        else:
            schema_file = Path(schema_file)
            if any(f"{i}.json" == schema_file.name for i in tables):
                create_table(schema_file)


def create_infrastructure_for_schema_in_directory(directory, tables=None):
    from .table_existence import convert_schema_to_infrastructure_code
    schemas = [i for i in Path(directory).iterdir() if i.suffix == ".json"]

    data = dict()
    for schema_file in schemas:
        if not tables:
            with open(schema_file, "r") as f:
                schema = json.load(f)
            infrastructure = convert_schema_to_infrastructure_code(schema)
        else:
            schema_file = Path(schema_file)
            if any(f"{i}.json" == schema_file.name for i in tables):
                with open(schema_file, "r") as f:
                    schema = json.load(f)
                infrastructure = convert_schema_to_infrastructure_code(schema)
            else:
                continue
        data[Path(schema_file).stem] = infrastructure
    return data


if __name__ == "__main__":
    from os import environ as os_environ
    from argparse import ArgumentParser

    __parser = ArgumentParser()
    __parser.add_argument(
        "command",
        help="what shall be done",
        choices=["create_table", "export_infrastructure"]
    )

    __parser.add_argument(
        "--stage",
        "-s",
        help="stage name",
        default="dev",
    )
    __parser.add_argument(
        "--stack",
        "-st",
        help="stack name",
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
        "--tables",
        "-t",
        help="which tables to create",
        nargs="*",
        default=None
    )

    __parser.add_argument(
        "--directory",
        "-d",
        help="directory of schema files",
        default="./",
    )

    __parser.add_argument(
        "--infrastructure_export_type",
        "-it",
        help="data format type of the infrastructure",
        choices=["json", "yml", "yaml"],
        default="yml"
    )

    __vars = vars(__parser.parse_args())
    os_environ["ENV"] = __vars["environment"]
    if __vars["stage"]:
        os_environ['DYNAMO_DB_RESOURCE_STAGE_NAME'] = __vars["stage"].upper()
    if __vars["stack"]:
        os_environ['DYNAMO_DB_RESOURCE_STACK_NAME'] = __vars["stack"].upper()

    if __vars["command"] == "create_table":
        os_environ["AWS_REGION"] = __vars["region"]
        create_table_for_schema_in_directory(__vars["directory"], None)
    if __vars["command"] == "export_infrastructure":
        infrastructure = create_infrastructure_for_schema_in_directory(__vars["directory"], __vars["tables"])
        if __vars["infrastructure_export_type"] != "json":
            from yaml import safe_dump
            print(safe_dump(infrastructure))
        else:
            from json import dumps
            print(dumps(infrastructure))
