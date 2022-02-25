"API Graphic resource."

import http.client

import flask
import flask_cors

import datagraphics.dataset
from datagraphics.graphic import (
    GraphicSaver,
    get_graphic,
    allow_view,
    allow_edit,
    allow_delete,
)
from datagraphics import constants
from datagraphics import utils
from datagraphics.api import schema_definitions

blueprint = flask.Blueprint("api_graphic", __name__)


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
            saver.set_public(data.get("public"))
            saver.set_dataset(dataset)
            saver.set_specification(data.get("specification"))
    except ValueError as error:
        return str(error), http.client.BAD_REQUEST
    graphic = saver.doc
    graphic["$id"] = flask.url_for(
        "api_graphic.serve", iuid=graphic["_id"], _external=True
    )
    set_links(graphic)
    return utils.jsonify(
        graphic, schema=flask.url_for("api_schema.graphic", _external=True)
    )


@blueprint.route("/<iuid:iuid>", methods=["GET", "POST", "DELETE"])
@flask_cors.cross_origin(methods=["GET"])
def serve(iuid):
    "Return graphic information, update it, or delete it."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)

    if utils.http_GET():
        if not allow_view(graphic):
            flask.abort(http.client.FORBIDDEN)
        set_links(graphic)
        return utils.jsonify(
            graphic, schema=flask.url_for("api_schema.graphic", _external=True)
        )

    elif utils.http_POST(csrf=False):
        if not allow_edit(graphic):
            flask.abort(http.client.FORBIDDEN)
        try:
            data = flask.request.get_json()
            with GraphicSaver(graphic) as saver:
                try:
                    saver.set_title(data["title"])
                except KeyError:
                    pass
                try:
                    saver.set_description(data["description"])
                except KeyError:
                    pass
                try:
                    saver.set_public(data["public"])
                except KeyError:
                    pass
                try:
                    saver.set_specification(data["specification"])
                except KeyError:
                    pass
        except ValueError as error:
            return str(error), http.client.BAD_REQUEST
        graphic = saver.doc
        set_links(graphic)
        return utils.jsonify(
            graphic, schema=flask.url_for("api_schema.graphic", _external=True)
        )

    elif utils.http_DELETE():
        if not allow_delete(graphic):
            flask.abort(http.client.FORBIDDEN)
        flask.g.db.delete(graphic)
        for log in utils.get_logs(graphic["_id"], cleanup=False):
            flask.g.db.delete(log)
        return "", http.client.NO_CONTENT


@blueprint.route("/<iuid:iuid>/logs")
@flask_cors.cross_origin(methods=["GET"])
def logs(iuid):
    "Return all log entries for the given graphic."
    try:
        graphic = get_graphic(iuid)
    except ValueError as error:
        flask.abort(http.client.NOT_FOUND)
    if not allow_view(graphic):
        flask.abort(http.client.FORBIDDEN)
    entity = {
        "type": "graphic",
        "iuid": iuid,
        "href": flask.url_for("api_graphic.serve", iuid=iuid, _external=True),
    }
    return utils.jsonify(
        {"entity": entity, "logs": utils.get_logs(graphic["_id"])},
        schema=flask.url_for("api_schema.logs", _external=True),
    )


def set_links(graphic):
    "Set the links in the dataset."
    # Convert 'owner' to an object with a link to the user account.
    graphic["owner"] = {
        "username": graphic["owner"],
        "href": flask.url_for(
            "api_user.serve", username=graphic["owner"], _external=True
        ),
    }
    # Convert dataset IUID to href and IUID.
    dataset = datagraphics.dataset.get_dataset(graphic["dataset"])
    if datagraphics.dataset.allow_view(dataset):
        graphic["dataset"] = {
            "title": dataset["title"],
            "modified": dataset["modified"],
            "iuid": dataset["_id"],
            "href": flask.url_for(
                "api_dataset.serve", iuid=dataset["_id"], _external=True
            ),
        }
    else:
        graphic["dataset"] = None
    # Add link to logs.
    graphic["logs"] = {
        "href": flask.url_for(".logs", iuid=graphic["_id"], _external=True)
    }


schema = {
    "$schema": constants.JSON_SCHEMA_URL,
    "title": "JSON Schema for API Graphic resource.",
    "type": "object",
    "properties": {
        "$id": {"type": "string", "format": "uri"},
        "timestamp": {"type": "string", "format": "date-time"},
        "iuid": {"type": "string", "pattern": "^[0-9a-f]{32,32}$"},
        "created": {"type": "string", "format": "date-time"},
        "modified": {"type": "string", "format": "date-time"},
        "owner": schema_definitions.user,
        "title": {"type": "string"},
        "description": {"type": "string"},
        "public": {"type": "boolean"},
        "dataset": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "iuid": {"type": "string", "pattern": "^[0-9a-f]{32,32}$"},
                        "modified": {"type": "string", "format": "date-time"},
                        "href": {"type": "string", "format": "uri"},
                    },
                    "required": ["title", "iuid", "modified", "href"],
                    "additionalProperties": False,
                },
                {"type": "null"},
            ]
        },
        "specification": {"type": "object"},
        "error": {"type": ["null", "string"]},
        "logs": schema_definitions.logs_link,
    },
    "required": [
        "$id",
        "timestamp",
        "iuid",
        "created",
        "modified",
        "owner",
        "title",
        "description",
        "public",
        "dataset",
        "specification",
        "error",
        "logs",
    ],
    "additionalProperties": False,
}
