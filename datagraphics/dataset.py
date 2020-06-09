"Dataset to display graphic of."

import csv
import io
import json
import http.client
import statistics

import couchdb2
import flask

import datagraphics.user
import datagraphics.graphic
from datagraphics import constants
from datagraphics import utils

from datagraphics.saver import EntitySaver

TYPE_NAME_MAP = {int: "integer",
                 float: "number",
                 bool: "boolean",
                 str: "string"}

def init(app):
    "Initialize; update CouchDB design document."
    db = utils.get_db(app=app)
    logger = utils.get_logger(app)
    if db.put_design("datasets", DESIGN_DOC):
        logger.info("Updated datasets design document.")

DESIGN_DOC = {
    "views": {
        "public_modified": {"reduce": "_count",
                            "map": "function(doc) {if (doc.doctype !== 'dataset' || !doc.public) return; emit(doc.modified, doc.title);}"},
        "owner_modified": {"reduce": "_count",
                           "map": "function(doc) {if (doc.doctype !== 'dataset') return; emit([doc.owner, doc.modified], doc.title);}"},
        "file_size": {"reduce": "_sum",
                      "map": "function(doc) {if (doc.doctype !== 'dataset' || !doc._attachments) return; for (var key in doc._attachments) if (doc._attachments.hasOwnProperty(key)) emit(doc.owner, doc._attachments[key].length);}"}
    },
}

blueprint = flask.Blueprint("dataset", __name__)

@blueprint.route("/", methods=["GET", "POST"])
@utils.login_required
def create():
    "Create a new dataset."
    if utils.http_GET():
        return flask.render_template("dataset/create.html")

    elif utils.http_POST():
        try:
            with DatasetSaver() as saver:
                saver.set_title()
                saver.set_description()
                saver.set_public(False)
                saver.set_data()
        except ValueError as error:
            utils.flash_error(str(error))
            return flask.redirect(utils.url_referrer())
        return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

@blueprint.route("/<iuid:iuid>")
def display(iuid):
    "Display the dataset."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(flask.url_for("home"))
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.url_referrer())
    storage = sum([s['length'] 
                   for s in dataset.get('_attachments', {}).values()])
    skeleton_graphic = datagraphics.graphic.get_skeleton_graphic()
    return flask.render_template("dataset/display.html",
                                 dataset=dataset,
                                 graphics=get_graphics(dataset),
                                 storage=storage,
                                 skeleton_graphic=skeleton_graphic,
                                 allow_edit=allow_edit(dataset),
                                 allow_delete=allow_delete(dataset),
                                 possible_delete=possible_delete(dataset))

