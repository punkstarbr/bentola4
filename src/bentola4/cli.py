"""Command-line entry points for bentola4."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import __version__
from .installer import executable, install


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bentola4",
        description="Instala e executa as ferramentas oficiais do Bento4.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install", help="baixar e instalar o Bento4")
    install_parser.add_argument("--force", action="store_true", help="reinstalar mesmo que já exista")
    install_parser.add_argument("--url", help="URL direta de um ZIP compatível")
    install_parser.add_argument("--dir", type=Path, help="diretório de instalação")

    update_parser = subparsers.add_parser("update", help="baixar novamente a versão mais recente")
    update_parser.add_argument("--url", help="URL direta de um ZIP compatível")
    update_parser.add_argument("--dir", type=Path, help="diretório de instalação")

    return parser


def mp4decrypt_main() -> int:
    """Lazy wrapper exposed as the ``mp4decrypt`` command."""
    try:
        binary = executable("mp4decrypt")
    except Exception as error:  # pragma: no cover - exercised on a clean machine
        print(f"bentola4: falha ao instalar Bento4: {error}", file=sys.stderr)
        return 1
    completed = subprocess.run([str(binary), *sys.argv[1:]])
    return completed.returncode


def main() -> int:
    parser = _parser()
    args = parser.parse_args()

    if args.command == "install":
        try:
            install(args.dir, url=args.url, force=args.force)
            return 0
        except Exception as error:
            print(f"bentola4: falha na instalação: {error}", file=sys.stderr)
            return 1

    if args.command == "update":
        try:
            install(args.dir, url=args.url, force=True)
            return 0
        except Exception as error:
            print(f"bentola4: falha na atualização: {error}", file=sys.stderr)
            return 1

    parser.print_help()
    return 0
