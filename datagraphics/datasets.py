"Lists of datasets."

import flask

import datagraphics.dataset
import datagraphics.user

from datagraphics import constants
from datagraphics import utils

blueprint = flask.Blueprint("datasets", __name__)

@blueprint.route("/")
def display():
    "Show logged-in user's tags, or public tags."
    if flask.g.current_user:
        username = flask.g.current_user["username"]
        datasets = [r.doc for r in flask.g.db.view("datasets", "owner_modified",
                                                   startkey=(username,"ZZZZZZ"),
                                                   endkey=(username, ""),
                                                   include_docs=True,
                                                   descending=True)]
    else:
        datasets = [r.doc for r in flask.g.db.view("datasets","public_modified",
                                                   startkey="ZZZZZZ",
                                                   endkey="",
                                                   include_docs=True,
                                                   descending=True)]
    return flask.render_template("datasets/display.html",
                                 datasets=datasets,
                                 show_public=bool(flask.g.current_user))

@blueprint.route("/public")
def public():
    "Display list of public datasets."
    datasets = [r.doc for r in flask.g.db.view("datasets", "public_modified",
                                               startkey="ZZZZZZ",
                                               endkey="",
                                               include_docs=True,
                                               descending=True)]
    return flask.render_template("datasets/public.html", datasets=datasets)

@blueprint.route("/user/<name:username>")
@utils.login_required
def user(username):
    "Display list of user's datasets."
    user = datagraphics.user.get_user(username=username)
    if user is None:
        utils.flash_error("No such user.")
        return flask.redirect(flask.url_for("home"))
    if not datagraphics.user.am_admin_or_self(user):
        utils.flash_error("View access to user is not allowed.")
        return flask.redirect(flask.url_for("home"))
    datasets = [r.doc for r in flask.g.db.view("datasets", "owner_modified",
                                               startkey=(username, "ZZZZZZ"),
                                               endkey=(username, ""),
                                               include_docs=True,
                                               descending=True)]
    return flask.render_template("datasets/user.html",
                                 user=user,
                                 datasets=datasets,
                                 show_public=True)
