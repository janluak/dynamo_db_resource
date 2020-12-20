import subprocess


def check_if_instance_running():
    result = subprocess.check_output("docker ps", shell=True)
    if "amazon/dynamodb-local" in str(result):
        return True
    else:
        return False


if __name__ == "__main__":
    if not check_if_instance_running():
        try:
            subprocess.call("/usr/local/bin/docker-compose up", shell=True)
        except KeyboardInterrupt:
            print("local DynamoDB instance stopped")
    else:
        print("already running a DDB docker")
