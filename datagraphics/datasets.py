"Lists of datasets."

import flask

import datagraphics.dataset
import datagraphics.user

from datagraphics import constants
from datagraphics import utils

blueprint = flask.Blueprint("datasets", __name__)

@blueprint.route("/")
def display():
    "Show logged-in user's datasets, or public datasets."
    if flask.g.current_user:
        datasets = get_datasets_owner(flask.g.current_user["username"],
                                      full=True)
    else:
        datasets = get_datasets_public(full=True)
    return flask.render_template("datasets/display.html",
                                 datasets=datasets,
                                 show_public=bool(flask.g.current_user))

@blueprint.route("/public")
def public():
    "Display list of public datasets."
    datasets = get_datasets_public(full=True)
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
    datasets = get_datasets_owner(username, full=True)
    return flask.render_template("datasets/user.html",
                                 user=user,
                                 datasets=datasets,
                                 show_public=True)

def get_datasets_owner(username, full=False):
    "Get the datasets owned by the given user."
    view = flask.g.db.view("datasets", "owner_modified",
                           startkey=(username,"ZZZZZZ"),
                           endkey=(username, ""),
                           include_docs=full,
                           reduce=False,
                           descending=True)
    result = []
    if full:
        for row in view:
            flask.g.cache[row.doc["_id"]] = row.doc
            result.append(row.doc)
    else:
        for row in view:
            result.append((row.id, row.value, row.key[1]))
    return result

def get_datasets_public(full=False):
    "Get the public datasets."
    view = flask.g.db.view("datasets", "public_modified",
                           startkey="ZZZZZZ",
                           endkey="",
                           include_docs=full,
                           reduce=False,
                           descending=True)
    result = []
    if full:
        for row in view:
            flask.g.cache[row.doc["_id"]] = row.doc
            result.append(row.doc)
    else:
        for row in view:
            result.append((row.id, row.value, row.key))
    return result
