import http.client

import flask

import datagraphics.datasets
import datagraphics.user
from datagraphics import utils

blueprint = flask.Blueprint("api_datasets", __name__)

@blueprint.route("/public")
def public():
    datasets = []
    for iuid, title, modified in datagraphics.datasets.get_datasets_public():
        datasets.append({"title": title,
                         "href": flask.url_for("api_dataset.serve",
                                               iuid=iuid,
                                               _external=True),
                         "modified": modified})
    return flask.jsonify(utils.get_json(datasets=datasets))

@blueprint.route("/user/<username>")
def user(username):
    if not datagraphics.user.am_admin_or_self(username=username):
        flask.abort(http.client.FORBIDDEN)
    datasets = []
    for iuid, title, modified in datagraphics.datasets.get_datasets_owner(username):
        datasets.append({"title": title,
                         "href": flask.url_for("api_dataset.serve",
                                               iuid=iuid,
                                               _external=True),
                         "modified": modified})
    return flask.jsonify(utils.get_json(datasets=datasets))
