"About API endpoints."

import flask

import datagraphics.about
from datagraphics import utils

blueprint = flask.Blueprint("api_about", __name__)

@blueprint.route("/software")
def software():
    "Return information about the system software and versions."
    result = [{"name": s[0], "version": s[1], "href": s[2]}
              for s in datagraphics.about.get_software()]
    return flask.jsonify(utils.get_json(software=result))
