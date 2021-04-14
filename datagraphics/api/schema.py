"API Schema resource."

import flask
import flask_cors

from datagraphics import constants
from datagraphics import utils
from datagraphics.api import root as api_root
from datagraphics.api import about as api_about
from datagraphics.api import dataset as api_dataset
from datagraphics.api import datasets as api_datasets
from datagraphics.api import graphic as api_graphic
from datagraphics.api import graphics as api_graphics
from datagraphics.api import user as api_user
from datagraphics.api import users as api_users

blueprint = flask.Blueprint("api_schema", __name__)

@blueprint.route("")
@flask_cors.cross_origin(methods=["GET"])
def all():
    "Map of all JSON schemas for DataGraphics."
    return utils.jsonify(
        {"title": "Map of available JSON schemas.",
         "schemas": {
             "root": {"href": flask.url_for("api_schema.root", _external=True),
                      "title": api_root.schema["title"]},
             "about": {"href": flask.url_for("api_schema.about",
                                             _external=True),
                       "title": api_about.schema["title"]},
             "dataset": {"href": flask.url_for("api_schema.dataset",
                                               _external=True),
                         "title": api_dataset.schema["title"]},
             "datasets": {"href": flask.url_for("api_schema.datasets",
                                                _external=True),
                          "title": api_datasets.schema["title"]},
             "graphic": {"href": flask.url_for("api_schema.graphic",
                                               _external=True),
                         "title": api_graphic.schema["title"]},
             "graphics": {"href": flask.url_for("api_schema.graphics",
                                                _external=True),
                         "title": api_graphics.schema["title"]},
             "user": {"href": flask.url_for("api_schema.user",
                                            _external=True),
                      "title": api_user.schema["title"]},
             "users": {"href": flask.url_for("api_schema.users",
                                             _external=True),
                       "title": api_users.schema["title"]},
             "schemas": {"href": flask.url_for("api_schema.schemas",
                                               _external=True),
                         "title": schema["title"]},
             "logs": {"href": flask.url_for("api_schema.logs",
                                            _external=True),
                      "title": logs_schema["title"]},
         }
        },
        schema=flask.url_for("api_schema.schemas", _external=True)
    )

@blueprint.route("root")
@flask_cors.cross_origin(methods=["GET"])
def root():
    "JSON schema for API Root resource."
    return utils.jsonify(api_root.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("about")
@flask_cors.cross_origin(methods=["GET"])
def about():
    "JSON schema for API About resource."
    return utils.jsonify(api_about.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("dataset")
@flask_cors.cross_origin(methods=["GET"])
def dataset():
    "JSON schema for API Dataset resource."
    return utils.jsonify(api_dataset.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("datasets")
@flask_cors.cross_origin(methods=["GET"])
def datasets():
    "JSON schema for API Dataset resource."
    return utils.jsonify(api_datasets.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("graphic")
@flask_cors.cross_origin(methods=["GET"])
def graphic():
    "JSON schema for API Graphic resource."
    return utils.jsonify(api_graphic.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("graphics")
@flask_cors.cross_origin(methods=["GET"])
def graphics():
    "JSON schema for API Graphics resource."
    return utils.jsonify(api_graphics.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("user")
@flask_cors.cross_origin(methods=["GET"])
def user():
    "JSON schema for API User resource."
    return utils.jsonify(api_user.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("users")
@flask_cors.cross_origin(methods=["GET"])
def users():
    "JSON schema for API Users resource."
    return utils.jsonify(api_users.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("logs")
@flask_cors.cross_origin(methods=["GET"])
def logs():
    "JSON schema for API Logs resource."
    return utils.jsonify(logs_schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("schemas")
@flask_cors.cross_origin(methods=["GET"])
def schemas():
    "JSON schema for API Schema resource."
    return utils.jsonify(schema, schema=constants.JSON_SCHEMA_URL)


schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Logs resource.",
    "definitions": {
        "link": {
            "title": "A link to a resource.",
            "type": "object",
            "properties": {
                "href": {"type": "string", "format": "uri"},
                "title": {"type": "string"}
            },
            "required": ["href"],
            "additionalProperties": False
        }
    },
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "title": {"type": "string"},
        "schemas": {
            "properties": {
                "root": {"$ref": "#/definitions/link"},
                "about": {"$ref": "#/definitions/link"},
                "dataset": {"$ref": "#/definitions/link"},
                "datasets": {"$ref": "#/definitions/link"},
                "graphic": {"$ref": "#/definitions/link"},
                "graphics": {"$ref": "#/definitions/link"},
                "user": {"$ref": "#/definitions/link"},
                "users": {"$ref": "#/definitions/link"},
                "schemas": {"$ref": "#/definitions/link"},
                "logs": {"$ref": "#/definitions/link"}
            }
        }
    }
}

logs_schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Logs resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "entity": {
            "oneOf": [
                {"type": "object",
                 "properties": {
                     "type": {"type": "string", "enum": ["dataset", "graphic"]},
                     "iuid": {"type": "string", "pattern": "^[0-9a-f]{32,32}$"},
                     "href": {"type": "string", "format": "uri"}
                 },
                 "required": ["type", "iuid", "href"],
                 "additionalProperties": False
                },
                {"type": "object",
                 "properties": {
                     "type": {"const": "user"},
                     "username": {"type": "string"},
                     "href": {"type": "string", "format": "uri"}
                 },
                 "required": ["type", "username", "href"],
                 "additionalProperties": False
                }
            ]
        },
        "logs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "added": {
                        "type": "array",
                        "items": {"type": "string"}
                        },
                    "attachments_added": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "attachments_deleted": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "updated": {"type": "object"},
                    "removed": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "username": {"type": ["null", "string"]},
                    "remote_addr": {"type": ["null", "string"]},
                    "user_agent": {"type": ["null", "string"]}
                },
                "required": ["added", "updated", "removed", "timestamp",
                             "username", "remote_addr", "user_agent"],
                "additionalProperties": False
            }
        }
    },
    "required": ["$id", "timestamp", "entity", "logs"],
    "additionalProperties": False
}
