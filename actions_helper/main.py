import click

from actions_helper.commands.revamp import poetry_update, process_outdated_packages
from actions_helper.common.github_helpers import check_and_push_changes
from actions_helper.common.templating import render_string_from_template


@click.group()
def cli():
    pass


@cli.command(name="revamp-dependencies")
@click.option("--dry-run", default="true", type=str)
@click.option("--toplevel", default="false", type=str)
@click.option("--reviewers", default="", type=str)
def cmd_revamp(dry_run: str, reviewers: str, toplevel: str):
    dry_run = True if dry_run.lower() == "true" else False
    toplevel = True if toplevel.lower() == "true" else True
    reviewers = reviewers.split(",") if reviewers else []
    outdated_packages = process_outdated_packages()
    packaged_update = poetry_update(dry_run=dry_run)
    package_update_names = [package.package_name for package in packaged_update]

    rendered_message = render_string_from_template(
        "pr-description.j2",
        context={
            "toplevel": toplevel,
            "packaged_update": packaged_update,
            "outdated_package_names": [package.package_name for package in outdated_packages],
            "skipped": [package for package in outdated_packages if package.package_name not in package_update_names],
        },
    )

    if not dry_run:
        print("Revamp: Commiting to GitHub...")
        check_and_push_changes(
            pr_body=rendered_message,
            reviewers=reviewers,
        )
    else:
        print(rendered_message)


if __name__ == "__main__":
    cli()
