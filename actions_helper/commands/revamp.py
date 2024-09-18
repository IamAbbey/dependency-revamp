import re
from dataclasses import dataclass
from typing import Optional, Sequence

from cleo.testers.application_tester import ApplicationTester
from poetry.console.application import Application


@dataclass
class ShowCommandOutput:
    package_name: str
    current_version: str
    new_version: str
    description: str
    current_hash: Optional[str] = None
    new_hash: Optional[str] = None

    @property
    def is_outdated(self) -> bool:
        return (self.current_version != self.new_version) or (self.current_hash != self.new_hash)


def revamp(dry_run: bool) -> Sequence[ShowCommandOutput]:
    app = Application()
    # command = load_command("show")()
    # app.add(command)
    tester = ApplicationTester(app)
    tester.execute("show --outdated")

    if tester.io.fetch_error():
        print(tester.io.fetch_error())
    else:
        output = tester.io.fetch_output()

        line_regex = re.compile(r"\s+")

        line_by_columns = [line_regex.split(line, maxsplit=5) for line in output.split("\n") if line]

        show_outputs = []

        for column in line_by_columns:
            # Usually a line should conform to
            # cleo     2.1.0   2.1.0  Cleo allows you to create beautiful and testable command-line interfaces.

            # But some line's third column might be the commit hash for GitHub dependencies
            # moneymeets-utils     0.1.0 6268fab 0.1.0 6268fab Common moneymeets Python utilities

            # if the third column is a version number; then it is the usual case
            if re.compile(r"(\d+\.)(\d+\.)(\*|\d+)").match(column[2]):
                show_outputs.append(
                    ShowCommandOutput(
                        package_name=column[0],
                        current_version=column[1],
                        new_version=column[2],
                        description=" ".join(column[3:]),
                    ),
                )
            else:
                show_outputs.append(
                    ShowCommandOutput(
                        package_name=column[0],
                        current_version=column[1],
                        current_hash=column[2],
                        new_version=column[3],
                        new_hash=column[4],
                        description=" ".join(column[5:]),
                    ),
                )

        assert len(show_outputs) == len(output.split("\n")) - 1
        if dry_run:
            print("Revamp: Dry Run")
            print(output)
        return show_outputs
