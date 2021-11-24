"Command line interface to the DataGraphics instance."

import json
import os.path

import click
import flask

import datagraphics.app
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
    with datagraphics.app.app.app_context():
        utils.set_db()
        click.echo(f"{utils.get_count('users', 'username'):>5} users")

@cli.command()
@click.option("--username", help="Username for the new admin account.",
              prompt=True)
@click.option("--email", help="Email address for the new admin account.",
              prompt=True)
@click.option("--password", help="Password for the new admin account.",
              prompt=True, hide_input=True)
def create_admin(username, email, password):
    "Create a new admin account."
    with datagraphics.app.app.app_context():
        try:
            with datagraphics.user.UserSaver() as saver:
                saver.set_username(username)
                saver.set_email(email)
                saver.set_password(password)
                saver.set_role(constants.ADMIN)
                saver.set_status(constants.ENABLED)
        except ValueError as error:
            raise click.ClickException(str(error))

@cli.command()
@click.option("--username", help="Username for the new user account.",
              prompt=True)
@click.option("--email", help="Email address for the new user account.",
              prompt=True)
@click.option("--password", help="Password for the new user account.",
              prompt=True, hide_input=True)
def create_user(username, email, password):
    "Create a new user account."
    with datagraphics.app.app.app_context():
        try:
            with datagraphics.user.UserSaver() as saver:
                saver.set_username(username)
                saver.set_email(email)
                saver.set_password(password)
                saver.set_role(constants.USER)
                saver.set_status(constants.ENABLED)
        except ValueError as error:
            raise click.ClickException(str(error))

@cli.command()
@click.option("--username", help="Username for the user account.",
              prompt=True)
@click.option("--password", help="New password for the user account.",
              prompt=True, hide_input=True)
def password(username, password):
    "Set the password for a user account."
    with datagraphics.app.app.app_context():
        user = datagraphics.user.get_user(username=username)
        if user:
            with datagraphics.user.UserSaver(user) as saver:
                saver.set_password(password)
        else:
            raise click.ClickException("No such user.")


if __name__ == '__main__':
    cli()
