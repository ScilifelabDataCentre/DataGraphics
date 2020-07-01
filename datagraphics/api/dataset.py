"API Dataset resource."

import io
import http.client

import flask
from flask_cors import CORS

from datagraphics.dataset import (DatasetSaver,
                                  get_dataset,
                                  get_graphics,
                                  allow_view,
                                  allow_edit,
                                  possible_delete,
                                  allow_delete)
from datagraphics import constants
from datagraphics import utils
from datagraphics.api import schema_definitions

blueprint = flask.Blueprint("api_dataset", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("/", methods=["POST"])
def create():
    "Create an empty dataset."
    if not flask.g.current_user:
        flask.abort(http.client.FORBIDDEN)
    data = flask.request.get_json()
    try:
        with DatasetSaver() as saver:
            saver.set_title(data.get("title"))
            saver.set_description(data.get("description"))
            saver.set_public(data.get("public"))
    except ValueError as error:
        return str(error), http.client.BAD_REQUEST
    dataset = saver.doc
    dataset["$id"] = flask.url_for("api_dataset.serve",
                                   iuid=dataset["_id"],
                                   _external=True)
    set_links(dataset)
    return utils.jsonify(dataset)

@blueprint.route("/<iuid:iuid>", methods=["GET", "POST", "DELETE"])
def serve(iuid):
    """Return dataset's information (metadata), update it, or delete it.
    The content of the dataset cannot be update via this resource.
    """
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)

    if utils.http_GET():
        if not allow_view(dataset):
            flask.abort(http.client.FORBIDDEN)
        set_links(dataset)
        return utils.jsonify(dataset,
                             schema=flask.url_for("api_schema.dataset",
                                                  _external=True))

    elif utils.http_POST(csrf=False):
        if not allow_edit(dataset):
            flask.abort(http.client.FORBIDDEN)
        try:
            data = flask.request.get_json()
            with DatasetSaver(dataset) as saver:
                try:
                    saver.set_title(data["title"])
                except KeyError:
                    pass
                try:
                    saver.set_description(data["description"])
                except KeyError:
                    pass
                try:
                    saver.set_public(data["public"])
                except KeyError:
                    pass
                try:
                    saver.set_vega_lite_types(data["meta"])
                except KeyError:
                    pass
        except ValueError as error:
            return str(error), http.client.BAD_REQUEST
        return flask.redirect(flask.url_for(".serve", iuid=iuid))

    elif utils.http_DELETE():
        if not possible_delete(dataset):
            flask.abort(http.client.FORBIDDEN)
        if not allow_delete(dataset):
            flask.abort(http.client.FORBIDDEN)
        flask.g.db.delete(dataset)
        for log in utils.get_logs(dataset["_id"], cleanup=False):
            flask.g.db.delete(log)
        return "", http.client.NO_CONTENT

@blueprint.route("/<iuid:iuid>.<ext>", methods=["GET", "PUT"])
def content(iuid, ext):
    "Fetch or update the content of the dataset as JSON or CSV file."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)

    if utils.http_GET():
        if not allow_view(dataset):
            flask.abort(http.client.FORBIDDEN)
        if not dataset.get("_attachments", None):
            return "", http.client.NO_CONTENT
        if ext == "json":
            outfile = flask.g.db.get_attachment(dataset, "data.json")
            response = flask.make_response(outfile.read())
            response.headers.set("Content-Type", constants.JSON_MIMETYPE)
        elif ext == "csv":
            outfile = flask.g.db.get_attachment(dataset, "data.csv")
            response = flask.make_response(outfile.read())
            response.headers.set("Content-Type", constants.CSV_MIMETYPE)
        else:
            flask.abort(http.client.NOT_FOUND)
        return response

    elif utils.http_PUT():
        if not allow_edit(dataset):
            flask.abort(http.client.FORBIDDEN)
        if ext == "json":
            content_type = constants.JSON_MIMETYPE
        elif ext == "csv":
            content_type = constants.CSV_MIMETYPE
        else:
            flask.abort(http.client.NOT_FOUND)
        try:
            with DatasetSaver(dataset) as saver:
                saver.set_data(infile=io.BytesIO(flask.request.data),
                               content_type=content_type)
        except ValueError as error:
            return str(error), http.client.BAD_REQUEST
        return "", http.client.NO_CONTENT

