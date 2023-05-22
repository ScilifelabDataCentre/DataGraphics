"Command line interface to the DataGraphics instance."

import json
import os.path
import time

import click
import flask

import datagraphics.main
import datagraphics.user
from datagraphics import constants
from datagraphics import utils


@click.group()
def cli():
    "Command line interface to the DataGraphics instance."
    pass


@cli.command()
def counts():
    "Output counts of entities in the system."
    with datagraphics.main.app.app_context():
        utils.set_db()
        click.echo(f"{utils.get_count('users', 'username'):>5} users")
        click.echo(f"{utils.get_count('datasets', 'owner_modified'):>5} datasets")
        click.echo(f"{utils.get_count('graphics', 'owner_modified'):>5} graphics")


@cli.command()
@click.option("--username", help="Username for the new admin account.", prompt=True)
@click.option("--email", help="Email address for the new admin account.", prompt=True)
@click.option(
    "--password",
    help="Password for the new admin account.",
    prompt=True,
    hide_input=True,
)
def create_admin(username, email, password):
    "Create a new admin account."
    with datagraphics.main.app.app_context():
        utils.set_db()
        try:
            with datagraphics.user.UserSaver() as saver:
                saver.set_username(username)
                saver.set_email(email)
                saver.set_password(password)
                saver.set_apikey()
                saver.set_role(constants.ADMIN)
                saver.set_status(constants.ENABLED)
        except ValueError as error:
            raise click.ClickException(str(error))


@cli.command()
@click.option("--username", help="Username for the new user account.", prompt=True)
@click.option("--email", help="Email address for the new user account.", prompt=True)
@click.option(
    "--password",
    help="Password for the new user account.",
    prompt=True,
    hide_input=True,
)
def create_user(username, email, password):
    "Create a new user account."
    with datagraphics.main.app.app_context():
        utils.set_db()
        try:
            with datagraphics.user.UserSaver() as saver:
                saver.set_username(username)
                saver.set_email(email)
                saver.set_password(password)
                saver.set_apikey()
                saver.set_role(constants.USER)
                saver.set_status(constants.ENABLED)
        except ValueError as error:
            raise click.ClickException(str(error))


@cli.command()
@click.option("--username", help="Username for the user account.", prompt=True)
@click.option(
    "--password",
    help="New password for the user account.",
    prompt=True,
    hide_input=True,
)
def password(username, password):
    "Set the password for a user account."
    with datagraphics.main.app.app_context():
        utils.set_db()
        user = datagraphics.user.get_user(username=username)
        if user:
            with datagraphics.user.UserSaver(user) as saver:
                saver.set_password(password)
        else:
            raise click.ClickException("No such user.")


@cli.command()
@click.option(
    "-d",
    "--dumpfile",
    type=str,
    help="The path of the DataGraphics database dump file.",
)
@click.option(
    "-D",
    "--dumpdir",
    type=str,
    help="The directory to write the dump file in, using the default name.",
)
@click.option(
    "--progressbar/--no-progressbar", default=True, help="Display a progressbar."
)
def dump(dumpfile, dumpdir, progressbar):
    "Dump all data in the database to a .tar.gz dump file."
    with datagraphics.main.app.app_context():
        utils.set_db()
        if not dumpfile:
            dumpfile = "dump_{0}.tar.gz".format(time.strftime("%Y-%m-%d"))
            if dumpdir:
                dumpfile = os.path.join(dumpdir, dumpfile)
        ndocs, nfiles = flask.g.db.dump(
            dumpfile, exclude_designs=True, progressbar=progressbar
        )
        click.echo(f"Dumped {ndocs} documents and {nfiles} files to {dumpfile}")


@cli.command()
@click.argument("dumpfile", type=click.Path(exists=True))
@click.option(
    "--progressbar/--no-progressbar", default=True, help="Display a progressbar."
)
def undump(dumpfile, progressbar):
    "Load a DataGraphics database dump file. The database must be empty."
    with datagraphics.main.app.app_context():
        utils.set_db()
        if utils.get_count("users", "username") != 0:
            raise click.ClickException(
                f"The database '{datagraphics.main.app.config['COUCHDB_DBNAME']}'"
                " is not empty."
            )
        ndocs, nfiles = flask.g.db.undump(dumpfile, progressbar=progressbar)
        click.echo(f"Loaded {ndocs} documents and {nfiles} files.")

@cli.command()
@click.argument("old_baseurl", type=str)
@click.argument("new_baseurl", type=str)
def baseurl(old_baseurl, new_baseurl):
    "Exchange the base URL of all data sources for all graphics."
    def exchange(data, old_baseurl, new_baseurl):
        if isinstance(data, dict):
            for key, value in list(data.items()):
                if isinstance(value, (dict, list)):
                    exchange(value, old_baseurl, new_baseurl)
                elif key == "url" and value.startswith(old_baseurl):
                    data["url"] = new_baseurl + value[len(old_baseurl):]
                    click.echo(f"{value} -> {data['url']}")
        elif isinstance(data, list):
            for pos, value in enumerate(data):
                if isinstance(value, (dict, list)):
                    exchange(value, old_baseurl, new_baseurl)

    with datagraphics.main.app.app_context():
        utils.set_db()
        view = flask.g.db.view(
            "graphics",
            "owner_modified",
            startkey=("ZZZZZZ", "ZZZZZZ"),
            endkey=("", ""),
            include_docs=True,
            reduce=False,
            descending=True
        )
        for row in view:
            exchange(row.doc, old_baseurl, new_baseurl)
            flask.g.db.put(row.doc)


if __name__ == "__main__":
    cli()
