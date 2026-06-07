#!/usr/bin/env python3
"""Run `lbg sdbx` with BOHR_ACCESS_KEY mapped for the lbg beta CLI."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_lbg() -> str:
    found = shutil.which("lbg")
    if found:
        return found
    candidates = [
        Path(sys.executable).with_name("lbg"),
        Path.home() / "Library" / "Python" / f"{sys.version_info.major}.{sys.version_info.minor}" / "bin" / "lbg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    print("ERROR: lbg CLI not found. Install with: python3 -m pip install --pre --upgrade lbg", file=sys.stderr)
    return ""


def main() -> int:
    lbg = resolve_lbg()
    if not lbg:
        return 2

    env = os.environ.copy()
    ak = env.get("BOHR_ACCESS_KEY", "")
    if ak and not env.get("BOHRIUM_ACCESS_KEY"):
        env["BOHRIUM_ACCESS_KEY"] = ak

    return subprocess.run([lbg, "sdbx", *sys.argv[1:]], env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
