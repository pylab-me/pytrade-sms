from pathlib import Path

from buildkit.commands import ReleaseBuild
from buildkit.options import default_build_options
from buildkit.plan import BuildPlan
from buildkit.version import read_version
from setuptools import setup
from setuptools.dist import Distribution


BASE_DIR = Path(__file__).resolve().parent
DIST_NAME = "pytrade-sms"
MODULE_ROOT = "pytrade"
VERSION_FILE = BASE_DIR / MODULE_ROOT / "sms" / "version.py"

# 解析 --old / --release
options = default_build_options()
options.use_namespace_packages = True
options.use_temp_build = False
# - 只写 exclude_sources -> 不编译 .pyd，但可能还有 .py。
# - 只写 exclude_modules -> 不打包 .py，但可能还有 .pyd。
# - 两者都写 -> 在 wheel 里完全消失。
options.exclude_sources = ["pytrade/sms/pipeline.py", "**/pipeline.py"]
options.exclude_modules = ["pytrade/sms/pipeline.py", "pipeline.py"]
options.exclude_sources += [
    "pytrade/sms/core.py",
    "**/core.py",
    "pytrade/sms/inner_tests.py",
    "**/inner_tests.py",
    "pytrade/sms/power.py",
    "**/power.py",
]
options.exclude_modules += [
    "pytrade/sms/core.py",
    "core.py",
    "pytrade/sms/inner_tests.py",
    "inner_tests.py",
    "pytrade/sms/power.py",
    "power.py",
]
options.exclude_package_patterns = ["tests", "examples*"]


class BuildExt(ReleaseBuild):
    options = options
    keep_files = {
        "__init__.py",
        "__main__.py",
        "pkg_info.py",
        "version.py",
    }


class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True


plan = BuildPlan(
    options=options,
    packages=[MODULE_ROOT, f"{MODULE_ROOT}.*"],
    package_dir={MODULE_ROOT: MODULE_ROOT},
    exclude_packages=[
        f"{MODULE_ROOT}.data",
        f"{MODULE_ROOT}.data.*",
        f"{MODULE_ROOT}.providers",
        f"{MODULE_ROOT}.providers.*",
    ],
    exclude_source_globs=[f"**/{file}" for file in BuildExt.keep_files],
)

setup_kwargs, ext_modules = plan.build()
setup_kwargs["cmdclass"] = plan.cmdclass(build_ext_cls=BuildExt)

setup(
    name=DIST_NAME,
    version=read_version(VERSION_FILE),
    description="SMS metadata engine with Rust runtime core.",
    author="HarmonSir",
    author_email="git@pylab.me",
    license="MIT",
    python_requires=">=3.12",
    include_package_data=True,
    package_data={
        "pytrade.sms": [
            "*.pyd",
            "*.so",
            "*.dll",
            "*.dylib",
        ],
    },
    distclass=BinaryDistribution,
    zip_safe=False,
    install_requires=[
        "orjson",
        "pandas[excel]",
    ],
    ext_modules=ext_modules,
    **setup_kwargs,
)
