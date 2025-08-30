import os
import json
from typing import Dict, List
from setuptools import setup, find_namespace_packages


CODEBASE_PATH = os.environ.get(
    "CODEBASE_PATH",
    default=os.path.join("src", "main"),
)

with open("requirements.txt", "r") as file:
    requirements = [line for line in file.read().splitlines() if line and not line.startswith("#")]

version_filepath = os.path.join(CODEBASE_PATH, "fred", "version")
with open(version_filepath, "r") as file:
    version = file.read().strip()

with open("README.md") as file:
    readme = file.read()

setup(
    name="fred-oss",
    version=version,
    description="FREDOSS",
    long_description=readme,
    long_description_content_type='text/markdown',
    url="https://fred.fahera.mx",
    author="Fahera Research, Education, and Development",
    author_email="fred@fahera.mx",
    packages=find_namespace_packages(where=CODEBASE_PATH),
    package_dir={
        "": CODEBASE_PATH
    },
    package_data={
        "": [
            version_filepath,
        ]
    },
    entry_points={
        "console_scripts": [
            "fred=fred.cli.main:CLI.cli_exec",
        ]
    },
    install_requires=requirements,
    include_package_data=True,
    # Python version should be aligned to the latest databricks LTS runtime at the moment.
    # For more info: https://docs.databricks.com/aws/en/release-notes/runtime/ 
    # Reference: Databricks Runtime 16.4 LTS Using Python 3.12.3
    python_requires=">=3.12",
)
