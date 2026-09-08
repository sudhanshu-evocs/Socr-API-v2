"""Build and verify release artifacts for the Docuverus package."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"


def run(command: list[str]) -> None:
    print(f"\n> {' '.join(command)}")
    subprocess.run(command, cwd=REPOSITORY_ROOT, check=True)


def read_project_metadata() -> tuple[str, str]:
    with PYPROJECT_PATH.open("rb") as pyproject_file:
        project = tomllib.load(pyproject_file)["project"]
    return project["name"], project["version"]


def verify_wheel(wheel_path: Path) -> tuple[int, int]:
    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()

    python_files = [name for name in names if name.startswith("docuverus/") and name.endswith(".py")]
    json_resources = [name for name in names if name.startswith("docuverus/") and name.endswith(".json")]

    if not python_files:
        raise RuntimeError(f"No Docuverus Python modules were found in {wheel_path.name}")
    if not json_resources:
        raise RuntimeError(f"No Docuverus JSON resources were found in {wheel_path.name}")

    return len(python_files), len(json_resources)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(version: str, artifacts: list[Path], output_directory: Path) -> Path:
    checksum_path = output_directory / f"SHA256SUMS-{version}.txt"
    content = "".join(f"{sha256(artifact)}  {artifact.name}\n" for artifact in artifacts)
    checksum_path.write_text(content, encoding="utf-8")
    return checksum_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Build without running pytest. Do not use this for a normal release.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist"),
        help="Artifact directory relative to the repository root (default: dist).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package_name, version = read_project_metadata()
    output_directory = (REPOSITORY_ROOT / args.output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    print(f"Building {package_name} {version}")
    if not args.skip_tests:
        run([sys.executable, "-m", "pytest"])

    run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--sdist",
            "--outdir",
            str(output_directory),
        ]
    )

    normalized_name = package_name.replace("-", "_")
    wheel_path = output_directory / f"{normalized_name}-{version}-py3-none-any.whl"
    source_path = output_directory / f"{package_name}-{version}.tar.gz"
    missing = [path.name for path in (wheel_path, source_path) if not path.is_file()]
    if missing:
        raise RuntimeError(f"Expected build artifacts were not generated: {', '.join(missing)}")

    python_count, json_count = verify_wheel(wheel_path)
    checksum_path = write_checksums(version, [wheel_path, source_path], output_directory)

    print("\nPackage build completed successfully")
    print(f"  Wheel:       {wheel_path}")
    print(f"  Source:      {source_path}")
    print(f"  Checksums:   {checksum_path}")
    print(f"  Wheel files: {python_count} Python modules, {json_count} JSON resources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
