from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


NATIVE_SUFFIXES = {".so", ".pyd", ".dll", ".dylib"}


def _find_runtime_binaries(extract_root: Path) -> list[Path]:
    binaries: list[Path] = []
    for path in extract_root.rglob("*"):
        if not path.is_file() or path.suffix not in NATIVE_SUFFIXES:
            continue
        if path.name.startswith("sms_runtime") or path.name.startswith("libsms_runtime"):
            binaries.append(path)
    return sorted(binaries)


def _repair_linux_wheels(assembly_dir: Path, built_wheels: list[Path]) -> list[Path]:
    wheelhouse = assembly_dir / "wheelhouse"
    wheelhouse.mkdir(exist_ok=True)
    for built_wheel in built_wheels:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "auditwheel",
                "repair",
                str(built_wheel),
                "-w",
                str(wheelhouse),
            ],
            cwd=assembly_dir,
            check=True,
        )
    repaired = sorted(wheelhouse.glob("*.whl"))
    if not repaired:
        raise SystemExit("auditwheel did not produce a repaired wheel")
    return repaired


def _copy_public_package_tree(repo_root: Path, assembly_dir: Path, private_root: Path) -> None:
    package_src = repo_root / "pytrade"
    setup_src = repo_root / "setup.py"
    readme_src = repo_root / "README.md"
    license_src = repo_root / "LICENSE"
    private_version_src = private_root / "pytrade" / "sms" / "version.py"

    if not package_src.exists():
        raise SystemExit("pytrade package directory not found")
    if not setup_src.exists():
        raise SystemExit("setup.py not found")
    if not readme_src.exists():
        raise SystemExit("README.md not found")
    if not license_src.exists():
        raise SystemExit("LICENSE not found")
    if not private_version_src.exists():
        raise SystemExit("private version.py not found")

    shutil.copytree(package_src, assembly_dir / "pytrade", dirs_exist_ok=True)
    shutil.copy2(setup_src, assembly_dir / "setup.py")
    shutil.copy2(readme_src, assembly_dir / "README.md")
    shutil.copy2(license_src, assembly_dir / "LICENSE")
    shutil.copy2(private_version_src, assembly_dir / "pytrade" / "sms" / "version.py")


def main() -> None:
    repo_root = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd())).resolve()
    private_root = repo_root / os.environ.get("PYTRADE_SMS_PRIVATE_SRC", "private-src")
    dist_dir = repo_root / os.environ.get("PYTRADE_SMS_DIST_DIR", "dist")

    if not private_root.exists():
        raise SystemExit("private source repository not found")

    source_wheels = sorted(dist_dir.glob("*.whl"))
    if not source_wheels:
        raise SystemExit("No wheels found in dist")

    for source_wheel in source_wheels:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source_extract_dir = temp_dir / "source"
            assembly_dir = temp_dir / "assembly"
            source_extract_dir.mkdir()
            assembly_dir.mkdir()

            with zipfile.ZipFile(source_wheel, "r") as archive:
                archive.extractall(source_extract_dir)

            runtime_binaries = _find_runtime_binaries(source_extract_dir)
            if not runtime_binaries:
                raise SystemExit(f"sms_runtime binary not found in {source_wheel.name}")

            _copy_public_package_tree(repo_root, assembly_dir, private_root)

            package_sms_dir = assembly_dir / "pytrade" / "sms"
            for runtime_binary in runtime_binaries:
                shutil.copy2(runtime_binary, package_sms_dir / runtime_binary.name)

            source_wheel.unlink()
            subprocess.run(
                [sys.executable, "setup.py", "bdist_wheel", "--py-limited-api=cp310"],
                cwd=assembly_dir,
                check=True,
            )

            built_wheels = sorted((assembly_dir / "dist").glob("*.whl"))
            if not built_wheels:
                raise SystemExit("bdist_wheel did not produce a wheel")

            if sys.platform.startswith("linux"):
                built_wheels = _repair_linux_wheels(assembly_dir, built_wheels)

            for built_wheel in built_wheels:
                shutil.copy2(built_wheel, dist_dir / built_wheel.name)


if __name__ == "__main__":
    main()
