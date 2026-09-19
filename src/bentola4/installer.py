"""Download and installation helpers for Bento4 command-line binaries."""

from __future__ import annotations

import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Tuple

DOWNLOADS_PAGE = "https://www.bento4.com/downloads/"
DEFAULT_INSTALL_DIR = Path.home() / ".local" / "share" / "bentola4"


def _http_get(url: str, timeout: int = 60) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; bentola4/0.1.0)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except Exception as error:
        curl = shutil.which("curl")
        if curl is None:
            raise error
        result = subprocess.run(
            [curl, "-fsSL", "--retry", "3", "--retry-delay", "1", "-A", "Mozilla/5.0", url],
            capture_output=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise error
        return result.stdout


def _linux_asset_pattern() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return r"Bento4-SDK-[^\"'<> ]+\.(?:x86_64-unknown-linux|x86_64-linux)\.zip"
    if machine in {"aarch64", "arm64"}:
        return r"Bento4-SDK-[^\"'<> ]+\.(?:aarch64-unknown-linux|arm64-linux)\.zip"
    raise RuntimeError(
        "Arquitetura Linux não suportada automaticamente: "
        f"{platform.machine()}. Use BENTOLA4_URL para informar um pacote compatível."
    )


def find_download_url(page: Optional[str] = None) -> str:
    """Find the newest official Bento4 binary URL for the current platform."""
    page = page if page is not None else _http_get(DOWNLOADS_PAGE).decode("utf-8", "replace")
    system = platform.system().lower()

    if system == "linux":
        pattern = _linux_asset_pattern()
    elif system == "darwin":
        machine = platform.machine().lower()
        if machine in {"arm64", "aarch64"}:
            pattern = r"Bento4-SDK-[^\"'<> ]+\.(?:universal-apple-macosx|arm64-apple-macosx)\.zip"
        else:
            pattern = r"Bento4-SDK-[^\"'<> ]+\.universal-apple-macosx\.zip"
    elif system == "windows":
        pattern = r"Bento4-SDK-[^\"'<> ]+\.x86_64-microsoft-win32\.zip"
    else:
        raise RuntimeError(f"Sistema operacional não suportado automaticamente: {platform.system()}")

    matches = re.findall(r"href=[\"']([^\"']+" + pattern + r")[\"']", page, flags=re.IGNORECASE)
    if not matches:
        raise RuntimeError(
            "Não foi encontrado um binário Bento4 compatível na página oficial. "
            "Defina BENTOLA4_URL com uma URL direta para um ZIP compatível."
        )

    return urllib.parse.urljoin(DOWNLOADS_PAGE, matches[0])


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; bentola4/0.1.0)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
        return
    except Exception as error:
        curl = shutil.which("curl")
        if curl is None:
            raise error
        result = subprocess.run(
            [
                curl,
                "-fL",
                "--retry",
                "3",
                "--retry-delay",
                "1",
                "-A",
                "Mozilla/5.0",
                "-o",
                str(destination),
                url,
            ],
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise error


def _extract_archive(archive: Path, destination: Path) -> None:
    if archive.suffix.lower() == ".zip" or zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zf:
            # Prevent path traversal when extracting an archive downloaded remotely.
            root = destination.resolve()
            for member in zf.infolist():
                target = (destination / member.filename).resolve()
                if os.path.commonpath((str(root), str(target))) != str(root):
                    raise RuntimeError("O arquivo Bento4 contém um caminho de extração inválido.")
            zf.extractall(destination)
        return

    if archive.name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive, "r:gz") as tf:
            root = destination.resolve()
            for member in tf.getmembers():
                target = (destination / member.name).resolve()
                if os.path.commonpath((str(root), str(target))) != str(root):
                    raise RuntimeError("O arquivo Bento4 contém um caminho de extração inválido.")
            tf.extractall(destination)
        return

    raise RuntimeError(f"Formato de arquivo Bento4 não suportado: {archive.name}")


def _find_executable(root: Path, name: str) -> Optional[Path]:
    names = [name]
    if platform.system().lower() == "windows":
        names.append(name + ".exe")
    for candidate in root.rglob("*"):
        if candidate.is_file() and candidate.name in names:
            return candidate
    return None


def install(
    install_dir: Optional[Path] = None,
    url: Optional[str] = None,
    force: bool = False,
    quiet: bool = False,
) -> Path:
    """Download the official Bento4 SDK and return the installed directory."""
    install_dir = Path(install_dir or os.environ.get("BENTOLA4_HOME", DEFAULT_INSTALL_DIR)).expanduser()
    url = url or os.environ.get("BENTOLA4_URL") or find_download_url()

    if install_dir.exists() and not force:
        existing = _find_executable(install_dir, "mp4decrypt")
        if existing:
            return install_dir

    install_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bentola4-") as temporary:
        temp = Path(temporary)
        archive = temp / "bento4-download.zip"
        extracted = temp / "extracted"
        extracted.mkdir()
        if not quiet:
            print(f"Baixando Bento4: {url}", file=sys.stderr)
        _download(url, archive)
        _extract_archive(archive, extracted)
        executable = _find_executable(extracted, "mp4decrypt")
        if executable is None:
            raise RuntimeError("O pacote baixado não contém bin/mp4decrypt.")

        staged = temp / "installed"
        staged.mkdir()
        shutil.copytree(executable.parent.parent, staged / "sdk", dirs_exist_ok=True)

        if install_dir.exists():
            shutil.rmtree(install_dir)
        shutil.move(str(staged / "sdk"), str(install_dir))

    for candidate in install_dir.rglob("*"):
        if candidate.is_file() and (candidate.name == "mp4decrypt" or candidate.name == "mp4decrypt.exe"):
            if os.name != "nt":
                candidate.chmod(candidate.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    installed = _find_executable(install_dir, "mp4decrypt")
    if installed is None:
        raise RuntimeError("A instalação terminou, mas mp4decrypt não foi localizado.")
    if not quiet:
        print(f"Instalado em: {installed}", file=sys.stderr)
    return install_dir


def executable(name: str = "mp4decrypt", install_dir: Optional[Path] = None) -> Path:
    """Return a Bento4 executable, installing Bento4 first if needed."""
    root = Path(install_dir or os.environ.get("BENTOLA4_HOME", DEFAULT_INSTALL_DIR)).expanduser()
    found = _find_executable(root, name)
    if found is None:
        install(root)
        found = _find_executable(root, name)
    if found is None:
        raise FileNotFoundError(f"Executável Bento4 não encontrado: {name}")
    return found


def run(name: str, *args: str, install_dir: Optional[Path] = None) -> int:
    """Run a Bento4 executable and return its exit code."""
    command = [str(executable(name, install_dir)), *args]
    return subprocess.call(command)