@blueprint.route("/<iuid:iuid>/logs")
def logs(iuid):
    "Return all log entries for the given dataset."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)
    if not allow_view(dataset):
        flask.abort(http.client.FORBIDDEN)
    entity = {"type": "dataset",
              "iuid": iuid,
              "href": flask.url_for("api_dataset.serve",
                                    iuid=iuid,
                                    _external=True)}
    return utils.jsonify({"entity": entity,
                          "logs": utils.get_logs(dataset["_id"])},
                         schema=flask.url_for("api_schema.logs",_external=True))

def set_links(dataset):
    "Set the links in the dataset."
    # Convert 'owner' to an object with a link to the user account.
    dataset["owner"] = {"username": dataset["owner"],
                        "href": flask.url_for("api_user.display",
                                              username=dataset["owner"],
                                              _external=True)}
    # Convert the '_attachments' item to links to contents.
    atts = dataset.pop("_attachments", None)
    if atts:
        dataset["content"] = {
            "csv": {"href": flask.url_for("api_dataset.content",
                                          iuid=dataset["_id"],
                                          ext="csv",
                                          _external=True),
                    "size": atts["data.csv"]["length"]},
            "json": {"href": flask.url_for("api_dataset.content",
                                           iuid=dataset["_id"],
                                           ext="json",
                                           _external=True),
                     "size": atts["data.json"]["length"]}
        }
    # Add the links to the graphics for the dataset.
    dataset["graphics"] = [{"title": g["title"],
                            "modified": g["modified"],
                            "href": flask.url_for("api_graphic.serve",
                                                  iuid=g["_id"],
                                                  _external=True)}
                           for g in get_graphics(dataset)]
    # Add link to logs.
    dataset["logs"] = {"href": flask.url_for(".logs", 
                                             iuid=dataset["_id"],
                                             _external=True)}

schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Dataset resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "iuid": {"type": "string", "pattern": "^[0-9a-f]{32,32}$"},
        "created": {"type": "string", "format": "date-time"},
        "modified": {"type": "string", "format": "date-time"},
        "owner": schema_definitions.user,
        "title": {"type": "string"},
        "description": {"type": "string"},
        "public": {"type": "boolean"},
        "meta": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["string", "integer", "number", "boolean"]
                    },
                    "vega_lite_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": constants.VEGA_LITE_TYPES
                        }
                    },
                    "n_null": {"type": "integer", "minimum": 0},
                    "n_distinct": {"type": "integer", "minimum": 0},
                    "min": {"type": ["number", "string"]},
                    "max": {"type": ["number", "string"]},
                    "mean": {"type": "number"},
                    "median": {"type": "number"},
                    "stdev": {"type": "number", "minimum": 0.0}
                },
                "required": ["type", "n_null"],
                "additionalProperties": False
            }
        },
        "n_records": {"type": "integer", "minimum": 0},
        "content": {
            "type": "object",
            "properties": {
                "csv": {
                    "type": "object",
                    "properties": {
                        "href": {"type": "string", "format": "uri"},
                        "size": {"type": "integer", "minimum": 0}
                    }
                },
                "json": {
                    "type": "object",
                    "properties": {
                        "href": {"type": "string", "format": "uri"},
                        "size": {"type": "integer", "minimum": 0}
                    }
                }
            },
            "required": ["csv", "json"],
            "additionalProperties": False
        },
        "graphics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "modified":  {"type": "string", "format": "date-time"},
                    "href":  {"type": "string", "format": "uri"}
                },
                "required": ["title", "modified", "href"],
                "additionalProperties": False
            }
        },
        "logs": schema_definitions.logs_link
    },
    "required": ["$id", "timestamp", "iuid", "created", "modified",
                 "owner", "title", "description", "public",
                 "meta", "graphics", "logs"],
    "additionalProperties": False
}
