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

    if "AWS_SAM_LOCAL" in environ:
        environ["ENV"] = "local"
        environ["STAGE"] = "TEST"
    elif "AWS_LAMBDA_FUNCTION_NAME" in os_environ:
        environ["ENV"] = "cloud"
    elif "UnitTest" in environ:
        environ["ENV"] = "local"
        environ["STAGE"] = "TEST"
    else:
        if not all(key in environ for key in ["STAGE", "ENV"]):
            raise ValueError("'STAGE' and 'ENV' need to be provided in os.environ")
        # else:
        #     env = environ["ENV"]

    return __switch_db_resource_config[environ["ENV"]]


resource_config = craft_config()
