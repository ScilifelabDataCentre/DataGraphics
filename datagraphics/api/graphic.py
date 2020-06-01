"Graphic API endpoints."

import http.client

import flask
from flask_cors import CORS

import datagraphics.dataset
from datagraphics.graphic import (GraphicSaver,
                                  get_graphic,
                                  allow_view,
                                  allow_edit,
                                  allow_delete)
from datagraphics import utils
from datagraphics import constants

blueprint = flask.Blueprint("api_graphic", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("/", methods=["POST"])
def create():
    "Create a graphic."
    if not flask.g.current_user:
        flask.abort(http.client.FORBIDDEN)
    data = flask.request.get_json()
    try:
        dataset = datagraphics.dataset.get_dataset(data.get("dataset"))
        if not datagraphics.dataset.allow_view(dataset):
            raise ValueError("View access to dataset not allowed.")
        with GraphicSaver() as saver:
            saver.set_title(data.get("title"))
            saver.set_description(data.get("description"))
            saver.set_public(False)
            saver.set_dataset(dataset)
            saver.set_specification(data.get("specification"))
    except ValueError as error:
        return str(error), http.client.BAD_REQUEST
    return flask.jsonify(utils.get_json(**saver.doc))

@blueprint.route("/<iuid:iuid>", methods=["GET", "POST", "DELETE"])
def serve(iuid):
    "Return graphic information, update it, or delete it."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)

    if utils.http_GET():
        if not allow_view(graphic):
            flask.abort(http.client.FORBIDDEN)
        result = utils.get_json(**graphic)
        result["dataset"] = {"iuid": result["dataset"],
                             "href": flask.url_for("api_dataset.serve",
                                                   iuid=result["dataset"],
                                                   _external=True)}
        return flask.jsonify(result)

    elif utils.http_POST(csrf=False):
        if not allow_edit(graphic):
            flask.abort(http.client.FORBIDDEN)
        try:
            data = flask.request.get_json()
            with GraphicsSaver(graphic) as saver:
                try:
                    saver.set_title(data["title"])
                except KeyError:
                    pass
                try:
                    saver.set_title(data["description"])
                except KeyError:
                    pass
                try:
                    saver.set_title(data["public"])
                except KeyError:
                    pass
                try:
                    saver.set_specification(data["specification"])
                except KeyError:
                    pass
        except ValueError as error:
            return str(error), http.client.BAD_REQUEST
        return flask.jsonify(utils.get_json(**saver.doc))

    elif utils.http_DELETE():
        if not allow_delete(graphic):
            flask.abort(http.client.FORBIDDEN)
        flask.g.db.delete(graphic)
        for log in utils.get_logs(graphic["_id"], cleanup=False):
            flask.g.db.delete(log)
        return "", http.client.NO_CONTENT
