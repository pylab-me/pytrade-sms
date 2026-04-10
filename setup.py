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


setup(
    name="pytrade-sms",
    version=read_version(),
    description="SMS metadata engine with Rust runtime core.",
    author="HarmonSir",
    author_email="git@pylab.me",
    license="MIT",
    python_requires=">=3.10",
    packages=find_namespace_packages(include=["pytrade.sms"]),
    include_package_data=False,
    package_data={"pytrade.sms": RUNTIME_PATTERNS},
    cmdclass={"build_py": PublicOnlyBuildPy},
    distclass=BinaryDistribution,
    zip_safe=False,
)
