"API Datasets resource."

import http.client

import flask
import flask_cors

from datagraphics.datasets import (
    get_datasets_public,
    get_datasets_all,
    get_datasets_owner,
    get_datasets_editor,
)
import datagraphics.user
from datagraphics import constants
from datagraphics import utils
from datagraphics.api import schema_definitions

blueprint = flask.Blueprint("api_datasets", __name__)


@blueprint.route("/public")
@flask_cors.cross_origin(methods=["GET"])
def public():
    "Get all public datasets."
    datasets = []
    for dataset in get_datasets_public(full=True):
        datasets.append(
            {
                "href": flask.url_for(
                    "api_dataset.serve", iuid=dataset["_id"], _external=True
                ),
                "title": dataset["title"],
                "owner": dataset["owner"],
                "modified": dataset["modified"],
            }
        )
    return utils.jsonify(
        {"datasets": datasets},
        schema=flask.url_for("api_schema.datasets", _external=True),
    )


@blueprint.route("/user/<username>")
def user(username):
    "Get the datasets owned by the given user."
    if not datagraphics.user.am_admin_or_self(username=username):
        flask.abort(http.client.FORBIDDEN)
    datasets = []
    for iuid, title, modified in get_datasets_owner(username):
        datasets.append(
            {
                "href": flask.url_for("api_dataset.serve", iuid=iuid, _external=True),
                "title": title,
                "modified": modified,
            }
        )
    return utils.jsonify(
        {"datasets": datasets},
        schema=flask.url_for("api_schema.datasets", _external=True),
    )


@blueprint.route("/user/<username>/editor")
def editor(username):
    "Get the datasets which the given user is editor of."
    if not datagraphics.user.am_admin_or_self(username=username):
        flask.abort(http.client.FORBIDDEN)
    datasets = []
    for iuid, title, modified in get_datasets_editor(username):
        datasets.append(
            {
                "href": flask.url_for("api_dataset.serve", iuid=iuid, _external=True),
                "title": title,
                "modified": modified,
            }
        )
    return utils.jsonify(
        {"datasets": datasets},
        schema=flask.url_for("api_schema.datasets", _external=True),
    )


@blueprint.route("/all")
def all():
    "Get all datasets."
    if not flask.g.am_admin:
        flask.abort(http.client.FORBIDDEN)
    datasets = []
    for iuid, title, owner, modified in get_datasets_all():
        datasets.append(
            {
                "href": flask.url_for("api_dataset.serve", iuid=iuid, _external=True),
                "title": title,
                "owner": owner,
                "modified": modified,
            }
        )
    return utils.jsonify(
        {"datasets": datasets},
        schema=flask.url_for("api_schema.datasets", _external=True),
    )


schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Datasets resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "datasets": {"type": "array", "items": schema_definitions.link},
    },
    "required": ["$id", "timestamp", "datasets"],
    "additionalProperties": False,
}
