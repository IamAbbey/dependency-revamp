import click

from actions_helper.commands.revamp import revamp
from actions_helper.common.github_helpers import check_and_push_changes
from actions_helper.common.utils import _run_process

@click.group()
def cli():
    pass


@cli.command(name="revamp-dependencies")
@click.option("--dry-run/--no-dry-run", default=True, type=bool)
def cmd_revamp(dry_run: str):

    changes = revamp(dry_run=dry_run)
    if changes:
        if not dry_run:
            _run_process("poetry update")

    if not dry_run:
        check_and_push_changes()
