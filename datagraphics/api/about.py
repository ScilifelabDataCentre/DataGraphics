"API About resources."

import flask
from flask_cors import CORS

import datagraphics.about
from datagraphics import constants
from datagraphics import utils
from datagraphics.api import schema_definitions

blueprint = flask.Blueprint("api_about", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("/software")
def software():
    "API About: Information about the system software and versions."
    result = {"title": __doc__,
              "software": [{"name": s[0], "version": s[1], "href": s[2]}
                           for s in datagraphics.about.get_software()]}
    url = flask.url_for("api_schema.about", _external=True)
    return utils.jsonify(result, schema_url=url)

schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API About resources.",
    "definitions": {
        "link": schema_definitions.link,
    },
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "title": {"type": "string"},
        "software": {
            "type": "array",
            "items": {
                "object": {
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "href": {"type": "string", "format": "uri"}
                    },
                    "required": ["name", "version", "href"],
                    "additionalProperties": False
                }
            }
        }
    },
    "required": ["$id", "timestamp", "title"]
}
