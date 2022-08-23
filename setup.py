"""
    This is part of Kerykeion (C) 2022 Giacomo Battaglia
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setup(
    name="kerykeion",
    version="3.1.9",
    author="Giacomo Battaglia",
    author_email="battaglia.giacomo@yahoo.it",
    description="A python library for astrology.",
    home_page="https://github.com/g-battaglia/kerykeion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/g-battaglia/kerykeion",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Typing :: Typed",
    ],
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "pyswisseph",
        "pytz",
        "jsonpickle",
        "requests",
        "requests_cache",
        "pydantic",
    ],
)
