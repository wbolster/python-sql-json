import os

from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "README.rst")) as fp:
    long_description = fp.read()

setup(
    name="sql-json",
    description="",
    long_description=long_description,
    version="0.0.1",
    author="wouter bolsterlee",
    author_email="wouter@bolsterl.ee",
    url="https://github.com/wbolster/python-sql-json",
    license="BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
