"About API endpoints."

import flask
from flask_cors import CORS

from datagraphics import constants
from datagraphics import utils

from datagraphics.datasets import (count_datasets_public,
                                    count_datasets_owner,
                                    count_datasets_all)

blueprint = flask.Blueprint("api", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("")
def root():
    "API root; links to other resources."
    items = {"version": constants.VERSION}
    items["about"] = {"software": {"href": flask.url_for("api_about.software",
                                                         _external=True)}
    }
    items["datasets"] = {"public": 
                         {"count": count_datasets_public(),
                          "href": flask.url_for("api_datasets.public",
                                                 _external=True)}}
    items["graphics"] = []
    if flask.g.current_user:
        username = flask.g.current_user["username"]
        items["datasets"]["owner"] = {"count": count_datasets_owner(username),
                                      "href": flask.url_for("api_datasets.user",
                                                            username=username,
                                                            _external=True)}
        items["user"] = {
            "username": flask.g.current_user["username"],
            "href": flask.url_for("api_user.display",
                                  username=flask.g.current_user["username"],
                                  _external=True)
        }
    if flask.g.am_admin:
        items["datasets"]["all"] = {"count": count_datasets_all(),
                                    "href": flask.url_for("api_datasets.all",
                                                          _external=True)}
        items["users"] = {
            "href": flask.url_for("api_user.all", _external=True)
        }
    return flask.jsonify(utils.get_json(**items))
