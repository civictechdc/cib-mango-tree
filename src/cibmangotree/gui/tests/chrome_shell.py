"""Find Chrome's headless shell for Screen tests.

chrome-headless-shell is the separate headless
program and does not appear. The download is cached and reused.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import stat
import subprocess
import urllib.request
import zipfile
from pathlib import Path

import platformdirs
from filelock import FileLock

_KNOWN_GOOD_URL = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "last-known-good-versions-with-downloads.json"
)


def chrome_headless_shell() -> Path:
    """Return the chrome-headless-shell executable, downloading it if needed."""
    configured = os.environ.get("CHROME_HEADLESS_SHELL")
    if configured:
        path = Path(configured)
        if not path.is_file():
            raise FileNotFoundError(f"CHROME_HEADLESS_SHELL does not exist: {path}")
        return path

    platform_key = _platform_key()
    version, url = _stable_download(platform_key)
    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / version / platform_key
    binary_name = (
        "chrome-headless-shell.exe"
        if platform.system() == "Windows"
        else "chrome-headless-shell"
    )
    with FileLock(cache / ".lock"):
        binary = _find_binary(destination, binary_name)
        if binary is None:
            _install(url, destination, binary_name)
            binary = _find_binary(destination, binary_name)
        if binary is None:
            raise RuntimeError(
                f"chrome-headless-shell was not in the archive for {platform_key}"
            )
        return binary


def matching_chromedriver(browser: Path) -> Path:
    """Return a chromedriver that matches the browser, downloading it if needed."""
    version = _browser_version(browser)
    platform_key = _platform_key()
    binary_name = (
        "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
    )
    cache = _cache_dir().parent / "chromedriver"
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / version / platform_key
    url = (
        "https://storage.googleapis.com/chrome-for-testing-public/"
        f"{version}/{platform_key}/chromedriver-{platform_key}.zip"
    )
    with FileLock(cache / ".lock"):
        binary = _find_binary(destination, binary_name)
        if binary is None:
            _install(url, destination, binary_name, timeout=30)
            binary = _find_binary(destination, binary_name)
        if binary is None:
            raise RuntimeError(
                f"chromedriver was not in the archive for {platform_key}"
            )
        return binary


def _browser_version(browser: Path) -> str:
    completed = subprocess.run(
        [str(browser), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", completed.stdout)
    if match is None:
        raise RuntimeError(f"Could not read a browser version from {browser}")
    return match.group(1)


def _platform_key() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    arm = machine in {"arm64", "aarch64"}
    if system == "Darwin":
        return "mac-arm64" if arm else "mac-x64"
    if system == "Linux":
        return "linux-arm64" if arm else "linux64"
    if system == "Windows":
        return "win64" if machine in {"amd64", "x86_64"} else "win32"
    raise RuntimeError(f"chrome-headless-shell is not available for {system} {machine}")


def _cache_dir() -> Path:
    configured = os.environ.get("CHROME_HEADLESS_SHELL_DIR")
    if configured:
        return Path(configured)
    return (
        Path(platformdirs.user_cache_dir("cibmangotree", "Civic Tech DC"))
        / "chrome-headless-shell"
    )


def _stable_download(platform_key: str) -> tuple[str, str]:
    with urllib.request.urlopen(_KNOWN_GOOD_URL, timeout=60) as response:
        payload = json.load(response)
    stable = payload["channels"]["Stable"]
    downloads = stable["downloads"]["chrome-headless-shell"]
    match = next((item for item in downloads if item["platform"] == platform_key), None)
    if match is None:
        raise RuntimeError(
            f"No stable chrome-headless-shell download for {platform_key}"
        )
    return stable["version"], match["url"]


def _install(url: str, destination: Path, binary_name: str, timeout: int = 120) -> None:
    staging = destination.with_name(destination.name + ".partial")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    archive = staging / "chrome-headless-shell.zip"
    try:
        _download(url, archive, timeout=timeout)
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(staging)
        archive.unlink()
        binary = _find_binary(staging, binary_name)
        if binary is None:
            raise RuntimeError(f"Downloaded archive did not contain {binary_name}")
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        _clear_quarantine(staging)
        shutil.rmtree(destination, ignore_errors=True)
        staging.rename(destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _download(url: str, destination: Path, timeout: int = 120) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "cibmangotree-tests"})
    with (
        urllib.request.urlopen(request, timeout=timeout) as response,
        destination.open("wb") as handle,
    ):
        shutil.copyfileobj(response, handle)


def _find_binary(root: Path, name: str) -> Path | None:
    if not root.exists():
        return None
    matches = [path for path in root.rglob(name) if path.is_file()]
    return matches[0] if matches else None


def _clear_quarantine(directory: Path) -> None:
    """Downloaded macOS binaries are blocked until the quarantine flag is removed."""
    if platform.system() != "Darwin":
        return
    subprocess.run(["xattr", "-cr", str(directory)], check=False)
