import http.client

import flask

from datagraphics.datasets import (get_datasets_public,
                                   get_datasets_all,
                                   get_datasets_owner)
import datagraphics.user
from datagraphics import utils

blueprint = flask.Blueprint("api_datasets", __name__)

@blueprint.route("/public")
def public():
    datasets = []
    for dataset in get_datasets_public(full=True):
        datasets.append({"title": dataset["title"],
                         "href": flask.url_for("api_dataset.serve",
                                               iuid=dataset["_id"],
                                               _external=True),
                         "owner": dataset["owner"],
                         "modified": dataset["modified"]})
    return flask.jsonify(utils.get_json(datasets=datasets))

@blueprint.route("/user/<username>")
def user(username):
    if not datagraphics.user.am_admin_or_self(username=username):
        flask.abort(http.client.FORBIDDEN)
    datasets = []
    for iuid, title, modified in get_datasets_owner(username):
        datasets.append({"title": title,
                         "href": flask.url_for("api_dataset.serve",
                                               iuid=iuid,
                                               _external=True),
                         "modified": modified})
    return flask.jsonify(utils.get_json(datasets=datasets))

@blueprint.route("/all")
def all():
    if not flask.g.am_admin:
        flask.abort(http.client.FORBIDDEN)
    datasets = []
    for iuid, title, owner, modified in get_datasets_all():
        datasets.append({"title": title,
                         "href": flask.url_for("api_dataset.serve",
                                               iuid=iuid,
                                               _external=True),
                         "owner": owner,
                         "modified": modified})
    return flask.jsonify(utils.get_json(datasets=datasets))
