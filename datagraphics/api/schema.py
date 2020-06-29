"JSON Schema for API resources."

import flask

from datagraphics import utils
from datagraphics.api import root as api_root
from datagraphics.api import about as api_about

blueprint = flask.Blueprint("api_schema", __name__)


@blueprint.route("")
def schema():
    "Map of available JSON schemas."
    return utils.jsonify(
        {"title": schema.__doc__,
         "schemas": {
             "root": {"href": flask.url_for("api_schema.root", _external=True),
                      "title": api_root.schema["title"]},
             "about": {"href": flask.url_for("api_schema.about", _external=True),
                       "title": api_about.schema["title"]}}
        })

@blueprint.route("root")
def root():
    "JSON schema for root API."
    return utils.jsonify(api_root.schema)

@blueprint.route("about")
def about():
    "JSON schema for about API."
    return utils.jsonify(api_about.schema)
