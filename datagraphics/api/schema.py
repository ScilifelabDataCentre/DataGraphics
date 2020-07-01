"API Schema resource."

import flask

from datagraphics import constants
from datagraphics import utils
from datagraphics.api import root as api_root
from datagraphics.api import about as api_about
from datagraphics.api import dataset as api_dataset
from datagraphics.api import datasets as api_datasets
from datagraphics.api import graphic as api_graphic
from datagraphics.api import user as api_user

blueprint = flask.Blueprint("api_schema", __name__)

@blueprint.route("")
def schema():
    "Map of available JSON schemas."
    return utils.jsonify(
        {"title": schema.__doc__,
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
             "user": {"href": flask.url_for("api_schema.user",
                                            _external=True),
                      "title": api_user.schema["title"]},
             "logs": {"href": flask.url_for("api_schema.logs",
                                            _external=True),
                      "title": logs_schema["title"]},
         }
        })

@blueprint.route("root")
def root():
    "JSON schema for API Root resource."
    return utils.jsonify(api_root.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("about")
def about():
    "JSON schema for API About resource."
    return utils.jsonify(api_about.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("dataset")
def dataset():
    "JSON schema for API Dataset resource."
    return utils.jsonify(api_dataset.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("datasets")
def datasets():
    "JSON schema for API Dataset resource."
    return utils.jsonify(api_datasets.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("graphic")
def graphic():
    "JSON schema for API Graphic resource."
    return utils.jsonify(api_graphic.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("user")
def user():
    "JSON schema for API User resource."
    return utils.jsonify(api_user.schema, schema=constants.JSON_SCHEMA_URL)

@blueprint.route("logs")
def logs():
    "JSON schema for API Logs resource."
    return utils.jsonify(logs_schema, schema=constants.JSON_SCHEMA_URL)

logs_schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Logs resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "entity": {
            "type": "object"
        },
        "logs": {
            "type": "array",
            "items": {
                "type": "object"
            }
        }
    },
    "required": ["$id", "timestamp", "entity", "logs"],
    "additionalProperties": False
}
