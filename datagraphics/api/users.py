"API Users resource."

import http.client

import flask
from flask_cors import CORS

import datagraphics.user
from datagraphics import constants
from datagraphics import utils
from datagraphics.api import schema_definitions

blueprint = flask.Blueprint("api_users", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("/all")
def all():
    "Information about all users."
    if not flask.g.am_admin:
        flask.abort(http.client.FORBIDDEN)
    users = []
    for user in datagraphics.user.get_users():
        users.append({"href": flask.url_for("api_user.serve",
                                            username=user["username"],
                                            _external=True),
                      "username": user["username"]})
    return utils.jsonify({"users": users},
                         schema=flask.url_for("api_schema.users",
                                              _external=True))

schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Users resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "users": {
            "type": "array",
            "items": schema_definitions.link
        }
    },
    "required": ["$id", "timestamp", "users"],
    "additionalProperties": False
}
