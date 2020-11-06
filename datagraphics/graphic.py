"Graphic to display dataset."

from copy import deepcopy
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
        "editor_modified": {"reduce": "_count",
                            "map": "function(doc) {if (doc.doctype !== 'graphic') return; if (!doc.editors) return; for (var i=0; i<doc.editors.length; i++) { emit([doc.editors[i], doc.modified], doc.title);}}"},
        "dataset": {"reduce": "_count",
                    "map": "function(doc) {if (doc.doctype !== 'graphic') return; emit(doc.dataset, doc.title);}"}
    }
}

blueprint = flask.Blueprint("graphic", __name__)

@blueprint.route("/", methods=["GET", "POST"])
@utils.login_required
def create():
    "Create a new graphic for dataset given as form argument."
    try:
        iuid = flask.request.values.get("dataset")
        if not iuid:
            raise ValueError("No dataset IUID provided.")
        dataset = datagraphics.dataset.get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for("home"))
    if not datagraphics.dataset.allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.url_referrer())

    if utils.http_GET():
        graphic = {"$schema": constants.VEGA_LITE_SCHEMA_URL,
                   "data": {"url": flask.url_for("api_dataset.content",
                                                 iuid=dataset["_id"],
                                                 ext="csv",
                                                 _external=True)}}
        return flask.render_template("graphic/create.html",
                                     dataset=dataset,
                                     graphic=graphic)

    elif utils.http_POST():
        try:
            with GraphicSaver() as saver:
                saver.set_dataset(dataset)
                saver.set_title()
                saver.set_description()
                saver.set_public(False)
                saver.set_specification()
        except ValueError as error:
            utils.flash_error(str(error))
            return flask.redirect(utils.url_referrer())
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
        return flask.redirect(utils.url_referrer())
    dataset = get_dataset(graphic)
    if dataset:
        other_graphics = [gr 
                          for gr in datagraphics.dataset.get_graphics(dataset)
                          if gr["_id"] != graphic["_id"]]
    else:
        other_graphics = []
    if flask.g.current_user and \
       flask.g.current_user["username"] == graphic["owner"] and \
       dataset["owner"] != graphic["owner"]:
        utils.flash_warning("The dataset is not owned by you."
                            " This graphic may become invalid if the owner of"
                            " the dataset deletes it or makes it inaccessible.")
    return flask.render_template("graphic/display.html",
                                 graphic=graphic,
                                 slug=utils.slugify(graphic['title']),
                                 dataset=dataset,
                                 other_graphics=other_graphics,
                                 am_owner=am_owner(graphic),
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
        return flask.redirect(utils.url_referrer())

    if utils.http_GET():
        if not allow_edit(graphic):
            utils.flash_error("Edit access to graphic not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        return flask.render_template("graphic/edit.html",
                                     am_owner=am_owner(graphic),
                                     graphic=graphic)

    elif utils.http_POST():
        if not allow_edit(graphic):
            utils.flash_error("Edit access to graphic not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        try:
            with GraphicSaver(graphic) as saver:
                saver.set_title()
                if flask.g.am_admin:
                    saver.change_owner()
                if am_owner(graphic):
                    saver.set_editors()
                saver.set_description()
                saver.set_specification()
        except ValueError as error:
            utils.flash_error(str(error))
            return flask.redirect(utils.url_referrer())
        return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

    elif utils.http_DELETE():
        if not allow_delete(graphic):
            utils.flash_error("Delete access to graphic not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        flask.g.db.delete(graphic)
        for log in utils.get_logs(graphic["_id"], cleanup=False):
            flask.g.db.delete(log)
        utils.flash_message("The graphic was deleted.")
        return flask.redirect(
            flask.url_for("dataset.display", iuid=graphic["dataset"]))

@blueprint.route("/<iuid:iuid>/copy", methods=["POST"])
@utils.login_required
def copy(iuid):
    "Copy the graphic."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(graphic):
        utils.flash_error("View access to graphic not allowed.")
        return flask.redirect(flask.url_for(".display", iuid=iuid))
    try:
        with GraphicSaver() as saver:
            saver.copy(graphic)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

@blueprint.route("/<iuid:iuid>/public", methods=["POST"])
@utils.login_required
def public(iuid):
    "Set the graphic to public access."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if am_owner(graphic):
        if not graphic["public"]:
            with GraphicSaver(graphic) as saver:
                saver.set_public(True)
    else:
        utils.flash_error("Only owner may make graphic public.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))

@blueprint.route("/<iuid:iuid>/private", methods=["POST"])
@utils.login_required
def private(iuid):
    "Set the graphic to private access."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if am_owner(graphic):
        if graphic["public"]:
            with GraphicSaver(graphic) as saver:
                saver.set_public(False)
    else:
        utils.flash_error("Only owner may make graphic private.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))

@blueprint.route("/<iuid:iuid>.<ext>")
def download(iuid, ext):
    "Download the JSON or JavaScript specification of the Vega-Lite graphic."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(graphic):
        utils.flash_error("View access to graphic not allowed.")
        return flask.redirect(utils.url_referrer())
    dataset = get_dataset(graphic)
    if not dataset:
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.url_referrer())

    spec = graphic["specification"]
    slug = utils.slugify(graphic['title'])
    id = flask.request.args.get("id") or "graphic"

    if utils.to_bool(flask.request.args.get("inline")):
        outfile = flask.g.db.get_attachment(dataset, "data.json")
        spec["data"] = {"values": json.load(outfile)}
    if ext == "json":
        response = flask.jsonify(spec)
        response.headers.set("Content-Type", constants.JSON_MIMETYPE)
    elif ext == "js":
        spec = json.dumps(spec)
        response = flask.make_response(f'vegaEmbed("#{id}", {spec},'
                                       f' {{downloadFileName: "{slug}"}})'
                                       '.then(result=>console.log(result))'
                                       '.catch(console.warn);')
        response.headers.set("Content-Type", constants.JS_MIMETYPE)
    elif ext == "html":
        html = flask.render_template("graphic/vega_lite.html",
                                     graphic=graphic,
                                     id=id,
                                     slug=slug)
        response = flask.make_response(html)
        response.headers.set("Content-Type", constants.HTML_MIMETYPE)
    else:
        utils.flash_error("Invalid file type requested.")
        return flask.redirect(utils.url_referrer())
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
        return flask.redirect(utils.url_referrer())
    if not allow_view(graphic):
        utils.flash_error("View access to graphic not allowed.")
        return flask.redirect(utils.url_referrer())
    return flask.render_template(
        "logs.html",
        title=f"Graphic {graphic['title']}",
        cancel_url=flask.url_for(".display", iuid=iuid),
        logs=utils.get_logs(iuid))


@blueprint.route("/stencil", methods=["GET", "POST"])
@utils.login_required
def stencil():
    "Select a stencil for the dataset given as form argument."
    try:
        iuid = flask.request.values.get("dataset")
        if not iuid:
            raise ValueError("No dataset IUID provided.")
        dataset = datagraphics.dataset.get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for("home"))
    if not datagraphics.dataset.allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.url_referrer())

    if utils.http_GET():
        stencils = []
        for name in flask.current_app.config["STENCILS"]:
            header = deepcopy(flask.current_app.config["STENCILS"][name]["header"])
            field_variables = [v for v in header["variables"]
                               if v.get("class") == "field"]
            header["combinations"] = combinations(field_variables,
                                                  dataset["meta"].items())
            if header["combinations"]:
                stencils.append(header)
        stencils.sort(key=lambda h: (h.get("weight", 0), h["title"]))
        return flask.render_template("graphic/stencil.html",
                                     dataset=dataset,
                                     stencils=stencils)
    elif utils.http_POST():
        try:
            spec = deepcopy(flask.current_app.config["STENCILS"]\
                            [flask.request.form["stencil"]])
            header = spec.pop("header")
            setfields = SetFields(flask.request.form["combination"])
            url = flask.url_for("api_dataset.content",
                                iuid=dataset["_id"],
                                ext="csv",
                                _external=True)
            for variable in header["variables"]:
                if variable.get("class") == "dataset":
                    setfields.lookup["/".join(variable["path"])] = url
            setfields.traverse(spec)
            with GraphicSaver() as saver:
                saver.set_dataset(dataset)
                saver.set_title(header["title"])
                saver.set_description(f"Created from stencil {header['name']}.")
                saver.set_public(False)
                saver.set_specification(spec)
        except (KeyError, ValueError) as error:
            utils.flash_error(str(error))
            return flask.redirect(utils.url_referrer())
        return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

def combinations(variables, field_items, current=None):
    """Return all combinations of variables in the stencil
    with fields in the dataset.
    """
    result = []
    if current is None:
        current = []
    pos = len(current)
    for name, field in field_items:
        if not field.get("vega_lite_types"): continue
        if variables[pos]["type"] not in field["vega_lite_types"]: continue
        if name in current: continue
        extended = current + [name]
        if pos + 1 == len(variables):
            value = []
            title = []
            for vname, vtitle, fname in zip([v["name"] for v in variables], 
                                            [v["title"] for v in variables],
                                            extended):
                value.append(f"{vname}={fname}")
                title.append(f"{vtitle} = {fname}")
            result.append((";".join(value), "; ".join(title)))
        else:
            result.extend(combinations(variables, field_items, extended))
    return result

class SetFields(utils.JsonTraverser):
    "Set the fields in the specification according to the combination."

    replace = True

    def __init__(self, combination):
        self.lookup = dict([p.split("=") for p in combination.split(";")])

    def handle(self, value):
        "Return field value or lookup value if any."
        try:
            return self.lookup["/".join([str(p) for p in self.path])]
        except KeyError:
            return value


class GraphicSaver(EntitySaver):
    "Graphic saver context with file attachment handling."

    DOCTYPE = constants.DOCTYPE_GRAPHIC

    def set_dataset(self, dataset):
        "Set the dataset that is the basis for this graphic."
        if not datagraphics.dataset.allow_view(dataset):
            raise ValueError("View access to dataset not allowed.")
        if not dataset["meta"] or not dataset["n_records"]:
            raise ValueError("Cannot create graphics for empty dataset.")
        self.doc["dataset"] = dataset["_id"]

    def set_specification(self, specification=None, origin_dataset_id=None):
        """Set the Vega-Lite JSON specification.
        Optionally change old data urls to the new value."""
        if specification is None:
            specification = flask.request.form.get("specification") or "{}"
            # If it is not even valid JSON, then don't save it, just complain.
            specification = json.loads(specification)

        # Ensure that item '$schema' is kept fixed.
        specification["$schema"] = constants.VEGA_LITE_SCHEMA_URL

        # Change the dataset URLs if origin is different from current.
        if origin_dataset_id is not None:
            old_data_urls = set([flask.url_for("api_dataset.content",
                                               iuid=origin_dataset_id,
                                               ext="csv",
                                               _external=True),
                                 flask.url_for("api_dataset.content",
                                               iuid=origin_dataset_id,
                                               ext="json",
                                               _external=True)])
            new_data_url = flask.url_for("api_dataset.content",
                                         iuid=self.doc["dataset"],
                                         ext="csv",
                                         _external=True)
            replacer = ReplaceDataUrl(old_data_urls, new_data_url)
            replacer.traverse(specification)

        # Sanity and validation check of the specification.
        dataset_urls = set([flask.url_for("api_dataset.content",
                                          iuid=self.doc["dataset"],
                                          ext="csv",
                                          _external=True),
                            flask.url_for("api_dataset.content",
                                          iuid=self.doc["dataset"],
                                          ext="json",
                                          _external=True)])
        data_urls = DataUrls()
        data_urls.traverse(specification)
        if dataset_urls.intersection(data_urls):
            try:
                utils.validate_vega_lite(specification)
            except jsonschema.ValidationError as error:
                self.doc["error"] = str(error)
            else:
                self.doc["error"] = None
        else:
            self.doc["error"] = "The graphic does not refer to its dataset."

        # Save it, even if incorrect Vega-Lite.
        self.doc["specification"] = specification

    def copy(self, graphic, dataset=None):
        """Copy everything from the given graphic into this.
        If the source dataset is given then update the data URLs."""
        self.set_title(f"Copy of {graphic['title']}")
        self.set_editors(graphic.get("editors") or [])
        self.set_description(graphic["description"])
        self.set_public(False)
        if dataset is None:
            self.set_specification(graphic["specification"])
        else:
            self.set_dataset(dataset)
            self.set_specification(graphic["specification"],
                                   origin_dataset_id=graphic["dataset"])


class DataUrls(utils.JsonTraverser):
    "Extract the data URLs from the specification."

    def __init__(self):
        self.result = []

    def handle(self, value):
        "Record all values for the fragment 'data.url'."
        if self.path[-2:] == ["data", "url"]:
            self.result.append(value)

    def __iter__(self):
        yield from self.result


class ReplaceDataUrl(utils.JsonTraverser):
    "Replace a given data URL with another."

    replace = True

    def __init__(self, old_data_urls, new_data_url):
        "Note: The old urls must be a set (or iterable, at least)!"
        self.old_data_urls = old_data_urls
        self.new_data_url = new_data_url

    def handle(self, value):
        "Record all values for the fragment 'data.url'."
        if self.path[-2:] == ["data", "url"]:
            if value in self.old_data_urls:
                return self.new_data_url
        return value


# Utility functions

def get_graphic(iuid):
    "Get the graphic given its IUID."
    if not iuid:
        raise ValueError("No IUID given for graphic.")
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

def am_owner(graphic):
    "Is the current user the owner of the graphic? Includes admin."
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.g.current_user["username"] == graphic["owner"]

def allow_view(graphic):
    "Is the current user allowed to view the graphic?"
    if graphic.get("public"): return True
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    if flask.g.current_user["username"] == graphic["owner"]: return True
    return flask.g.current_user["username"] in graphic.get("editors", [])

def allow_edit(graphic):
    "Is the current user allowed to edit the graphic?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    if flask.g.current_user["username"] == graphic["owner"]: return True
    return flask.g.current_user["username"] in graphic.get("editors", [])

def allow_delete(graphic):
    "Is the current user allowed to delete the graphic?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.g.current_user["username"] == graphic["owner"]

def get_dataset(graphic):
    "Get the dataset for the graphic, if allowed. Else None."
    try:
        dataset = datagraphics.dataset.get_dataset(graphic["dataset"])
    except ValueError as error:
        return None
    if not allow_view(dataset):
        return None
    return dataset
