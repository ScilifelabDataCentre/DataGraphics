"API Graphics resource."

import http.client

import flask
from flask_cors import CORS

from datagraphics.graphics import (get_graphics_public,
                                   get_graphics_all,
                                   get_graphics_owner)
import datagraphics.user
from datagraphics import constants
from datagraphics import utils

blueprint = flask.Blueprint("api_graphics", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("/public")
def public():
    graphics = []
    for graphic in get_graphics_public(full=True):
        graphics.append({"title": graphic["title"],
                         "href": flask.url_for("api_graphic.serve",
                                               iuid=graphic["_id"],
                                               _external=True),
                         "owner": graphic["owner"],
                         "modified": graphic["modified"]})
    return utils.jsonify({"graphics": graphics},
                         schema=flask.url_for("api_schema.graphics",
                                              _external=True))

@blueprint.route("/user/<username>")
def user(username):
    if not datagraphics.user.am_admin_or_self(username=username):
        flask.abort(http.client.FORBIDDEN)
    graphics = []
    for iuid, title, modified in get_graphics_owner(username):
        graphics.append({"title": title,
                         "href": flask.url_for("api_graphic.serve",
                                               iuid=iuid,
                                               _external=True),
                         "modified": modified})
    return utils.jsonify({"graphics": graphics},
                         schema=flask.url_for("api_schema.graphics",
                                              _external=True))

@blueprint.route("/all")
def all():
    if not flask.g.am_admin:
        flask.abort(http.client.FORBIDDEN)
    graphics = []
    for iuid, title, owner, modified in get_graphics_all():
        graphics.append({"title": title,
                         "href": flask.url_for("api_graphic.serve",
                                               iuid=iuid,
                                               _external=True),
                         "owner": owner,
                         "modified": modified})
    return utils.jsonify({"graphics": graphics},
                         schema=flask.url_for("api_schema.graphics",
                                              _external=True))

schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Graphics resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "graphics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "href": {"type": "string", "format": "uri"},
                    "modified": {"type": "string", "format": "date-time"},
                    "owner": {"type": "string"}
                },
                "required": ["title", "href", "modified"],
                "additionalProperties": False
            }
        }
    },
    "required": ["$id", "timestamp", "graphics"],
    "additionalProperties": False
}
