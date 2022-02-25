"API Root resource."

import flask
import flask_cors

from datagraphics import constants
from datagraphics import utils
from datagraphics.api import schema_definitions

from datagraphics.datasets import (
    count_datasets_public,
    count_datasets_owner,
    count_datasets_all,
)
from datagraphics.graphics import (
    count_graphics_public,
    count_graphics_owner,
    count_graphics_all,
)

blueprint = flask.Blueprint("api", __name__)


@blueprint.route("")
@flask_cors.cross_origin(methods=["GET"])
def root():
    "API Root; links to other resources."
    items = {
        "version": constants.VERSION,
        "title": __doc__,
        "schemas": {"href": flask.url_for("api_schema.all", _external=True)},
        "software": {"href": flask.url_for("api_about.software", _external=True)},
        "datasets": {
            "public": {
                "count": count_datasets_public(),
                "href": flask.url_for("api_datasets.public", _external=True),
            }
        },
        "graphics": {
            "public": {
                "count": count_graphics_public(),
                "href": flask.url_for("api_graphics.public", _external=True),
            }
        },
    }
    if flask.g.current_user:
        username = flask.g.current_user["username"]
        items["datasets"]["owner"] = {
            "count": count_datasets_owner(username),
            "href": flask.url_for(
                "api_datasets.user", username=username, _external=True
            ),
        }
        items["graphics"]["owner"] = {
            "count": count_graphics_owner(username),
            "href": flask.url_for(
                "api_graphics.user", username=username, _external=True
            ),
        }
        items["user"] = {
            "username": flask.g.current_user["username"],
            "href": flask.url_for(
                "api_user.serve",
                username=flask.g.current_user["username"],
                _external=True,
            ),
        }
    if flask.g.am_admin:
        items["datasets"]["all"] = {
            "count": count_datasets_all(),
            "href": flask.url_for("api_datasets.all", _external=True),
        }
        items["graphics"]["all"] = {
            "count": count_graphics_all(),
            "href": flask.url_for("api_graphics.all", _external=True),
        }
        items["users"] = {
            "all": {"href": flask.url_for("api_users.all", _external=True)}
        }
    return utils.jsonify(items, schema=flask.url_for("api_schema.root", _external=True))


schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Root resource.",
    "definitions": {
        "link": schema_definitions.link,
    },
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "title": {"type": "string"},
        "version": {"type": "string", "pattern": "^0\.[0-9]+\.[0-9]+$"},
        "schemas": {
            "title": "Link to list of the schema documents.",
            "$ref": "#/definitions/link",
        },
        "software": {
            "title": "Link to list of the software used.",
            "$ref": "#/definitions/link",
        },
        "datasets": {
            "title": "Links to collections of datasets.",
            "type": "object",
            "properties": {
                "all": {
                    "title": "Link to list of all datasets.",
                    "$ref": "#/definitions/link",
                },
                "owner": {
                    "title": "Link to list of datasets owned by the current user.",
                    "$ref": "#/definitions/link",
                },
                "public": {
                    "title": "Link to list of public datasets.",
                    "$ref": "#/definitions/link",
                },
            },
            "required": ["public"],
            "additionalProperties": False,
        },
        "graphics": {
            "title": "Links to collections of graphics.",
            "type": "object",
            "properties": {
                "all": {
                    "title": "Link to list of all graphics.",
                    "$ref": "#/definitions/link",
                },
                "owner": {
                    "title": "Link to list of graphics owned by the current user.",
                    "$ref": "#/definitions/link",
                },
                "public": {
                    "title": "Link to list of public graphics.",
                    "$ref": "#/definitions/link",
                },
            },
            "required": ["public"],
            "additionalProperties": False,
        },
        "users": {
            "title": "Links to collections of users.",
            "type": "object",
            "properties": {
                "all": {
                    "title": "Link to list of all users",
                    "$ref": "#/definitions/link",
                }
            },
            "required": ["all"],
            "additionalProperties": False,
        },
        "user": schema_definitions.user,
        "operations": schema_definitions.operations,
    },
    "required": [
        "$id",
        "timestamp",
        "title",
        "version",
        "schemas",
        "software",
        "datasets",
        "graphics",
    ],
    "additionalProperties": False,
}
