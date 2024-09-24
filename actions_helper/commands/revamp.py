import re
from dataclasses import dataclass
from typing import Literal, Optional, Sequence

from cleo.testers.application_tester import ApplicationTester
from poetry.console.application import Application


@dataclass
class ShowCommandOutput:
    package_name: str
    version_installed: str
    version_available: str
    current_hash: Optional[str] = None
    new_hash: Optional[str] = None

    @property
    def is_outdated(self) -> bool:
        return (self.version_installed != self.version_available) or (self.current_hash != self.new_hash)


@dataclass
class UpdateCommandOutput:
    package_name: str
    action: Literal["Removing"] | Literal["Updating"] | Literal["Installing"]
    version_available: Optional[str] = None
    version_installed: Optional[str] = None


app = Application()
tester = ApplicationTester(app)

# ?: makes or's | bracket a non-group
VERSION_NUMBER_REGEX = r"\d+\.\d+\.?(?:\*|\d+)?.*"


def process_outdated_packages() -> Sequence[ShowCommandOutput]:
    status_code = tester.execute("show  --latest --top-level --no-ansi")

    if status_code != 0:
        print(tester.io.fetch_error())
        raise

    output = tester.io.fetch_output()

    line_regex = re.compile(r"\s+")

    line_by_columns = [line_regex.split(line, maxsplit=6) for line in output.split("\n") if line]

    show_outputs = []

    for column in line_by_columns:
        # Usually a line should conform to
        # cleo     2.1.0   2.1.0  Cleo allows you to create beautiful and testable command-line interfaces.

        # But some line's third column might be the commit hash for GitHub dependencies
        # moneymeets-utils     0.1.0 6268fab 0.1.0 6268fab Common moneymeets Python utilities

        # (!) may be present in the second column to denote not-installed at all packages
        # pydantic-settings         (!) 2.5.2            2.5.2            Settings management using Pydantic

        padding = 0
        if column[1] == "(!)":
            padding = 1

        # if the third column is a version number; then it is the usual case
        if re.compile(VERSION_NUMBER_REGEX).match(column[2 + padding]):
            # if the versions are not outdated do not append
            if column[1 + padding] != column[2 + padding]:
                show_outputs.append(
                    ShowCommandOutput(
                        package_name=column[0],
                        version_installed=column[1 + padding],
                        version_available=column[2 + padding],
                    ),
                )
        else:
            # if the versions and hash are not outdated do not append
            if (column[1 + padding] != column[3 + padding]) or (column[2 + padding] != column[4 + padding]):
                show_outputs.append(
                    ShowCommandOutput(
                        package_name=column[0],
                        version_installed=column[1 + padding],
                        current_hash=column[2 + padding],
                        version_available=column[3 + padding],
                        new_hash=column[4 + padding],
                    ),
                )

    # assert len(show_outputs) == len(output.split("\n")) - 1
    return show_outputs


def poetry_update(dry_run: bool) -> Sequence[UpdateCommandOutput]:
    status_code = tester.execute(f"update {'--dry-run' if dry_run else ''}")

    if status_code != 0:
        print(tester.io.fetch_error())
        raise

    output = tester.io.fetch_output()

    line_regex = re.compile(
        # rf"- (Removing|Updating) ([^ ]+) \(({VERSION_NUMBER_REGEX})\s*[->]*\s*({VERSION_NUMBER_REGEX})?\)",
        r"- (Removing|Updating|Installing) ([^ ]+) \(([^->]+)\s*[->]*\s*([^->]+)?\)",
        # Updating django-bootstrap4 (24.3 -> 24.4)
        # Updating moneymeets-utils (0.1.0 6268fab -> 0.1.0 00332cb)
        # Removing asgiref (3.8.1)
        # Installing tenacity (9.0.0)
    )

    line_by_columns = [
        line_regex.match(line.strip())
        for line in output.split("\n")
        if line and " - " in line and "Skipped" not in line
    ]

    update_outputs = []

    for column in line_by_columns:
        group = column.groups()
        if group[0] == "Removing":
            update_outputs.append(
                UpdateCommandOutput(
                    action=group[0],
                    package_name=group[1],
                    version_installed=group[2],
                ),
            )
        elif group[0] == "Installing":
            update_outputs.append(
                UpdateCommandOutput(
                    action=group[0],
                    package_name=group[1],
                    version_available=group[2],
                ),
            )
        elif group[0] == "Updating":
            update_outputs.append(
                UpdateCommandOutput(
                    action="Updating",
                    package_name=group[1],
                    version_installed=group[2],
                    version_available=group[3],
                ),
            )

    assert len(update_outputs) == len(
        [line for line in output.split("\n") if line and line.strip().startswith("-") and "Skipped" not in line],
    )

    return update_outputs
