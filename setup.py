import os
import setuptools

with open("README.md", "r") as f:
    readme = f.read()


required_packages = ["sagemaker"]

setuptools.setup(
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=required_packages
)