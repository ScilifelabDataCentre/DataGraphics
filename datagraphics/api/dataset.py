"Dataset API endpoints."

import io
import http.client

import flask
from flask_cors import cross_origin

from datagraphics.dataset import (DatasetSaver,
                                  get_dataset,
                                  allow_view,
                                  allow_edit,
                                  possible_delete,
                                  allow_delete)
from datagraphics import utils
from datagraphics import constants

blueprint = flask.Blueprint("api_dataset", __name__)

@blueprint.route("/", methods=["POST"])
def create():
    "Create an empty dataset."
    if not flask.g.current_user:
        flask.abort(http.client.FORBIDDEN)
    data = flask.request.get_json()
    try:
        with DatasetSaver() as saver:
            saver.set_title(data.get("title"))
            saver.set_description(data.get("description"))
            saver.set_public(False)
    except ValueError:
        flask.abort(http.client.BAD_REQUEST)
    return flask.jsonify(utils.get_json(**saver.doc))

@blueprint.route("/<iuid:iuid>", methods=["GET", "DELETE"])
def serve(iuid):
    "Return dataset information, or delete the dataset."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)

    if utils.http_GET():
        if not allow_view(dataset):
            flask.abort(http.client.FORBIDDEN)
        result = utils.get_json(**dataset)
        atts = result.pop("_attachments", None)
        if atts:
            result["content"] = {
                "csv": {"href": flask.url_for("api_dataset.content",
                                              iuid=dataset["_id"],
                                              ext="csv",
                                              _external=True),
                        "size": atts["data.csv"]["length"]},
                "json": {"href": flask.url_for("api_dataset.content",
                                               iuid=dataset["_id"],
                                               ext="json",
                                               _external=True),
                         "size": atts["data.json"]["length"]}
            }
        return flask.jsonify(result)

    elif utils.http_DELETE():
        if not possible_delete(dataset):
            flask.abort(http.client.FORBIDDEN)
        if not allow_delete(dataset):
            flask.abort(http.client.FORBIDDEN)
        flask.g.db.delete(dataset)
        for log in utils.get_logs(dataset["_id"], cleanup=False):
            flask.g.db.delete(log)
        return "", http.client.NO_CONTENT

@blueprint.route("/<iuid:iuid>.<ext>", methods=["GET", "PUT"])
@cross_origin()
def content(iuid, ext):
    "Fetch or update the content of the dataset as JSON or CSV file."
    try:
        dataset = get_dataset(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)

    if utils.http_GET():
        if not allow_view(dataset):
            flask.abort(http.client.FORBIDDEN)
        if not dataset.get("_attachments", None):
            return "", http.client.NO_CONTENT
        if ext == "json":
            outfile = flask.g.db.get_attachment(dataset, "data.json")
            response = flask.make_response(outfile.read())
            response.headers.set("Content-Type", constants.JSON_MIMETYPE)
        elif ext == "csv":
            outfile = flask.g.db.get_attachment(dataset, "data.csv")
            response = flask.make_response(outfile.read())
            response.headers.set("Content-Type", constants.CSV_MIMETYPE)
        else:
            flask.abort(http.client.NOT_FOUND)
        return response

    elif utils.http_PUT():
        if not allow_edit(dataset):
            flask.abort(http.client.FORBIDDEN)
        if ext == "json":
            content_type = constants.JSON_MIMETYPE
        elif ext == "csv":
            content_type = constants.CSV_MIMETYPE
        else:
            flask.abort(http.client.NOT_FOUND)
        try:
            with DatasetSaver(dataset) as saver:
                saver.set_data(infile=io.BytesIO(flask.request.data),
                               content_type=content_type)
        except ValueError as error:
            flask.abort(http.client.BAD_REQUEST)
        return "", http.client.NO_CONTENT
