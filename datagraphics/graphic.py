"Graphic to display dataset."

import json

import couchdb2
import flask
import jsonschema

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
        "public_modified": {"reduce": "_count",
                            "map": "function(doc) {if (doc.doctype !== 'graphic' || !doc.public) return; emit(doc.modified, doc.title);}"},
        "owner_modified": {"reduce": "_count",
                           "map": "function(doc) {if (doc.doctype !== 'graphic') return; emit([doc.owner, doc.modified], doc.title);}"},
        "dataset": {"map": "function(doc) {if (doc.doctype !== 'graphic') return; emit(doc.dataset, doc.title);}"}
    }
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
            saver.set_public(False)
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
    return flask.render_template("graphic/display.html",
                                 graphic=graphic,
                                 slug=utils.slugify(graphic['title']),
                                 dataset=get_dataset(graphic),
                                 allow_edit=allow_edit(graphic),
                                 allow_delete=allow_delete(graphic))

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
                if flask.g.am_admin:
                    saver.change_owner()
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
    try:
        with GraphicSaver() as saver:
            saver.set_title(f"Copy of {graphic['title']}")
            saver.set_description(graphic["description"])
            saver.set_public(False)
            saver.set_dataset(datagraphics.dataset.get_dataset(graphic["dataset"]))
            saver.set_specification(graphic["specification"])
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

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
def download(iuid, ext):
    "Download the JSON or JavaScript specification of the Vega-Lite graphic."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if not allow_view(graphic):
        utils.flash_error("View access to graphic not allowed.")
        return flask.redirect(utils.referrer())
    dataset = get_dataset(graphic)
    if not dataset:
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.referrer())
    spec = graphic["specification"]
    if utils.to_bool(flask.request.args.get("inline")):
        outfile = flask.g.db.get_attachment(dataset, "data.json")
        spec["data"] = {"values": json.load(outfile)}
    if ext == "json":
        response = flask.jsonify(spec)
        response.headers.set("Content-Type", constants.JSON_MIMETYPE)
    elif ext == "js":
        spec = json.dumps(spec)
        id = flask.request.args.get("id") or "graphic"
        response = flask.make_response(f"vegaEmbed('#{id}', {spec});")
        response.headers.set("Content-Type", constants.JS_MIMETYPE)
    else:
        utils.flash_error("Invalid file type requested.")
        return flask.redirect(utils.referrer())
    slug = utils.slugify(graphic['title'])
    response.headers.set("Content-Disposition", "attachment", 
                         filename=f"{slug}.{ext}")
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
        if not dataset["meta"] or not dataset["n_records"]:
            raise ValueError("Cannot create graphics for empty dataset.")
        self.doc["dataset"] = dataset["_id"]

    def set_specification(self, specification=None):
        "Set the Vega-Lite JSON specification."
        if specification is None:
            specification = flask.request.form.get("specification") or ""
            # If it is not even valid JSON, then don't save it, just complain.
            specification = json.loads(specification)
        # Ensure that the fixed items stay put.
        # A bit complicated; to keep fixed items at the top, and
        # the rest of the items in the order specified in the input.
        spec = {"$schema": flask.current_app.config['VEGA_LITE_SCHEMA_URL']}
        spec["title"] = self.doc["title"]
        spec["data"] = {"url": flask.url_for("api_dataset.content",
                                             iuid=self.doc["dataset"],
                                             ext="csv",
                                             _external=True),
                        "format": {"type": "csv"}
        }
        specification.pop("$schema", None)
        specification.pop("title", None)
        specification.pop("data", None)
        spec.update(specification)
        try:
            utils.validate_vega_lite(spec)
        except jsonschema.ValidationError as error:
            self.doc["error"] = str(error)
        else:
            self.doc["error"] = None
        # Save it, even if incorrect Vega-Lite.
        self.doc["specification"] = spec

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

def get_dataset(graphic):
    "Get the dataset for the graphic, if allowed. Else None."
    try:
        dataset = datagraphics.dataset.get_dataset(graphic["dataset"])
    except ValueError as error:
        return None
    if not allow_view(dataset):
        return None
    return dataset
