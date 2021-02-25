from aws_environ_helper import environ
from os import environ as os_environ

__all__ = ["resource_config"]


def craft_config():
    __switch_local_docker_env = {
        "UnitTest": "http://localhost:8000",
        "AWS_SAM_LOCAL": "http://docker.for.mac.localhost:8000",
    }
    __switch_db_resource_config = {
        "local": {
            "endpoint_url": __switch_local_docker_env[
                "UnitTest" if "AWS_SAM_LOCAL" not in environ else "AWS_SAM_LOCAL"
            ],
            "region_name": "dummy",
            "aws_access_key_id": "dummy",
            "aws_secret_access_key": "dummy",
        },
        "cloud": {"region_name": environ["AWS_REGION"]},
    }

    if all(key in os_environ for key in ["STAGE", "ENV"]):
        return __switch_db_resource_config[os_environ["ENV"]]

    return {"region_name": environ["AWS_REGION"]}


resource_config = craft_config()
