#!/usr/bin/env python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    os.environ["CUSTOM_COMPILE_COMMAND"] = "requirements/compile.py"
    os.environ["PIP_REQUIRE_VIRTUALENV"] = "0"
    common_args = [
        "-m",
        "piptools",
        "compile",
        "--generate-hashes",
        "--allow-unsafe",
    ] + sys.argv[1:]

    subprocess.run(
        [
            "python3.10",
            *common_args,
            "-P",
            "Django>=4.2a1,<5.0",
            "-o",
            "py310-django42.txt",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "python3.10",
            *common_args,
            "-P",
            "Django>=5.0a1,<5.1",
            "-o",
            "py310-django50.txt",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "python3.11",
            *common_args,
            "-P",
            "Django>=4.2a1,<5.0",
            "-o",
            "py311-django42.txt",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "python3.11",
            *common_args,
            "-P",
            "Django>=5.0a1,<5.1",
            "-o",
            "py311-django50.txt",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "python3.12",
            *common_args,
            "-P",
            "Django>=4.2a1,<5.0",
            "-o",
            "py312-django42.txt",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "python3.12",
            *common_args,
            "-P",
            "Django>=5.0a1,<5.1",
            "-o",
            "py312-django50.txt",
        ],
        check=True,
        capture_output=True,
    )
