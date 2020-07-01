"API Datasets resource."

import http.client

import flask
from flask_cors import CORS

from datagraphics.datasets import (get_datasets_public,
                                   get_datasets_all,
                                   get_datasets_owner)
import datagraphics.user
from datagraphics import constants
from datagraphics import utils

blueprint = flask.Blueprint("api_datasets", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("/public")
def public():
    datasets = []
    for dataset in get_datasets_public(full=True):
        datasets.append({"title": dataset["title"],
                         "href": flask.url_for("api_dataset.serve",
                                               iuid=dataset["_id"],
                                               _external=True),
                         "owner": dataset["owner"],
                         "modified": dataset["modified"]})
    return utils.jsonify({"datasets": datasets})

@blueprint.route("/user/<username>")
def user(username):
    if not datagraphics.user.am_admin_or_self(username=username):
        flask.abort(http.client.FORBIDDEN)
    datasets = []
    for iuid, title, modified in get_datasets_owner(username):
        datasets.append({"title": title,
                         "href": flask.url_for("api_dataset.serve",
                                               iuid=iuid,
                                               _external=True),
                         "modified": modified})
    return utils.jsonify({"datasets": datasets})

@blueprint.route("/all")
def all():
    if not flask.g.am_admin:
        flask.abort(http.client.FORBIDDEN)
    datasets = []
    for iuid, title, owner, modified in get_datasets_all():
        datasets.append({"title": title,
                         "href": flask.url_for("api_dataset.serve",
                                               iuid=iuid,
                                               _external=True),
                         "owner": owner,
                         "modified": modified})
    return utils.jsonify({"datasets": datasets})

schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Datasets resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "datasets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "href": {"type": "string", "format": "uri"},
                    "modified": {"type": "string", "format": "date-time"}
                },
                "required": ["title", "href", "modified"],
                "additionalProperties": False
            }
        }
    },
    "required": ["$id", "timestamp", "datasets"],
    "additionalProperties": False
}
