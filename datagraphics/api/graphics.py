"API Graphics resource."

import http.client

import flask
import flask_cors

from datagraphics.graphics import (get_graphics_public,
                                   get_graphics_all,
                                   get_graphics_owner,
                                   get_graphics_editor)
import datagraphics.user
from datagraphics import constants
from datagraphics import utils
from datagraphics.api import schema_definitions

blueprint = flask.Blueprint("api_graphics", __name__)

@blueprint.route("/public")
@flask_cors.cross_origin(methods=["GET"])
def public():
    graphics = []
    for graphic in get_graphics_public(full=True):
        graphics.append({"href": flask.url_for("api_graphic.serve",
                                               iuid=graphic["_id"],
                                               _external=True),
                         "title": graphic["title"],
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
        graphics.append({"href": flask.url_for("api_graphic.serve",
                                               iuid=iuid,
                                               _external=True),
                         "title": title,
                         "modified": modified})
    return utils.jsonify({"graphics": graphics},
                         schema=flask.url_for("api_schema.graphics",
                                              _external=True))

@blueprint.route("/user/<username>/editor")
def editor(username):
    "Get the graphics which the given user is editor of."
    if not datagraphics.user.am_admin_or_self(username=username):
        flask.abort(http.client.FORBIDDEN)
    graphics = []
    for iuid, title, modified in get_graphics_editor(username):
        graphics.append({"href": flask.url_for("api_graphic.serve",
                                               iuid=iuid,
                                               _external=True),
                         "title": title,
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
        graphics.append({"href": flask.url_for("api_graphic.serve",
                                               iuid=iuid,
                                               _external=True),
                         "title": title,
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
            "items": schema_definitions.link
        }
    },
    "required": ["$id", "timestamp", "graphics"],
    "additionalProperties": False
}
