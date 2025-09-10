#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="devix",
    version="1.0.0",
    author="Tom Sapletta",
    description="Automatyczny system rozwoju i naprawy kodu",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "pytest>=7.0.0",
        "pylint>=2.15.0",
        "pyautogui>=0.9.53",
        "psutil>=5.9.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "devix=devix.supervisor:main",
        ],
    },
)
