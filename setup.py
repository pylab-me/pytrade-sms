from __future__ import annotations

from pathlib import Path

from setuptools import Distribution, find_namespace_packages, setup
from setuptools.command.build_py import build_py


BASE_DIR = Path(__file__).resolve().parent
VERSION_FILE = BASE_DIR / "pytrade" / "sms" / "version.py"
RUNTIME_PATTERNS = ["*.pyd", "*.so", "*.dll", "*.dylib"]
EXCLUDED_SMS_MODULES = {"inner_tests", "pipeline", "power", "private_api"}


def read_version() -> str:
    namespace: dict[str, str] = {}
    exec(VERSION_FILE.read_text(encoding="utf-8"), namespace)
    return namespace["__VERSION__"]


class BinaryDistribution(Distribution):
    def has_ext_modules(self) -> bool:
        return True


class PublicOnlyBuildPy(build_py):
    def find_package_modules(self, package: str, package_dir: str):
        modules = super().find_package_modules(package, package_dir)
        if package != "pytrade.sms":
            return modules
        return [
            module
            for module in modules
            if module[1] not in EXCLUDED_SMS_MODULES
        ]


README = Path(__file__).resolve().parent / "README.md"

setup(
    name="pytrade-sms",
    version=read_version(),
    description="SMS metadata engine with Rust runtime core.",
    long_description=README.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="HarmonSir",
    author_email="git@pylab.me",
    license="Apache-2.0",
    python_requires=">=3.10",
    packages=find_namespace_packages(include=["pytrade.sms"]),
    include_package_data=False,
    package_data={"pytrade.sms": RUNTIME_PATTERNS},
    cmdclass={"build_py": PublicOnlyBuildPy},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Rust",
        "Typing :: Typed",
    ],
    distclass=BinaryDistribution,
    zip_safe=False,
)
