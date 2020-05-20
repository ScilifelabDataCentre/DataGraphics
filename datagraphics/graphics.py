"Lists of graphics."

import flask

import datagraphics.graphic
import datagraphics.user

from datagraphics import constants
from datagraphics import utils

blueprint = flask.Blueprint("graphics", __name__)

@blueprint.route("/")
def display():
    "Show logged-in user's graphics, or public graphics."
    if flask.g.current_user:
        username = flask.g.current_user["username"]
        graphics = [r.doc for r in flask.g.db.view("graphics", "owner_modified",
                                                   startkey=(username,"ZZZZZZ"),
                                                   endkey=(username, ""),
                                                   include_docs=True,
                                                   descending=True)]
    else:
        graphics = [r.doc for r in flask.g.db.view("graphics","public_modified",
                                                   startkey="ZZZZZZ",
                                                   endkey="",
                                                   include_docs=True,
                                                   descending=True)]
    return flask.render_template("graphics/display.html",
                                 graphics=graphics,
                                 show_public=bool(flask.g.current_user))

@blueprint.route("/public")
def public():
    "Display list of public graphics."
    graphics = [r.doc for r in flask.g.db.view("graphics", "public_modified",
                                               startkey="ZZZZZZ",
                                               endkey="",
                                               include_docs=True,
                                               descending=True)]
    return flask.render_template("graphics/public.html", graphics=graphics)

@blueprint.route("/user/<name:username>")
@utils.login_required
def user(username):
    "Display list of user's graphics."
    user = datagraphics.user.get_user(username=username)
    if user is None:
        utils.flash_error("No such user.")
        return flask.redirect(flask.url_for("home"))
    if not datagraphics.user.am_admin_or_self(user):
        utils.flash_error("View access to user is not allowed.")
        return flask.redirect(flask.url_for("home"))
    graphics = [r.doc for r in flask.g.db.view("graphics", "owner_modified",
                                               startkey=(username, "ZZZZZZ"),
                                               endkey=(username, ""),
                                               include_docs=True,
                                               descending=True)]
    return flask.render_template("graphics/user.html",
                                 user=user,
                                 graphics=graphics,
                                 show_public=True)
