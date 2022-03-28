"""
    This is part of Kerykeion (C) 2020 Giacomo Battaglia
"""

import setuptools

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kerykeion",
    version="2.2.5",
    author="Giacomo Battaglia",
    author_email="battaglia.giacomo@yahoo.it",
    description="A python library for astrology.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/g-battaglia/kerykeion",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=['pyswisseph', 'pytz', 'jsonpickle'],
)