@blueprint.route("/<iuid:iuid>/edit", methods=["GET", "POST", "DELETE"])
@utils.login_required
def edit(iuid):
    "Edit the dataset, or delete it."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())

    if utils.http_GET():
        if not allow_edit(dataset):
            utils.flash_error("Edit access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        return flask.render_template("dataset/edit.html", dataset=dataset)

    elif utils.http_POST():
        if not allow_edit(dataset):
            utils.flash_error("Edit access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        try:
            with DatasetSaver(dataset) as saver:
                saver.set_title()
                if flask.g.am_admin:
                    saver.change_owner()
                saver.set_description()
                saver.set_data()
        except ValueError as error:
            utils.flash_error(str(error))
        return flask.redirect(flask.url_for(".display", iuid=iuid))

    elif utils.http_DELETE():
        if not possible_delete(dataset):
            utils.flash_error("Dataset cannot be deleted; use by graphics.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        if not allow_delete(dataset):
            utils.flash_error("Delete access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        flask.g.db.delete(dataset)
        for log in utils.get_logs(dataset["_id"], cleanup=False):
            flask.g.db.delete(log)
        utils.flash_message("The dataset was deleted.")
        return flask.redirect(flask.url_for("datasets.display"))

@blueprint.route("/<iuid:iuid>/copy", methods=["POST"])
@utils.login_required
def copy(iuid):
    "Copy the dataset, including its data content."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(flask.url_for(".display", iuid=iuid))
    try:
        with DatasetSaver() as saver:
            saver.set_title(f"Copy of {dataset['title']}")
            saver.set_description(dataset["description"])
            saver.set_public(False)
            saver.set_data(flask.g.db.get_attachment(dataset, "data.json"),
                           content_type=constants.JSON_MIMETYPE)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    return flask.redirect(flask.url_for(".display", iuid=saver.doc["_id"]))

@blueprint.route("/<iuid:iuid>/public", methods=["POST"])
@utils.login_required
def public(iuid):
    "Set the dataset to public access."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if allow_edit(dataset):
        if not dataset["public"]:
            with DatasetSaver(dataset) as saver:
                saver.set_public(True)
    else:
        utils.flash_error("Edit access to dataset not allowed.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))

@blueprint.route("/<iuid:iuid>/private", methods=["POST"])
@utils.login_required
def private(iuid):
    "Set the dataset to private access."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if allow_edit(dataset):
        if dataset["public"]:
            with DatasetSaver(dataset) as saver:
                saver.set_public(False)
    else:
        utils.flash_error("Edit access to dataset not allowed.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))

@blueprint.route("/<iuid:iuid>.<ext>")
def download(iuid, ext):
    """Download the content of the dataset as JSON or CSV file.
    This is for use in the HTML pages, not for API calls.
    """
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset is not allowed.")
        return flask.redirect(utils.url_referrer())
    if not dataset.get("_attachments", None):
        utils.flash_error("Dataset does not contain any data.")
        return flask.redirect(utils.url_referrer())
    if ext == "json":
        outfile = flask.g.db.get_attachment(dataset, "data.json")
        response = flask.make_response(outfile.read())
        response.headers.set("Content-Type", constants.JSON_MIMETYPE)
    elif ext == "csv":
        outfile = flask.g.db.get_attachment(dataset, "data.csv")
        response = flask.make_response(outfile.read())
        response.headers.set("Content-Type", constants.CSV_MIMETYPE)
    else:
        utils.flash_error("Invalid file type requested.")
        return flask.redirect(utils.url_referrer())
    slug = utils.slugify(dataset['title'])
    response.headers.set("Content-Disposition", "attachment", 
                         filename=f"{slug}.{ext}")
    return response

@blueprint.route("/<iuid:iuid>/logs")
def logs(iuid):
    "Display the log records of the given dataset."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.url_referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.url_referrer())
    return flask.render_template(
        "logs.html",
        title=f"Dataset {dataset['title'] or 'No title'}",
        cancel_url=flask.url_for(".display", iuid=iuid),
        logs=utils.get_logs(iuid))


class DatasetSaver(EntitySaver):
    "Dataset saver context with data content handling."

    DOCTYPE = constants.DOCTYPE_DATASET

    def initialize(self):
        super().initialize()
        self.doc["meta"] = {}

    def set_data(self, infile=None, content_type=None):
        "Set the data for this dataset from the input file (CSV or JSON)."
        if infile is None:
            infile = flask.request.files.get("file")
        if not infile: return

        if content_type is None:
            content_type = infile.content_type
        if content_type == constants.JSON_MIMETYPE:
            data = self.get_json_data(infile)
        elif content_type == constants.CSV_MIMETYPE:
            data = self.get_csv_data(infile)
        else:
            raise ValueError("Cannot handle data file of type"
                             f" {infile.content_type}.")
        self.doc["n_records"] = len(data)
        self.update_meta(data)

        json_content = json.dumps(data)

        outfile = io.StringIO()
        writer = csv.DictWriter(outfile, fieldnames=list(data[0].keys()))
        writer.writeheader()
        for record in data:
            writer.writerow(record)
        outfile.seek(0)
        csv_content = outfile.read()

        if flask.g.current_user.get("quota_storage"):
            username = flask.g.current_user["username"]
            total = len(json_content) + len(csv_content) + \
                    datagraphics.user.get_storage(username)
            if total > flask.g.current_user["quota_storage"]:
                raise ValueError(f"File {infile.filename} not added;"
                                 " quota storage reached.")
        self.add_attachment("data.json",
                            json_content,
                            constants.JSON_MIMETYPE)
        self.add_attachment("data.csv",
                            csv_content,
                            constants.CSV_MIMETYPE)

    def get_json_data(self, infile):
        """Return the data from the given JSON infile.
        If there is a 'meta' entry for the dataset, check against types it.
        Otherwise set it. Update the 'meta' entries.
        """
        data = json.load(infile)
        if not data:
            raise ValueError("No data in JSON file.")
        if not isinstance(data, list):
            raise ValueError("JSON data does not contain a list.")
        first = data[0]
        if not first:
            raise ValueError("Empty first record in JSON data.")
        if not isinstance(first, dict):
            raise ValueError(f"JSON data record 0 '{first}' is not an object.")
        meta = self.doc["meta"]
        if not meta:
            # The 'meta' entry for the dataset has not been set.
            # Figure out the types from the items in the first data record.
            for key in first:
                meta[key] = {}
            for key, value in first.items():
                try:
                    meta[key]["type"] = TYPE_NAME_MAP[type(value)]
                except KeyError:
                    raise ValueError(f"JSON data item 0 '{first}'"
                                     " contains illegal type")
        # Check data homogeneity, and set 'null' in 'meta'.
        TYPE_OBJECT_MAP = dict((n, o) for o, n in TYPE_NAME_MAP.items())
        keys = list(meta.keys())
        for pos, record in enumerate(data):
            if not isinstance(record, dict):
                raise ValueError(f"JSON data record {pos} '{record}'"
                                 " is not an object.")
            for key in keys:
                try:
                    value = record[key]
                except KeyError:
                    record[key] = value = None
                if value is not None and \
                   type(value) != TYPE_OBJECT_MAP[meta[key]["type"]]:
                    raise ValueError(f"JSON data record {pos} '{record}'"
                                     " contains wrong type.")
        return data

    def get_csv_data(self, infile):
        """Retun the data frin the given CSV infile.
        If there is a 'meta' entry for the dataset, check against types it.
        Otherwise set it. Update the 'meta' entries.
        """
        reader = csv.DictReader(io.StringIO(infile.read().decode("utf-8")))
        data = list(reader)
        if not data:
            raise ValueError("No data in CSV file.")

        TYPE_OBJECT_MAP = dict((n, o) for o, n in TYPE_NAME_MAP.items())
        def bool2(s):
            if s == "True": return True
            if s == "true": return True
            if s == "False": return False
            if s == "false": return False
            if not s: return None
            raise ValueError(f"invalid bool '{s}'")
        TYPE_OBJECT_MAP["boolean"] = bool2

        meta = self.doc["meta"]
        if not meta:
            # The 'meta' entry for the dataset has not been set.
            # Figure out the types from the items in the first data record.
            first = data[0]
            for key in first:
                meta[key] = {}
            for key, value in first.items():
                try:
                    int(value)
                    meta[key]["type"] = "integer"
                except ValueError:
                    try:
                        float(value)
                        meta[key]["type"] = "number"
                    except ValueError:
                        try:
                            bool2(value)
                            meta[key]["type"] = "boolean"
                        except ValueError:
                            meta[key]["type"] = "string"
        # Convert values; checks homogeneity and set 'null' in 'meta'.
        keys = list(meta.keys())
        for pos, record in enumerate(data):
            for key, value in record.items():
                if value:
                    try:
                        record[key] = TYPE_OBJECT_MAP[meta[key]["type"]](value)
                    except ValueError:
                        raise ValueError(f"JSON data record {pos} '{record}'"
                                         " contains wrong type.")
                elif meta[key]["type"] != "string":
                    # An empty string is a string when type is 'string'.
                    # Otherwise None.
                    record[key] = None
        return data

    def update_meta(self, data):
        "Update the 'meta' entry given the data."
        for key, meta in self.doc["meta"].items():
            meta["n_null"] = len([r[key] for r in data if r[key] is None])
            if meta["type"] in ("string", "integer"):
                distinct = set(r[key] for r in data if r[key] is not None)
                meta["n_distinct"] = len(distinct)
                try:
                    meta["min"] = min(distinct)
                except ValueError:
                    meta["min"] = None
                try:
                    meta["max"] = max(distinct)
                except ValueError:
                    meta["max"] = None
            if meta["type"] in ("integer", "number"):
                values = [r[key] for r in data if r[key] is not None]
                try:
                    meta["min"] = min(values)
                except ValueError:
                    meta["min"] = None
                try:
                    meta["max"] = max(values)
                except ValueError:
                    meta["max"] = None
                try:
                    meta["mean"] = statistics.mean(values)
                except statistics.StatisticsError:
                    meta["mean"] = None
                try:
                    meta["median"] = statistics.median(values)
                except statistics.StatisticsError:
                    meta["median"] = None
                try:
                    meta["stdev"] = statistics.stdev(values)
                except statistics.StatisticsError:
                    meta["stdev"] = None
            if meta["type"] == "boolean":
                meta["n_true"] = len([r[key] for r in data if r[key] is True])
                meta["n_false"] = len([r[key] for r in data if r[key] is False])

    def remove_data(self):
        "Remove the data."
        for filename in list(self.doc.get("_attachments", {}).keys()):
            self.delete_attachment(filename)
        for meta in self.doc["meta"].valuess():
            for item in ("distinct", "min", "max", "mean", "media", "stdev"):
                meta.pop(item, None)


# Utility functions

def get_dataset(iuid):
    "Get the dataset given its IUID."
    try:
        try:
            doc = flask.g.cache[iuid]
        except KeyError:
            doc = flask.g.db[iuid]
    except couchdb2.NotFoundError:
        raise ValueError("No such dataset.")
    if doc.get("doctype") != constants.DOCTYPE_DATASET:
        raise ValueError(f"Database entry {iuid} is not a dataset.")
    flask.g.cache[iuid] = doc
    return doc

def get_graphics(dataset):
    """Get the graphics entities the dataset is used for.
    Exclude those not allowed to view.
    """
    from datagraphics.graphic import allow_view
    result = []
    for row in flask.g.db.view("graphics", "dataset",
                               key=dataset["_id"],
                               include_docs=True):
        if allow_view(row.doc):
            flask.g.cache[row.doc["_id"]] = row.doc
            result.append(row.doc)
    return sorted(result, key=lambda g: g["title"])

def allow_view(dataset):
    "Is the current user allowed to view the dataset?"
    if dataset.get("public"): return True
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.g.current_user["username"] == dataset["owner"]

def allow_edit(dataset):
    "Is the current user allowed to edit the dataset?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.g.current_user["username"] == dataset["owner"]

def allow_delete(dataset):
    "Is the current user allowed to delete the dataset?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.g.current_user["username"] == dataset["owner"]

def possible_delete(dataset):
    "Is it possible to delete the dataset?"
    return not get_graphics(dataset)
