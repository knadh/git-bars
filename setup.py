#!/usr/bin/env python

from setuptools import setup

setup(
    name="git-bars",
    version="1.5",
    description="A utility for visualising git commit activity as bars on the terminal",
    author="Kailash Nadh",
    author_email="kailash@nadh.in",
    url="https://github.com/knadh/git-bars",
    packages=["gitbars"],
    download_url="https://github.com/knadh/git-bars",
    license="MIT License",
    entry_points={
        "console_scripts": [
            "git-bars = gitbars.gitbars:main",
        ],
    },
    classifiers=[
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Version Control :: Git",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ]
)
