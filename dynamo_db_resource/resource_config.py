__all__ = ["create_resource_config"]


def create_resource_config(region: str = "eu-central-1", unittest: bool = False, aws_sam: bool = False) -> dict:
    if region == "local" and not unittest and not aws_sam:
        raise TypeError("if local=True either unittest or aws_sam must be true")
    if unittest and aws_sam:
        raise TypeError("only unittest or aws_sam may be specified")

    __switch_local_docker_env = {
        "UnitTest": "http://localhost:8000",
        "AWS_SAM_LOCAL": "http://docker.for.mac.localhost:8000",
    }
    __switch_db_resource_config = {
        "local": {
            "endpoint_url": __switch_local_docker_env[
                "UnitTest" if unittest else "AWS_SAM_LOCAL"
            ],
            "region_name": "dummy",
            "aws_access_key_id": "dummy",
            "aws_secret_access_key": "dummy",
        },
        "cloud": {"region_name": region},
    }
    return __switch_db_resource_config["cloud" if region != "local" else region]

