"API User resource."

import http.client

import flask
from flask_cors import CORS

import datagraphics.user
from datagraphics import constants
from datagraphics import utils
from datagraphics.api import schema_definitions

blueprint = flask.Blueprint("api_user", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("/<name:username>")
def serve(username):
    "Information about the given user."
    user = datagraphics.user.get_user(username=username)
    if not user:
        flask.abort(http.client.NOT_FOUND)
    # XXX Use 'allow' function
    if not datagraphics.user.am_admin_or_self(user):
        flask.abort(http.client.FORBIDDEN)
    user.pop("password", None)
    user.pop("apikey", None)
    set_links(user)
    return utils.jsonify(user,
                         schema=flask.url_for("api_schema.user",
                                              _external=True))

@blueprint.route("/<name:username>/logs")
def logs(username):
    "Return all log entries for the given user."
    user = datagraphics.user.get_user(username=username)
    if not user:
        flask.abort(http.client.NOT_FOUND)
    # XXX Use 'allow' function
    if not datagraphics.user.am_admin_or_self(user):
        flask.abort(http.client.FORBIDDEN)
    entity = {"type": "user",
              "username": user["username"],
              "href": flask.url_for(".serve",
                                    username=user["username"],
                                    _external=True)}
    return utils.jsonify({"entity": entity,
                          "logs": utils.get_logs(user["_id"])},
                         schema=flask.url_for("api_schema.logs",_external=True))

def set_links(user):
    "Set the links in the user object."
    user["logs"] = {"href": flask.url_for(".logs", 
                                          username=user["username"],
                                          _external=True)}

schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API User resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "iuid": {"type": "string", "pattern": "^[0-9a-f]{32,32}$"},
        "created": {"type": "string", "format": "date-time"},
        "modified": {"type": "string", "format": "date-time"},
        "status": {
            "type": "string",
            "enum": ["pending", "enabled", "disabled"]
        },
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "role": {"type": "string", "enum": ["admin", "user"]},
        "logs": schema_definitions.logs_link
    }
}
