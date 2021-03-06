#!/usr/bin/env python
#
#  TODO:
#   * Figure out how to compile and install documentation automatically
#   * Add download_url


import codecs
import os
from distutils.util import convert_path
from fnmatch import fnmatchcase


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import versioneer


CLASSIFIERS = """\
Development Status :: 6 - Mature
Intended Audience :: Education
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved :: BSD License
Programming Language :: Python
Topic :: Software Development :: Code Generators
Topic :: Software Development :: Compilers
Topic :: Scientific/Engineering :: Mathematics
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
Programming Language :: Python :: 3
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.9
"""
NAME = "Aesara-PyMC"
MAINTAINER = "PyMC developers"
MAINTAINER_EMAIL = "pymc-devs@gmail.com"
DESCRIPTION = (
    "Optimizing compiler for evaluating mathematical " + "expressions on CPUs and GPUs."
)
LONG_DESCRIPTION = (
    codecs.open("DESCRIPTION.txt", encoding="utf-8").read()
    + "\n\n"
    + codecs.open("NEWS.txt", encoding="utf-8").read()
)
URL = "http://deeplearning.net/software/aesara/"
DOWNLOAD_URL = ""
LICENSE = "BSD"
CLASSIFIERS = [_f for _f in CLASSIFIERS.split("\n") if _f]
AUTHOR = "LISA laboratory, University of Montreal"
AUTHOR_EMAIL = "pymc-devs@gmail.com"
PLATFORMS = ["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"]


def find_packages(where=".", exclude=()):
    out = []
    stack = [(convert_path(where), "")]
    while stack:
        where, prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if (
                "." not in name
                and os.path.isdir(fn)
                and os.path.isfile(os.path.join(fn, "__init__.py"))
            ):
                out.append(prefix + name)
                stack.append((fn, prefix + name + "."))
    for pat in list(exclude) + ["ez_setup", "distribute_setup"]:
        out = [item for item in out if not fnmatchcase(item, pat)]
    return out


version_data = versioneer.get_versions()

if version_data["error"] is not None:
    # Get the fallback version
    # We can't import aesara.version as it isn't yet installed, so parse it.
    fname = os.path.join(os.path.split(__file__)[0], "aesara", "version.py")
    with open(fname) as f:
        lines = f.readlines()
    lines = [l for l in lines if l.startswith("FALLBACK_VERSION")]
    assert len(lines) == 1

    FALLBACK_VERSION = lines[0].split("=")[1].strip().strip('"')

    version_data["version"] = FALLBACK_VERSION


def do_setup():
    setup(
        name=NAME,
        version=version_data["version"],
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        classifiers=CLASSIFIERS,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,
        license=LICENSE,
        platforms=PLATFORMS,
        packages=find_packages(),
        cmdclass=versioneer.get_cmdclass(),
        install_requires=["numpy>=1.9.1", "scipy>=0.14"],
        package_data={
            "": [
                "*.txt",
                "*.rst",
                "*.cu",
                "*.cuh",
                "*.c",
                "*.sh",
                "*.pkl",
                "*.h",
                "*.cpp",
                "ChangeLog",
                "c_code/*",
            ],
            "aesara.misc": ["*.sh"],
            "aesara.d3viz": ["html/*", "css/*", "js/*"],
        },
        entry_points={
            "console_scripts": [
                "aesara-cache = bin.aesara_cache:main",
            ]
        },
        keywords=" ".join(
            [
                "aesara",
                "math",
                "numerical",
                "symbolic",
                "blas",
                "numpy",
                "gpu",
                "autodiff",
                "differentiation",
            ]
        ),
    )


if __name__ == "__main__":
    do_setup()
