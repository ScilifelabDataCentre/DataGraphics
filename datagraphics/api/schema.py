"JSON Schema API endpoints."

import flask

from datagraphics import utils
from datagraphics.api import root as root_schema

blueprint = flask.Blueprint("api_schema", __name__)


@blueprint.route("")
def schema():
    "Map of available JSON schemas."
    return flask.jsonify(
        {"$id": flask.request.url,
         "title": schema.__doc__,
         "schemas": {
             "root": {"href": flask.url_for("api_schema.root", _external=True),
                      "title": root_schema.schema["title"]}}
        })

@blueprint.route("root")
def root():
    "JSON schema for root API."
    return utils.jsonify(root_schema.schema)
