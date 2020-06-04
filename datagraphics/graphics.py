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
        graphics = get_graphics_owner(flask.g.current_user["username"],
                                      full=True)
    else:
        graphics = get_graphics_public(full=True)
    return flask.render_template("graphics/display.html",
                                 graphics=graphics,
                                 show_public=bool(flask.g.current_user))

@blueprint.route("/public")
def public():
    "Display list of public graphics."
    graphics = get_graphics_public(full=True)
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
    graphics = get_graphics_owner(username, full=True)
    return flask.render_template("graphics/user.html",
                                 user=user,
                                 graphics=graphics,
                                 show_public=True)

@blueprint.route("/all")
def all():
    "Display list of graphics."
    if not flask.g.am_admin:
        utils.flash_error("Not logged in as admin.")
        return flask.redirect(flask.url_for("home"))
    graphics = get_graphics_all(full=True)
    return flask.render_template("graphics/all.html", graphics=graphics)

def get_graphics_owner(username, full=False):
    """Get the graphics owned by the given user.
    If full is True, as docs.
    If full is False, as list of tuples (iuid, title, modified).
    """
    view = flask.g.db.view("graphics", "owner_modified",
                           startkey=(username, "ZZZZZZ"),
                           endkey=(username, ""),
                           include_docs=full,
                           reduce=False,
                           descending=True)
    if full:
        result = []
        for row in view:
            graphic = row.doc
            fetch_dataset(graphic)
            flask.g.cache[graphic["_id"]] = graphic
            result.append(graphic)
        return result
    else:
        return [(row.id, row.value, row.key[1]) for row in view]

def count_graphics_owner(username):
    "Return the number of graphics owned by the given user."
    view = flask.g.db.view("graphics", "owner_modified",
                           startkey=(username, ""),
                           endkey=(username, "ZZZZZZ"),
                           reduce=True)
    rows = list(view)
    if rows:
        return rows[0].value
    else:
        return 0

def get_graphics_public(full=False, limit=None):
    """Get the public graphics.
    If full is True, as docs.
    If full is False, as list of tuples (iuid, title, modified).
    """
    view = flask.g.db.view("graphics", "public_modified",
                           startkey="ZZZZZZ",
                           endkey="",
                           limit=limit,
                           include_docs=full,
                           reduce=False,
                           descending=True)
    if full:
        result = []
        for row in view:
            graphic = row.doc
            fetch_dataset(graphic)
            flask.g.cache[graphic["_id"]] = graphic
            result.append(graphic)
        return result
    else:
        return [(row.id, row.value, row.key) for row in view]

def count_graphics_public():
    "Return the number of public graphics."
    view = flask.g.db.view("graphics", "public_modified", reduce=True)
    rows = list(view)
    if rows:
        return rows[0].value
    else:
        return 0

def get_graphics_all(full=False):
    """Get all graphics.
    If full is True, as docs.
    If full is False, as list of tuples (iuid, title, owner, modified).
    """
    view = flask.g.db.view("graphics", "owner_modified",
                           startkey=("ZZZZZZ", "ZZZZZZ"),
                           endkey=("", ""),
                           include_docs=full,
                           reduce=False,
                           descending=True)
    if full:
        result = []
        for row in view:
            graphic = row.doc
            fetch_dataset(graphic)
            flask.g.cache[graphic["_id"]] = graphic
            result.append(graphic)
        return result
    else:
        return [(row.id, row.value, row.key[0], row.key[1]) for row in view]

def count_graphics_all():
    "Return the total number of graphics."
    view = flask.g.db.view("graphics", "owner_modified", reduce=True)
    rows = list(view)
    if rows:
        return rows[0].value
    else:
        return 0

def fetch_dataset(graphic):
    "Set the dataset in the graphic to the instance, if possible."
    dataset = datagraphics.graphic.get_dataset(graphic)
    if dataset is not None:
        if not datagraphics.dataset.allow_view(dataset): dataset = None
    graphic["dataset"] = dataset
