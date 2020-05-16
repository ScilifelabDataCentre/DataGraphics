"Dataset to display graphic of."

import csv
import json

import couchdb2
import flask

from datagraphics import constants
from datagraphics import utils

from datagraphics.saver import EntitySaver


def init(app):
    "Initialize; update CouchDB design document."
    db = utils.get_db(app=app)
    logger = utils.get_logger(app)
    if db.put_design("datasets", DESIGN_DOC):
        logger.info("Updated datasets design document.")

DESIGN_DOC = {
    "views": {
        "public_modified": {"map": "function(doc) {if (doc.doctype !== 'dataset' || !doc.public) return; emit(doc.modified, doc.title);}"},
        "owner_modified": {"reduce": "_count",
                           "map": "function(doc) {if (doc.doctype !== 'dataset') return; emit([doc.owner, doc.modified], doc.title);}"},
        "file_size": {"reduce": "_sum",
                      "map": "function(doc) {if (doc.doctype !== 'dataset' || !doc._attachments) return; for (var key in doc._attachments) if (doc._attachments.hasOwnProperty(key)) emit(doc.owner, doc._attachments[key].length);}"}
    },
}

blueprint = flask.Blueprint("dataset", __name__)

@blueprint.route("/", methods=["POST"])
@utils.login_required
def create():
    "Create a new dataset."
    try:
        with DatasetSaver() as saver:
            saver.set_title()
            saver.set_description()
            saver.set_public(False)
            saver.set_data()
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
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
        return flask.redirect(utils.referrer())

    return flask.render_template("dataset/display.html",
                                 dataset=dataset,
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
        return flask.redirect(utils.referrer())

    if utils.http_GET():
        if not allow_edit(dataset):
            utils.flash_error("Edit access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        raise NotImplementedError

    elif utils.http_POST():
        if not allow_edit(dataset):
            utils.flash_error("Edit access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        raise NotImplementedError

    elif utils.http_DELETE():
        if not possible_delete(dataset):
            utils.flash_error("Dataset cannot be deleted; use by graphics.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        if not allow_delete(dataset):
            utils.flash_error("Delete access to dataset not allowed.")
            return flask.redirect(flask.url_for(".display", iuid=iuid))
        flask.g.db.delete(dataset)
        utils.flash_message("The dataset was deleted.")
        return flask.redirect(flask.url_for("home"))

@blueprint.route("/<iuid:iuid>/copy", methods=["POST"])
@utils.login_required
def copy(iuid):
    "Copy the dataset, including its file, but not its binders."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(flask.url_for(".display", iuid=iuid))

    raise NotImplementedError

@blueprint.route("/<iuid:iuid>/public", methods=["POST"])
@utils.login_required
def public(iuid):
    "Set the dataset to public access."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
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
        return flask.redirect(utils.referrer())
    if allow_edit(dataset):
        if dataset["public"]:
            with DatasetSaver(dataset) as saver:
                saver.set_public(False)
    else:
        utils.flash_error("Edit access to dataset not allowed.")
    return flask.redirect(flask.url_for(".display", iuid=iuid))

@blueprint.route("/<iuid:iuid>/file/<filename>")
def download(iuid, filename):
    "Download the file attachment; the dataset itself."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.referrer())
    try:
        stub = dataset["_attachments"][filename]
    except KeyError:
        utils.flash_error("No such file attached to dataset.")
        return flask.redirect(flask.url(".display", iuid=iuid))
    outfile = flask.g.db.get_attachment(dataset, filename)
    response = flask.make_response(outfile.read())
    response.headers.set("Content-Type", stub["content_type"])
    response.headers.set("Content-Disposition", "attachment", 
                         filename=filename)
    return response

@blueprint.route("/<iuid:iuid>/logs")
def logs(iuid):
    "Display the log records of the given dataset."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        utils.flash_error(str(error))
        return flask.redirect(utils.referrer())
    if not allow_view(dataset):
        utils.flash_error("View access to dataset not allowed.")
        return flask.redirect(utils.referrer())
    return flask.render_template(
        "logs.html",
        title=f"Dataset {dataset['title'] or 'No title'}",
        cancel_url=flask.url_for(".display", iuid=iuid),
        logs=utils.get_logs(iuid))


class DatasetSaver(EntitySaver):
    "Dataset saver context with data content handling."

    DOCTYPE = constants.DOCTYPE_DATASET

    def set_public(self, public=None):
        if public is None:
            public = utils.to_bool(flask.request.form.get("public"))
        self.doc["public"] = public

    def set_data(self, infile=None):
        "Set the data for this dataset from the input file (CSV or JSON)."
        if infile is None:
            infile = flask.request.files.get("file")
        if not infile: return

        # JSON data; check homogeneity.
        if infile.content_type == constants.JSON_MIMETYPE:
            data = json.load(infile)
            if not data:
                raise ValueError("No data in JSON file.")
            if not isinstance(data, list):
                raise ValueError("JSON data file does not contain a list.")
            first = data[0]
            if not first:
                raise ValueError("Empty first item in JSON file.")
            if not isinstance(first, dict):
                raise ValueError(f"JSON data file item 0 '{first}'"
                                 " is not an object.")
            keys = list(item.keys())
            for pos, item in enumerate(data[1:]):
                if not isinstance(item, dict):
                    raise ValueError(f"JSON data file item {pos+1} '{item}'"
                                     " is not an object.")
                for key in keys:
                    try:
                        value = item[key]
                    except KeyError:
                        item[key] = None
                    else:
                        if type(first[key]) != type(value):
                            raise ValueError(f"JSON data file item {pos+1}"
                                             f" '{item}' is inhomogenous.")
        elif infile.content_type == constants.CSV_MIMETYPE:
            reader = csv.reader(infile)
            header = next(reader)
            
        else:
            raise ValueError(f"Cannot handle data file of type {infile.content_type}.")
        json_content = json.dumps(data)
        # XXX
        # csv_content
        # if flask.g.current_user.get("quota_file_size"):
        #     username = flask.g.current_user["username"]
        #     total = len(content) + datagraphics.user.get_sum_file_size(username)
        #     if total > flask.g.current_user["quota_file_size"]:
        #         raise ValueError(f"File {infile.filename} not added;"
        #                          " quota file size reached.")
        # self.add_attachment(infile.filename,
        #                     content,
        #                     infile.mimetype)

    def remove_data(self):
        "Remove the data, if any."
        for filename in list(self.doc.get("_attachments", {}).keys()):
            self.delete_attachment(filename)


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
    "Get the graphics entities the dataset is used for."
    result = []
    for row in flask.g.db.view("graphics", "dataset",
                               key=dataset["_id"],
                               include_docs=True):
        flask.g.cache[row.doc["_id"]] = row.doc
        result.append(row.doc)
    return result

def allow_view(dataset):
    "Is the current user allowed to view the dataset?"
    if dataset.get("public"): return True
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.current_user["username"] == dataset["owner"]

def allow_edit(dataset):
    "Is the current user allowed to edit the dataset?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.current_user["username"] == dataset["owner"]

def allow_delete(dataset):
    "Is the current user allowed to delete the dataset?"
    if not flask.g.current_user: return False
    if flask.g.am_admin: return True
    return flask.current_user["username"] == dataset["owner"]

def possible_delete(dataset):
    "Is it possible to delete the dataset?"
    return not get_graphics(dataset)
