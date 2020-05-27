"Dataset API endpoints."

import http.client

import flask

import datagraphics.dataset
from datagraphics import utils

blueprint = flask.Blueprint("api_dataset", __name__)

@blueprint.route("/<iuid:iuid>")
def serve(iuid):
    try:
        dataset = datagraphics.dataset.get_dataset(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)
    if not datagraphics.dataset.allow_view(dataset):
        flask.abort(http.client.FORBIDDEN)
    result = utils.get_json(**dataset)
    atts = result.pop("_attachments", None)
    return flask.jsonify(result)
