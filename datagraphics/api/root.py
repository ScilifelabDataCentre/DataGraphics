"About API endpoints."

import flask

from datagraphics import utils


blueprint = flask.Blueprint("api", __name__)

@blueprint.route("")
def root():
    "API root."
    items = {
        "about": {
            "software": {"href": utils.url_for("api_about.software")}
        }
    }
    if flask.g.current_user:
        items["user"] = {
            "username": flask.g.current_user["username"],
            "href": utils.url_for("api_user.display",
                                  username=flask.g.current_user["username"])
        }
    if flask.g.am_admin:
        items["users"] = {
            "href": utils.url_for("api_user.all")
        }
    return flask.jsonify(utils.get_json(**items))
