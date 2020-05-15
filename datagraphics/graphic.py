"Graphic to display dataset."

import couchdb2
import flask

from datagraphics import constants
from datagraphics import utils

from datagraphics.saver import EntitySaver, add_entity_file


def init(app):
    "Initialize; update CouchDB design document."
    db = utils.get_db(app=app)
    logger = utils.get_logger(app)
    if db.put_design("graphics", DESIGN_DOC):
        logger.info("Updated graphics design document.")

DESIGN_DOC = {
    "views": {
        "public_modified": {"map": "function(doc) {if (doc.doctype !== 'graphic' || !doc.public) return; emit(doc.modified, doc.title);}"},
        "owner_modified": {"reduce": "_count",
                           "map": "function(doc) {if (doc.doctype !== 'graphic') return; emit([doc.owner, doc.modified], doc.title);}"},
        "file_size": {"reduce": "_sum",
                      "map": "function(doc) {if (doc.doctype !== 'graphic' || !doc._attachments) return; for (var key in doc._attachments) if (doc._attachments.hasOwnProperty(key)) emit(doc.owner, doc._attachments[key].length);}"}
    },
}

blueprint = flask.Blueprint("graphic", __name__)

@blueprint.route("/", methods=["POST"])
@utils.login_required
def create():
    "Create a new graphic."
    try:
        with GraphicSaver() as saver:
            saver.set_title()
            saver.set_public(False)
            saver.set_text()
            saver.set_file()
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

@blueprint.route("/<iuid:iuid>")
def display(iuid):
    "Display the graphic."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for("home"))
    if not allow_view(graphic):
        utils.flash_error("View access to graphic not allowed.")
        return flask.redirect(utils.referrer())

    raise NotImplementedError

@blueprint.route("/<iuid:iuid>/edit", methods=["GET", "POST", "DELETE"])
@utils.login_required
def edit(iuid):
    "Edit the graphic, or delete it."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())

    if utils.http_GET():
        if not allow_edit(graphic):
            utils.flash_error("Edit access to graphic not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        raise NotImplementedError

    elif utils.http_POST():
        if not allow_edit(graphic):
            utils.flash_error("Edit access to graphic not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        raise NotImplementedError

    elif utils.http_DELETE():
        if not possible_delete(graphic):
            utils.flash_error("Graphic cannot be deleted; use by graphics.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        if not allow_delete(graphic):
            utils.flash_error("Delete access to graphic not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        flask.g.db.delete(graphic)
        utils.flash_message("The graphic was deleted.")
        return flask.redirect(flask.url_for("home"))

@blueprint.route("/<iuid:iuid>/copy", methods=["POST"])
@utils.login_required
def copy(iuid):
    "Copy the graphic, including its file, but not its binders."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if not allow_view(graphic):
        utils.flash_error("View access to graphic not allowed.")
        return flask.redirect(flask.url_for(".display", iuid=iuid))

    raise NotImplementedError

@blueprint.route("/<iuid:iuid>/public", methods=["POST"])
@utils.login_required
def public(iuid):
    "Set the graphic to public access."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if allow_edit(graphic):
        if not graphic["public"]:
            with GraphicSaver(graphic) as saver:
                saver.set_public(True)
    else:
        utils.flash_error("Edit access to graphic not allowed.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))

@blueprint.route("/<iuid:iuid>/private", methods=["POST"])
@utils.login_required
def private(iuid):
    "Set the graphic to private access."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if allow_edit(graphic):
        if graphic["public"]:
            with GraphicSaver(graphic) as saver:
                saver.set_public(False)
    else:
        utils.flash_error("Edit access to graphic not allowed.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))


class GraphicSaver(EntitySaver):
    "Graphic saver context with file attachment handling."

    DOCTYPE = constants.DOCTYPE_GRAPHIC


# Utility functions

def get_graphic(iuid, get_file=False):
    "Get the graphic given its IUID."
    try:
        try:
            doc = flask.g.cache[iuid]
        except KeyError:
            doc = flask.g.db[iuid]
    except couchdb2.NotFoundError:
        raise ValueError("No such graphic.")
    if doc.get("doctype") != constants.DOCTYPE_GRAPHIC:
        raise ValueError(f"Database entry {iuid} is not a graphic.")
    if get_file:
        add_entity_file(doc)
    flask.g.cache[iuid] = doc
    return doc

def allow_view(graphic):
    "Is the current user allowed to view the graphic?"
    if graphic.get("public"): return True
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.current_user["username"] == graphic["owner"]

def allow_edit(graphic):
    "Is the current user allowed to edit the graphic?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.current_user["username"] == graphic["owner"]

def allow_delete(graphic):
    "Is the current user allowed to delete the graphic?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.current_user["username"] == graphic["owner"]

def possible_delete(graphic):
    "Is it possible to delete the graphic?"
    return True
