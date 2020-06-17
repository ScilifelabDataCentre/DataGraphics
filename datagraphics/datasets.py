"Lists of datasets."

import flask

import datagraphics.dataset
import datagraphics.user

from datagraphics import constants
from datagraphics import utils

blueprint = flask.Blueprint("datasets", __name__)

@blueprint.route("/")
def display():
    "Redirect to logged-in user's datasets, or public datasets."
    if flask.g.current_user:
        return flask.redirect(
            flask.url_for(".user", username=flask.g.current_user["username"]))
    else:
        return flask.redirect(flask.url_for(".public"))

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

@blueprint.route("/all")
def all():
    "Display list of datasets."
    if not flask.g.am_admin:
        utils.flash_error("Not logged in as admin.")
        return flask.redirect(flask.url_for("home"))
    datasets = get_datasets_all(full=True)
    return flask.render_template("datasets/all.html", datasets=datasets)

def get_datasets_owner(username, full=False):
    """Get the datasets owned by the given user.
    If full is True, as docs.
    If full is False, as list of tuples (iuid, title, modified).
    """
    view = flask.g.db.view("datasets", "owner_modified",
                           startkey=(username, "ZZZZZZ"),
                           endkey=(username, ""),
                           include_docs=full,
                           reduce=False,
                           descending=True)
    if full:
        result = []
        for row in view:
            dataset = row.doc
            dataset["count_graphics"] = count_graphics(dataset["_id"])
            flask.g.cache[dataset["_id"]] = dataset
            result.append(dataset)
        return result
    else:
        return [(row.id, row.value, row.key[1]) for row in view]

def count_datasets_owner(username):
    "Return the number of datasets owned by the given user."
    view = flask.g.db.view("datasets", "owner_modified",
                           startkey=(username, ""),
                           endkey=(username, "ZZZZZZ"),
                           reduce=True)
    rows = list(view)
    if rows:
        return rows[0].value
    else:
        return 0

def get_datasets_public(full=False, limit=None):
    """Get the public datasets.
    If full is True, as docs.
    If full is False, as list of tuples (iuid, title, modified).
    """
    view = flask.g.db.view("datasets", "public_modified",
                           startkey="ZZZZZZ",
                           endkey="",
                           limit=limit,
                           include_docs=full,
                           reduce=False,
                           descending=True)
    if full:
        result = []
        for row in view:
            dataset = row.doc
            dataset["count_graphics"] = count_graphics(dataset["_id"])
            flask.g.cache[dataset["_id"]] = dataset
            result.append(dataset)
        return result
    else:
        return [(row.id, row.value, row.key) for row in view]

def count_datasets_public():
    "Return the number of public datasets."
    view = flask.g.db.view("datasets", "public_modified", reduce=True)
    rows = list(view)
    if rows:
        return rows[0].value
    else:
        return 0

def get_datasets_all(full=False):
    """Get all datasets.
    If full is True, as docs.
    If full is False, as list of tuples (iuid, title, owner, modified).
    """
    view = flask.g.db.view("datasets", "owner_modified",
                           startkey=("ZZZZZZ", "ZZZZZZ"),
                           endkey=("", ""),
                           include_docs=full,
                           reduce=False,
                           descending=True)
    if full:
        result = []
        for row in view:
            dataset = row.doc
            dataset["count_graphics"] = count_graphics(dataset["_id"])
            flask.g.cache[dataset["_id"]] = dataset
            result.append(dataset)
        return result
    else:
        return [(row.id, row.value, row.key[0], row.key[1]) for row in view]

def count_datasets_all():
    "Return the total number of datasets."
    view = flask.g.db.view("datasets", "owner_modified", reduce=True)
    rows = list(view)
    if rows:
        return rows[0].value
    else:
        return 0

def count_graphics(dataset_iuid):
    "Return the number of graphics for the dataset given by its iuid."
    view = flask.g.db.view("graphics", "dataset",
                           key=dataset_iuid,
                           reduce=True)
    rows = list(view)
    if rows:
        return rows[0].value
    else:
        return 0
