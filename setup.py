import os

from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "README.rst")) as fp:
    long_description = fp.read()

with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as fp:
    install_requires = fp.readlines()

setup(
    name="sql-json",
    description="",
    long_description=long_description,
    version="0.0.1",
    author="wouter bolsterlee",
    author_email="wouter@bolsterl.ee",
    url="https://github.com/wbolster/python-sql-json",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=install_requires,
    license="BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
