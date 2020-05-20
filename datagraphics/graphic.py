"Graphic to display dataset."

import json

import couchdb2
import flask

import datagraphics.dataset
import datagraphics.user
from datagraphics import constants
from datagraphics import utils
from datagraphics.saver import EntitySaver


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
        "dataset": {"map": "function(doc) {if (doc.doctype !== 'graphic') return; emit(doc.dataset, doc.title);}"},
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
            saver.set_description()
            saver.set_dataset(datagraphics.dataset.get_dataset(
                flask.request.form.get("dataset")))
            saver.set_specification()
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
    try:
        dataset = datagraphics.dataset.get_dataset(graphic["dataset"])
    except ValueError as error: # Should not happen.
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for("home"))
    if not allow_view(dataset):
        utils.flash_error("View access to dataset of graphic not allowed.")
        return flask.redirect(utils.referrer())
    am_admin_or_self = datagraphics.user.am_admin_or_self(username=graphic["owner"])
    return flask.render_template("graphic/display.html",
                                 graphic=graphic,
                                 dataset=dataset,
                                 allow_edit=allow_edit(graphic),
                                 am_admin_or_self=am_admin_or_self)

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
        return flask.render_template("graphic/edit.html", graphic=graphic)

    elif utils.http_POST():
        if not allow_edit(graphic):
            utils.flash_error("Edit access to graphic not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        try:
            with GraphicSaver(graphic) as saver:
                saver.set_title()
                saver.set_description()
                saver.set_specification()
        except ValueError as error:
            utils.flash_error(str(error))
            return flask.redirect(utils.referrer())
        return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

    elif utils.http_DELETE():
        if not allow_delete(graphic):
            utils.flash_error("Delete access to graphic not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        flask.g.db.delete(graphic)
        for log in utils.get_logs(graphic["_id"], cleanup=False):
            flask.g.db.delete(log)
        utils.flash_message("The graphic was deleted.")
        return flask.redirect(flask.url_for("home"))

@blueprint.route("/<iuid:iuid>/copy", methods=["POST"])
@utils.login_required
def copy(iuid):
    "Copy the graphic."
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

@blueprint.route("/<iuid:iuid>.<ext>")
def serve(iuid, ext):
    "Return the JSON or JavaScript specification of the Vega-Lite graphic."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if not allow_view(graphic):
        utils.flash_error("View access to graphic not allowed.")
        return flask.redirect(utils.referrer())
    filename = "vega_lite_specification.json"
    try:
        stub = graphic["_attachments"][filename]
    except KeyError:
        utils.flash_error("No Vega-Lite JSON for the graphic.")
        return flask.redirect(flask.url(".display", iuid=iuid))
    outfile = flask.g.db.get_attachment(graphic, filename)
    if ext == "json":
        response = flask.make_response(outfile.read())
        response.headers.set("Content-Type", constants.JSON_MIMETYPE)
    elif ext == "js":
        spec = outfile.read()
        divid = flask.request.args.get("divid") or "graphic"
        response = flask.make_response(f"vegaEmbed('#{divid}', {spec});")
        response.headers.set("Content-Type", constants.JS_MIMETYPE)
    if utils.to_bool(flask.request.args.get("download")):
        response.headers.set("Content-Disposition", "attachment", 
                             filename=f"{graphic['title']}.{ext}")
    return response

@blueprint.route("/<iuid:iuid>/logs")
def logs(iuid):
    "Display the log records of the given graphic."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if not allow_view(graphic):
        utils.flash_error("View access to graphic not allowed.")
        return flask.redirect(utils.referrer())
    return flask.render_template(
        "logs.html",
        title=f"Graphic {graphic['title']}",
        cancel_url=flask.url_for(".display", iuid=iuid),
        logs=utils.get_logs(iuid))


class GraphicSaver(EntitySaver):
    "Graphic saver context with file attachment handling."

    DOCTYPE = constants.DOCTYPE_GRAPHIC

    def set_dataset(self, dataset):
        if not datagraphics.dataset.allow_view(dataset):
            raise ValueError("View access to dataset not allowed.")
        self.doc["dataset"] = dataset["_id"]

    def set_specification(self, specification=None):
        "Set the Vega-Lite JSON specification."
        if specification is None:
            specification = flask.request.form.get("specification") or ""
        specification = json.loads(specification)
        # XXX Check against JSON Schema
        self.doc["specification"] = specification


# Utility functions

def get_graphic(iuid):
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
