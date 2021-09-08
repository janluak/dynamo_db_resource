"""
The setup file_name.
If development mode (=changes in package code directly delivered to python) `pip install -e .` in directory of this file_name
"""

from setuptools import setup, find_packages
from dynamo_db_resource import __version__

# https://python-packaging.readthedocs.io/en/latest/minimal.html

with open("README.md", "r") as f:
    long_description = f.read()

requirements_file = 'requirements.txt'
with open(requirements_file) as f:
    requirements = f.read().splitlines()
test_requirements_file = 'requirements-test.txt'
with open(test_requirements_file) as f:
    test_requirements = f.read().splitlines()


setup(
    name="dynamo_db_resource",
    version=__version__,
    description="abstraction of AWS Dynamo DB",
    url="https://github.com/janluak/dynamo_db_resource",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jan Lukas Braje",
    author_email="aws_dynamo_db@getkahawa.com",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
    ],
    # https://pypi.org/pypi?%3Aaction=list_classifiers
    install_requires=requirements,
    extra_require={"testing": test_requirements},
)
