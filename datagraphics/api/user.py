"User API endpoints."

import http.client

import flask
from flask_cors import CORS

import datagraphics.user
from datagraphics import utils

blueprint = flask.Blueprint("api_user", __name__)

CORS(blueprint, supports_credentials=True)

@blueprint.route("/")
def all():
    "Information about all users."
    if not flask.g.am_admin:
        flask.abort(http.client.FORBIDDEN)
    users = [get_user_basic(u) for u in datagraphics.user.get_users()]
    return utils.jsonify({"users": users})

@blueprint.route("/<name:username>")
def display(username):
    "Information about the given user."
    user = datagraphics.user.get_user(username=username)
    if not user:
        flask.abort(http.client.NOT_FOUND)
    if not datagraphics.user.am_admin_or_self(user):
        flask.abort(http.client.FORBIDDEN)
    user.pop("password", None)
    user.pop("apikey", None)
    user["logs"] = {"href": flask.url_for(".logs", 
                                          username=user["username"],
                                          _external=True)}
    return utils.jsonify(user)

@blueprint.route("/<name:username>/logs")
def logs(username):
    "Return all log entries for the given user."
    user = datagraphics.user.get_user(username=username)
    if not user:
        flask.abort(http.client.NOT_FOUND)
    # XXX Use 'allow' function
    if not datagraphics.user.am_admin_or_self(user):
        flask.abort(http.client.FORBIDDEN)
    return utils.jsonify({"user": get_user_basic(user),
                          "logs": utils.get_logs(user["_id"])})

def get_user_basic(user):
    "Return the basic JSON data for a user."
    return {"username": user["username"],
            "href": flask.url_for(".display",
                                  username=user["username"],
                                  _external=True)}
