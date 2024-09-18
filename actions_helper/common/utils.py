import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Optional

GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS", "false") == "true"


def set_multiline_github_output(name, value):
    if GITHUB_ACTIONS:
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as fh:
            delimiter = uuid.uuid1()
            print(f"{name}<<{delimiter}", file=fh)
            print(value, file=fh)
            print(delimiter, file=fh)


def set_github_output(name, value):
    if GITHUB_ACTIONS:
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as fh:
            print(f"{name}={value}", file=fh)


def set_error(message: str, file: Optional[str] = None, line: Optional[str] = None):
    print(f"::error {f'file={file}' if file else ''}{f',line={line}' if line else ''}::{message}")
    exit(1)


def _run_process(command: str, check: bool = True, capture_output: bool = False):
    logging.info(f"RUNNING {command}")
    return subprocess.run(command, check=check, shell=True, text=True, capture_output=capture_output)
